"""
FX Pricing API Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from decimal import Decimal
from datetime import datetime, timedelta
import uuid

router = APIRouter(prefix="/api/v1/fx/pricing", tags=["pricing"])

class QuoteRequest(BaseModel):
    source_currency: str
    target_currency: str
    amount: float
    customer_id: str
    segment: str = "MID_MARKET"
    direction: str = "SELL"
    negotiated_discount_bps: float = 0

class QuoteResponse(BaseModel):
    quote_id: str
    source_currency: str
    target_currency: str
    source_amount: float
    target_amount: float
    mid_rate: float
    customer_rate: float
    margin_bps: float
    margin_percent: float
    segment: str
    amount_tier: str
    currency_category: str
    direction: str
    valid_until: str
    margin_breakdown: dict

SEGMENTS = {
    "INSTITUTIONAL": {"base": 5, "min": 2, "max": 20, "vol_disc": True, "neg_rates": True},
    "LARGE_CORPORATE": {"base": 25, "min": 10, "max": 75, "vol_disc": True, "neg_rates": True},
    "MID_MARKET": {"base": 75, "min": 40, "max": 150, "vol_disc": True, "neg_rates": False},
    "SMALL_BUSINESS": {"base": 150, "min": 100, "max": 250, "vol_disc": False, "neg_rates": False},
    "RETAIL": {"base": 300, "min": 200, "max": 500, "vol_disc": False, "neg_rates": False},
    "PRIVATE_BANKING": {"base": 50, "min": 20, "max": 100, "vol_disc": True, "neg_rates": True},
}

TIERS = [
    {"id": "TIER_1", "min": 0, "max": 10000, "adj": 50},
    {"id": "TIER_2", "min": 10000, "max": 50000, "adj": 25},
    {"id": "TIER_3", "min": 50000, "max": 100000, "adj": 0},
    {"id": "TIER_4", "min": 100000, "max": 500000, "adj": -15},
    {"id": "TIER_5", "min": 500000, "max": 1000000, "adj": -25},
    {"id": "TIER_6", "min": 1000000, "max": None, "adj": -40},
]

CURRENCY_CATEGORIES = {
    "G10": {"currencies": ["USD", "EUR", "JPY", "GBP", "CHF", "AUD", "NZD", "CAD", "SEK", "NOK"], "retail": 50, "corp": 15, "inst": 2},
    "MINOR": {"currencies": ["SGD", "HKD", "DKK", "PLN", "CZK", "HUF"], "retail": 100, "corp": 30, "inst": 5},
    "EXOTIC": {"currencies": ["TRY", "ZAR", "MXN", "BRL", "ARS", "RUB"], "retail": 200, "corp": 75, "inst": 15},
    "RESTRICTED": {"currencies": ["INR", "CNY", "KRW", "TWD", "PHP", "IDR", "MYR", "THB", "VND"], "retail": 300, "corp": 100, "inst": 25},
}

MOCK_RATES = {
    "USDINR": 84.50, "EURINR": 89.20, "GBPINR": 106.50, "EURUSD": 1.0557,
    "GBPUSD": 1.2604, "USDJPY": 154.80, "USDAED": 3.6725, "USDSGD": 1.3450,
    "AUDINR": 54.20, "CADINR": 59.80, "CHFINR": 94.50, "USDCHF": 0.8950,
}

def get_mid_rate(source: str, target: str) -> float:
    pair = source + target
    if pair in MOCK_RATES:
        return MOCK_RATES[pair]
    reverse = target + source
    if reverse in MOCK_RATES:
        return 1 / MOCK_RATES[reverse]
    return 84.50

def get_tier(amount: float) -> dict:
    for tier in TIERS:
        if tier["max"] is None or amount < tier["max"]:
            return tier
    return TIERS[-1]

def get_currency_category(currency: str) -> tuple:
    for cat, data in CURRENCY_CATEGORIES.items():
        if currency in data["currencies"]:
            return cat, data
    return "RESTRICTED", CURRENCY_CATEGORIES["RESTRICTED"]

def get_currency_factor(segment: str, category_data: dict) -> int:
    if segment in ["INSTITUTIONAL"]:
        return category_data["inst"]
    elif segment in ["LARGE_CORPORATE", "MID_MARKET", "PRIVATE_BANKING"]:
        return category_data["corp"]
    return category_data["retail"]

@router.get("/health")
async def health():
    return {"status": "healthy", "service": "fx-pricing", "segments_loaded": len(SEGMENTS), "tiers_loaded": len(TIERS)}

@router.get("/segments")
async def get_segments():
    result = []
    for seg, data in SEGMENTS.items():
        result.append({
            "segment_id": seg,
            "segment_name": seg.replace("_", " ").title(),
            "base_margin_bps": data["base"],
            "min_margin_bps": data["min"],
            "max_margin_bps": data["max"],
            "volume_discount_eligible": data["vol_disc"],
            "negotiated_rates_allowed": data["neg_rates"],
        })
    return result

@router.get("/tiers")
async def get_tiers():
    result = []
    for t in TIERS:
        max_str = "Unlimited" if t["max"] is None else t["max"]
        result.append({
            "tier_id": t["id"],
            "min_amount": t["min"],
            "max_amount": t["max"],
            "adjustment_bps": t["adj"],
            "description": str(t["min"]) + " - " + str(max_str),
        })
    return result

@router.get("/categories")
async def get_categories():
    return CURRENCY_CATEGORIES

@router.post("/quote", response_model=QuoteResponse)
async def get_quote(request: QuoteRequest):
    if request.segment not in SEGMENTS:
        raise HTTPException(status_code=400, detail="Invalid segment: " + request.segment)
    
    seg_config = SEGMENTS[request.segment]
    mid_rate = get_mid_rate(request.source_currency, request.target_currency)
    tier = get_tier(request.amount)
    cat_name, cat_data = get_currency_category(request.target_currency)
    currency_factor = get_currency_factor(request.segment, cat_data)
    
    total_margin_bps = seg_config["base"] + tier["adj"] + currency_factor - request.negotiated_discount_bps
    total_margin_bps = max(seg_config["min"], min(seg_config["max"], total_margin_bps))
    margin_percent = total_margin_bps / 10000
    
    if request.direction == "SELL":
        customer_rate = mid_rate * (1 - margin_percent)
    else:
        customer_rate = mid_rate * (1 + margin_percent)
    
    target_amount = request.amount * customer_rate
    
    return QuoteResponse(
        quote_id="QT-" + uuid.uuid4().hex[:8].upper(),
        source_currency=request.source_currency,
        target_currency=request.target_currency,
        source_amount=request.amount,
        target_amount=round(target_amount, 2),
        mid_rate=mid_rate,
        customer_rate=round(customer_rate, 4),
        margin_bps=total_margin_bps,
        margin_percent=round(margin_percent * 100, 4),
        segment=request.segment,
        amount_tier=tier["id"],
        currency_category=cat_name,
        direction=request.direction,
        valid_until=(datetime.utcnow() + timedelta(seconds=30)).isoformat(),
        margin_breakdown={
            "segment_base_bps": seg_config["base"],
            "tier_adjustment_bps": tier["adj"],
            "currency_factor_bps": currency_factor,
            "negotiated_discount_bps": request.negotiated_discount_bps,
            "total_before_constraints": seg_config["base"] + tier["adj"] + currency_factor - request.negotiated_discount_bps,
        }
    )

@router.get("/margin/{base}/{quote}")
async def get_margin_info(base: str, quote: str, segment: str = "MID_MARKET", amount: float = 100000):
    if segment not in SEGMENTS:
        raise HTTPException(status_code=400, detail="Invalid segment: " + segment)
    
    seg_config = SEGMENTS[segment]
    tier = get_tier(amount)
    cat_name, cat_data = get_currency_category(quote)
    currency_factor = get_currency_factor(segment, cat_data)
    
    total = seg_config["base"] + tier["adj"] + currency_factor
    total = max(seg_config["min"], min(seg_config["max"], total))
    
    return {
        "currency_pair": base + "/" + quote,
        "segment": segment,
        "amount": amount,
        "tier": tier["id"],
        "currency_category": cat_name,
        "margin_bps": total,
        "margin_percent": round(total / 100, 4),
        "breakdown": {
            "segment_base": seg_config["base"],
            "tier_adjustment": tier["adj"],
            "currency_factor": currency_factor,
        }
    }
