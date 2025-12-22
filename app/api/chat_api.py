"""
FX Chat API with Claude Tools - Calls Real API Endpoints
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os
import json

router = APIRouter(prefix="/api/v1/fx", tags=["chat"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
API_BASE_URL = "http://127.0.0.1:8000"

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

# Define tools that match your MCP server
TOOLS = [
    {
        "name": "fx_get_rate",
        "description": "Get current FX rate for a currency pair like USDINR, EURUSD, GBPINR. Returns bid, ask, mid rates.",
        "input_schema": {
            "type": "object",
            "properties": {
                "currency_pair": {"type": "string", "description": "Currency pair like USDINR, EURUSD, GBPINR"}
            },
            "required": ["currency_pair"]
        }
    },
    {
        "name": "fx_get_pricing_quote",
        "description": "Get a pricing quote for FX conversion with customer segment and margin breakdown",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_currency": {"type": "string", "description": "Source currency code like USD"},
                "target_currency": {"type": "string", "description": "Target currency code like INR"},
                "amount": {"type": "number", "description": "Amount to convert"},
                "segment": {"type": "string", "description": "Customer segment: RETAIL, SMALL_BUSINESS, MID_MARKET, LARGE_CORPORATE, PRIVATE_BANKING, INSTITUTIONAL"},
                "direction": {"type": "string", "description": "SELL or BUY"}
            },
            "required": ["source_currency", "target_currency", "amount"]
        }
    },
    {
        "name": "fx_list_deals",
        "description": "List all FX treasury deals with their status",
        "input_schema": {
            "type": "object",
            "properties": {
                "status": {"type": "string", "description": "Filter by status: DRAFT, PENDING_APPROVAL, ACTIVE, EXPIRED"},
                "currency_pair": {"type": "string", "description": "Filter by currency pair"}
            },
            "required": []
        }
    },
    {
        "name": "fx_get_active_deals",
        "description": "Get active deals for a specific currency pair",
        "input_schema": {
            "type": "object",
            "properties": {
                "currency_pair": {"type": "string", "description": "Currency pair like USDINR"}
            },
            "required": ["currency_pair"]
        }
    },
    {
        "name": "fx_list_cbdcs",
        "description": "List available CBDCs (Central Bank Digital Currencies) with mBridge support info",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "fx_list_stablecoins",
        "description": "List available stablecoins with regulatory status",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "fx_get_segments",
        "description": "Get customer pricing segments with their margin rates",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "fx_get_tiers",
        "description": "Get amount-based pricing tiers with volume discounts",
        "input_schema": {
            "type": "object",
            "properties": {},
            "required": []
        }
    },
    {
        "name": "fx_recommend_route",
        "description": "Get optimal FX route recommendation for a transaction",
        "input_schema": {
            "type": "object",
            "properties": {
                "currency_pair": {"type": "string", "description": "Currency pair like USDINR"},
                "amount": {"type": "number", "description": "Transaction amount in USD"},
                "side": {"type": "string", "description": "BUY or SELL"},
                "customer_tier": {"type": "string", "description": "PLATINUM, GOLD, SILVER, BRONZE, RETAIL"}
            },
            "required": ["currency_pair", "amount"]
        }
    },
    {
        "name": "fx_multi_rail_route",
        "description": "Find optimal route across Fiat, CBDC, and Stablecoin rails",
        "input_schema": {
            "type": "object",
            "properties": {
                "source_currency": {"type": "string", "description": "Source currency (USD, EUR, e-INR, USDC)"},
                "target_currency": {"type": "string", "description": "Target currency (INR, e-CNY, USDT)"},
                "amount": {"type": "number", "description": "Transaction amount"}
            },
            "required": ["source_currency", "target_currency", "amount"]
        }
    }
]

async def call_api(method: str, endpoint: str, params: dict = None, json_data: dict = None) -> dict:
    """Make HTTP request to FastAPI server"""
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            url = f"{API_BASE_URL}{endpoint}"
            
            if method == "GET":
                response = await client.get(url, params=params)
            elif method == "POST":
                response = await client.post(url, params=params, json=json_data)
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                return {"error": f"API returned status {response.status_code}", "detail": response.text}
    
    except httpx.ConnectError:
        return {"error": "Cannot connect to API endpoint"}
    except Exception as e:
        return {"error": str(e)}

async def execute_tool(tool_name: str, tool_input: dict) -> str:
    """Execute a tool by calling the real API endpoints"""
    
    if tool_name == "fx_get_rate":
        pair = tool_input.get("currency_pair", "USDINR").upper()
        result = await call_api("GET", f"/api/v1/fx/routing/treasury-rates/{pair}")
        return json.dumps(result)
    
    elif tool_name == "fx_get_pricing_quote":
        json_data = {
            "source_currency": tool_input.get("source_currency", "USD"),
            "target_currency": tool_input.get("target_currency", "INR"),
            "amount": tool_input.get("amount", 100000),
            "customer_id": "CHAT-USER",
            "segment": tool_input.get("segment", "MID_MARKET"),
            "direction": tool_input.get("direction", "SELL")
        }
        result = await call_api("POST", "/api/v1/fx/pricing/quote", json_data=json_data)
        return json.dumps(result)
    
    elif tool_name == "fx_list_deals":
        params = {}
        if tool_input.get("status"):
            params["status"] = tool_input["status"]
        if tool_input.get("currency_pair"):
            params["currency_pair"] = tool_input["currency_pair"].upper()
        result = await call_api("GET", "/api/v1/fx/deals", params=params)
        return json.dumps(result)
    
    elif tool_name == "fx_get_active_deals":
        pair = tool_input.get("currency_pair", "USDINR").upper()
        result = await call_api("GET", "/api/v1/fx/deals/active", params={"currency_pair": pair})
        return json.dumps(result)
    
    elif tool_name == "fx_list_cbdcs":
        result = await call_api("GET", "/api/v1/fx/multi-rail/cbdc")
        return json.dumps(result)
    
    elif tool_name == "fx_list_stablecoins":
        result = await call_api("GET", "/api/v1/fx/multi-rail/stablecoins")
        return json.dumps(result)
    
    elif tool_name == "fx_get_segments":
        result = await call_api("GET", "/api/v1/fx/pricing/segments")
        return json.dumps(result)
    
    elif tool_name == "fx_get_tiers":
        result = await call_api("GET", "/api/v1/fx/pricing/tiers")
        return json.dumps(result)
    
    elif tool_name == "fx_recommend_route":
        params = {
            "pair": tool_input.get("currency_pair", "USDINR").upper(),
            "amount": tool_input.get("amount", 100000),
            "side": tool_input.get("side", "SELL"),
            "customer_tier": tool_input.get("customer_tier", "GOLD"),
            "objective": "OPTIMUM"
        }
        result = await call_api("POST", "/api/v1/fx/routing/recommend", params=params)
        return json.dumps(result)
    
    elif tool_name == "fx_multi_rail_route":
        params = {
            "source": tool_input.get("source_currency", "USD").upper(),
            "target": tool_input.get("target_currency", "INR").upper(),
            "amount": tool_input.get("amount", 100000)
        }
        result = await call_api("POST", "/api/v1/fx/multi-rail/route", params=params)
        return json.dumps(result)
    
    return json.dumps({"error": f"Unknown tool: {tool_name}"})

SYSTEM_PROMPT = """You are an FX Smart Routing Assistant powered by Fintaar.ai.

