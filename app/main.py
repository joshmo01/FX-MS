from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.multi_rail_api import router as multi_rail_router
from app.api.routing_api import router as routing_router

app = FastAPI(
    title="FX Smart Routing Engine",
    description="Universal Currency Conversion with Treasury Management, Customer Tiers, and Multi-Rail Routing",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(routing_router)
app.include_router(multi_rail_router)

@app.get("/")
def root():
    return {
        "service": "FX Smart Routing Engine",
        "version": "2.0.0",
        "status": "running",
        "features": [
            "Treasury rate management",
            "Customer tier pricing",
            "7 FX providers",
            "4 routing objectives",
            "9 conversion types",
            "CBDC support",
            "Stablecoin support",
            "mBridge routing",
            "Atomic swaps"
        ],
        "docs": "/docs"
    }

@app.get("/api/v1/fx/health")
def health():
    return {"status": "healthy", "version": "2.0.0"}
