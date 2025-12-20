# FX Pricing Integration for FX-MS

## Quick Start

### Step 1: Copy Files

Copy these files to your FX-MS repository:

```bash
# From fx-ms-files/ directory:

# 1. Domain models
cp app/models/pricing.py → FX-MS/app/models/pricing.py

# 2. Create core directory if needed
mkdir -p FX-MS/app/core
cp app/core/pricing_engine.py → FX-MS/app/core/pricing_engine.py
touch FX-MS/app/core/__init__.py

# 3. Services
cp app/services/pricing_service.py → FX-MS/app/services/pricing_service.py

# 4. API endpoints
cp app/api/pricing.py → FX-MS/app/api/pricing.py

# 5. Configuration data
cp app/data/segments.json → FX-MS/app/data/segments.json
cp app/data/tiers.json → FX-MS/app/data/tiers.json
cp app/data/currency_markups.json → FX-MS/app/data/currency_markups.json

# 6. Tests
cp tests/test_pricing.py → FX-MS/tests/test_pricing.py
```

### Step 2: Update main.py

Add to your `app/main.py`:

```python
# Add import
from app.api.pricing import router as pricing_router

# Add router (after conversion_router)
app.include_router(pricing_router)
```

### Step 3: Connect to Your FX Rate Service

Edit `app/api/pricing.py` and update the `get_pricing_service_dep()` function:

```python
def get_pricing_service_dep() -> PricingService:
    # Uncomment and use your actual service:
    from app.services.fx_provider import get_fx_rate_service
    fx_service = get_fx_rate_service()
    return PricingService(fx_rate_service=fx_service)
```

### Step 4: Test

```bash
# Run tests
pytest tests/test_pricing.py -v

# Start server
uvicorn app.main:app --reload

# Test endpoints
curl http://localhost:8000/api/v1/fx/pricing/health
curl http://localhost:8000/api/v1/fx/pricing/segments
curl http://localhost:8000/api/v1/fx/pricing/tiers

# Generate a priced quote
curl -X POST http://localhost:8000/api/v1/fx/pricing/quote \
  -H "Content-Type: application/json" \
  -d '{
    "source_currency": "USD",
    "target_currency": "INR",
    "amount": 100000,
    "customer_id": "CUST-001",
    "segment": "MID_MARKET",
    "direction": "SELL"
  }'
```

## New Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/fx/pricing/quote` | Generate priced quote |
| GET | `/api/v1/fx/pricing/segments` | List customer segments |
| GET | `/api/v1/fx/pricing/tiers` | List amount tiers |
| GET | `/api/v1/fx/pricing/margin/{base}/{quote}` | Get margin info |
| POST | `/api/v1/fx/pricing/margin/calculate` | Calculate margin |
| GET | `/api/v1/fx/pricing/categories` | List currency categories |
| GET | `/api/v1/fx/pricing/health` | Health check |

## Files Added

```
FX-MS/
├── app/
│   ├── api/
│   │   └── pricing.py          ← NEW (API endpoints)
│   ├── core/
│   │   ├── __init__.py         ← NEW (empty)
│   │   └── pricing_engine.py   ← NEW (core logic)
│   ├── data/
│   │   ├── segments.json       ← NEW (6 customer segments)
│   │   ├── tiers.json          ← NEW (6 amount tiers)
│   │   └── currency_markups.json ← NEW (currency categories)
│   ├── models/
│   │   └── pricing.py          ← NEW (domain models)
│   └── services/
│       └── pricing_service.py  ← NEW (service layer)
└── tests/
    └── test_pricing.py         ← NEW (unit tests)
```

## Pricing Logic Summary

```
Customer Rate = Mid-Rate × (1 ± Margin)

Margin = Base + Tier Adjustment + Currency Factor - Discount

Where:
- Base: From customer segment (5-300 bps)
- Tier: From transaction amount (-40 to +50 bps)
- Currency: From pair category (2-300 bps)
- Discount: Negotiated customer discount
```

### Customer Segments

| Segment | Base Margin | Range |
|---------|-------------|-------|
| INSTITUTIONAL | 5 bps | 2-20 |
| LARGE_CORPORATE | 25 bps | 10-75 |
| MID_MARKET | 75 bps | 40-150 |
| SMALL_BUSINESS | 150 bps | 100-250 |
| RETAIL | 300 bps | 200-500 |
| PRIVATE_BANKING | 50 bps | 20-100 |

### Amount Tiers

| Tier | Amount Range | Adjustment |
|------|--------------|------------|
| TIER_1 | < $10K | +50 bps |
| TIER_2 | $10K-$50K | +25 bps |
| TIER_3 | $50K-$100K | 0 bps |
| TIER_4 | $100K-$500K | -15 bps |
| TIER_5 | $500K-$1M | -25 bps |
| TIER_6 | > $1M | -40 bps |

### Currency Categories

| Category | Currencies | Retail Markup |
|----------|------------|---------------|
| G10 | USD, EUR, JPY, GBP, etc. | 50 bps |
| MINOR | SGD, HKD, DKK, etc. | 100 bps |
| EXOTIC | TRY, ZAR, MXN, BRL | 200 bps |
| RESTRICTED | INR, CNY, KRW, etc. | 300 bps |

## Example Response

```json
{
  "quote_id": "PQ-20241220143052-A1B2C3D4",
  "source_currency": "USD",
  "target_currency": "INR",
  "mid_rate": 83.5,
  "customer_rate": 82.4525,
  "margin_bps": 125.0,
  "margin_percent": 1.25,
  "margin_breakdown": {
    "segment_base_bps": 75.0,
    "tier_adjustment_bps": -15.0,
    "currency_factor_bps": 100.0,
    "negotiated_discount_bps": 0.0
  },
  "source_amount": 100000.0,
  "target_amount": 8245250.0,
  "segment": "MID_MARKET",
  "amount_tier": "TIER_4",
  "currency_category": "RESTRICTED",
  "valid_until": "2024-12-20T14:31:22.123456Z",
  "rate_type": "FIRM"
}
```
