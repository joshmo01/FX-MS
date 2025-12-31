from fastapi import APIRouter, Query
from typing import Optional
from app.services.smart_routing_engine import routing_engine

router = APIRouter(prefix="/api/v1/fx/routing", tags=["Smart Routing"])

@router.get("/treasury-rates")
def get_treasury_rates():
    return routing_engine.treasury_rates

@router.get("/treasury-rates/{pair}")
def get_treasury_rate(pair: str):
    rate = routing_engine.get_treasury_rate(pair)
    if not rate:
        return {"error": f"Pair {pair} not found"}
    return {"pair": pair, "rate": rate}

@router.get("/customer-tiers")
def get_customer_tiers():
    return routing_engine.customer_tiers

@router.get("/customer-tiers/{tier_id}")
def get_customer_tier(tier_id: str):
    tier = routing_engine.get_customer_tier(tier_id)
    if not tier:
        return {"error": f"Tier {tier_id} not found"}
    return {"tier_id": tier_id, "tier": tier}

@router.get("/providers")
def get_providers():
    return routing_engine.fx_providers

@router.get("/providers/{provider_id}")
def get_provider(provider_id: str):
    provider = routing_engine.get_provider(provider_id)
    if not provider:
        return {"error": f"Provider {provider_id} not found"}
    return {"provider_id": provider_id, "provider": provider}

@router.get("/providers/{provider_id}/score")
def get_provider_score(provider_id: str, objective: str = "OPTIMUM"):
    score = routing_engine.score_provider(provider_id, objective)
    return {"provider_id": provider_id, "objective": objective, "score": score}

@router.get("/effective-rate/{pair}")
def get_effective_rate(
    pair: str,
    side: str = Query("BUY", regex="^(BUY|SELL)$"),
    amount: float = 10000,
    customer_tier: str = "RETAIL"
):
    return routing_engine.calculate_effective_rate(pair, side, amount, customer_tier)

@router.post("/recommend")
def recommend_route(
    pair: str,
    amount: float = 10000,
    side: str = "BUY",
    customer_tier: str = "RETAIL",
    objective: str = "OPTIMUM",
    customer_segment: Optional[str] = None,
    office: Optional[str] = None,
    region: Optional[str] = None
):
    return routing_engine.recommend_route(
        pair, amount, side, customer_tier, objective,
        customer_segment=customer_segment, office=office, region=region
    )

@router.get("/objectives")
def get_routing_objectives():
    return routing_engine.fx_providers.get("routing_objectives", {})
