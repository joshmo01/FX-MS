"""
FX Smart Routing API Router

REST API endpoints for smart routing recommendations.
"""
import logging
from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends

from app.models.routing_models import (
    SmartRoutingRequest,
    SmartRoutingResponse,
    CustomerContext,
    CustomerTier,
    RoutingObjective,
    Direction,
)
from app.services.smart_routing_engine import get_routing_engine, SmartRoutingEngine

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fx/routing", tags=["Smart Routing"])


def get_engine() -> SmartRoutingEngine:
    """Dependency to get routing engine"""
    return get_routing_engine()


# =============================================================================
# Smart Routing Endpoints
# =============================================================================

@router.post(
    "/recommend",
    response_model=SmartRoutingResponse,
    summary="Get Smart Route Recommendation",
    description="""
    Get intelligent routing recommendation for an FX transaction.
    
    **Factors Considered:**
    - Currency pair liquidity and availability
    - Treasury rates and position management
    - Multiple FX provider comparison
    - Triangulation opportunities
    - Customer tier and pricing
    - Volume-based discounts
    - Settlement speed requirements
    
    **Routing Objectives:**
    - `BEST_RATE`: Optimize for lowest cost
    - `OPTIMUM`: Balance of cost, speed, reliability
    - `FASTEST_EXECUTION`: Prioritize settlement speed
    - `MAX_STP`: Maximize straight-through processing
    """
)
async def get_smart_route(
    request: SmartRoutingRequest,
    engine: SmartRoutingEngine = Depends(get_engine)
) -> SmartRoutingResponse:
    """
    Get smart routing recommendation for FX transaction.
    """
    try:
        result = await engine.get_smart_route(request)
        logger.info(
            f"Smart routing completed: {request.source_currency}/{request.target_currency}, "
            f"Recommended: {result.recommended_route.provider_name if result.recommended_route else 'None'}"
        )
        return result
    
    except ValueError as e:
        logger.warning(f"Routing validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Routing error: {e}", exc_info=True)
        raise HTTPException(
            status_code=500,
            detail="Unable to process routing request"
        )


@router.post(
    "/compare",
    summary="Compare Routes Without Recommendation",
    description="Get all available routes without scoring/ranking for analysis."
)
async def compare_routes(
    request: SmartRoutingRequest,
    engine: SmartRoutingEngine = Depends(get_engine)
):
    """
    Compare all available routes without recommendation scoring.
    """
    try:
        result = await engine.get_smart_route(request)
        
        # Return all routes without ranking
        all_routes = [result.recommended_route] + result.alternative_routes if result.recommended_route else []
        
        return {
            "request_id": result.request_id,
            "currency_pair": f"{request.source_currency}/{request.target_currency}",
            "amount": float(request.amount),
            "routes_found": len(all_routes),
            "routes": [
                {
                    "provider": r.provider_name,
                    "rate": float(r.customer_rate),
                    "target_amount": float(r.target_amount),
                    "settlement_hours": r.settlement_hours,
                    "stp_enabled": r.stp_enabled,
                    "cost_breakdown": {k: float(v) for k, v in r.cost_breakdown.items()}
                }
                for r in all_routes
            ],
            "triangulation": {
                "available": result.triangulation.is_triangulated or result.triangulation.recommended,
                "bridge_currency": result.triangulation.bridge_currency,
                "potential_savings_bps": result.triangulation.savings_bps
            }
        }
    
    except Exception as e:
        logger.error(f"Compare routes error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))


# =============================================================================
# Reference Data Endpoints
# =============================================================================

@router.get(
    "/objectives",
    summary="List Routing Objectives",
    description="Get available routing objectives with their weight configurations."
)
async def list_objectives(engine: SmartRoutingEngine = Depends(get_engine)):
    """
    List all available routing objectives.
    """
    return {
        "objectives": engine.routing_config["routing_objectives"],
        "default": engine.routing_config["default_objective"]
    }


@router.get(
    "/providers",
    summary="List FX Providers",
    description="Get list of configured FX providers."
)
async def list_providers(engine: SmartRoutingEngine = Depends(get_engine)):
    """
    List all configured FX providers.
    """
    providers = []
    for pid, p in engine.providers_config["providers"].items():
        providers.append({
            "id": pid,
            "name": p["name"],
            "type": p["type"],
            "is_active": p["is_active"],
            "stp_enabled": p["capabilities"].get("stp_enabled", False),
            "reliability_score": p.get("reliability_score", 0),
            "settlement_hours": p.get("settlement_hours", 24),
            "supported_pairs": p["supported_pairs"]
        })
    
    return {"providers": providers, "count": len(providers)}


@router.get(
    "/customer-tiers",
    summary="List Customer Tiers",
    description="Get customer tier configurations and pricing rules."
)
async def list_customer_tiers(engine: SmartRoutingEngine = Depends(get_engine)):
    """
    List customer tier configurations.
    """
    tiers = []
    for tier_id, config in engine.customer_config["customer_tiers"].items():
        tiers.append({
            "id": tier_id,
            "name": config["name"],
            "description": config["description"],
            "markup_discount_pct": config["markup_discount_pct"],
            "spread_reduction_bps": config["spread_reduction_bps"],
            "max_transaction_usd": config["max_transaction_usd"],
            "stp_threshold_usd": config["stp_threshold_usd"],
            "providers_allowed": config["providers_allowed"]
        })
    
    return {"tiers": tiers}


@router.get(
    "/treasury/positions",
    summary="Get Treasury Positions",
    description="Get current treasury positions and rates."
)
async def get_treasury_positions(engine: SmartRoutingEngine = Depends(get_engine)):
    """
    Get treasury positions for all currency pairs.
    """
    positions = []
    for pair, info in engine.treasury_config["treasury_rates"].items():
        positions.append({
            "pair": pair,
            "position": info["position"],
            "mid_rate": info["mid"],
            "bid": info["bid"],
            "ask": info["ask"],
            "exposure_pct": (info["current_exposure_usd"] / info["max_exposure_usd"]) * 100,
            "max_exposure_usd": info["max_exposure_usd"]
        })
    
    return {"positions": positions, "timestamp": datetime.utcnow().isoformat()}


# =============================================================================
# Health Endpoint
# =============================================================================

@router.get("/health", summary="Smart Routing Health Check")
async def health_check(engine: SmartRoutingEngine = Depends(get_engine)):
    """Check smart routing service health."""
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat(),
        "providers_configured": len(engine.providers_config["providers"]),
        "providers_active": sum(
            1 for p in engine.providers_config["providers"].values() 
            if p["is_active"]
        ),
        "treasury_pairs": len(engine.treasury_config["treasury_rates"])
    }
