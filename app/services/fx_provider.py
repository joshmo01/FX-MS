"""
Refinitiv (Reuters) FX Rate Provider Service

This module provides integration with Refinitiv's Pricing API for real-time
and historical FX rates. Includes fallback to mock data for development.
"""
import httpx
import json
import logging
from datetime import datetime, timedelta
from decimal import Decimal
from typing import Optional, Dict, Any, Tuple
from pathlib import Path
import asyncio
from abc import ABC, abstractmethod

from app.core.config import get_settings
from app.models.schemas import ExchangeRate, RateType

logger = logging.getLogger(__name__)


class FXRateProvider(ABC):
    """Abstract base class for FX rate providers"""
    
    @abstractmethod
    async def get_rate(
        self, 
        base_currency: str, 
        quote_currency: str
    ) -> Optional[ExchangeRate]:
        """Get exchange rate for a currency pair"""
        pass
    
    @abstractmethod
    async def health_check(self) -> bool:
        """Check if provider is healthy"""
        pass


class RefinitivProvider(FXRateProvider):
    """
    Refinitiv (LSEG) FX Rate Provider
    
    Uses Refinitiv Data Platform API for real-time FX rates.
    Documentation: https://developers.lseg.com/en/api-catalog/refinitiv-data-platform
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.base_url = self.settings.refinitiv_base_url
        self.token_url = self.settings.refinitiv_token_url
        self._access_token: Optional[str] = None
        self._token_expiry: Optional[datetime] = None
        self._client: Optional[httpx.AsyncClient] = None
        
        # Load RIC mapping from config
        self._load_ric_mapping()
    
    def _load_ric_mapping(self):
        """Load Reuters Instrument Codes mapping"""
        config_path = Path("app/data/fx_providers.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                self.ric_mapping = config["providers"]["refinitiv"]["ric_mapping"]
        else:
            # Default RIC mapping
            self.ric_mapping = {
                "USD": "USD=", "EUR": "EUR=", "GBP": "GBP=",
                "INR": "INR=", "JPY": "JPY=", "AED": "AED=",
                "SGD": "SGD=", "AUD": "AUD=", "CAD": "CAD=", "CHF": "CHF="
            }
    
    async def _get_client(self) -> httpx.AsyncClient:
        """Get or create HTTP client"""
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(timeout=10.0)
        return self._client
    
    async def _authenticate(self) -> str:
        """
        Authenticate with Refinitiv OAuth2 and get access token.
        
        Returns:
            Access token string
        """
        # Check if we have a valid cached token
        if self._access_token and self._token_expiry:
            if datetime.utcnow() < self._token_expiry - timedelta(minutes=5):
                return self._access_token
        
        client_id = self.settings.refinitiv_client_id
        client_secret = self.settings.refinitiv_client_secret
        
        if not client_id or not client_secret:
            raise ValueError("Refinitiv credentials not configured")
        
        client = await self._get_client()
        
        response = await client.post(
            self.token_url,
            data={
                "grant_type": "client_credentials",
                "client_id": client_id,
                "client_secret": client_secret,
                "scope": "trapi.data.pricing.read"
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        
        if response.status_code != 200:
            logger.error(f"Refinitiv auth failed: {response.text}")
            raise Exception(f"Authentication failed: {response.status_code}")
        
        data = response.json()
        self._access_token = data["access_token"]
        self._token_expiry = datetime.utcnow() + timedelta(seconds=data.get("expires_in", 3600))
        
        return self._access_token
    
    async def get_rate(
        self, 
        base_currency: str, 
        quote_currency: str
    ) -> Optional[ExchangeRate]:
        """
        Get real-time FX rate from Refinitiv.
        
        Args:
            base_currency: Base currency code (e.g., USD)
            quote_currency: Quote currency code (e.g., INR)
            
        Returns:
            ExchangeRate object with bid/ask/mid rates
        """
        try:
            token = await self._authenticate()
            client = await self._get_client()
            
            # Construct RIC for the currency pair
            # Format: USDINR=R for USD/INR
            ric = f"{base_currency}{quote_currency}=R"
            
            response = await client.get(
                f"{self.base_url}/data/pricing/snapshots/v1/{ric}",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Accept": "application/json"
                }
            )
            
            if response.status_code != 200:
                logger.error(f"Refinitiv rate fetch failed: {response.text}")
                return None
            
            data = response.json()
            
            # Parse Refinitiv response
            # Response structure varies - this is a typical format
            fields = data.get("data", [{}])[0].get("fields", {})
            
            bid = Decimal(str(fields.get("BID", 0)))
            ask = Decimal(str(fields.get("ASK", 0)))
            mid = (bid + ask) / 2
            
            now = datetime.utcnow()
            
            return ExchangeRate(
                base_currency=base_currency,
                quote_currency=quote_currency,
                bid_rate=bid,
                ask_rate=ask,
                mid_rate=mid,
                spread_bps=int((ask - bid) / mid * 10000),
                rate_type=RateType.SPOT,
                provider="Refinitiv",
                timestamp=now,
                valid_until=now + timedelta(seconds=30)
            )
            
        except Exception as e:
            logger.error(f"Error fetching rate from Refinitiv: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check Refinitiv API health"""
        try:
            await self._authenticate()
            return True
        except Exception:
            return False
    
    async def close(self):
        """Close HTTP client"""
        if self._client:
            await self._client.aclose()


