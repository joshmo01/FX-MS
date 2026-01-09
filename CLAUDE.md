# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FX Smart Routing Engine v2.x - A multi-rail FX routing system supporting traditional FIAT, CBDC (Central Bank Digital Currencies), and Stablecoin rails with atomic swap support.

**Structure:**
- **Backend**: Python FastAPI service (this directory)
- **Frontend**: React + Vite application (`fx-ui/`)

## Common Commands

### Backend

```bash
# Install dependencies
pip install -r requirements.txt

# Run API server (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
# Or via make
make run

# Run all tests
pytest tests/ -v
make test

# Run single test file
pytest tests/api/test_01_routing_api.py -v

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=html
make test-cov

# Format code
black app/ tests/
isort app/ tests/
make format

# Type checking
mypy app/
make lint

# Run demo scenarios
python demo_all_routes.py --mode quick    # Key scenarios
python demo_all_routes.py --mode full     # All 30+ scenarios
python demo_all_routes.py --mode atomic   # Atomic swap focused
make demo
```

### Frontend (`fx-ui/`)

```bash
cd fx-ui
npm install
npm run dev     # Development server on :5173
npm run build   # Production build
npm run lint
```

### Docker

```bash
docker build -t fx-smart-routing:latest .
docker run -p 8000:8000 fx-smart-routing:latest
```

## Architecture

### Backend Structure (`app/`)

```
app/
├── main.py                 # FastAPI entry, router registration, CORS setup
├── api/                    # API route handlers (all under /api/v1/fx/)
│   ├── routing_api.py      # Traditional FX routing, provider recommendation
│   ├── multi_rail_api.py   # CBDC & Stablecoin multi-rail routing
│   ├── deals_api.py        # Treasury deals CRUD & approval workflow
│   ├── pricing.py          # Customer-specific pricing with segmentation
│   ├── rules_api.py        # Dynamic pricing rules management
│   ├── chat_api.py         # AI assistant (requires ANTHROPIC_API_KEY)
│   └── admin_api.py        # Reference table CRUD
├── services/               # Business logic layer
│   ├── smart_routing_engine.py   # Core routing with objective-based scoring
│   ├── deals_service.py          # Deal lifecycle: DRAFT→PENDING→ACTIVE
│   ├── pricing_service.py        # Margin calculations with tier/segment
│   ├── fx_provider.py            # Provider configs and rate adjustments
│   └── rules_engine/             # Dynamic JSON rules evaluation
│       ├── engine.py             # Rule execution and action application
│       ├── evaluator.py          # Condition matching logic
│       ├── loader.py             # JSON rule loading from config/rules/
│       └── models.py             # Rule, Condition, Action Pydantic models
└── models/                 # Request/Response Pydantic models
```

### Frontend Structure (`fx-ui/src/`)

```
src/
├── App.jsx                 # Main app: dashboard, deals, rates, routes, pricing, rules tabs
├── services/api.js         # Axios client with all API endpoints
└── components/
    ├── FXRulesManager.jsx  # Dynamic pricing rules UI (create/edit/toggle)
    ├── AdminPanel.jsx      # Reference table management
    └── *Table.jsx          # Various data display components
```

### Configuration (`config/`)

- `treasury_rates.json` - FX rates with bid/ask/mid and treasury position
- `customer_tiers.json` - Tier configs (PLATINUM→RETAIL with discount percentages)
- `fx_providers.json` - 7 providers with STP capability, latency, reliability scores
- `pricing_segments.json` - Customer segments (RETAIL→INSTITUTIONAL margins)
- `pricing_tiers.json` - Amount-based tier adjustments
- `rules/pricing_rules.json` - Dynamic margin adjustment rules

### Data Files (`data/`)

- `deals.json` - Persistent deal storage
- `deal_audit_log.json` - Deal workflow audit trail

## API Structure

Base path: `/api/v1/fx/`

| Module | Endpoints |
|--------|-----------|
| Routing | `POST /routing/recommend`, `GET /routing/treasury-rates`, `GET /routing/providers` |
| Multi-Rail | `POST /multi-rail/route`, `GET /multi-rail/cbdc`, `GET /multi-rail/stablecoins` |
| Pricing | `POST /pricing/quote`, `GET /pricing/segments`, `GET /pricing/tiers` |
| Deals | `GET/POST /deals`, `POST /deals/{id}/submit`, `POST /deals/{id}/approve` |
| Rules | `GET/POST/DELETE /rules/`, `POST /rules/{id}/toggle` |
| Admin | `GET/POST/PUT/DELETE /admin/{resource_type}` |
| Chat | `POST /chat` |

## Key Domain Concepts

**Rails:**
- FIAT: Traditional bank transfers (SWIFT/local) - 1-2 day settlement
- CBDC: e-INR, e-CNY, e-HKD, e-THB, e-AED, e-SGD - near-instant via mBridge
- STABLECOIN: USDC, USDT, EURC, PYUSD, XSGD - minutes to hours

**Routing Objectives:** BEST_RATE (70% rate weight), OPTIMUM (balanced), FASTEST_EXECUTION (45% speed), MAX_STP (40% automation)

**Customer Tiers:** PLATINUM (50% discount) → GOLD → SILVER → BRONZE → RETAIL (0% discount)

**Deal Workflow:** DRAFT → (submit) → PENDING_APPROVAL → (approve) → ACTIVE → EXPIRED/FULLY_UTILIZED

**Rules Engine:** JSON-based conditions (currency_pair, segment, amount_range) → actions (set_margin_bps, adjust_margin_bps, select_provider)

## Environment Variables

```bash
ANTHROPIC_API_KEY=xxx    # Required for chat API
```

Frontend (`fx-ui/.env`):
```bash
VITE_API_BASE_URL=http://127.0.0.1:8000
```

## Testing

Tests in `tests/api/` follow numbered convention for execution order:
- `test_01_routing_api.py` - Basic routing
- `test_03_deals_api.py` - Deal CRUD
- `test_04_deals_workflow_api.py` - Approval workflow
- `test_05_pricing_api.py` - Pricing with segments/tiers
- `test_06_rules_api.py` - Rules engine
- `test_10_negative_tests.py` - Error handling
- `test_11_edge_cases.py` - Boundary conditions
- `test_12_integration.py` - End-to-end flows

Base test setup in `tests/base/test_base.py`.

## Deployment

### Render (Backend)

Configured via `render.yaml`:
- Docker-based deployment using `Dockerfile`
- Service: `fx-ms-backend`
- Port: 8000
- Health check: `/api/v1/fx/health`

```bash
# Deploy: Push to repo, Render auto-builds from Dockerfile
# Or manually via Render dashboard
```

### Vercel (Frontend)

Configured via `fx-ui/vercel.json`:
- Framework: Vite
- Build: `npm run build`
- Output: `dist/`
- SPA rewrites enabled for client-side routing

**Required env var in Vercel dashboard:**
```
VITE_API_BASE_URL=https://your-render-backend-url.onrender.com
```

### Deployment Flow

1. **Backend**: Push to main → Render builds Docker image → Deploys API
2. **Frontend**: Push `fx-ui/` → Vercel builds with Vite → Deploys static site
3. Set `VITE_API_BASE_URL` in Vercel to point to Render backend URL
