"""
Currency Conversion API Router

REST API endpoints for currency conversion operations.
"""
import logging
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, HTTPException, Query, Depends, Request
from fastapi.responses import JSONResponse

from app.models.schemas import (
    CurrencyConversionRequest,
    CurrencyConversionResponse,
    QuoteRequest,
    QuoteResponse,
    ExchangeRate,
    CurrencyListResponse,
    CurrencyPairListResponse,
    ErrorResponse,
    ErrorDetail,
)
from app.services.conversion_service import get_conversion_service, CurrencyConversionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/v1/fx", tags=["Currency Conversion"])


def get_service() -> CurrencyConversionService:
    """Dependency to get conversion service"""
    return get_conversion_service()


# =============================================================================
# Currency Conversion Endpoints
# =============================================================================

@router.post(
    "/convert",
    response_model=CurrencyConversionResponse,
    summary="Convert Currency",
    description="""
    Convert an amount from one currency to another.
    
    **Features:**
    - Real-time exchange rates from Refinitiv (Reuters)
    - Bid/Ask spread applied based on direction
    - Amount validation against currency limits
    - Support for major and exotic currency pairs
    
    **Direction:**
    - SELL: Customer sells source currency (uses bid rate)
    - BUY: Customer buys source currency (uses ask rate)
    """,
    responses={
        200: {"description": "Successful conversion"},
        400: {"model": ErrorResponse, "description": "Validation error"},
        503: {"model": ErrorResponse, "description": "Rate provider unavailable"}
    }
)
async def convert_currency(
    request: CurrencyConversionRequest,
    service: CurrencyConversionService = Depends(get_service)
) -> CurrencyConversionResponse:
    """
    Perform currency conversion with real-time exchange rates.
    """
    try:
        result = await service.convert(request)
        logger.info(
            f"Conversion completed: {request.source_currency} -> "
            f"{request.target_currency}, ID: {result.conversion_id}"
        )
        return result
    
    except ValueError as e:
        logger.warning(f"Conversion validation error: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Conversion error: {e}")
        raise HTTPException(
            status_code=503, 
            detail="Unable to process conversion. Please try again."
        )


@router.post(
    "/quote",
    response_model=QuoteResponse,
    summary="Get Conversion Quote",
    description="""
    Get a conversion quote without executing the transaction.
    
    Quote is valid for 30 seconds and includes:
    - Current exchange rate with bid/ask spread
    - Calculated target amount
    - Quote ID for reference
    """
)
async def get_quote(
    request: QuoteRequest,
    service: CurrencyConversionService = Depends(get_service)
) -> QuoteResponse:
    """
    Get a conversion quote for the specified amount and currencies.
    """
    try:
        return await service.get_quote(request)
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    
    except Exception as e:
        logger.error(f"Quote error: {e}")
        raise HTTPException(
            status_code=503,
            detail="Unable to get quote. Please try again."
        )


@router.get(
    "/rate/{base_currency}/{quote_currency}",
    response_model=ExchangeRate,
    summary="Get Exchange Rate",
    description="""
    Get the current exchange rate for a currency pair.
    
    Returns bid, ask, and mid rates along with:
    - Spread in basis points
    - Rate provider name
    - Rate timestamp and validity period
    """
)
async def get_exchange_rate(
    base_currency: str,
    quote_currency: str,
    service: CurrencyConversionService = Depends(get_service)
) -> ExchangeRate:
    """
    Get exchange rate for a specific currency pair.
    """
    rate = await service.get_rate_only(
        base_currency.upper(),
        quote_currency.upper()
    )
    
    if not rate:
        raise HTTPException(
            status_code=404,
            detail=f"Rate not available for {base_currency}/{quote_currency}"
        )
    
    return rate


# =============================================================================
# Reference Data Endpoints
# =============================================================================

@router.get(
    "/currencies",
    response_model=CurrencyListResponse,
    summary="List Supported Currencies",
    description="Get list of all supported currencies with their configurations."
)
async def list_currencies(
    service: CurrencyConversionService = Depends(get_service)
) -> CurrencyListResponse:
    """
    Get all supported currencies.
    """
    currencies = service.get_supported_currencies()
    return CurrencyListResponse(
        currencies=currencies,
        count=len(currencies),
        timestamp=datetime.utcnow()
    )


@router.get(
    "/currencies/{currency_code}",
    summary="Get Currency Details",
    description="Get details for a specific currency."
)
async def get_currency(
    currency_code: str,
    service: CurrencyConversionService = Depends(get_service)
):
    """
    Get details for a specific currency code.
    """
    currency = service.get_currency(currency_code.upper())
    
    if not currency:
        raise HTTPException(
            status_code=404,
            detail=f"Currency {currency_code} not found"
        )
    
    return currency


@router.get(
    "/pairs",
    response_model=CurrencyPairListResponse,
    summary="List Currency Pairs",
    description="Get list of all supported currency pairs with their configurations."
)
async def list_currency_pairs(
    service: CurrencyConversionService = Depends(get_service)
) -> CurrencyPairListResponse:
    """
    Get all supported currency pairs.
    """
    pairs = service.get_supported_pairs()
    return CurrencyPairListResponse(
        pairs=pairs,
        count=len(pairs),
        timestamp=datetime.utcnow()
    )


# =============================================================================
# Health & Status Endpoints
# =============================================================================

@router.get(
    "/health",
    summary="Health Check",
    description="Check the health status of the FX service and its providers."
)
async def health_check(
    service: CurrencyConversionService = Depends(get_service)
):
    """
    Check service health including rate providers.
    """
    provider_health = await service.fx_service.health_check()
    
    return {
        "status": "healthy" if any(provider_health.values()) else "degraded",
        "timestamp": datetime.utcnow().isoformat(),
        "providers": provider_health
    }
