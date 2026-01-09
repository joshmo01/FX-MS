"""
FX Smart Routing - Main Application

Comprehensive FX routing system supporting:
- Traditional Fiat FX
- CBDC (Central Bank Digital Currencies)
- Stablecoins (USDC, USDT, etc.)
- All cross-type conversions

9 Conversion Types Supported:
1. FIAT ↔ FIAT
2. FIAT ↔ CBDC
3. CBDC ↔ FIAT
4. CBDC ↔ CBDC
5. FIAT ↔ STABLECOIN
6. STABLECOIN ↔ FIAT
7. STABLECOIN ↔ STABLECOIN
8. CBDC ↔ STABLECOIN
9. STABLECOIN ↔ CBDC
"""
import logging
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import time
import uuid

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    logger.info("🚀 Starting FX Smart Routing Engine...")
    logger.info("📊 Supported conversions: 9 types")
    logger.info("🏛️ CBDCs: e-INR, e-CNY, e-HKD, e-THB, e-AED, e-SGD")
    logger.info("🪙 Stablecoins: USDC, USDT, EURC, PYUSD, XSGD")
    yield
    logger.info("👋 Shutting down FX Smart Routing Engine...")


# Create FastAPI app
app = FastAPI(
    title="FX Smart Routing Engine",
    description="""
    ## Universal FX Conversion Engine
    
    Intelligent routing across all payment rails:
    
    ### Supported Currency Types
    - **Fiat**: USD, EUR, GBP, INR, SGD, AED, CNY, HKD, THB, JPY
    - **CBDC**: e-INR, e-CNY, e-HKD, e-THB, e-AED, e-SGD
    - **Stablecoin**: USDC, USDT, EURC, PYUSD, XSGD
    
    ### Conversion Types (9)
    1. FIAT → FIAT (Traditional FX)
    2. FIAT → CBDC (Mint)
    3. CBDC → FIAT (Redeem)
    4. CBDC → CBDC (mBridge / Cross-border)
    5. FIAT → STABLECOIN (On-ramp)
    6. STABLECOIN → FIAT (Off-ramp)
    7. STABLECOIN → STABLECOIN (DEX/CEX)
    8. CBDC → STABLECOIN (Bridge)
    9. STABLECOIN → CBDC (Bridge)
    
    ### Features
    - Multi-provider comparison
    - Treasury integration
    - Customer tier pricing
    - Compliance scoring
    - Settlement time optimization
    """,
    version="2.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request ID middleware
@app.middleware("http")
async def add_request_id(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    start_time = time.time()
    
    response = await call_next(request)
    
    process_time = time.time() - start_time
    response.headers["X-Request-ID"] = request_id
    response.headers["X-Process-Time"] = str(process_time)
    
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    
    return response


# Global exception handler
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={"detail": "Internal server error", "error": str(exc)}
    )


# Import and include routers
from app.api.routing_api import router as routing_router
from app.api.multi_rail_api import router as multi_rail_router
from app.api.universal_api import router as universal_router

app.include_router(routing_router)
app.include_router(multi_rail_router)
app.include_router(universal_router)


# Root endpoint
@app.get("/", tags=["Root"])
async def root():
    """Welcome endpoint with API overview"""
    return {
        "service": "FX Smart Routing Engine",
        "version": "2.0.0",
        "description": "Universal FX routing across Fiat, CBDC, and Stablecoin",
        "endpoints": {
            "smart_routing": "/api/v1/fx/routing/recommend",
            "multi_rail": "/api/v1/fx/multi-rail/route",
            "universal": "/api/v1/fx/universal/convert",
            "docs": "/docs",
            "redoc": "/redoc"
        },
        "supported_conversions": [
            "FIAT_TO_FIAT",
            "FIAT_TO_CBDC",
            "CBDC_TO_FIAT",
            "CBDC_TO_CBDC",
            "FIAT_TO_STABLECOIN",
            "STABLECOIN_TO_FIAT",
            "STABLECOIN_TO_STABLECOIN",
            "CBDC_TO_STABLECOIN",
            "STABLECOIN_TO_CBDC"
        ]
    }


# Health check
@app.get("/health", tags=["Health"])
async def health_check():
    """Overall health check"""
    return {
        "status": "healthy",
        "service": "FX Smart Routing Engine",
        "version": "2.0.0",
        "components": {
            "smart_routing": "operational",
            "multi_rail": "operational",
            "universal_conversion": "operational"
        }
    }


# API summary
@app.get("/api", tags=["API Info"])
async def api_info():
    """API information and capabilities"""
    return {
        "api_version": "v1",
        "capabilities": {
            "fiat_currencies": ["USD", "EUR", "GBP", "INR", "SGD", "AED", "CNY", "HKD", "THB", "JPY"],
            "cbdc_currencies": ["e-INR", "e-CNY", "e-HKD", "e-THB", "e-AED", "e-SGD"],
            "stablecoins": ["USDC", "USDT", "EURC", "PYUSD", "XSGD"],
            "mbridge_participants": ["e-CNY", "e-HKD", "e-THB", "e-AED"],
            "stablecoin_networks": ["ETHEREUM", "POLYGON", "SOLANA", "TRON", "AVALANCHE"]
        },
        "features": {
            "multi_provider_routing": True,
            "treasury_integration": True,
            "customer_tier_pricing": True,
            "cbdc_support": True,
            "stablecoin_bridge": True,
            "atomic_settlement": True,
            "compliance_scoring": True
        }
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