class MockFXProvider(FXRateProvider):
    """
    Mock FX Rate Provider for development and testing.
    
    Uses realistic sample rates based on actual market data.
    """
    
    def __init__(self):
        # Sample rates (as of late 2024 - for development only)
        self._base_rates: Dict[str, Decimal] = {
    # Existing rates
    "USDINR": Decimal("84.50"),
    "EURINR": Decimal("89.20"),
    "GBPINR": Decimal("106.50"),
    "EURUSD": Decimal("1.0557"),
    "GBPUSD": Decimal("1.2604"),
    "USDJPY": Decimal("154.80"),
    "AEDINR": Decimal("23.01"),
    "SGDINR": Decimal("62.85"),
    "AUDINR": Decimal("54.20"),
    "CADINR": Decimal("59.80"),
    "CHFINR": Decimal("94.50"),
    
    # ADD THESE NEW RATES
    "USDCHF": Decimal("0.8950"),
    "EURCHF": Decimal("0.9450"),
    "GBPCHF": Decimal("1.1280"),
    "EURGBP": Decimal("0.8375"),
    "AUDUSD": Decimal("0.6420"),
    "NZDUSD": Decimal("0.5890"),
    "USDCAD": Decimal("1.4150"),
    "USDSGD": Decimal("1.3450"),
    "USDHKD": Decimal("7.8100"),
    "USDAED": Decimal("3.6725"),
}
        
        # Default spreads in basis points
        self._spreads: Dict[str, int] = {
            "USDINR": 25, "EURINR": 30, "GBPINR": 30,
            "EURUSD": 10, "GBPUSD": 12, "USDJPY": 15,
            "AEDINR": 35, "SGDINR": 30, "AUDINR": 28,
            "CADINR": 28, "CHFINR": 25
        }
        
        # Load currency pairs config for spread overrides
        self._load_spreads()
    
    def _load_spreads(self):
        """Load spread configuration from currency pairs JSON"""
        config_path = Path("app/data/currency_pairs.json")
        if config_path.exists():
            with open(config_path) as f:
                config = json.load(f)
                for pair in config["currency_pairs"]:
                    self._spreads[pair["pair_id"]] = pair["spread_bps"]
    
    def _get_pair_key(self, base: str, quote: str) -> Tuple[str, bool]:
        """
        Get the pair key and whether it needs to be inverted.
        
        Returns:
            Tuple of (pair_key, is_inverted)
        """
        direct_key = f"{base}{quote}"
        inverse_key = f"{quote}{base}"
        
        if direct_key in self._base_rates:
            return direct_key, False
        elif inverse_key in self._base_rates:
            return inverse_key, True
        else:
            return direct_key, False
    
    async def get_rate(
        self, 
        base_currency: str, 
        quote_currency: str
    ) -> Optional[ExchangeRate]:
        """
        Get mock FX rate with realistic bid/ask spread.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            
        Returns:
            ExchangeRate object
        """
        pair_key, is_inverted = self._get_pair_key(base_currency, quote_currency)
        
        if pair_key not in self._base_rates and not is_inverted:
            # Try to calculate cross rate via USD
            rate = await self._calculate_cross_rate(base_currency, quote_currency)
            if rate:
                return rate
            logger.warning(f"No rate available for {base_currency}/{quote_currency}")
            return None
        
        # Get base mid rate
        if is_inverted:
            inverse_key = f"{quote_currency}{base_currency}"
            mid_rate = Decimal("1") / self._base_rates[inverse_key]
        else:
            mid_rate = self._base_rates[pair_key]
        
        # Apply spread
        spread_bps = self._spreads.get(pair_key, 25)
        spread_pct = Decimal(spread_bps) / Decimal("10000")
        
        half_spread = mid_rate * spread_pct / 2
        bid_rate = mid_rate - half_spread
        ask_rate = mid_rate + half_spread
        
        now = datetime.utcnow()
        
        return ExchangeRate(
            base_currency=base_currency,
            quote_currency=quote_currency,
            bid_rate=bid_rate.quantize(Decimal("0.0001")),
            ask_rate=ask_rate.quantize(Decimal("0.0001")),
            mid_rate=mid_rate.quantize(Decimal("0.0001")),
            spread_bps=spread_bps,
            rate_type=RateType.SPOT,
            provider="Mock Provider (Development)",
            timestamp=now,
            valid_until=now + timedelta(seconds=30)
        )
    
    async def _calculate_cross_rate(
        self, 
        base: str, 
        quote: str
    ) -> Optional[ExchangeRate]:
        """Calculate cross rate via USD if direct rate not available"""
        
        # Try BASE/USD and USD/QUOTE
        base_usd_key = f"{base}USD"
        usd_quote_key = f"USD{quote}"
        
        base_usd_rate = None
        usd_quote_rate = None
        
        if base_usd_key in self._base_rates:
            base_usd_rate = self._base_rates[base_usd_key]
        elif f"USD{base}" in self._base_rates:
            base_usd_rate = Decimal("1") / self._base_rates[f"USD{base}"]
        
        if usd_quote_key in self._base_rates:
            usd_quote_rate = self._base_rates[usd_quote_key]
        elif f"{quote}USD" in self._base_rates:
            usd_quote_rate = Decimal("1") / self._base_rates[f"{quote}USD"]
        
        if base_usd_rate and usd_quote_rate:
            mid_rate = base_usd_rate * usd_quote_rate
            spread_bps = 40  # Higher spread for cross rates
            spread_pct = Decimal(spread_bps) / Decimal("10000")
            half_spread = mid_rate * spread_pct / 2
            
            now = datetime.utcnow()
            
            return ExchangeRate(
                base_currency=base,
                quote_currency=quote,
                bid_rate=(mid_rate - half_spread).quantize(Decimal("0.0001")),
                ask_rate=(mid_rate + half_spread).quantize(Decimal("0.0001")),
                mid_rate=mid_rate.quantize(Decimal("0.0001")),
                spread_bps=spread_bps,
                rate_type=RateType.INDICATIVE,
                provider="Mock Provider (Cross Rate)",
                timestamp=now,
                valid_until=now + timedelta(seconds=30)
            )
        
        return None
    
    async def health_check(self) -> bool:
        """Mock provider is always healthy"""
        return True


