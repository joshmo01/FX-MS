"""
Unit tests for FX Pricing Engine
Add this file to: tests/test_pricing.py
"""
import pytest
from decimal import Decimal

# Adjust import path based on your project structure
from app.core.pricing_engine import FXPricingEngine, get_pricing_engine
from app.models.pricing import CustomerSegment, CurrencyCategory


@pytest.fixture
def engine():
    """Create fresh pricing engine for tests."""
    return FXPricingEngine()


class TestSegmentConfiguration:
    """Test customer segment pricing configuration."""
    
    def test_all_segments_loaded(self, engine):
        """All 6 segments should be loaded."""
        segments = engine.get_all_segments()
        assert len(segments) == 6
    
    def test_retail_highest_margin(self, engine):
        """Retail should have highest base margin."""
        config = engine.get_segment_config(CustomerSegment.RETAIL)
        assert config.base_margin_bps == 300
        assert config.min_margin_bps == 200
        assert config.max_margin_bps == 500
    
    def test_institutional_lowest_margin(self, engine):
        """Institutional should have lowest base margin."""
        config = engine.get_segment_config(CustomerSegment.INSTITUTIONAL)
        assert config.base_margin_bps == 5
        assert config.min_margin_bps == 2
        assert config.max_margin_bps == 20
    
    def test_volume_discount_eligibility(self, engine):
        """Check volume discount eligibility per segment."""
        # Eligible for volume discounts
        assert engine.get_segment_config(CustomerSegment.INSTITUTIONAL).volume_discount_eligible is True
        assert engine.get_segment_config(CustomerSegment.LARGE_CORPORATE).volume_discount_eligible is True
        assert engine.get_segment_config(CustomerSegment.MID_MARKET).volume_discount_eligible is True
        assert engine.get_segment_config(CustomerSegment.PRIVATE_BANKING).volume_discount_eligible is True
        
        # Not eligible for volume discounts
        assert engine.get_segment_config(CustomerSegment.RETAIL).volume_discount_eligible is False
        assert engine.get_segment_config(CustomerSegment.SMALL_BUSINESS).volume_discount_eligible is False
    
    def test_negotiated_rates_allowed(self, engine):
        """Check which segments allow negotiated rates."""
        assert engine.get_segment_config(CustomerSegment.INSTITUTIONAL).negotiated_rates_allowed is True
        assert engine.get_segment_config(CustomerSegment.LARGE_CORPORATE).negotiated_rates_allowed is True
        assert engine.get_segment_config(CustomerSegment.PRIVATE_BANKING).negotiated_rates_allowed is True
        
        assert engine.get_segment_config(CustomerSegment.MID_MARKET).negotiated_rates_allowed is False
        assert engine.get_segment_config(CustomerSegment.SMALL_BUSINESS).negotiated_rates_allowed is False
        assert engine.get_segment_config(CustomerSegment.RETAIL).negotiated_rates_allowed is False


class TestAmountTiers:
    """Test amount tier configuration and logic."""
    
    def test_all_tiers_loaded(self, engine):
        """All 6 tiers should be loaded."""
        tiers = engine.get_all_tiers()
        assert len(tiers) == 6
    
    def test_small_amount_premium(self, engine):
        """Small amounts (<$10K) should get premium tier."""
        tier = engine.get_amount_tier(Decimal("5000"))
        assert tier.tier_id == "TIER_1"
        assert tier.margin_adjustment_bps == 50  # Premium
    
    def test_base_tier(self, engine):
        """$50K-$100K should get base tier (no adjustment)."""
        tier = engine.get_amount_tier(Decimal("75000"))
        assert tier.tier_id == "TIER_3"
        assert tier.margin_adjustment_bps == 0
    
    def test_large_amount_discount(self, engine):
        """Large amounts (>$1M) should get maximum discount."""
        tier = engine.get_amount_tier(Decimal("5000000"))
        assert tier.tier_id == "TIER_6"
        assert tier.margin_adjustment_bps == -40  # Discount
    
    def test_tier_boundaries(self, engine):
        """Test tier boundary conditions."""
        # Just under $10K
        tier_9999 = engine.get_amount_tier(Decimal("9999.99"))
        assert tier_9999.tier_id == "TIER_1"
        
        # Exactly $10K
        tier_10000 = engine.get_amount_tier(Decimal("10000"))
        assert tier_10000.tier_id == "TIER_2"
        
        # Just under $50K
        tier_49999 = engine.get_amount_tier(Decimal("49999.99"))
        assert tier_49999.tier_id == "TIER_2"
        
        # Exactly $50K
        tier_50000 = engine.get_amount_tier(Decimal("50000"))
        assert tier_50000.tier_id == "TIER_3"


