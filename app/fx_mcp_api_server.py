"""
FX Smart Routing MCP Server - API Integration
Calls FastAPI endpoints for FX routing recommendations
"""
from mcp.server.fastmcp import FastMCP
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum
import httpx
import json

# Initialize MCP Server
mcp = FastMCP("fx_routing_mcp")

# API Base URL
API_BASE_URL = "http://127.0.0.1:8000"

# Enums
class Side(str, Enum):
    BUY = "BUY"
    SELL = "SELL"

class CustomerTier(str, Enum):
    PLATINUM = "PLATINUM"
    GOLD = "GOLD"
    SILVER = "SILVER"
    BRONZE = "BRONZE"
    RETAIL = "RETAIL"

class RoutingObjective(str, Enum):
    BEST_RATE = "BEST_RATE"
    OPTIMUM = "OPTIMUM"
    FASTEST_EXECUTION = "FASTEST_EXECUTION"
    MAX_STP = "MAX_STP"

# Input Models
class GetRateInput(BaseModel):
    currency_pair: str = Field(..., description="Currency pair like USDINR, EURUSD, GBPINR")

class EffectiveRateInput(BaseModel):
    currency_pair: str = Field(..., description="Currency pair like USDINR, EURUSD")
    side: Side = Field(default=Side.BUY, description="BUY or SELL")
    amount_usd: float = Field(default=10000, description="Transaction amount in USD", ge=0)
    customer_tier: CustomerTier = Field(default=CustomerTier.RETAIL, description="Customer tier")

class RouteRecommendInput(BaseModel):
    currency_pair: str = Field(..., description="Currency pair like USDINR, EURUSD")
    amount_usd: float = Field(default=10000, description="Transaction amount in USD", ge=0)
    side: Side = Field(default=Side.BUY, description="BUY or SELL")
    customer_tier: CustomerTier = Field(default=CustomerTier.RETAIL, description="Customer tier")
    objective: RoutingObjective = Field(default=RoutingObjective.OPTIMUM, description="Routing objective")

class MultiRailRouteInput(BaseModel):
    source_currency: str = Field(..., description="Source currency (USD, EUR, e-INR, USDC, etc)")
    target_currency: str = Field(..., description="Target currency (INR, e-CNY, USDT, etc)")
    amount: float = Field(default=10000, description="Transaction amount", ge=0)


