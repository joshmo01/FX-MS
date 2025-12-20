"""
FX Smart Routing Engine v2.1.0
Main FastAPI Application
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from pathlib import Path
from app.api.pricing import router as pricing_router
from app.api.routing_api import router as routing_router
from app.api.multi_rail_api import router as multi_rail_router
from app.api.deals_api import router as deals_router
from app.api.chat_api import router as chat_router

app = FastAPI(
    title="FX Smart Routing Engine",
    description="Multi-rail FX routing with CBDC, Stablecoin support and Treasury Deals",
    version="2.1.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routing_router)
app.include_router(multi_rail_router)
app.include_router(deals_router)
app.include_router(chat_router)
app.include_router(pricing_router)

@app.get("/")
async def root():
    return {
        "service": "FX Smart Routing Engine",
        "version": "2.1.0",
        "features": [
            "Treasury rate management",
            "Customer tier pricing",
            "Multi-provider routing",
            "CBDC support (6 currencies)",
            "Stablecoin support (5 coins)",
            "mBridge cross-border",
            "Treasury deals with approval workflow",
            "Chat assistant"
        ]
    }

@app.get("/api/v1/fx/health")
async def health():
    return {"status": "healthy", "version": "2.1.0"}

@app.get("/ui", response_class=HTMLResponse, include_in_schema=False)
async def pricing_ui():
    """Serve the FX Pricing UI"""
    html_path = Path(__file__).parent / "static" / "index.html"
    if html_path.exists():
        return html_path.read_text()
    return "<h1>UI not found</h1><p>Place index.html in app/static/</p>"