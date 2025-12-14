"""
Chat API - Claude integration for FX Assistant
"""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
import httpx
import os

router = APIRouter(prefix="/api/v1/fx", tags=["Chat"])

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

class ChatRequest(BaseModel):
    message: str

class ChatResponse(BaseModel):
    response: str

SYSTEM_PROMPT = """You are an FX Smart Routing Assistant for a treasury desk. You help users with:
- FX rates for currency pairs (USDINR, EURUSD, GBPUSD, etc.)
- Treasury deal management (creating, approving, utilizing deals)
- Route recommendations for FX transactions
- CBDC and stablecoin information

Current rates (approximate):
- USDINR: 84.42 / 84.58
- EURUSD: 1.0550 / 1.0564
- GBPUSD: 1.2590 / 1.2610
- USDJPY: 149.80 / 150.10

Available CBDCs: e-INR (RBI), e-CNY (PBoC), e-HKD (HKMA), e-THB (BoT), e-AED (CBUAE), e-SGD (MAS)
Available Stablecoins: USDC, USDT, EURC, PYUSD, XSGD

Be concise and helpful. Format numbers clearly. If asked about specific rates, provide the approximate values above."""

@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    if not ANTHROPIC_API_KEY:
        # Return a helpful response even without API key
        return ChatResponse(response=get_fallback_response(request.message))
    
    try:
        async with httpx.AsyncClient() as client:
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
                    "messages": [{"role": "user", "content": request.message}],
                },
                timeout=30.0,
            )
            
            if response.status_code != 200:
                return ChatResponse(response=get_fallback_response(request.message))
            
            data = response.json()
            return ChatResponse(response=data["content"][0]["text"])
    
    except Exception as e:
        return ChatResponse(response=get_fallback_response(request.message))


def get_fallback_response(message: str) -> str:
    """Provide basic responses without API"""
    msg = message.lower()
    
    if "usdinr" in msg or "usd inr" in msg:
        return "USDINR rates:\n• Bid: 84.42\n• Ask: 84.58\n• Position: LONG"
    
    if "eurusd" in msg or "eur usd" in msg:
        return "EURUSD rates:\n• Bid: 1.0550\n• Ask: 1.0564\n• Position: LONG"
    
    if "gbpusd" in msg or "gbp usd" in msg:
        return "GBPUSD rates:\n• Bid: 1.2590\n• Ask: 1.2610\n• Position: NEUTRAL"
    
    if "rate" in msg:
        return "Available rates:\n• USDINR: 84.42/84.58\n• EURUSD: 1.0550/1.0564\n• GBPUSD: 1.2590/1.2610\n• USDJPY: 149.80/150.10"
    
    if "cbdc" in msg:
        return "Available CBDCs:\n• e-INR (RBI, India)\n• e-CNY (PBoC, China) - mBridge\n• e-HKD (HKMA) - mBridge\n• e-THB (BoT) - mBridge\n• e-AED (CBUAE) - mBridge\n• e-SGD (MAS)"
    
    if "stablecoin" in msg:
        return "Available Stablecoins:\n• USDC (Circle) ✅ Regulated\n• USDT (Tether)\n• EURC (Circle) ✅ Regulated\n• PYUSD (Paxos) ✅ Regulated\n• XSGD (StraitsX) ✅ Regulated"
    
    if "deal" in msg:
        return "To manage deals:\n• Go to the Deals tab to create new deals\n• Submit deals for approval\n• Approve pending deals\n• Active deals can be utilized by customers"
    
    if "help" in msg:
        return "I can help you with:\n• FX rates (ask 'USDINR rate')\n• CBDC info (ask 'list CBDCs')\n• Stablecoin info (ask 'stablecoins')\n• Deal management (ask 'how to create deal')"
    
    return "I can help with FX rates, CBDCs, stablecoins, and deal management. Try asking:\n• 'USDINR rate'\n• 'List CBDCs'\n• 'Show stablecoins'\n• 'How to create a deal'"