# Helper function for API calls
async def call_api(method: str, endpoint: str, params: dict = None, json_data: dict = None) -> str:
    """Make HTTP request to FastAPI server"""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            url = f"{API_BASE_URL}{endpoint}"
            
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, params=params, json=json_data)
            
            if response.status_code == 200:
                return json.dumps(response.json(), indent=2)
            else:
                return json.dumps({"error": f"API returned status {response.status_code}", "detail": response.text})
    
    except httpx.ConnectError:
        return json.dumps({
            "error": "Cannot connect to FX API server",
            "hint": "Make sure FastAPI is running: uvicorn app.main:app --port 8000"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


# MCP Tools

@mcp.tool(
    name="fx_get_rate",
    annotations={
        "title": "Get FX Rate",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_get_rate(params: GetRateInput) -> str:
    """Get current FX rate for a currency pair.
    
    Returns bid, ask, mid rates and treasury position for pairs like USDINR, EURUSD, GBPINR.
    Available pairs: USDINR, EURINR, GBPINR, EURUSD, AEDINR, GBPUSD, USDJPY, USDSGD, USDAED, USDCNY
    """
    pair = params.currency_pair.upper()
    return await call_api("GET", f"/api/v1/fx/routing/treasury-rates/{pair}")


@mcp.tool(
    name="fx_get_effective_rate",
    annotations={
        "title": "Calculate Effective FX Rate",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_get_effective_rate(params: EffectiveRateInput) -> str:
    """Calculate effective FX rate with all adjustments applied.
    
    Includes treasury position adjustment, customer tier discount, and volume-based pricing.
    Customer tiers: PLATINUM, GOLD, SILVER, BRONZE, RETAIL
    """
    pair = params.currency_pair.upper()
    query_params = {
        "side": params.side.value,
        "amount": params.amount_usd,
        "customer_tier": params.customer_tier.value
    }
    return await call_api("GET", f"/api/v1/fx/routing/effective-rate/{pair}", params=query_params)


@mcp.tool(
    name="fx_recommend_route",
    annotations={
        "title": "Get FX Route Recommendation",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_recommend_route(params: RouteRecommendInput) -> str:
    """Get optimal FX route recommendation with provider ranking.
    
    Analyzes all available providers and ranks them based on routing objective.
    Objectives: BEST_RATE, OPTIMUM, FASTEST_EXECUTION, MAX_STP
    """
    query_params = {
        "pair": params.currency_pair.upper(),
        "amount": params.amount_usd,
        "side": params.side.value,
        "customer_tier": params.customer_tier.value,
        "objective": params.objective.value
    }
    return await call_api("POST", "/api/v1/fx/routing/recommend", params=query_params)


@mcp.tool(
    name="fx_multi_rail_route",
    annotations={
        "title": "Multi-Rail Route (Fiat/CBDC/Stablecoin)",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_multi_rail_route(params: MultiRailRouteInput) -> str:
    """Find optimal route across Fiat, CBDC, and Stablecoin rails.
    
    Supports 9 conversion types including mBridge for CBDC-to-CBDC.
    CBDCs: e-INR, e-CNY, e-HKD, e-THB, e-AED, e-SGD
    Stablecoins: USDC, USDT, EURC, PYUSD, XSGD
    """
    query_params = {
        "source": params.source_currency.upper(),
        "target": params.target_currency.upper(),
        "amount": params.amount
    }
    return await call_api("POST", "/api/v1/fx/multi-rail/route", params=query_params)


@mcp.tool(
    name="fx_list_cbdc",
    annotations={
        "title": "List Available CBDCs",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_list_cbdc() -> str:
    """List all supported Central Bank Digital Currencies (CBDCs).
    
    Includes mBridge participation status and settlement times.
    """
    return await call_api("GET", "/api/v1/fx/multi-rail/cbdc")


@mcp.tool(
    name="fx_list_stablecoins",
    annotations={
        "title": "List Available Stablecoins",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_list_stablecoins() -> str:
    """List all supported stablecoins.
    
    Includes regulatory status and fee information.
    """
    return await call_api("GET", "/api/v1/fx/multi-rail/stablecoins")


@mcp.tool(
    name="fx_list_providers",
    annotations={
        "title": "List FX Providers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_list_providers() -> str:
    """List all available FX providers with their capabilities.
    
    Shows reliability scores, latency, markup, and supported pairs.
    """
    return await call_api("GET", "/api/v1/fx/routing/providers")


@mcp.tool(
    name="fx_list_customer_tiers",
    annotations={
        "title": "List Customer Tiers",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_list_customer_tiers() -> str:
    """List all customer pricing tiers.
    
    Shows volume requirements, discounts, and transaction limits.
    Tiers: PLATINUM, GOLD, SILVER, BRONZE, RETAIL
    """
    return await call_api("GET", "/api/v1/fx/routing/customer-tiers")


@mcp.tool(
    name="fx_list_routing_objectives",
    annotations={
        "title": "List Routing Objectives",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_list_routing_objectives() -> str:
    """List available routing objectives with their weight configurations.
    
    Objectives: BEST_RATE, OPTIMUM, FASTEST_EXECUTION, MAX_STP
    """
    return await call_api("GET", "/api/v1/fx/routing/objectives")


@mcp.tool(
    name="fx_health_check",
    annotations={
        "title": "API Health Check",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": True
    }
)
async def fx_health_check() -> str:
    """Check if the FX API server is running and healthy."""
    return await call_api("GET", "/api/v1/fx/health")


# Run server
if __name__ == "__main__":
    mcp.run()
