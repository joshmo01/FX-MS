from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.multi_rail_api import router as multi_rail_router

app = FastAPI(
    title="FX Smart Routing Engine",
    description="Universal Currency Conversion: Fiat, CBDC, Stablecoin with Atomic Swaps",
    version="2.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v2.0 multi-rail routes
app.include_router(multi_rail_router)

@app.get("/")
def root():
    return {
        "service": "FX Smart Routing Engine",
        "version": "2.0.0",
        "status": "running",
        "features": ["9 conversion types", "CBDC", "Stablecoin", "mBridge", "Atomic Swaps"],
        "docs": "/docs"
    }

@app.get("/api/v1/fx/health")
def health():
    return {"status": "healthy", "version": "2.0.0"}
