"""
Pricing Service - Integration layer with existing FX rate service
Add this file to: app/services/pricing_service.py
"""
import logging
from decimal import Decimal
from typing import Optional

from app.core.pricing_engine import FXPricingEngine, get_pricing_engine
from app.models.pricing import CustomerSegment, PricedQuote

logger = logging.getLogger(__name__)


class PricingService:
    """
    Service layer that combines FX rates with pricing logic.
    
    This integrates with your existing FXRateService/fx_provider
    to add customer-specific pricing.
    """
    
    def __init__(
        self,
        fx_rate_service,  # Your existing FXRateService
        pricing_engine: Optional[FXPricingEngine] = None
    ):
        self.fx_rate_service = fx_rate_service
        self.pricing_engine = pricing_engine or get_pricing_engine()
    
    async def get_priced_quote(
        self,
        source_currency: str,
        target_currency: str,
        amount: Decimal,
        customer_id: str,
        segment: CustomerSegment,
        direction: str = "SELL",
        negotiated_discount_bps: int = 0
    ) -> PricedQuote:
        """
        Get a fully priced FX quote.
        
        1. Fetches mid-market rate from existing FX service
        2. Applies customer-specific pricing
        3. Returns priced quote
        
        Args:
            source_currency: Source/base currency code
            target_currency: Target/quote currency code
            amount: Amount in source currency
            customer_id: Customer identifier
            segment: Customer segment for pricing tier
            direction: 'BUY' or 'SELL' from customer perspective
            negotiated_discount_bps: Pre-negotiated discount
        
        Returns:
            PricedQuote with full pricing details
        """
        # Step 1: Get mid-rate from existing service
        # Adjust this based on your fx_provider.py response structure
        rate_response = await self.fx_rate_service.get_rate(
            source_currency, 
            target_currency
        )
        
        # Extract mid-rate - adjust based on your response structure
        # Your service might return: rate_response.mid, rate_response.mid_rate, 
        # rate_response["mid"], etc.
        if hasattr(rate_response, 'mid'):
            mid_rate = Decimal(str(rate_response.mid))
        elif hasattr(rate_response, 'mid_rate'):
            mid_rate = Decimal(str(rate_response.mid_rate))
        elif isinstance(rate_response, dict):
            mid_rate = Decimal(str(rate_response.get('mid') or rate_response.get('mid_rate')))
        else:
            # Fallback - calculate from bid/ask if available
            bid = Decimal(str(getattr(rate_response, 'bid', rate_response.get('bid', 0))))
            ask = Decimal(str(getattr(rate_response, 'ask', rate_response.get('ask', 0))))
            mid_rate = (bid + ask) / 2
        
        # Step 2: Generate priced quote
        priced_quote = self.pricing_engine.generate_priced_quote(
            base_currency=source_currency,
            quote_currency=target_currency,
            amount=amount,
            mid_rate=mid_rate,
            customer_id=customer_id,
            segment=segment,
            direction=direction,
            negotiated_discount_bps=negotiated_discount_bps
        )
        
        return priced_quote
    
    def get_margin_info(
        self,
        base_currency: str,
        quote_currency: str,
        amount: Decimal,
        segment: CustomerSegment
    ) -> dict:
        """
        Get margin information without generating a full quote.
        
        Useful for displaying pricing to customers before they commit.
        """
        margin_bps, breakdown, tier, category = self.pricing_engine.calculate_margin(
            segment=segment,
            amount=amount,
            base_currency=base_currency,
            quote_currency=quote_currency
        )
        
        return {
            "currency_pair": f"{base_currency.upper()}/{quote_currency.upper()}",
            "segment": segment.value,
            "amount": float(amount),
            "total_margin_bps": float(margin_bps),
            "margin_percent": float(margin_bps / 100),
            "tier": tier.tier_id,
            "category": category.value,
            "breakdown": {
                "segment_base_bps": float(breakdown.segment_base_bps),
                "tier_adjustment_bps": float(breakdown.tier_adjustment_bps),
                "currency_factor_bps": float(breakdown.currency_factor_bps),
                "negotiated_discount_bps": float(breakdown.negotiated_discount_bps)
            }
        }
    
    def calculate_margin_only(
        self,
        base_currency: str,
        quote_currency: str,
        amount: Decimal,
        segment: CustomerSegment,
        negotiated_discount_bps: int = 0
    ) -> Decimal:
        """
        Calculate just the margin in basis points.
        
        Quick method when you just need the margin number.
        """
        margin_bps, _, _, _ = self.pricing_engine.calculate_margin(
            segment=segment,
            amount=amount,
            base_currency=base_currency,
            quote_currency=quote_currency,
            negotiated_discount_bps=negotiated_discount_bps
        )
        return margin_bps
    
    def get_all_segments(self):
        """Get all available customer segments."""
        return self.pricing_engine.get_all_segments()
    
    def get_all_tiers(self):
        """Get all available amount tiers."""
        return self.pricing_engine.get_all_tiers()
