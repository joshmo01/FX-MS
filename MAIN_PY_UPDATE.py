"""
INSTRUCTIONS: How to update your existing main.py
=================================================

Add these lines to your existing app/main.py file:

1. Add import at the top (with other imports):
"""

# Add this import
from app.api.pricing import router as pricing_router


"""
2. Add the router (where other routers are included):

Find where you include the conversion router, and add pricing router:
"""

# Example - your main.py might look like this:

from fastapi import FastAPI
from app.api.conversion import router as conversion_router
from app.api.pricing import router as pricing_router  # <-- ADD THIS

app = FastAPI(
    title="FX Currency Conversion Microservice",
    description="Real-time currency conversion with Refinitiv integration and customer pricing",
    version="2.0.0"
)

# Include routers
app.include_router(conversion_router)
app.include_router(pricing_router)  # <-- ADD THIS


"""
3. Optionally, create an __init__.py in app/core/ if it doesn't exist:
"""

# app/core/__init__.py
# (can be empty, just needs to exist)


"""
4. Full example main.py with pricing integrated:
"""

# ============================================
# COMPLETE MAIN.PY EXAMPLE
# ============================================

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Import routers
from app.api.conversion import router as conversion_router
from app.api.pricing import router as pricing_router

app = FastAPI(
    title="FX Currency Conversion Microservice",
    description="Real-time currency conversion with Refinitiv integration and customer-specific pricing",
    version="2.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(conversion_router)  # Existing conversion endpoints
app.include_router(pricing_router)      # NEW pricing endpoints


@app.get("/")
async def root():
    return {
        "service": "FX Currency Conversion Microservice",
        "version": "2.0.0",
        "endpoints": {
            "conversion": "/api/v1/fx/convert",
            "pricing": "/api/v1/fx/pricing/quote",
            "docs": "/docs"
        }
    }


@app.get("/health")
async def health():
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
