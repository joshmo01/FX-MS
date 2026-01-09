"""
Universal Conversion API

REST API for the Universal Conversion Engine supporting all paths:
Fiat ↔ CBDC ↔ Stablecoin
"""
import logging
from datetime import datetime
from decimal import Decimal
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends, Query
from pydantic import BaseModel, Field
from enum import Enum

from app.services.universal_conversion_engine import (
    get_universal_engine,
    UniversalConversionEngine,
    ConversionType,
    ConversionRoute,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fx/universal", tags=["Universal Conversion"])


# =============================================================================
# Request/Response Models
# =============================================================================

class CurrencyTypeEnum(str, Enum):
    FIAT = "FIAT"
    CBDC = "CBDC"
    STABLECOIN = "STABLECOIN"


class UniversalConversionRequest(BaseModel):
    source_currency: str = Field(..., min_length=2, max_length=10, description="e.g., USD, e-INR, USDC")
    source_type: CurrencyTypeEnum
    target_currency: str = Field(..., min_length=2, max_length=10)
    target_type: CurrencyTypeEnum
    amount: float = Field(..., gt=0)
    preferred_network: Optional[str] = Field(default=None, description="For stablecoin: ETHEREUM, POLYGON, etc.")


class LegResponse(BaseModel):
    leg_number: int
    from_currency: str
    from_type: str
    to_currency: str
    to_type: str
    provider: str
    rate: float
    amount_in: float
    amount_out: float
    fee_bps: int
    settlement_seconds: int
    network: Optional[str] = None
    description: str


class RouteResponse(BaseModel):
    route_id: str
    route_name: str
    conversion_type: str
    route_method: str
    legs: List[LegResponse]
    source_currency: str
    source_type: str
    source_amount: float
    target_currency: str
    target_type: str
    target_amount: float
    effective_rate: float
    total_fee_bps: int
    total_fee_usd: float
    total_settlement_seconds: int
    settlement_human: str
    stp_enabled: bool
    cost_score: float
    speed_score: float
    reliability_score: float
    overall_score: float
    kyc_level: str
    travel_rule: bool
    regulated_path: bool
    warnings: List[str]


class UniversalConversionResponse(BaseModel):
    request_id: str
    timestamp: str
    conversion_type: str
    source: dict
    target: dict
    routes_found: int
    recommended_route: Optional[RouteResponse]
    all_routes: List[RouteResponse]
    comparison: dict


def get_engine() -> UniversalConversionEngine:
    return get_universal_engine()


def format_settlement(seconds: int) -> str:
    """Format seconds into human readable"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds // 60} minutes"
    elif seconds < 86400:
        hours = seconds / 3600
        return f"{hours:.1f} hours"
    else:
        days = seconds / 86400
        return f"{days:.1f} days"


def route_to_response(route: ConversionRoute) -> RouteResponse:
    """Convert internal route to API response"""
    return RouteResponse(
        route_id=route.route_id,
        route_name=route.route_name,
        conversion_type=route.conversion_type.value,
        route_method=route.route_method,
        legs=[LegResponse(
            leg_number=leg.leg_number,
            from_currency=leg.from_currency,
            from_type=leg.from_type,
            to_currency=leg.to_currency,
            to_type=leg.to_type,
            provider=leg.provider,
            rate=float(leg.rate),
            amount_in=float(leg.amount_in),
            amount_out=float(leg.amount_out),
            fee_bps=leg.fee_bps,
            settlement_seconds=leg.settlement_seconds,
            network=leg.network,
            description=leg.description
        ) for leg in route.legs],
        source_currency=route.source_currency,
        source_type=route.source_type,
        source_amount=float(route.source_amount),
        target_currency=route.target_currency,
        target_type=route.target_type,
        target_amount=float(route.target_amount),
        effective_rate=float(route.effective_rate),
        total_fee_bps=route.total_fee_bps,
        total_fee_usd=float(route.total_fee_usd),
        total_settlement_seconds=route.total_settlement_seconds,
        settlement_human=format_settlement(route.total_settlement_seconds),
        stp_enabled=route.stp_enabled,
        cost_score=route.cost_score,
        speed_score=route.speed_score,
        reliability_score=route.reliability_score,
        overall_score=route.overall_score,
        kyc_level=route.kyc_level,
        travel_rule=route.travel_rule,
        regulated_path=route.regulated_path,
        warnings=route.warnings or []
    )


# =============================================================================
# Endpoints
# =============================================================================

@router.post(
    "/convert",
    response_model=UniversalConversionResponse,
    summary="Universal Currency Conversion",
    description="""
    Find all possible conversion routes between ANY currency types:
    
    **Supported Conversions (9 types):**
    - FIAT ↔ FIAT (traditional FX)
    - FIAT ↔ CBDC (mint/redeem)
    - CBDC ↔ CBDC (mBridge or via fiat)
    - FIAT ↔ STABLECOIN (on/off ramp)
    - STABLECOIN ↔ STABLECOIN (DEX/CEX)
    - CBDC ↔ STABLECOIN (via fiat bridge)
    
    **Example Requests:**
    - USD (FIAT) → INR (FIAT)
    - USD (FIAT) → e-INR (CBDC)
    - e-CNY (CBDC) → e-AED (CBDC) via mBridge
    - USD (FIAT) → USDC (STABLECOIN)
    - USDC (STABLECOIN) → e-INR (CBDC)
    - e-INR (CBDC) → USDT (STABLECOIN)
    """
)
async def universal_convert(
    request: UniversalConversionRequest,
    engine: UniversalConversionEngine = Depends(get_engine)
) -> UniversalConversionResponse:
    """Find all conversion routes between source and target currencies."""
    try:
        routes = await engine.find_all_routes(
            source_currency=request.source_currency.upper(),
            source_type=request.source_type.value,
            target_currency=request.target_currency.upper(),
            target_type=request.target_type.value,
            amount=Decimal(str(request.amount))
        )
        
        if not routes:
            raise HTTPException(
                status_code=404,
                detail=f"No routes found for {request.source_currency} ({request.source_type}) → "
                       f"{request.target_currency} ({request.target_type})"
            )
        
        # Filter by network if specified
        if request.preferred_network:
            filtered = [r for r in routes if any(
                leg.network == request.preferred_network for leg in r.legs
            )]
            if filtered:
                routes = filtered
        
        route_responses = [route_to_response(r) for r in routes]
        
        # Build comparison
        comparison = {
            "best_rate": {
                "route_id": min(routes, key=lambda r: r.total_fee_bps).route_id,
                "fee_bps": min(r.total_fee_bps for r in routes)
            },
            "fastest": {
                "route_id": min(routes, key=lambda r: r.total_settlement_seconds).route_id,
                "seconds": min(r.total_settlement_seconds for r in routes)
            },
            "most_reliable": {
                "route_id": max(routes, key=lambda r: r.reliability_score).route_id,
                "score": max(r.reliability_score for r in routes)
            }
        }
        
        return UniversalConversionResponse(
            request_id=f"UC-{routes[0].route_id.split('-')[1] if routes else 'NONE'}",
            timestamp=datetime.utcnow().isoformat(),
            conversion_type=routes[0].conversion_type.value if routes else "UNKNOWN",
            source={
                "currency": request.source_currency.upper(),
                "type": request.source_type.value,
                "amount": request.amount
            },
            target={
                "currency": request.target_currency.upper(),
                "type": request.target_type.value
            },
            routes_found=len(routes),
            recommended_route=route_responses[0] if route_responses else None,
            all_routes=route_responses,
            comparison=comparison
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Universal conversion error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


@router.get(
    "/routes/{source_type}/{source}/{target_type}/{target}",
    summary="Quick Route Lookup",
    description="Quick lookup of routes between two currencies."
)
async def quick_routes(
    source_type: CurrencyTypeEnum,
    source: str,
    target_type: CurrencyTypeEnum,
    target: str,
    amount: float = Query(default=10000, gt=0),
    engine: UniversalConversionEngine = Depends(get_engine)
):
    """Quick route lookup."""
    routes = await engine.find_all_routes(
        source_currency=source.upper(),
        source_type=source_type.value,
        target_currency=target.upper(),
        target_type=target_type.value,
        amount=Decimal(str(amount))
    )
    
    return {
        "conversion": f"{source.upper()} ({source_type.value}) → {target.upper()} ({target_type.value})",
        "amount": amount,
        "routes_found": len(routes),
        "routes": [
            {
                "name": r.route_name,
                "method": r.route_method,
                "legs": len(r.legs),
                "target_amount": float(r.target_amount),
                "fee_bps": r.total_fee_bps,
                "settlement": format_settlement(r.total_settlement_seconds),
                "score": round(r.overall_score, 1)
            }
            for r in routes[:5]
        ]
    }


@router.get(
    "/conversion-types",
    summary="List All Conversion Types",
    description="Get all 9 supported conversion types with examples."
)
async def list_conversion_types():
    """List all supported conversion types."""
    return {
        "conversion_types": [
            {
                "type": "FIAT_TO_FIAT",
                "description": "Traditional FX conversion",
                "example": "USD → INR",
                "typical_fee_bps": "25-50",
                "typical_settlement": "4-48 hours"
            },
            {
                "type": "FIAT_TO_CBDC",
                "description": "Fiat to Central Bank Digital Currency",
                "example": "INR → e-INR, USD → e-INR",
                "typical_fee_bps": "0-20",
                "typical_settlement": "5 sec - 4 hours"
            },
            {
                "type": "CBDC_TO_FIAT",
                "description": "CBDC redemption to fiat",
                "example": "e-INR → INR, e-INR → USD",
                "typical_fee_bps": "0-20",
                "typical_settlement": "5 sec - 4 hours"
            },
            {
                "type": "CBDC_TO_CBDC",
                "description": "Cross-border CBDC (mBridge or via fiat)",
                "example": "e-CNY → e-AED",
                "typical_fee_bps": "13-25",
                "typical_settlement": "10 sec - 4 hours"
            },
            {
                "type": "FIAT_TO_STABLECOIN",
                "description": "Fiat to stablecoin on-ramp",
                "example": "USD → USDC",
                "typical_fee_bps": "50-100",
                "typical_settlement": "1-4 hours"
            },
            {
                "type": "STABLECOIN_TO_FIAT",
                "description": "Stablecoin off-ramp to fiat",
                "example": "USDC → USD",
                "typical_fee_bps": "50-100",
                "typical_settlement": "1-24 hours"
            },
            {
                "type": "STABLECOIN_TO_STABLECOIN",
                "description": "Stablecoin swap (DEX/CEX)",
                "example": "USDC → USDT",
                "typical_fee_bps": "20-30",
                "typical_settlement": "10 sec - 1 min"
            },
            {
                "type": "CBDC_TO_STABLECOIN",
                "description": "CBDC to stablecoin via fiat bridge",
                "example": "e-INR → USDC",
                "typical_fee_bps": "50-100",
                "typical_settlement": "1-5 hours"
            },
            {
                "type": "STABLECOIN_TO_CBDC",
                "description": "Stablecoin to CBDC via fiat bridge",
                "example": "USDC → e-INR",
                "typical_fee_bps": "50-100",
                "typical_settlement": "1-5 hours"
            }
        ],
        "total_types": 9
    }


@router.get(
    "/currencies",
    summary="List All Supported Currencies",
    description="Get all supported currencies by type."
)
async def list_currencies(engine: UniversalConversionEngine = Depends(get_engine)):
    """List all supported currencies."""
    return {
        "fiat": list(set(
            list(engine._cbdc_fiat_map.values()) +
            list(engine._stable_fiat_map.values()) +
            ["USD", "EUR", "GBP", "JPY"]
        )),
        "cbdc": list(engine._cbdc_fiat_map.keys()),
        "stablecoin": list(engine._stable_fiat_map.keys()),
        "mbridge_cbdc": list(engine._mbridge_cbdcs)
    }


@router.get(
    "/matrix",
    summary="Get Conversion Matrix",
    description="Get the full conversion capability matrix."
)
async def get_matrix(engine: UniversalConversionEngine = Depends(get_engine)):
    """Get conversion matrix."""
    return engine.conversion_matrix


@router.get("/health", summary="Service Health")
async def health(engine: UniversalConversionEngine = Depends(get_engine)):
    """Health check."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "supported_conversions": 9,
        "fiat_currencies": len(set(engine._cbdc_fiat_map.values())),
        "cbdc_currencies": len(engine._cbdc_fiat_map),
        "stablecoins": len(engine._stable_fiat_map)
    }
