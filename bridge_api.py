"""
CBDC ↔ Stablecoin Bridge API

REST API endpoints for bridge operations between CBDCs and Stablecoins.
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from decimal import Decimal
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging

from ..services.cbdc_stable_bridge import get_bridge_engine, BridgeType, BridgeStatus

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/v1/fx/bridge", tags=["CBDC-Stablecoin Bridge"])


# =============================================================================
# Request/Response Models
# =============================================================================

class BridgeRouteRequest(BaseModel):
    """Request for bridge route recommendation"""
    source_asset: str = Field(..., description="Source asset code (e.g., e-INR, USDC)")
    source_type: str = Field(..., description="CBDC or STABLECOIN")
    target_asset: str = Field(..., description="Target asset code")
    target_type: str = Field(..., description="CBDC or STABLECOIN")
    amount: Decimal = Field(..., gt=0, description="Amount in source asset")
    preferred_network: Optional[str] = Field(None, description="Preferred blockchain network")
    max_slippage_bps: int = Field(50, ge=0, le=500, description="Max acceptable slippage in bps")
    require_regulated: bool = Field(True, description="Only return regulated routes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "source_asset": "e-INR",
                "source_type": "CBDC",
                "target_asset": "USDC",
                "target_type": "STABLECOIN",
                "amount": "1000000",
                "preferred_network": "ETHEREUM",
                "max_slippage_bps": 50,
                "require_regulated": True
            }
        }


class BridgeLegResponse(BaseModel):
    """Response model for a single bridge leg"""
    leg_id: str
    sequence: int
    from_asset: str
    from_type: str
    to_asset: str
    to_type: str
    provider: str
    protocol: str
    network: Optional[str]
    rate: str
    amount_in: str
    amount_out: str
    fee_bps: int
    gas_cost_usd: str
    settlement_seconds: int
    settlement_time_display: str
    requires_kyc: bool
    compliance_check: str
    description: str


class BridgeRouteResponse(BaseModel):
    """Response model for a bridge route"""
    route_id: str
    route_name: str
    bridge_type: str
    status: str
    legs: List[BridgeLegResponse]
    
    # Assets
    source_asset: str
    source_type: str
    source_amount: str
    target_asset: str
    target_type: str
    target_amount: str
    
    # Economics
    effective_rate: str
    total_fee_bps: int
    total_fee_display: str
    total_gas_usd: str
    slippage_tolerance_bps: int
    
    # Settlement
    total_settlement_seconds: int
    total_settlement_display: str
    settlement_finality: str
    
    # Scores
    liquidity_score: int
    counterparty_score: int
    smart_contract_score: int
    regulatory_score: int
    overall_score: float
    
    # Compliance
    kyc_required: bool
    travel_rule_applies: bool
    sanctions_check: bool
    jurisdictions: List[str]
    
    # Limits
    min_amount: str
    max_amount: str
    daily_limit: Optional[str]
    
    # Additional info
    warnings: List[str]
    benefits: List[str]
    is_recommended: bool = False


class BridgeRecommendationResponse(BaseModel):
    """Response with recommended route and alternatives"""
    request_id: str
    timestamp: str
    source_asset: str
    source_type: str
    target_asset: str
    target_type: str
    amount: str
    
    recommended_route: Optional[BridgeRouteResponse]
    alternative_routes: List[BridgeRouteResponse]
    
    total_routes_found: int
    conversion_type: str
    
    # Summary comparison
    comparison_summary: Dict[str, Any]


class SupportedPairsResponse(BaseModel):
    """Response with supported conversion pairs"""
    cbdc_to_stablecoin: List[str]
    stablecoin_to_cbdc: List[str]
    total_pairs: int


# =============================================================================
# Helper Functions
# =============================================================================

def format_settlement_time(seconds: int) -> str:
    """Convert seconds to human-readable time"""
    if seconds < 60:
        return f"{seconds} seconds"
    elif seconds < 3600:
        return f"{seconds // 60} minutes"
    elif seconds < 86400:
        hours = seconds // 3600
        mins = (seconds % 3600) // 60
        return f"{hours}h {mins}m" if mins else f"{hours} hours"
    else:
        days = seconds // 86400
        hours = (seconds % 86400) // 3600
        return f"{days}d {hours}h" if hours else f"{days} days"


def format_route_response(route, is_recommended: bool = False) -> BridgeRouteResponse:
    """Convert bridge route to API response"""
    legs = []
    for leg in route.legs:
        legs.append(BridgeLegResponse(
            leg_id=leg.leg_id,
            sequence=leg.sequence,
            from_asset=leg.from_asset,
            from_type=leg.from_type,
            to_asset=leg.to_asset,
            to_type=leg.to_type,
            provider=leg.provider,
            protocol=leg.protocol,
            network=leg.network,
            rate=str(leg.rate),
            amount_in=str(leg.amount_in),
            amount_out=str(leg.amount_out),
            fee_bps=leg.fee_bps,
            gas_cost_usd=str(leg.gas_cost_usd),
            settlement_seconds=leg.settlement_seconds,
            settlement_time_display=format_settlement_time(leg.settlement_seconds),
            requires_kyc=leg.requires_kyc,
            compliance_check=leg.compliance_check,
            description=leg.description
        ))
    
    return BridgeRouteResponse(
        route_id=route.route_id,
        route_name=route.route_name,
        bridge_type=route.bridge_type.value,
        status=route.status.value,
        legs=legs,
        source_asset=route.source_asset,
        source_type=route.source_type,
        source_amount=str(route.source_amount),
        target_asset=route.target_asset,
        target_type=route.target_type,
        target_amount=str(route.target_amount),
        effective_rate=str(route.effective_rate),
        total_fee_bps=route.total_fee_bps,
        total_fee_display=f"{route.total_fee_bps} bps ({route.total_fee_bps / 100:.2f}%)",
        total_gas_usd=str(route.total_gas_usd),
        slippage_tolerance_bps=route.slippage_tolerance_bps,
        total_settlement_seconds=route.total_settlement_seconds,
        total_settlement_display=format_settlement_time(route.total_settlement_seconds),
        settlement_finality=route.settlement_finality,
        liquidity_score=route.liquidity_score,
        counterparty_score=route.counterparty_score,
        smart_contract_score=route.smart_contract_score,
        regulatory_score=route.regulatory_score,
        overall_score=route.overall_score,
        kyc_required=route.kyc_required,
        travel_rule_applies=route.travel_rule_applies,
        sanctions_check=route.sanctions_check,
        jurisdictions=route.jurisdictions,
        min_amount=str(route.min_amount),
        max_amount=str(route.max_amount),
        daily_limit=str(route.daily_limit) if route.daily_limit else None,
        warnings=route.warnings,
        benefits=route.benefits,
        is_recommended=is_recommended
    )


# =============================================================================
# API Endpoints
# =============================================================================

@router.post("/route", response_model=BridgeRecommendationResponse)
async def get_bridge_route(request: BridgeRouteRequest):
    """
    Get optimal bridge route between CBDC and Stablecoin
    
    Returns recommended route with alternatives, sorted by overall score.
    Supports both CBDC→Stablecoin and Stablecoin→CBDC conversions.
    """
    try:
        engine = get_bridge_engine()
        
        # Determine conversion direction
        if request.source_type == "CBDC" and request.target_type == "STABLECOIN":
            routes = await engine.get_cbdc_to_stable_routes(
                cbdc=request.source_asset,
                stablecoin=request.target_asset,
                amount=request.amount,
                preferred_network=request.preferred_network,
                max_slippage_bps=request.max_slippage_bps,
                require_regulated=request.require_regulated
            )
            conversion_type = "CBDC_TO_STABLECOIN"
        
        elif request.source_type == "STABLECOIN" and request.target_type == "CBDC":
            routes = await engine.get_stable_to_cbdc_routes(
                stablecoin=request.source_asset,
                cbdc=request.target_asset,
                amount=request.amount,
                source_network=request.preferred_network,
                require_regulated=request.require_regulated
            )
            conversion_type = "STABLECOIN_TO_CBDC"
        
        else:
            raise HTTPException(
                status_code=400,
                detail="Invalid conversion type. Must be CBDC↔STABLECOIN"
            )
        
        if not routes:
            raise HTTPException(
                status_code=404,
                detail=f"No routes found for {request.source_asset} → {request.target_asset}"
            )
        
        # Build comparison summary
        comparison = {
            "lowest_fee_route": min(routes, key=lambda r: r.total_fee_bps).route_name,
            "lowest_fee_bps": min(r.total_fee_bps for r in routes),
            "fastest_route": min(routes, key=lambda r: r.total_settlement_seconds).route_name,
            "fastest_settlement": format_settlement_time(
                min(r.total_settlement_seconds for r in routes)
            ),
            "highest_regulatory_score": max(r.regulatory_score for r in routes),
            "route_types": list(set(r.bridge_type.value for r in routes))
        }
        
        import uuid
        return BridgeRecommendationResponse(
            request_id=str(uuid.uuid4()),
            timestamp=datetime.utcnow().isoformat() + "Z",
            source_asset=request.source_asset,
            source_type=request.source_type,
            target_asset=request.target_asset,
            target_type=request.target_type,
            amount=str(request.amount),
            recommended_route=format_route_response(routes[0], is_recommended=True),
            alternative_routes=[format_route_response(r) for r in routes[1:5]],
            total_routes_found=len(routes),
            conversion_type=conversion_type,
            comparison_summary=comparison
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Bridge route error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/cbdc-to-stable/{cbdc}/{stablecoin}")
async def quick_cbdc_to_stable(
    cbdc: str,
    stablecoin: str,
    amount: Decimal = Query(..., gt=0),
    network: Optional[str] = None
):
    """
    Quick lookup for CBDC → Stablecoin conversion
    
    Example: /api/v1/fx/bridge/cbdc-to-stable/e-INR/USDC?amount=1000000
    """
    request = BridgeRouteRequest(
        source_asset=cbdc,
        source_type="CBDC",
        target_asset=stablecoin,
        target_type="STABLECOIN",
        amount=amount,
        preferred_network=network
    )
    return await get_bridge_route(request)


@router.get("/stable-to-cbdc/{stablecoin}/{cbdc}")
async def quick_stable_to_cbdc(
    stablecoin: str,
    cbdc: str,
    amount: Decimal = Query(..., gt=0),
    network: Optional[str] = None
):
    """
    Quick lookup for Stablecoin → CBDC conversion
    
    Example: /api/v1/fx/bridge/stable-to-cbdc/USDC/e-INR?amount=100000
    """
    request = BridgeRouteRequest(
        source_asset=stablecoin,
        source_type="STABLECOIN",
        target_asset=cbdc,
        target_type="CBDC",
        amount=amount,
        preferred_network=network
    )
    return await get_bridge_route(request)


@router.get("/supported-pairs", response_model=SupportedPairsResponse)
async def get_supported_pairs():
    """Get all supported CBDC ↔ Stablecoin conversion pairs"""
    engine = get_bridge_engine()
    pairs = engine.get_supported_pairs()
    
    return SupportedPairsResponse(
        cbdc_to_stablecoin=pairs["cbdc_to_stablecoin"],
        stablecoin_to_cbdc=pairs["stablecoin_to_cbdc"],
        total_pairs=len(pairs["cbdc_to_stablecoin"]) + len(pairs["stablecoin_to_cbdc"])
    )


@router.get("/bridge-types")
async def get_bridge_types():
    """Get available bridge types with descriptions"""
    return {
        "bridge_types": [
            {
                "type": "FIAT_INTERMEDIARY",
                "name": "Fiat Intermediary Bridge",
                "description": "Standard path through fiat currency (CBDC → Fiat → Stablecoin)",
                "status": "ACTIVE",
                "typical_fee_bps": "25-65",
                "typical_settlement": "1-24 hours",
                "regulated": True
            },
            {
                "type": "CEX_BRIDGE",
                "name": "Centralized Exchange Bridge",
                "description": "Route through centralized exchange (Coinbase, Kraken)",
                "status": "ACTIVE",
                "typical_fee_bps": "50-75",
                "typical_settlement": "2-4 hours",
                "regulated": True
            },
            {
                "type": "HYBRID_MBRIDGE",
                "name": "mBridge Hybrid",
                "description": "Combine mBridge CBDC transfer with stablecoin on/off ramp",
                "status": "PILOT",
                "typical_fee_bps": "35-50",
                "typical_settlement": "1-2 hours",
                "regulated": True,
                "note": "Only for mBridge participant CBDCs"
            },
            {
                "type": "DEX_BRIDGE",
                "name": "Decentralized Exchange Bridge",
                "description": "Route through DEX (Uniswap, Curve) - requires token versions",
                "status": "EXPERIMENTAL",
                "typical_fee_bps": "5-30",
                "typical_settlement": "1-5 minutes",
                "regulated": False
            },
            {
                "type": "ATOMIC_SWAP",
                "name": "Atomic Swap",
                "description": "Direct trustless swap using HTLC (future capability)",
                "status": "EXPERIMENTAL",
                "typical_fee_bps": "5-10",
                "typical_settlement": "5-15 minutes",
                "regulated": False
            }
        ]
    }


@router.get("/providers")
async def get_bridge_providers():
    """Get available bridge providers"""
    engine = get_bridge_engine()
    return {"providers": engine.bridge_providers}


@router.get("/liquidity-pools")
async def get_liquidity_pools():
    """Get DeFi liquidity pool data for stablecoin swaps"""
    engine = get_bridge_engine()
    return {"liquidity_pools": engine.liquidity_pools}


@router.get("/compliance-matrix")
async def get_compliance_matrix():
    """Get compliance requirements by bridge type"""
    return {
        "compliance_matrix": {
            "FIAT_INTERMEDIARY": {
                "kyc_level": "FULL_KYC",
                "travel_rule": True,
                "sanctions_screening": True,
                "aml_checks": True,
                "reporting": "Automatic to regulators",
                "jurisdictions": "Source + Target"
            },
            "CEX_BRIDGE": {
                "kyc_level": "EXCHANGE_KYC",
                "travel_rule": True,
                "sanctions_screening": True,
                "aml_checks": True,
                "reporting": "Exchange-level",
                "jurisdictions": "Exchange jurisdiction"
            },
            "HYBRID_MBRIDGE": {
                "kyc_level": "CENTRAL_BANK_VALIDATED",
                "travel_rule": False,
                "sanctions_screening": True,
                "aml_checks": True,
                "reporting": "Central bank level",
                "jurisdictions": "mBridge participants"
            },
            "DEX_BRIDGE": {
                "kyc_level": "NONE",
                "travel_rule": False,
                "sanctions_screening": False,
                "aml_checks": False,
                "reporting": "None",
                "jurisdictions": "N/A",
                "warning": "Not suitable for regulated entities"
            },
            "ATOMIC_SWAP": {
                "kyc_level": "NONE",
                "travel_rule": False,
                "sanctions_screening": False,
                "aml_checks": False,
                "reporting": "None",
                "jurisdictions": "N/A",
                "warning": "Experimental - regulatory status unclear"
            }
        }
    }


@router.get("/health")
async def bridge_health_check():
    """Health check for bridge service"""
    try:
        engine = get_bridge_engine()
        pairs = engine.get_supported_pairs()
        
        return {
            "status": "healthy",
            "service": "CBDC-Stablecoin Bridge",
            "version": "1.0.0",
            "supported_cbdcs": len(engine.digital_currencies.get("cbdc", {})),
            "supported_stablecoins": len(engine.digital_currencies.get("stablecoins", {})),
            "total_pairs": len(pairs["cbdc_to_stablecoin"]) + len(pairs["stablecoin_to_cbdc"]),
            "bridge_providers": len(engine.bridge_providers),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
