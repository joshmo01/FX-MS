"""
Pricing API Endpoints
Add this file to: app/api/pricing.py
"""
from decimal import Decimal
from typing import List, Optional
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from app.models.pricing import CustomerSegment, CurrencyCategory
from app.core.pricing_engine import get_pricing_engine, FXPricingEngine
from app.services.pricing_service import PricingService

# Import your existing FX rate service - adjust import path as needed
# from app.services.fx_provider import get_fx_rate_service, FXRateService

router = APIRouter(prefix="/api/v1/fx/pricing", tags=["FX Pricing"])


# ============================================
# Pydantic Models for API
# ============================================

class MarginBreakdownResponse(BaseModel):
    """Margin breakdown in response"""
    segment_base_bps: float
    tier_adjustment_bps: float
    currency_factor_bps: float
    negotiated_discount_bps: float


class PricedQuoteRequest(BaseModel):
    """Request for a priced FX quote"""
    source_currency: str = Field(..., min_length=3, max_length=3, description="Source currency code")
    target_currency: str = Field(..., min_length=3, max_length=3, description="Target currency code")
    amount: float = Field(..., gt=0, description="Amount in source currency")
    customer_id: str = Field(..., description="Customer identifier")
    segment: CustomerSegment = Field(default=CustomerSegment.RETAIL, description="Customer segment")
    direction: str = Field(default="SELL", pattern="^(BUY|SELL)$", description="Transaction direction")
    negotiated_discount_bps: int = Field(default=0, ge=0, description="Pre-negotiated discount in bps")
    client_reference: Optional[str] = Field(None, description="Client reference number")

    class Config:
        json_schema_extra = {
            "example": {
                "source_currency": "USD",
                "target_currency": "INR",
                "amount": 100000.00,
                "customer_id": "CUST-12345",
                "segment": "MID_MARKET",
                "direction": "SELL",
                "negotiated_discount_bps": 0
            }
        }


class PricedQuoteResponse(BaseModel):
    """Response with priced quote"""
    quote_id: str
    source_currency: str
    target_currency: str
    mid_rate: float
    customer_rate: float
    margin_bps: float
    margin_percent: float
    margin_breakdown: MarginBreakdownResponse
    source_amount: float
    target_amount: float
    segment: str
    amount_tier: str
    currency_category: str
    valid_until: datetime
    rate_type: str = "FIRM"


class SegmentConfigResponse(BaseModel):
    """Segment configuration response"""
    segment_id: str
    segment_name: str
    base_margin_bps: int
    min_margin_bps: int
    max_margin_bps: int
    volume_discount_eligible: bool
    negotiated_rates_allowed: bool


class AmountTierResponse(BaseModel):
    """Amount tier response"""
    tier_id: str
    tier_order: int
    min_amount: float
    max_amount: Optional[float]
    adjustment_bps: int
    description: str


class MarginInfoResponse(BaseModel):
    """Margin information for a currency pair"""
    currency_pair: str
    segment: str
    amount: float
    total_margin_bps: float
    margin_percent: float
    tier: str
    category: str
    breakdown: MarginBreakdownResponse


class MarginCalculateRequest(BaseModel):
    """Request to calculate margin"""
    base_currency: str = Field(..., min_length=3, max_length=3)
    quote_currency: str = Field(..., min_length=3, max_length=3)
    amount: float = Field(..., gt=0)
    segment: CustomerSegment = Field(default=CustomerSegment.RETAIL)
    negotiated_discount_bps: int = Field(default=0, ge=0)


# ============================================
# Dependency Injection
# ============================================


def get_pricing_service_dep() -> PricingService:
    """
    Dependency injection for pricing service.
    Integrated with Refinitiv FX Rate Service.
    """
    from app.services.fx_provider import get_fx_service
    fx_service = get_fx_service()
    return PricingService(fx_rate_service=fx_service)

# ============================================
# API Endpoints
# ============================================

