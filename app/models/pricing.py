"""
FX Pricing Domain Models
Add this file to: app/models/pricing.py
"""
from enum import Enum
from decimal import Decimal
from dataclasses import dataclass
from typing import Optional
from datetime import datetime


class CustomerSegment(str, Enum):
    """Customer segmentation tiers - determines base margin"""
    INSTITUTIONAL = "INSTITUTIONAL"      # Banks, hedge funds, asset managers
    LARGE_CORPORATE = "LARGE_CORPORATE"  # MNCs, treasury operations
    MID_MARKET = "MID_MARKET"            # SMEs with regular FX needs
    SMALL_BUSINESS = "SMALL_BUSINESS"    # Occasional FX users
    RETAIL = "RETAIL"                    # Individual customers
    PRIVATE_BANKING = "PRIVATE_BANKING"  # HNW individuals


class CurrencyCategory(str, Enum):
    """Currency pair liquidity categories - determines currency markup"""
    G10 = "G10"              # Most liquid: USD, EUR, JPY, GBP, etc.
    MINOR = "MINOR"          # Less liquid G10 crosses
    EXOTIC = "EXOTIC"        # Emerging market currencies
    RESTRICTED = "RESTRICTED" # Capital control currencies (INR, CNY, etc.)


class QuoteSide(str, Enum):
    """Transaction direction from customer perspective"""
    BUY = "BUY"   # Customer buying base currency
    SELL = "SELL" # Customer selling base currency


class RateType(str, Enum):
    """Quote rate type"""
    FIRM = "FIRM"           # Executable rate
    INDICATIVE = "INDICATIVE" # Reference only


@dataclass
class SegmentConfig:
    """Customer segment pricing configuration"""
    segment_id: CustomerSegment
    segment_name: str
    base_margin_bps: int      # Base margin in basis points
    min_margin_bps: int       # Floor margin
    max_margin_bps: int       # Ceiling margin
    volume_discount_eligible: bool
    negotiated_rates_allowed: bool = False


@dataclass
class AmountTier:
    """Transaction amount tier configuration"""
    tier_id: str
    tier_order: int
    min_amount: Decimal
    max_amount: Optional[Decimal]  # None = unlimited
    margin_adjustment_bps: int     # Positive = premium, Negative = discount


@dataclass
class CurrencyMarkup:
    """Currency category markup configuration"""
    category: CurrencyCategory
    retail_markup_bps: int
    corporate_markup_bps: int
    institutional_markup_bps: int


@dataclass
class MarginBreakdown:
    """Detailed margin breakdown for transparency"""
    segment_base_bps: Decimal
    tier_adjustment_bps: Decimal
    currency_factor_bps: Decimal
    negotiated_discount_bps: Decimal = Decimal("0")
    
    @property
    def total_bps(self) -> Decimal:
        """Calculate total margin"""
        return (self.segment_base_bps + self.tier_adjustment_bps + 
                self.currency_factor_bps - self.negotiated_discount_bps)


@dataclass
class PricedQuote:
    """Complete priced FX quote"""
    quote_id: str
    base_currency: str
    quote_currency: str
    mid_rate: Decimal
    customer_rate: Decimal
    margin_bps: Decimal
    margin_breakdown: MarginBreakdown
    amount: Decimal
    converted_amount: Decimal
    segment: CustomerSegment
    amount_tier: str
    currency_category: CurrencyCategory
    valid_until: datetime
    rate_type: RateType = RateType.FIRM