You help users with:
- FX rates for currency pairs (USDINR, EURUSD, GBPINR, USDJPY, etc.)
- Pricing quotes with customer segmentation and margin breakdown
- Treasury deal information and active deals
- CBDC and stablecoin information
- Route recommendations for optimal execution

IMPORTANT: Always use the tools to get real data. Do not make up rates or information.

Tool usage guidelines:
- For rate queries: use fx_get_rate with the currency pair
- For price/quote/conversion: use fx_get_pricing_quote with currencies and amount
- For deals: use fx_list_deals or fx_get_active_deals
- For CBDCs: use fx_list_cbdcs
- For stablecoins: use fx_list_stablecoins
- For segments/tiers: use fx_get_segments or fx_get_tiers
- For routing: use fx_recommend_route or fx_multi_rail_route

Be concise. Format numbers with commas. Show rates to 4 decimal places."""

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not ANTHROPIC_API_KEY:
        return ChatResponse(response="Chat requires ANTHROPIC_API_KEY environment variable. Please set it and restart the server.\n\nExample: export ANTHROPIC_API_KEY='your-key-here'")
    
    try:
        messages = [{"role": "user", "content": request.message}]
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            # Initial request with tools
            response = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1024,
                    "system": SYSTEM_PROMPT,
                    "tools": TOOLS,
                    "messages": messages,
                },
            )
            
            if response.status_code != 200:
                error_detail = response.text
                return ChatResponse(response=f"API error ({response.status_code}): {error_detail[:200]}")
            
            data = response.json()
            
            # Handle tool use loop (max 5 iterations)
            iterations = 0
            while data.get("stop_reason") == "tool_use" and iterations < 5:
                iterations += 1
                assistant_content = data["content"]
                tool_results = []
                
                for block in assistant_content:
                    if block.get("type") == "tool_use":
                        tool_name = block["name"]
                        tool_input = block["input"]
                        print(f"[Chat] Calling tool: {tool_name}")
                        result = await execute_tool(tool_name, tool_input)
                        tool_results.append({
                            "type": "tool_result",
                            "tool_use_id": block["id"],
                            "content": result
                        })
                
                # Add assistant response and tool results
                messages.append({"role": "assistant", "content": assistant_content})
                messages.append({"role": "user", "content": tool_results})
                
                # Continue conversation
                response = await client.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": ANTHROPIC_API_KEY,
                        "anthropic-version": "2023-06-01",
                        "content-type": "application/json",
                    },
                    json={
                        "model": "claude-sonnet-4-20250514",
                        "max_tokens": 1024,
                        "system": SYSTEM_PROMPT,
                        "tools": TOOLS,
                        "messages": messages,
                    },
                )
                
                if response.status_code != 200:
                    return ChatResponse(response=f"API error: {response.status_code}")
                
                data = response.json()
            
            # Extract final text
            final_text = ""
            for block in data.get("content", []):
                if block.get("type") == "text":
                    final_text += block.get("text", "")
            
            return ChatResponse(response=final_text or "No response generated")
    
    except httpx.TimeoutException:
        return ChatResponse(response="Request timed out. Please try again.")
    except Exception as e:
        return ChatResponse(response=f"Error: {str(e)}")