class TestCurrencyCategories:
    """Test currency category classification."""
    
    def test_g10_pairs(self, engine):
        """G10 pairs should be classified correctly."""
        assert engine.get_currency_category("USD", "EUR") == CurrencyCategory.G10
        assert engine.get_currency_category("EUR", "USD") == CurrencyCategory.G10
        assert engine.get_currency_category("USD", "JPY") == CurrencyCategory.G10
        assert engine.get_currency_category("GBP", "USD") == CurrencyCategory.G10
        assert engine.get_currency_category("AUD", "NZD") == CurrencyCategory.G10
    
    def test_restricted_currencies(self, engine):
        """INR, CNY, KRW should be RESTRICTED."""
        assert engine.get_currency_category("USD", "INR") == CurrencyCategory.RESTRICTED
        assert engine.get_currency_category("EUR", "INR") == CurrencyCategory.RESTRICTED
        assert engine.get_currency_category("USD", "CNY") == CurrencyCategory.RESTRICTED
        assert engine.get_currency_category("USD", "KRW") == CurrencyCategory.RESTRICTED
    
    def test_exotic_currencies(self, engine):
        """TRY, ZAR, MXN should be EXOTIC."""
        assert engine.get_currency_category("USD", "TRY") == CurrencyCategory.EXOTIC
        assert engine.get_currency_category("USD", "ZAR") == CurrencyCategory.EXOTIC
        assert engine.get_currency_category("EUR", "MXN") == CurrencyCategory.EXOTIC
    
    def test_restricted_takes_priority(self, engine):
        """When one currency is restricted, pair is RESTRICTED."""
        # INR is restricted, EUR is G10 -> should be RESTRICTED
        assert engine.get_currency_category("EUR", "INR") == CurrencyCategory.RESTRICTED


class TestMarginCalculation:
    """Test full margin calculation logic."""
    
    def test_retail_small_g10(self, engine):
        """Retail + small amount + G10 = highest margin."""
        margin, breakdown, tier, category = engine.calculate_margin(
            segment=CustomerSegment.RETAIL,
            amount=Decimal("5000"),
            base_currency="USD",
            quote_currency="EUR"
        )
        
        # Retail (300) + NO tier adj (not eligible) + G10 (50) = 350
        assert margin == Decimal("350")
        assert breakdown.segment_base_bps == Decimal("300")
        assert breakdown.tier_adjustment_bps == Decimal("0")  # Retail not eligible
        assert breakdown.currency_factor_bps == Decimal("50")
        assert tier.tier_id == "TIER_1"
        assert category == CurrencyCategory.G10
    
    def test_institutional_large_g10(self, engine):
        """Institutional + large amount + G10 = lowest margin."""
        margin, breakdown, tier, category = engine.calculate_margin(
            segment=CustomerSegment.INSTITUTIONAL,
            amount=Decimal("5000000"),
            base_currency="USD",
            quote_currency="EUR"
        )
        
        # Institutional (5) + Tier 6 (-40) + G10 inst (2) = -33 -> floors at min (2)
        assert margin == Decimal("2")  # Min margin floor
        assert tier.tier_id == "TIER_6"
        assert category == CurrencyCategory.G10
    
    def test_mid_market_medium_restricted(self, engine):
        """Mid-Market + medium amount + RESTRICTED currency."""
        margin, breakdown, tier, category = engine.calculate_margin(
            segment=CustomerSegment.MID_MARKET,
            amount=Decimal("100000"),
            base_currency="USD",
            quote_currency="INR"
        )
        
        # Mid-Market (75) + Tier 4 (-15, eligible) + Restricted corp (100) = 160
        # But max is 150, so capped
        assert margin == Decimal("150")  # Max margin ceiling
        assert category == CurrencyCategory.RESTRICTED
    
    def test_margin_floor_enforcement(self, engine):
        """Margin should never go below segment minimum."""
        margin, _, _, _ = engine.calculate_margin(
            segment=CustomerSegment.INSTITUTIONAL,
            amount=Decimal("10000000"),  # Huge amount
            base_currency="EUR",
            quote_currency="USD"
        )
        
        # Should be floored at institutional min (2)
        config = engine.get_segment_config(CustomerSegment.INSTITUTIONAL)
        assert margin >= config.min_margin_bps
    
    def test_margin_ceiling_enforcement(self, engine):
        """Margin should never exceed segment maximum."""
        margin, _, _, _ = engine.calculate_margin(
            segment=CustomerSegment.RETAIL,
            amount=Decimal("1000"),  # Tiny amount
            base_currency="USD",
            quote_currency="INR"  # Restricted currency
        )
        
        # Should be capped at retail max (500)
        config = engine.get_segment_config(CustomerSegment.RETAIL)
        assert margin <= config.max_margin_bps