@router.post("/quote", response_model=PricedQuoteResponse)
async def generate_priced_quote(
    request: PricedQuoteRequest,
    pricing_service: PricingService = Depends(get_pricing_service_dep)
):
    """
    Generate FX quote with customer-specific pricing.
    
    Applies:
    - Customer segment base margin (Institutional to Retail)
    - Transaction amount tier adjustment (volume discounts)
    - Currency pair liquidity factor (G10/Minor/Exotic/Restricted)
    - Negotiated customer discounts (if applicable)
    
    Returns a firm quote valid for 30 seconds.
    """
    try:
        quote = await pricing_service.get_priced_quote(
            source_currency=request.source_currency.upper(),
            target_currency=request.target_currency.upper(),
            amount=Decimal(str(request.amount)),
            customer_id=request.customer_id,
            segment=request.segment,
            direction=request.direction,
            negotiated_discount_bps=request.negotiated_discount_bps
        )
        
        return PricedQuoteResponse(
            quote_id=quote.quote_id,
            source_currency=quote.base_currency,
            target_currency=quote.quote_currency,
            mid_rate=float(quote.mid_rate),
            customer_rate=float(quote.customer_rate),
            margin_bps=float(quote.margin_bps),
            margin_percent=float(quote.margin_bps / 100),
            margin_breakdown=MarginBreakdownResponse(
                segment_base_bps=float(quote.margin_breakdown.segment_base_bps),
                tier_adjustment_bps=float(quote.margin_breakdown.tier_adjustment_bps),
                currency_factor_bps=float(quote.margin_breakdown.currency_factor_bps),
                negotiated_discount_bps=float(quote.margin_breakdown.negotiated_discount_bps)
            ),
            source_amount=float(quote.amount),
            target_amount=float(quote.converted_amount),
            segment=quote.segment.value,
            amount_tier=quote.amount_tier,
            currency_category=quote.currency_category.value,
            valid_until=quote.valid_until
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate quote: {str(e)}")


@router.get("/segments", response_model=List[SegmentConfigResponse])
async def get_segments(
    engine: FXPricingEngine = Depends(get_pricing_engine)
):
    """
    Get all customer segment configurations.
    
    Returns the 6 standard segments with their pricing parameters:
    - INSTITUTIONAL: Banks, hedge funds (2-20 bps)
    - LARGE_CORPORATE: MNCs, treasury (10-75 bps)
    - MID_MARKET: SMEs (40-150 bps)
    - SMALL_BUSINESS: Occasional users (100-250 bps)
    - RETAIL: Individual customers (200-500 bps)
    - PRIVATE_BANKING: HNW individuals (20-100 bps)
    """
    segments = engine.get_all_segments()
    return [
        SegmentConfigResponse(
            segment_id=s.segment_id.value,
            segment_name=s.segment_name,
            base_margin_bps=s.base_margin_bps,
            min_margin_bps=s.min_margin_bps,
            max_margin_bps=s.max_margin_bps,
            volume_discount_eligible=s.volume_discount_eligible,
            negotiated_rates_allowed=s.negotiated_rates_allowed
        )
        for s in segments
    ]


@router.get("/tiers", response_model=List[AmountTierResponse])
async def get_amount_tiers(
    engine: FXPricingEngine = Depends(get_pricing_engine)
):
    """
    Get all amount tier configurations.
    
    Returns the 6 standard tiers with volume adjustments:
    - TIER_1: < $10K (+50 bps premium)
    - TIER_2: $10K-$50K (+25 bps)
    - TIER_3: $50K-$100K (base rate)
    - TIER_4: $100K-$500K (-15 bps discount)
    - TIER_5: $500K-$1M (-25 bps)
    - TIER_6: > $1M (-40 bps)
    """
    tiers = engine.get_all_tiers()
    return [
        AmountTierResponse(
            tier_id=t.tier_id,
            tier_order=t.tier_order,
            min_amount=float(t.min_amount),
            max_amount=float(t.max_amount) if t.max_amount else None,
            adjustment_bps=t.margin_adjustment_bps,
            description=f"{'Premium' if t.margin_adjustment_bps > 0 else 'Discount' if t.margin_adjustment_bps < 0 else 'Base'}: {abs(t.margin_adjustment_bps)} bps"
        )
        for t in tiers
    ]


@router.get("/margin/{base_ccy}/{quote_ccy}", response_model=MarginInfoResponse)
async def get_margin_info(
    base_ccy: str,
    quote_ccy: str,
    segment: CustomerSegment = Query(default=CustomerSegment.RETAIL, description="Customer segment"),
    amount: float = Query(default=10000, gt=0, description="Transaction amount"),
    pricing_service: PricingService = Depends(get_pricing_service_dep)
):
    """
    Get margin information for a currency pair without generating a quote.
    
    Useful for:
    - Displaying indicative pricing to customers
    - Calculating expected costs before committing
    - Comparing pricing across segments
    """
    info = pricing_service.get_margin_info(
        base_currency=base_ccy.upper(),
        quote_currency=quote_ccy.upper(),
        amount=Decimal(str(amount)),
        segment=segment
    )
    
    return MarginInfoResponse(
        currency_pair=info["currency_pair"],
        segment=info["segment"],
        amount=info["amount"],
        total_margin_bps=info["total_margin_bps"],
        margin_percent=info["margin_percent"],
        tier=info["tier"],
        category=info["category"],
        breakdown=MarginBreakdownResponse(**info["breakdown"])
    )


@router.post("/margin/calculate", response_model=MarginInfoResponse)
async def calculate_margin(
    request: MarginCalculateRequest,
    pricing_service: PricingService = Depends(get_pricing_service_dep)
):
    """
    Calculate margin for a specific scenario.
    
    POST alternative to GET /margin/{base}/{quote} for complex queries.
    """
    info = pricing_service.get_margin_info(
        base_currency=request.base_currency.upper(),
        quote_currency=request.quote_currency.upper(),
        amount=Decimal(str(request.amount)),
        segment=request.segment
    )
    
    return MarginInfoResponse(
        currency_pair=info["currency_pair"],
        segment=info["segment"],
        amount=info["amount"],
        total_margin_bps=info["total_margin_bps"],
        margin_percent=info["margin_percent"],
        tier=info["tier"],
        category=info["category"],
        breakdown=MarginBreakdownResponse(**info["breakdown"])
    )


@router.get("/categories")
async def get_currency_categories():
    """
    Get currency category definitions.
    
    Returns the 4 liquidity categories and their markup ranges.
    """
    return {
        "categories": [
            {
                "category": "G10",
                "description": "Most liquid major currencies",
                "currencies": ["USD", "EUR", "JPY", "GBP", "CHF", "AUD", "NZD", "CAD", "SEK", "NOK"],
                "retail_markup_bps": 50,
                "corporate_markup_bps": 15,
                "institutional_markup_bps": 2
            },
            {
                "category": "MINOR",
                "description": "Less liquid developed market currencies",
                "currencies": ["SGD", "HKD", "DKK", "PLN", "CZK", "HUF"],
                "retail_markup_bps": 100,
                "corporate_markup_bps": 30,
                "institutional_markup_bps": 5
            },
            {
                "category": "EXOTIC",
                "description": "Emerging market currencies",
                "currencies": ["TRY", "ZAR", "MXN", "BRL", "ARS", "RUB"],
                "retail_markup_bps": 200,
                "corporate_markup_bps": 75,
                "institutional_markup_bps": 15
            },
            {
                "category": "RESTRICTED",
                "description": "Capital control currencies",
                "currencies": ["INR", "CNY", "KRW", "TWD", "PHP", "IDR", "MYR", "THB", "VND"],
                "retail_markup_bps": 300,
                "corporate_markup_bps": 100,
                "institutional_markup_bps": 25
            }
        ]
    }


@router.get("/health")
async def pricing_health():
    """Pricing service health check."""
    try:
        engine = get_pricing_engine()
        return {
            "status": "healthy",
            "service": "fx-pricing",
            "segments_loaded": len(engine.get_all_segments()),
            "tiers_loaded": len(engine.get_all_tiers()),
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        return {
            "status": "unhealthy",
            "service": "fx-pricing",
            "error": str(e)
        }