class FXRateService:
    """
    FX Rate Service with provider failover and caching.
    
    Manages multiple rate providers and handles failover when primary
    provider is unavailable.
    """
    
    def __init__(self, use_mock: bool = True):
        """
        Initialize FX Rate Service.
        
        Args:
            use_mock: If True, use mock provider instead of Refinitiv
        """
        self.settings = get_settings()
        
        if use_mock or not self.settings.refinitiv_client_id:
            logger.info("Using Mock FX Provider")
            self.primary_provider = MockFXProvider()
        else:
            logger.info("Using Refinitiv FX Provider")
            self.primary_provider = RefinitivProvider()
        
        self.fallback_provider = MockFXProvider()
        
        # Simple in-memory cache
        self._cache: Dict[str, Tuple[ExchangeRate, datetime]] = {}
        self._cache_ttl = timedelta(seconds=self.settings.cache_ttl_seconds)
    
    def _get_cache_key(self, base: str, quote: str) -> str:
        """Generate cache key for currency pair"""
        return f"{base}_{quote}"
    
    def _get_from_cache(self, base: str, quote: str) -> Optional[ExchangeRate]:
        """Get rate from cache if valid"""
        key = self._get_cache_key(base, quote)
        if key in self._cache:
            rate, cached_at = self._cache[key]
            if datetime.utcnow() - cached_at < self._cache_ttl:
                return rate
        return None
    
    def _set_cache(self, base: str, quote: str, rate: ExchangeRate):
        """Store rate in cache"""
        key = self._get_cache_key(base, quote)
        self._cache[key] = (rate, datetime.utcnow())
    
    async def get_rate(
        self, 
        base_currency: str, 
        quote_currency: str,
        bypass_cache: bool = False
    ) -> Optional[ExchangeRate]:
        """
        Get exchange rate with caching and failover.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            bypass_cache: Skip cache lookup if True
            
        Returns:
            ExchangeRate object or None if unavailable
        """
        base = base_currency.upper()
        quote = quote_currency.upper()
        
        # Check cache first
        if not bypass_cache:
            cached = self._get_from_cache(base, quote)
            if cached:
                logger.debug(f"Cache hit for {base}/{quote}")
                return cached
        
        # Try primary provider
        try:
            rate = await self.primary_provider.get_rate(base, quote)
            if rate:
                self._set_cache(base, quote, rate)
                return rate
        except Exception as e:
            logger.warning(f"Primary provider failed: {e}")
        
        # Fallback to secondary provider
        try:
            rate = await self.fallback_provider.get_rate(base, quote)
            if rate:
                self._set_cache(base, quote, rate)
                return rate
        except Exception as e:
            logger.error(f"Fallback provider also failed: {e}")
        
        return None
    
    async def health_check(self) -> Dict[str, bool]:
        """Check health of all providers"""
        return {
            "primary": await self.primary_provider.health_check(),
            "fallback": await self.fallback_provider.health_check()
        }


# Singleton instance
_fx_service: Optional[FXRateService] = None


def get_fx_service() -> FXRateService:
    """Get or create FX Rate Service singleton"""
    global _fx_service
    if _fx_service is None:
        settings = get_settings()
        use_mock = not settings.refinitiv_client_id
        _fx_service = FXRateService(use_mock=use_mock)
    return _fx_service
