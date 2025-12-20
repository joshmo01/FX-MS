"""
FX Pricing Engine - Core pricing calculation logic
Add this file to: app/core/pricing_engine.py
"""
import json
import logging
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional, Dict, List
from uuid import uuid4

from app.models.pricing import (
    CustomerSegment, CurrencyCategory, SegmentConfig, 
    AmountTier, MarginBreakdown, PricedQuote, RateType
)

logger = logging.getLogger(__name__)

# Data directory - adjust path as needed
DATA_DIR = Path(__file__).parent.parent / "data"


class FXPricingEngine:
    """
    Core FX Pricing Engine implementing bank-standard pricing logic.
    
    Pricing Formula:
    Customer Rate = Mid-Market Rate × (1 ± Total Margin)
    
    Where Total Margin = Base Margin + Tier Adjustment + Currency Factor - Discounts
    
    Applies:
    - Customer segmentation (6 tiers from Institutional to Retail)
    - Transaction amount tiers (volume-based discounts)
    - Currency pair factors (G10/Minor/Exotic/Restricted)
    - Negotiated customer discounts
    """
    
    def __init__(self, quote_validity_seconds: int = 30):
        self.quote_validity_seconds = quote_validity_seconds
        self._segments: Dict[str, SegmentConfig] = {}
        self._tiers: List[AmountTier] = []
        self._currency_categories: Dict[str, CurrencyCategory] = {}
        self._category_markups: Dict[CurrencyCategory, Dict[str, int]] = {}
        self._load_configuration()
    
    def _load_configuration(self):
        """Load pricing configuration from JSON files."""
        try:
            # Load segments
            segments_file = DATA_DIR / "segments.json"
            if segments_file.exists():
                with open(segments_file) as f:
                    data = json.load(f)
                    for seg in data["segments"]:
                        self._segments[seg["segment_id"]] = SegmentConfig(
                            segment_id=CustomerSegment(seg["segment_id"]),
                            segment_name=seg["segment_name"],
                            base_margin_bps=seg["base_margin_bps"],
                            min_margin_bps=seg["min_margin_bps"],
                            max_margin_bps=seg["max_margin_bps"],
                            volume_discount_eligible=seg["volume_discount_eligible"],
                            negotiated_rates_allowed=seg.get("negotiated_rates_allowed", False)
                        )
            else:
                self._load_default_segments()
            
            # Load tiers
            tiers_file = DATA_DIR / "tiers.json"
            if tiers_file.exists():
                with open(tiers_file) as f:
                    data = json.load(f)
                    for tier in data["tiers"]:
                        self._tiers.append(AmountTier(
                            tier_id=tier["tier_id"],
                            tier_order=tier["tier_order"],
                            min_amount=Decimal(str(tier["min_amount"])),
                            max_amount=Decimal(str(tier["max_amount"])) if tier["max_amount"] else None,
                            margin_adjustment_bps=tier["margin_adjustment_bps"]
                        ))
                    self._tiers.sort(key=lambda t: t.tier_order)
            else:
                self._load_default_tiers()
            
            # Load currency markups
            markups_file = DATA_DIR / "currency_markups.json"
            if markups_file.exists():
                with open(markups_file) as f:
                    data = json.load(f)
                    for category_name, config in data["categories"].items():
                        category = CurrencyCategory(category_name)
                        for ccy in config["currencies"]:
                            self._currency_categories[ccy] = category
                        self._category_markups[category] = {
                            "retail": config["retail_markup_bps"],
                            "corporate": config["corporate_markup_bps"],
                            "institutional": config["institutional_markup_bps"]
                        }
            else:
                self._load_default_currency_markups()
            
            logger.info(f"Pricing engine loaded: {len(self._segments)} segments, "
                       f"{len(self._tiers)} tiers, {len(self._currency_categories)} currencies")
                       
        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            self._load_defaults()
    
    def _load_defaults(self):
        """Load default configuration if JSON files not found."""
        self._load_default_segments()
        self._load_default_tiers()
        self._load_default_currency_markups()
    
    def _load_default_segments(self):
        """Load default segment configuration."""
        defaults = [
            ("INSTITUTIONAL", "Institutional", 5, 2, 20, True, True),
            ("LARGE_CORPORATE", "Large Corporate", 25, 10, 75, True, True),
            ("MID_MARKET", "Mid-Market", 75, 40, 150, True, False),
            ("SMALL_BUSINESS", "Small Business", 150, 100, 250, False, False),
            ("RETAIL", "Retail", 300, 200, 500, False, False),
            ("PRIVATE_BANKING", "Private Banking", 50, 20, 100, True, True),
        ]
        for seg_id, name, base, min_m, max_m, vol_elig, neg_allowed in defaults:
            self._segments[seg_id] = SegmentConfig(
                segment_id=CustomerSegment(seg_id),
                segment_name=name,
                base_margin_bps=base,
                min_margin_bps=min_m,
                max_margin_bps=max_m,
                volume_discount_eligible=vol_elig,
                negotiated_rates_allowed=neg_allowed
            )
    
    def _load_default_tiers(self):
        """Load default tier configuration."""
        defaults = [
            ("TIER_1", 1, 0, 10000, 50),
            ("TIER_2", 2, 10000, 50000, 25),
            ("TIER_3", 3, 50000, 100000, 0),
            ("TIER_4", 4, 100000, 500000, -15),
            ("TIER_5", 5, 500000, 1000000, -25),
            ("TIER_6", 6, 1000000, None, -40),
        ]
        self._tiers = [
            AmountTier(
                tier_id=tid, tier_order=order,
                min_amount=Decimal(str(min_a)),
                max_amount=Decimal(str(max_a)) if max_a else None,
                margin_adjustment_bps=adj
            )
            for tid, order, min_a, max_a, adj in defaults
        ]
    
    def _load_default_currency_markups(self):
        """Load default currency markup configuration."""
        categories = {
            CurrencyCategory.G10: {
                "currencies": ["USD", "EUR", "JPY", "GBP", "CHF", "AUD", "NZD", "CAD", "SEK", "NOK"],
                "retail": 50, "corporate": 15, "institutional": 2
            },
            CurrencyCategory.MINOR: {
                "currencies": ["SGD", "HKD", "DKK", "PLN", "CZK", "HUF"],
                "retail": 100, "corporate": 30, "institutional": 5
            },
            CurrencyCategory.EXOTIC: {
                "currencies": ["TRY", "ZAR", "MXN", "BRL", "ARS", "RUB"],
                "retail": 200, "corporate": 75, "institutional": 15
            },
            CurrencyCategory.RESTRICTED: {
                "currencies": ["INR", "CNY", "KRW", "TWD", "PHP", "IDR", "MYR", "THB", "VND"],
                "retail": 300, "corporate": 100, "institutional": 25
            }
        }
        for category, config in categories.items():
            for ccy in config["currencies"]:
                self._currency_categories[ccy] = category
            self._category_markups[category] = {
                "retail": config["retail"],
                "corporate": config["corporate"],
                "institutional": config["institutional"]
            }
    
    def get_segment_config(self, segment: CustomerSegment) -> SegmentConfig:
        """Get configuration for a customer segment."""
        return self._segments[segment.value]
    
    def get_all_segments(self) -> List[SegmentConfig]:
        """Get all segment configurations."""
        return list(self._segments.values())
    
    def get_all_tiers(self) -> List[AmountTier]:
        """Get all amount tier configurations."""
        return self._tiers
    
    def get_amount_tier(self, amount: Decimal) -> AmountTier:
        """Determine which amount tier applies based on transaction size."""
        for tier in self._tiers:
            if tier.max_amount is None:
                if amount >= tier.min_amount:
                    return tier
            elif tier.min_amount <= amount < tier.max_amount:
                return tier
        return self._tiers[0]
    
    def get_currency_category(self, base: str, quote: str) -> CurrencyCategory:
        """
        Determine currency pair category.
        Uses the less liquid currency to determine category.
        Priority: RESTRICTED > EXOTIC > MINOR > G10
        """
        base_cat = self._currency_categories.get(base.upper(), CurrencyCategory.MINOR)
        quote_cat = self._currency_categories.get(quote.upper(), CurrencyCategory.MINOR)
        
        # Return the higher (less liquid) category
        category_order = [
            CurrencyCategory.G10, 
            CurrencyCategory.MINOR, 
            CurrencyCategory.EXOTIC, 
            CurrencyCategory.RESTRICTED
        ]
        
        base_idx = category_order.index(base_cat) if base_cat in category_order else 1
        quote_idx = category_order.index(quote_cat) if quote_cat in category_order else 1
        
        return category_order[max(base_idx, quote_idx)]
    
    def get_currency_markup(
        self, 
        category: CurrencyCategory, 
        segment: CustomerSegment
    ) -> int:
        """Get currency markup based on category and customer segment."""
        markup = self._category_markups.get(
            category, 
            self._category_markups[CurrencyCategory.MINOR]
        )
        
        if segment == CustomerSegment.INSTITUTIONAL:
            return markup["institutional"]
        elif segment in (CustomerSegment.LARGE_CORPORATE, CustomerSegment.MID_MARKET,
                        CustomerSegment.PRIVATE_BANKING):
            return markup["corporate"]
        return markup["retail"]
    
    def calculate_margin(
        self,
        segment: CustomerSegment,
        amount: Decimal,
        base_currency: str,
        quote_currency: str,
        negotiated_discount_bps: int = 0
    ) -> tuple[Decimal, MarginBreakdown, AmountTier, CurrencyCategory]:
        """
        Calculate total margin with full breakdown.
        
        Args:
            segment: Customer segment
            amount: Transaction amount in base currency
            base_currency: Base currency code
            quote_currency: Quote currency code
            negotiated_discount_bps: Pre-negotiated discount in basis points
        
        Returns:
            Tuple of (total_margin_bps, breakdown, tier, category)
        """
        # 1. Get segment config
        config = self.get_segment_config(segment)
        base_margin = config.base_margin_bps
        
        # 2. Get amount tier adjustment (only if eligible)
        tier = self.get_amount_tier(amount)
        tier_adj = tier.margin_adjustment_bps if config.volume_discount_eligible else 0
        
        # 3. Get currency markup
        category = self.get_currency_category(base_currency, quote_currency)
        currency_markup = self.get_currency_markup(category, segment)
        
        # 4. Apply negotiated discount (only if allowed)
        discount = negotiated_discount_bps if config.negotiated_rates_allowed else 0
        
        # 5. Calculate total
        total = base_margin + tier_adj + currency_markup - discount
        
        # 6. Apply min/max constraints
        total = max(config.min_margin_bps, min(config.max_margin_bps, total))
        
        breakdown = MarginBreakdown(
            segment_base_bps=Decimal(base_margin),
            tier_adjustment_bps=Decimal(tier_adj),
            currency_factor_bps=Decimal(currency_markup),
            negotiated_discount_bps=Decimal(discount)
        )
        
        return Decimal(total), breakdown, tier, category
    
    def apply_margin_to_rate(
        self,
        mid_rate: Decimal,
        margin_bps: Decimal,
        direction: str
    ) -> Decimal:
        """
        Apply margin to mid-market rate based on direction.
        
        Args:
            mid_rate: Mid-market rate
            margin_bps: Margin in basis points
            direction: 'BUY' or 'SELL' (from customer perspective)
        
        Returns:
            Customer rate with margin applied
        """
        margin_decimal = margin_bps / Decimal("10000")
        
        if direction.upper() == "BUY":
            # Customer buying base currency = bank selling = add margin
            customer_rate = mid_rate * (1 + margin_decimal)
        else:
            # Customer selling base currency = bank buying = subtract margin
            customer_rate = mid_rate * (1 - margin_decimal)
        
        return customer_rate.quantize(Decimal("0.000001"), ROUND_HALF_UP)
    
    def generate_priced_quote(
        self,
        base_currency: str,
        quote_currency: str,
        amount: Decimal,
        mid_rate: Decimal,
        customer_id: str,
        segment: CustomerSegment,
        direction: str = "SELL",
        negotiated_discount_bps: int = 0
    ) -> PricedQuote:
        """
        Generate a fully priced FX quote.
        
        This is the main entry point - call this after getting mid_rate
        from the existing FX rate service.
        
        Args:
            base_currency: Base currency code (e.g., 'USD')
            quote_currency: Quote currency code (e.g., 'INR')
            amount: Amount in base currency
            mid_rate: Mid-market rate from rate provider
            customer_id: Customer identifier for audit
            segment: Customer segment for pricing
            direction: 'BUY' or 'SELL' from customer perspective
            negotiated_discount_bps: Pre-negotiated discount
        
        Returns:
            PricedQuote with all pricing details
        """
        # Calculate margin
        margin_bps, breakdown, tier, category = self.calculate_margin(
            segment=segment,
            amount=amount,
            base_currency=base_currency,
            quote_currency=quote_currency,
            negotiated_discount_bps=negotiated_discount_bps
        )
        
        # Apply margin to rate
        customer_rate = self.apply_margin_to_rate(mid_rate, margin_bps, direction)
        
        # Calculate converted amount
        converted_amount = (amount * customer_rate).quantize(Decimal("0.01"), ROUND_HALF_UP)
        
        now = datetime.now(timezone.utc)
        
        quote = PricedQuote(
            quote_id=f"PQ-{now.strftime('%Y%m%d%H%M%S')}-{str(uuid4())[:8].upper()}",
            base_currency=base_currency.upper(),
            quote_currency=quote_currency.upper(),
            mid_rate=mid_rate,
            customer_rate=customer_rate,
            margin_bps=margin_bps,
            margin_breakdown=breakdown,
            amount=amount,
            converted_amount=converted_amount,
            segment=segment,
            amount_tier=tier.tier_id,
            currency_category=category,
            valid_until=now + timedelta(seconds=self.quote_validity_seconds),
            rate_type=RateType.FIRM
        )
        
        logger.info(
            f"Quote: {quote.quote_id} | {customer_id} | {segment.value} | "
            f"{base_currency}/{quote_currency} | Amt: {amount} | "
            f"Margin: {margin_bps}bps | Rate: {customer_rate}"
        )
        
        return quote


# Singleton instance
_pricing_engine: Optional[FXPricingEngine] = None


def get_pricing_engine() -> FXPricingEngine:
    """Get or create the pricing engine singleton."""
    global _pricing_engine
    if _pricing_engine is None:
        _pricing_engine = FXPricingEngine()
    return _pricing_engine