class TestQuoteGeneration:
    """Test priced quote generation."""
    
    def test_quote_generation_basic(self, engine):
        """Test basic quote generation."""
        quote = engine.generate_priced_quote(
            base_currency="USD",
            quote_currency="INR",
            amount=Decimal("100000"),
            mid_rate=Decimal("83.50"),
            customer_id="TEST-001",
            segment=CustomerSegment.MID_MARKET,
            direction="SELL"
        )
        
        assert quote.quote_id.startswith("PQ-")
        assert quote.base_currency == "USD"
        assert quote.quote_currency == "INR"
        assert quote.mid_rate == Decimal("83.50")
        assert quote.margin_bps > 0
        assert quote.customer_rate < quote.mid_rate  # SELL subtracts margin
        assert quote.segment == CustomerSegment.MID_MARKET
    
    def test_buy_direction_adds_margin(self, engine):
        """BUY direction should add margin to rate."""
        quote = engine.generate_priced_quote(
            base_currency="USD",
            quote_currency="EUR",
            amount=Decimal("100000"),
            mid_rate=Decimal("0.9250"),
            customer_id="TEST-001",
            segment=CustomerSegment.RETAIL,
            direction="BUY"
        )
        
        assert quote.customer_rate > quote.mid_rate
    
    def test_sell_direction_subtracts_margin(self, engine):
        """SELL direction should subtract margin from rate."""
        quote = engine.generate_priced_quote(
            base_currency="USD",
            quote_currency="EUR",
            amount=Decimal("100000"),
            mid_rate=Decimal("0.9250"),
            customer_id="TEST-001",
            segment=CustomerSegment.RETAIL,
            direction="SELL"
        )
        
        assert quote.customer_rate < quote.mid_rate
    
    def test_converted_amount_calculation(self, engine):
        """Converted amount should be calculated correctly."""
        quote = engine.generate_priced_quote(
            base_currency="USD",
            quote_currency="INR",
            amount=Decimal("1000"),
            mid_rate=Decimal("83.50"),
            customer_id="TEST-001",
            segment=CustomerSegment.RETAIL,
            direction="SELL"
        )
        
        expected = (Decimal("1000") * quote.customer_rate).quantize(Decimal("0.01"))
        assert quote.converted_amount == expected
    
    def test_quote_validity(self, engine):
        """Quote should have valid expiry time."""
        from datetime import datetime, timezone
        
        before = datetime.now(timezone.utc)
        quote = engine.generate_priced_quote(
            base_currency="USD",
            quote_currency="EUR",
            amount=Decimal("10000"),
            mid_rate=Decimal("0.9250"),
            customer_id="TEST-001",
            segment=CustomerSegment.RETAIL,
            direction="SELL"
        )
        after = datetime.now(timezone.utc)
        
        # Quote should expire ~30 seconds in the future
        assert quote.valid_until > before
        assert quote.valid_until > after


class TestEndToEndScenarios:
    """Test realistic end-to-end pricing scenarios."""
    
    def test_scenario_retail_remittance(self, engine):
        """Retail customer sending $5K to India."""
        quote = engine.generate_priced_quote(
            base_currency="USD",
            quote_currency="INR",
            amount=Decimal("5000"),
            mid_rate=Decimal("83.50"),
            customer_id="RETAIL-001",
            segment=CustomerSegment.RETAIL,
            direction="SELL"
        )
        
        # Expect high margin: Retail + Small amount + Restricted
        assert quote.margin_bps >= Decimal("200")
        assert quote.currency_category == CurrencyCategory.RESTRICTED
        assert quote.amount_tier == "TIER_1"
    
    def test_scenario_corporate_treasury(self, engine):
        """Corporate treasury converting $500K EUR to USD."""
        quote = engine.generate_priced_quote(
            base_currency="EUR",
            quote_currency="USD",
            amount=Decimal("500000"),
            mid_rate=Decimal("1.0810"),
            customer_id="CORP-001",
            segment=CustomerSegment.LARGE_CORPORATE,
            direction="SELL"
        )
        
        # Expect low margin: Large Corp + Large amount + G10
        assert quote.margin_bps <= Decimal("50")
        assert quote.currency_category == CurrencyCategory.G10
        assert quote.amount_tier in ["TIER_4", "TIER_5"]
    
    def test_scenario_institutional_fx(self, engine):
        """Institutional client trading $5M USD/JPY."""
        quote = engine.generate_priced_quote(
            base_currency="USD",
            quote_currency="JPY",
            amount=Decimal("5000000"),
            mid_rate=Decimal("149.50"),
            customer_id="INST-001",
            segment=CustomerSegment.INSTITUTIONAL,
            direction="BUY"
        )
        
        # Expect minimal margin: Institutional + Huge amount + G10
        assert quote.margin_bps <= Decimal("10")
        assert quote.currency_category == CurrencyCategory.G10
        assert quote.amount_tier == "TIER_6"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
