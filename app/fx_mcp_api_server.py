"""
FX Smart Routing MCP Server - API Integration
Calls FastAPI endpoints for FX routing recommendations and deals
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

class DealStatus(str, Enum):
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"
    REJECTED = "REJECTED"
    FULLY_UTILIZED = "FULLY_UTILIZED"

# Input Models - Existing
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

# Input Models - Deals
class CreateDealInput(BaseModel):
    currency_pair: str = Field(..., description="Currency pair e.g. USDINR")
    side: Side = Field(..., description="BUY or SELL from treasury perspective")
    buy_rate: float = Field(..., gt=0, description="Rate treasury buys at")
    sell_rate: float = Field(..., gt=0, description="Rate treasury sells at")
    amount: float = Field(..., gt=0, description="Total deal amount")
    valid_from: str = Field(..., description="Start of validity (ISO format)")
    valid_until: str = Field(..., description="End of validity (ISO format)")
    customer_tier: Optional[CustomerTier] = Field(None, description="Restrict to specific tier")
    min_amount: float = Field(default=1000, ge=0, description="Minimum transaction size")
    max_amount_per_txn: Optional[float] = Field(None, description="Maximum per transaction")
    notes: Optional[str] = Field(None, description="Internal notes")
    created_by: str = Field(..., description="Treasury user ID")

class GetDealInput(BaseModel):
    deal_id: str = Field(..., description="Deal ID")

class ListDealsInput(BaseModel):
    status: Optional[DealStatus] = Field(None, description="Filter by status")
    currency_pair: Optional[str] = Field(None, description="Filter by currency pair")

class SubmitDealInput(BaseModel):
    deal_id: str = Field(..., description="Deal ID")
    submitted_by: str = Field(..., description="User submitting for approval")

class ApproveDealInput(BaseModel):
    deal_id: str = Field(..., description="Deal ID")
    approved_by: str = Field(..., description="Approver user ID")
    comments: Optional[str] = Field(None, description="Approval comments")

class RejectDealInput(BaseModel):
    deal_id: str = Field(..., description="Deal ID")
    rejected_by: str = Field(..., description="Rejector user ID")
    rejection_reason: str = Field(..., description="Reason for rejection")

class UtilizeDealInput(BaseModel):
    deal_id: str = Field(..., description="Deal ID")
    amount: float = Field(..., gt=0, description="Amount to utilize")
    customer_id: str = Field(..., description="Customer identifier")
    customer_tier: CustomerTier = Field(..., description="Customer tier")
    transaction_ref: Optional[str] = Field(None, description="External reference")

class BestRateInput(BaseModel):
    currency_pair: str = Field(..., description="Currency pair")
    side: Side = Field(..., description="BUY or SELL")
    amount: float = Field(..., gt=0, description="Transaction amount")
    customer_tier: CustomerTier = Field(..., description="Customer tier")
    treasury_rate: float = Field(..., gt=0, description="Current treasury rate")

class ActiveDealsInput(BaseModel):
    currency_pair: str = Field(..., description="Currency pair")
    customer_tier: Optional[CustomerTier] = Field(None, description="Customer tier")


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
            elif method == "PUT":
                response = await client.put(url, params=params, json=json_data)
            elif method == "DELETE":
                response = await client.request("DELETE", url, params=params, json=json_data)
            
            if response.status_code in [200, 201]:
                return json.dumps(response.json(), indent=2, default=str)
            else:
                return json.dumps({"error": f"API returned status {response.status_code}", "detail": response.text})
    
    except httpx.ConnectError:
        return json.dumps({
            "error": "Cannot connect to FX API server",
            "hint": "Make sure FastAPI is running: python -m uvicorn app.main:app --port 8000"
        })
    except Exception as e:
        return json.dumps({"error": str(e)})


# ============== Existing MCP Tools ==============

@mcp.tool(name="fx_get_rate")
async def fx_get_rate(params: GetRateInput) -> str:
    """Get current FX rate for a currency pair. Returns bid, ask, mid rates and treasury position."""
    pair = params.currency_pair.upper()
    return await call_api("GET", f"/api/v1/fx/routing/treasury-rates/{pair}")

@mcp.tool(name="fx_get_effective_rate")
async def fx_get_effective_rate(params: EffectiveRateInput) -> str:
    """Calculate effective FX rate with all adjustments (tier, volume, position)."""
    pair = params.currency_pair.upper()
    query_params = {
        "side": params.side.value,
        "amount": params.amount_usd,
        "customer_tier": params.customer_tier.value
    }
    return await call_api("GET", f"/api/v1/fx/routing/effective-rate/{pair}", params=query_params)

@mcp.tool(name="fx_recommend_route")
async def fx_recommend_route(params: RouteRecommendInput) -> str:
    """Get optimal FX route recommendation with provider ranking."""
    query_params = {
        "pair": params.currency_pair.upper(),
        "amount": params.amount_usd,
        "side": params.side.value,
        "customer_tier": params.customer_tier.value,
        "objective": params.objective.value
    }
    return await call_api("POST", "/api/v1/fx/routing/recommend", params=query_params)

@mcp.tool(name="fx_multi_rail_route")
async def fx_multi_rail_route(params: MultiRailRouteInput) -> str:
    """Find optimal route across Fiat, CBDC, and Stablecoin rails."""
    query_params = {
        "source": params.source_currency.upper(),
        "target": params.target_currency.upper(),
        "amount": params.amount
    }
    return await call_api("POST", "/api/v1/fx/multi-rail/route", params=query_params)

@mcp.tool(name="fx_list_cbdc")
async def fx_list_cbdc() -> str:
    """List all supported Central Bank Digital Currencies (CBDCs)."""
    return await call_api("GET", "/api/v1/fx/multi-rail/cbdc")

@mcp.tool(name="fx_list_stablecoins")
async def fx_list_stablecoins() -> str:
    """List all supported stablecoins."""
    return await call_api("GET", "/api/v1/fx/multi-rail/stablecoins")

@mcp.tool(name="fx_list_providers")
async def fx_list_providers() -> str:
    """List all available FX providers with their capabilities."""
    return await call_api("GET", "/api/v1/fx/routing/providers")

@mcp.tool(name="fx_list_customer_tiers")
async def fx_list_customer_tiers() -> str:
    """List all customer pricing tiers."""
    return await call_api("GET", "/api/v1/fx/routing/customer-tiers")

@mcp.tool(name="fx_list_routing_objectives")
async def fx_list_routing_objectives() -> str:
    """List available routing objectives with their weight configurations."""
    return await call_api("GET", "/api/v1/fx/routing/objectives")

@mcp.tool(name="fx_health_check")
async def fx_health_check() -> str:
    """Check if the FX API server is running and healthy."""
    return await call_api("GET", "/api/v1/fx/health")


# ============== Deal MCP Tools ==============

@mcp.tool(name="fx_create_deal")
async def fx_create_deal(params: CreateDealInput) -> str:
    """Create a new FX deal in DRAFT status. Treasury creates deals with locked-in rates."""
    json_data = {
        "currency_pair": params.currency_pair.upper(),
        "side": params.side.value,
        "buy_rate": params.buy_rate,
        "sell_rate": params.sell_rate,
        "amount": params.amount,
        "valid_from": params.valid_from,
        "valid_until": params.valid_until,
        "customer_tier": params.customer_tier.value if params.customer_tier else None,
        "min_amount": params.min_amount,
        "max_amount_per_txn": params.max_amount_per_txn,
        "notes": params.notes,
        "created_by": params.created_by
    }
    return await call_api("POST", "/api/v1/fx/deals", json_data=json_data)

@mcp.tool(name="fx_get_deal")
async def fx_get_deal(params: GetDealInput) -> str:
    """Get deal details by ID."""
    return await call_api("GET", f"/api/v1/fx/deals/{params.deal_id}")

@mcp.tool(name="fx_list_deals")
async def fx_list_deals(params: ListDealsInput) -> str:
    """List all deals with optional status and currency pair filters."""
    query_params = {}
    if params.status:
        query_params["status"] = params.status.value
    if params.currency_pair:
        query_params["currency_pair"] = params.currency_pair.upper()
    return await call_api("GET", "/api/v1/fx/deals", params=query_params)

@mcp.tool(name="fx_submit_deal")
async def fx_submit_deal(params: SubmitDealInput) -> str:
    """Submit a DRAFT deal for approval. Changes status to PENDING_APPROVAL."""
    json_data = {"submitted_by": params.submitted_by}
    return await call_api("POST", f"/api/v1/fx/deals/{params.deal_id}/submit", json_data=json_data)

@mcp.tool(name="fx_approve_deal")
async def fx_approve_deal(params: ApproveDealInput) -> str:
    """Approve a PENDING_APPROVAL deal. Changes status to ACTIVE. Self-approval not allowed."""
    json_data = {
        "approved_by": params.approved_by,
        "comments": params.comments
    }
    return await call_api("POST", f"/api/v1/fx/deals/{params.deal_id}/approve", json_data=json_data)

@mcp.tool(name="fx_reject_deal")
async def fx_reject_deal(params: RejectDealInput) -> str:
    """Reject a PENDING_APPROVAL deal with reason. Changes status to REJECTED."""
    json_data = {
        "rejected_by": params.rejected_by,
        "rejection_reason": params.rejection_reason
    }
    return await call_api("POST", f"/api/v1/fx/deals/{params.deal_id}/reject", json_data=json_data)

@mcp.tool(name="fx_utilize_deal")
async def fx_utilize_deal(params: UtilizeDealInput) -> str:
    """Utilize part of an ACTIVE deal. Supports partial utilization."""
    json_data = {
        "amount": params.amount,
        "customer_id": params.customer_id,
        "customer_tier": params.customer_tier.value,
        "transaction_ref": params.transaction_ref
    }
    return await call_api("POST", f"/api/v1/fx/deals/{params.deal_id}/utilize", json_data=json_data)

@mcp.tool(name="fx_get_active_deals")
async def fx_get_active_deals(params: ActiveDealsInput) -> str:
    """Get active deals for a currency pair, optionally filtered by customer tier."""
    query_params = {"currency_pair": params.currency_pair.upper()}
    if params.customer_tier:
        query_params["customer_tier"] = params.customer_tier.value
    return await call_api("GET", "/api/v1/fx/deals/active", params=query_params)

@mcp.tool(name="fx_get_best_rate")
async def fx_get_best_rate(params: BestRateInput) -> str:
    """Get best available rate - checks active deals first, falls back to treasury rate."""
    query_params = {
        "currency_pair": params.currency_pair.upper(),
        "side": params.side.value,
        "amount": params.amount,
        "customer_tier": params.customer_tier.value,
        "treasury_rate": params.treasury_rate
    }
    return await call_api("GET", "/api/v1/fx/deals/best-rate", params=query_params)

@mcp.tool(name="fx_deal_audit_log")
async def fx_deal_audit_log(params: GetDealInput) -> str:
    """Get audit log history for a deal. Shows all actions taken on the deal."""
    return await call_api("GET", f"/api/v1/fx/deals/{params.deal_id}/audit-log")

@mcp.tool(name="fx_deal_utilizations")
async def fx_deal_utilizations(params: GetDealInput) -> str:
    """Get utilization history for a deal. Shows all partial utilizations."""
    return await call_api("GET", f"/api/v1/fx/deals/{params.deal_id}/utilizations")


# Run server
if __name__ == "__main__":
    mcp.run()
