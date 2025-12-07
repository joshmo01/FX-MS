"""
Pydantic models for Currency Conversion API
"""
from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class ConversionDirection(str, Enum):
    """Direction of currency conversion"""
    BUY = "BUY"   # Buying base currency
    SELL = "SELL"  # Selling base currency


class RateType(str, Enum):
    """Type of exchange rate"""
    SPOT = "SPOT"
    FORWARD = "FORWARD"
    INDICATIVE = "INDICATIVE"


# =============================================================================
# Request Models
# =============================================================================

class CurrencyConversionRequest(BaseModel):
    """Request model for currency conversion"""
    
    source_currency: str = Field(
        ..., 
        min_length=3, 
        max_length=3,
        description="Source currency code (ISO 4217)",
        examples=["USD"]
    )
    target_currency: str = Field(
        ..., 
        min_length=3, 
        max_length=3,
        description="Target currency code (ISO 4217)",
        examples=["INR"]
    )
    amount: Decimal = Field(
        ..., 
        gt=0,
        description="Amount to convert",
        examples=[1000.00]
    )
    direction: ConversionDirection = Field(
        default=ConversionDirection.SELL,
        description="BUY = buying target currency, SELL = selling source currency"
    )
    rate_type: RateType = Field(
        default=RateType.SPOT,
        description="Type of rate to use for conversion"
    )
    client_reference: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Client reference ID for tracking",
        examples=["TXN-2025-001"]
    )
    
    @field_validator('source_currency', 'target_currency')
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        return v.upper()
    
    @field_validator('amount')
    @classmethod
    def validate_amount(cls, v: Decimal) -> Decimal:
        if v <= 0:
            raise ValueError("Amount must be positive")
        return v.quantize(Decimal("0.01"))


class QuoteRequest(BaseModel):
    """Request model for getting a quote"""
    
    source_currency: str = Field(..., min_length=3, max_length=3)
    target_currency: str = Field(..., min_length=3, max_length=3)
    amount: Decimal = Field(..., gt=0)
    direction: ConversionDirection = Field(default=ConversionDirection.SELL)
    
    @field_validator('source_currency', 'target_currency')
    @classmethod
    def validate_currency_code(cls, v: str) -> str:
        return v.upper()


# =============================================================================
# Response Models
# =============================================================================

class ExchangeRate(BaseModel):
    """Exchange rate details"""
    
    base_currency: str = Field(..., description="Base currency code")
    quote_currency: str = Field(..., description="Quote currency code")
    bid_rate: Decimal = Field(..., description="Bid rate (bank buys base)")
    ask_rate: Decimal = Field(..., description="Ask rate (bank sells base)")
    mid_rate: Decimal = Field(..., description="Mid-market rate")
    spread_bps: int = Field(..., description="Spread in basis points")
    rate_type: RateType = Field(..., description="Type of rate")
    provider: str = Field(..., description="Rate provider name")
    timestamp: datetime = Field(..., description="Rate timestamp")
    valid_until: datetime = Field(..., description="Rate validity expiry")


class ConversionResult(BaseModel):
    """Result of currency conversion calculation"""
    
    source_amount: Decimal = Field(..., description="Original amount")
    source_currency: str = Field(..., description="Source currency code")
    target_amount: Decimal = Field(..., description="Converted amount")
    target_currency: str = Field(..., description="Target currency code")
    applied_rate: Decimal = Field(..., description="Exchange rate applied")
    inverse_rate: Decimal = Field(..., description="Inverse exchange rate")
    direction: ConversionDirection = Field(..., description="Conversion direction")


class CurrencyConversionResponse(BaseModel):
    """Response model for currency conversion"""
    
    success: bool = Field(..., description="Whether conversion was successful")
    conversion_id: str = Field(..., description="Unique conversion ID")
    conversion: ConversionResult = Field(..., description="Conversion details")
    rate: ExchangeRate = Field(..., description="Exchange rate used")
    fees: Optional[Decimal] = Field(default=None, description="Applied fees if any")
    total_cost: Decimal = Field(..., description="Total cost in source currency")
    client_reference: Optional[str] = Field(default=None)
    created_at: datetime = Field(..., description="Timestamp of conversion")
    
    class Config:
        json_encoders = {
            Decimal: lambda v: float(v),
            datetime: lambda v: v.isoformat()
        }


class QuoteResponse(BaseModel):
    """Response model for quote request"""
    
    quote_id: str = Field(..., description="Unique quote ID")
    source_currency: str
    target_currency: str
    source_amount: Decimal
    target_amount: Decimal
    rate: ExchangeRate
    valid_until: datetime = Field(..., description="Quote expiry time")
    created_at: datetime


# =============================================================================
# Reference Data Models
# =============================================================================

class Currency(BaseModel):
    """Currency reference data"""
    
    code: str
    name: str
    symbol: str
    decimal_places: int
    country: str
    is_major: bool
    is_active: bool
    min_amount: Decimal
    max_amount: Decimal


class CurrencyPair(BaseModel):
    """Currency pair configuration"""
    
    pair_id: str
    base_currency: str
    quote_currency: str
    is_active: bool
    spread_bps: int
    daily_limit_base: Decimal
    reuters_ric: str
    settlement_days: int


class CurrencyListResponse(BaseModel):
    """Response for listing supported currencies"""
    
    currencies: List[Currency]
    count: int
    timestamp: datetime


class CurrencyPairListResponse(BaseModel):
    """Response for listing supported currency pairs"""
    
    pairs: List[CurrencyPair]
    count: int
    timestamp: datetime


# =============================================================================
# Error Models
# =============================================================================

class ErrorDetail(BaseModel):
    """Error detail model"""
    
    code: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    field: Optional[str] = Field(default=None, description="Field that caused error")


class ErrorResponse(BaseModel):
    """Standard error response"""
    
    success: bool = False
    error: ErrorDetail
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    request_id: Optional[str] = None
