"""
Currency Conversion Service

Business logic for currency conversion operations.
"""
import json
import logging
import uuid
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, Dict, List
from pathlib import Path

from app.models.schemas import (
    CurrencyConversionRequest,
    CurrencyConversionResponse,
    ConversionResult,
    ConversionDirection,
    ExchangeRate,
    QuoteRequest,
    QuoteResponse,
    Currency,
    CurrencyPair,
)
from app.services.fx_provider import get_fx_service

logger = logging.getLogger(__name__)


class CurrencyConversionService:
    """
    Service for currency conversion operations.
    
    Handles conversion calculations, validation, and quote generation.
    """
    
    def __init__(self):
        self.fx_service = get_fx_service()
        self._currencies: Dict[str, Currency] = {}
        self._currency_pairs: Dict[str, CurrencyPair] = {}
        self._load_reference_data()
    
    def _load_reference_data(self):
        """Load currency and pair reference data"""
        # Load currencies
        currencies_path = Path("app/data/currencies.json")
        if currencies_path.exists():
            with open(currencies_path) as f:
                data = json.load(f)
                for curr in data["currencies"]:
                    self._currencies[curr["code"]] = Currency(**curr)
        
        # Load currency pairs
        pairs_path = Path("app/data/currency_pairs.json")
        if pairs_path.exists():
            with open(pairs_path) as f:
                data = json.load(f)
                for pair in data["currency_pairs"]:
                    self._currency_pairs[pair["pair_id"]] = CurrencyPair(**pair)
    
    def get_supported_currencies(self) -> List[Currency]:
        """Get list of supported currencies"""
        return [c for c in self._currencies.values() if c.is_active]
    
    def get_supported_pairs(self) -> List[CurrencyPair]:
        """Get list of supported currency pairs"""
        return [p for p in self._currency_pairs.values() if p.is_active]
    
    def is_currency_supported(self, currency_code: str) -> bool:
        """Check if a currency is supported"""
        currency = self._currencies.get(currency_code.upper())
        return currency is not None and currency.is_active
    
    def get_currency(self, code: str) -> Optional[Currency]:
        """Get currency by code"""
        return self._currencies.get(code.upper())
    
    def validate_amount(
        self, 
        amount: Decimal, 
        currency_code: str
    ) -> tuple[bool, Optional[str]]:
        """
        Validate conversion amount against currency limits.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        currency = self.get_currency(currency_code)
        if not currency:
            return False, f"Currency {currency_code} not supported"
        
        if amount < currency.min_amount:
            return False, f"Amount below minimum of {currency.min_amount} {currency_code}"
        
        if amount > currency.max_amount:
            return False, f"Amount exceeds maximum of {currency.max_amount} {currency_code}"
        
        return True, None
    
    def _round_amount(self, amount: Decimal, currency_code: str) -> Decimal:
        """Round amount to currency's decimal places"""
        currency = self.get_currency(currency_code)
        decimal_places = currency.decimal_places if currency else 2
        
        quantize_str = "1" if decimal_places == 0 else f"0.{'0' * decimal_places}"
        return amount.quantize(Decimal(quantize_str), rounding=ROUND_HALF_UP)
    
    async def convert(
        self, 
        request: CurrencyConversionRequest
    ) -> CurrencyConversionResponse:
        """
        Perform currency conversion.
        
        Args:
            request: Conversion request with source/target currencies and amount
            
        Returns:
            CurrencyConversionResponse with conversion details
            
        Raises:
            ValueError: If validation fails or rate unavailable
        """
        # Validate currencies
        if not self.is_currency_supported(request.source_currency):
            raise ValueError(f"Source currency {request.source_currency} not supported")
        
        if not self.is_currency_supported(request.target_currency):
            raise ValueError(f"Target currency {request.target_currency} not supported")
        
        if request.source_currency == request.target_currency:
            raise ValueError("Source and target currencies must be different")
        
        # Validate amount
        is_valid, error = self.validate_amount(
            request.amount, 
            request.source_currency
        )
        if not is_valid:
            raise ValueError(error)
        
        # Get exchange rate
        rate = await self.fx_service.get_rate(
            request.source_currency,
            request.target_currency
        )
        
        if not rate:
            raise ValueError(
                f"Exchange rate not available for "
                f"{request.source_currency}/{request.target_currency}"
            )
        
        # Calculate conversion
        # For SELL direction: customer is selling source, we use bid rate
        # For BUY direction: customer is buying source, we use ask rate
        if request.direction == ConversionDirection.SELL:
            applied_rate = rate.bid_rate
        else:
            applied_rate = rate.ask_rate
        
        target_amount = request.amount * applied_rate
        target_amount = self._round_amount(target_amount, request.target_currency)
        
        # Calculate inverse rate
        inverse_rate = (Decimal("1") / applied_rate).quantize(
            Decimal("0.000001"), 
            rounding=ROUND_HALF_UP
        )
        
        # Generate conversion ID
        conversion_id = f"CNV-{uuid.uuid4().hex[:12].upper()}"
        
        conversion_result = ConversionResult(
            source_amount=request.amount,
            source_currency=request.source_currency,
            target_amount=target_amount,
            target_currency=request.target_currency,
            applied_rate=applied_rate,
            inverse_rate=inverse_rate,
            direction=request.direction
        )
        
        return CurrencyConversionResponse(
            success=True,
            conversion_id=conversion_id,
            conversion=conversion_result,
            rate=rate,
            fees=None,  # Fees can be added based on business rules
            total_cost=request.amount,
            client_reference=request.client_reference,
            created_at=datetime.utcnow()
        )
    
    async def get_quote(self, request: QuoteRequest) -> QuoteResponse:
        """
        Get a conversion quote without executing the conversion.
        
        Quote is valid for 30 seconds.
        
        Args:
            request: Quote request details
            
        Returns:
            QuoteResponse with rate and converted amount
        """
        # Validate currencies
        if not self.is_currency_supported(request.source_currency):
            raise ValueError(f"Currency {request.source_currency} not supported")
        
        if not self.is_currency_supported(request.target_currency):
            raise ValueError(f"Currency {request.target_currency} not supported")
        
        # Get rate
        rate = await self.fx_service.get_rate(
            request.source_currency,
            request.target_currency
        )
        
        if not rate:
            raise ValueError(
                f"Rate not available for "
                f"{request.source_currency}/{request.target_currency}"
            )
        
        # Calculate target amount
        if request.direction == ConversionDirection.SELL:
            applied_rate = rate.bid_rate
        else:
            applied_rate = rate.ask_rate
        
        target_amount = request.amount * applied_rate
        target_amount = self._round_amount(target_amount, request.target_currency)
        
        now = datetime.utcnow()
        quote_id = f"QTE-{uuid.uuid4().hex[:12].upper()}"
        
        return QuoteResponse(
            quote_id=quote_id,
            source_currency=request.source_currency,
            target_currency=request.target_currency,
            source_amount=request.amount,
            target_amount=target_amount,
            rate=rate,
            valid_until=now + timedelta(seconds=30),
            created_at=now
        )
    
    async def get_rate_only(
        self, 
        base_currency: str, 
        quote_currency: str
    ) -> Optional[ExchangeRate]:
        """
        Get exchange rate without performing conversion.
        
        Args:
            base_currency: Base currency code
            quote_currency: Quote currency code
            
        Returns:
            ExchangeRate or None if unavailable
        """
        return await self.fx_service.get_rate(base_currency, quote_currency)


# Singleton instance
_conversion_service: Optional[CurrencyConversionService] = None


def get_conversion_service() -> CurrencyConversionService:
    """Get or create Currency Conversion Service singleton"""
    global _conversion_service
    if _conversion_service is None:
        _conversion_service = CurrencyConversionService()
    return _conversion_service
