"""
Multi-Rail FX Routing API

REST API endpoints for multi-rail routing (Fiat + CBDC + Stablecoin).
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Query
from typing import Optional

from app.models.multi_rail_models import (
    MultiRailRoutingRequest,
    MultiRailRoutingResponse,
    CurrencyType,
    RailPreference,
    BlockchainNetwork,
)
from app.services.multi_rail_engine import get_multi_rail_engine, MultiRailRoutingEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fx/multi-rail", tags=["Multi-Rail Routing"])


def get_engine() -> MultiRailRoutingEngine:
    """Dependency to get multi-rail engine"""
    return get_multi_rail_engine()


# =============================================================================
# Multi-Rail Routing Endpoints
# =============================================================================

@router.post(
    "/route",
    response_model=MultiRailRoutingResponse,
    summary="Get Multi-Rail Route Recommendation",
    description="""
    Get intelligent routing recommendation across all available rails:
    
    **Rails Evaluated:**
    - **Fiat**: Traditional SWIFT, local payment systems
    - **CBDC**: Domestic (e-₹, e-CNY) and cross-border (mBridge)
    - **Stablecoin**: USDC, USDT, EURC via various networks
    - **Hybrid**: Fiat→CBDC, Fiat→Stablecoin→Fiat combinations
    
    **Rail Preferences:**
    - `AUTO`: Best overall route
    - `CBDC_PREFERRED`: Prefer CBDC rails when available
    - `STABLECOIN_PREFERRED`: Prefer stablecoin for cost optimization
    - `FIAT_PREFERRED`: Traditional fiat rails
    - `FASTEST`: Prioritize settlement speed
    - `LOWEST_COST`: Minimize total fees
    
    **Example Paths:**
    - USD → INR (Fiat direct)
    - USD → e-INR (Fiat to CBDC)
    - CNY → AED via mBridge (CBDC cross-border)
    - USD → USDC → SGD (Stablecoin bridge)
    """
)
async def get_multi_rail_route(
    request: MultiRailRoutingRequest,
    engine: MultiRailRoutingEngine = Depends(get_engine)
) -> MultiRailRoutingResponse:
    """
    Get optimal route across Fiat, CBDC, and Stablecoin rails.
    """
    try:
        result = await engine.get_multi_rail_route(request)
        logger.info(
            f"Multi-rail routing: {request.source_currency} → {request.target_currency}, "
            f"Recommended: {result.recommended_route.route_name}"
        )
        return result
    
    except ValueError as e:
        logger.warning(f"Multi-rail routing error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Multi-rail routing error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="Unable to process routing request")


@router.get(
    "/compare/{source}/{target}",
    summary="Quick Route Comparison",
    description="Quick comparison of all available rails for a currency pair."
)
async def quick_compare(
    source: str,
    target: str,
    amount: float = Query(default=10000, gt=0),
    engine: MultiRailRoutingEngine = Depends(get_engine)
):
    """
    Quick comparison of routes for a currency pair.
    """
    from decimal import Decimal
    
    request = MultiRailRoutingRequest(
        source_currency=source.upper(),
        target_currency=target.upper(),
        source_amount=Decimal(str(amount)),
        rail_preference=RailPreference.AUTO
    )
    
    try:
        result = await engine.get_multi_rail_route(request)
        
        return {
            "currency_pair": f"{source.upper()}/{target.upper()}",
            "amount": amount,
            "rails_available": result.rails_evaluated,
            "comparison": {
                "fiat": {
                    "available": result.fiat_available,
                    "routes": len(result.fiat_routes),
                    "best_rate": float(result.fiat_routes[0].effective_rate) if result.fiat_routes else None,
                    "best_time_hours": result.fiat_routes[0].total_settlement_seconds / 3600 if result.fiat_routes else None
                },
                "cbdc": {
                    "available": result.cbdc_available,
                    "routes": len(result.cbdc_routes),
                    "best_rate": float(result.cbdc_routes[0].effective_rate) if result.cbdc_routes else None,
                    "best_time_seconds": result.cbdc_routes[0].total_settlement_seconds if result.cbdc_routes else None
                },
                "stablecoin": {
                    "available": result.stablecoin_available,
                    "routes": len(result.stablecoin_routes),
                    "best_rate": float(result.stablecoin_routes[0].effective_rate) if result.stablecoin_routes else None,
                    "best_time_hours": result.stablecoin_routes[0].total_settlement_seconds / 3600 if result.stablecoin_routes else None
                }
            },
            "recommended": {
                "route": result.recommended_route.route_name,
                "type": result.recommended_route.route_type,
                "rate": float(result.recommended_route.effective_rate),
                "target_amount": float(result.recommended_route.target_amount),
                "cost_bps": result.recommended_route.total_cost_bps,
                "settlement_seconds": result.recommended_route.total_settlement_seconds
            }
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Reference Data Endpoints
# =============================================================================

@router.get(
    "/cbdc",
    summary="List Available CBDCs",
    description="Get list of supported CBDCs with their configurations."
)
async def list_cbdc(engine: MultiRailRoutingEngine = Depends(get_engine)):
    """List all supported CBDCs."""
    cbdcs = []
    for code, info in engine.digital_currencies["cbdc"].items():
        cbdcs.append({
            "code": code,
            "name": info["name"],
            "issuer": info["issuer"],
            "country": info["country"],
            "fiat_currency": info["fiat_currency"],
            "status": info["status"],
            "is_active": info["is_active"],
            "cross_border": info.get("cross_border_enabled", False),
            "mbridge": info.get("mbridge_participant", False),
            "settlement_seconds": info.get("settlement_seconds", 5)
        })
    
    return {
        "cbdcs": cbdcs,
        "count": len(cbdcs),
        "mbridge_participants": [c["code"] for c in cbdcs if c["mbridge"]]
    }


@router.get(
    "/stablecoins",
    summary="List Available Stablecoins",
    description="Get list of supported stablecoins with their networks."
)
async def list_stablecoins(engine: MultiRailRoutingEngine = Depends(get_engine)):
    """List all supported stablecoins."""
    stables = []
    for code, info in engine.digital_currencies["stablecoins"].items():
        stables.append({
            "code": code,
            "name": info["name"],
            "issuer": info["issuer"],
            "pegged_currency": info["pegged_currency"],
            "is_active": info["is_active"],
            "regulatory_status": info.get("regulatory_status", "UNREGULATED"),
            "liquidity_score": info.get("liquidity_score", 0),
            "networks": [n["chain"] for n in info["networks"]],
            "market_cap_usd": info.get("market_cap_usd", 0)
        })
    
    return {
        "stablecoins": stables,
        "count": len(stables),
        "regulated": [s["code"] for s in stables if "REGULATED" in s["regulatory_status"]]
    }


@router.get(
    "/rails",
    summary="List Available Rails",
    description="Get list of all available payment/settlement rails."
)
async def list_rails(engine: MultiRailRoutingEngine = Depends(get_engine)):
    """List all available rails."""
    rails = []
    for rail_id, info in engine.digital_rails["digital_rails"].items():
        rails.append({
            "rail_id": rail_id,
            "name": info["name"],
            "type": info["type"],
            "is_active": info["is_active"],
            "settlement_type": info.get("settlement_type", "VARIABLE"),
            "avg_settlement_seconds": info.get("avg_settlement_seconds"),
            "description": info.get("description", "")
        })
    
    return {"rails": rails, "count": len(rails)}


@router.get(
    "/on-off-ramps",
    summary="List On/Off Ramp Providers",
    description="Get list of fiat on-ramp and off-ramp providers for stablecoins."
)
async def list_ramp_providers(engine: MultiRailRoutingEngine = Depends(get_engine)):
    """List on/off ramp providers."""
    providers = []
    for pid, info in engine.digital_rails["on_off_ramp_providers"].items():
        providers.append({
            "id": pid,
            "name": info["name"],
            "type": info["type"],
            "is_active": info["is_active"],
            "supported_stablecoins": info.get("supported_stablecoins", []),
            "supported_fiat": info.get("supported_fiat", []),
            "on_ramp_fee_bps": info["on_ramp"]["fee_bps"],
            "off_ramp_fee_bps": info["off_ramp"]["fee_bps"],
            "stp_enabled": info.get("stp_enabled", False)
        })
    
    return {"providers": providers, "count": len(providers)}


# =============================================================================
# Health Endpoint
# =============================================================================

@router.get("/health", summary="Multi-Rail Service Health Check")
async def health_check(engine: MultiRailRoutingEngine = Depends(get_engine)):
    """Check multi-rail service health."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "cbdc_supported": len(engine.digital_currencies["cbdc"]),
        "stablecoins_supported": len(engine.digital_currencies["stablecoins"]),
        "rails_configured": len(engine.digital_rails["digital_rails"]),
        "ramp_providers": len(engine.digital_rails["on_off_ramp_providers"])
    }
