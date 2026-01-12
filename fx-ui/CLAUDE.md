# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

FX Smart Routing Engine - A multi-rail FX routing system supporting traditional FIAT, CBDC (Central Bank Digital Currencies), and Stablecoin rails. The project consists of:

- **Backend**: Python FastAPI service (parent directory `../`)
- **Frontend**: React + Vite application (this directory `fx-ui/`)

## Common Commands

### Backend (run from parent directory `../`)

```bash
# Install dependencies
pip install -r requirements.txt

# Run API server (development)
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Run tests
pytest tests/ -v

# Run single test file
pytest tests/api/test_01_routing_api.py -v

# Run tests with coverage
pytest tests/ -v --cov=app --cov-report=html

# Format code
black app/ tests/
isort app/ tests/

# Type checking
mypy app/

# Run demo scenarios
python demo_all_routes.py --mode quick
```

### Frontend (run from `fx-ui/`)

```bash
# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Lint
npm run lint
```

## Architecture

### Backend Structure (`../app/`)

```
app/
├── main.py                 # FastAPI application entry, router registration
├── api/                    # API route handlers
│   ├── routing_api.py      # Traditional FX routing endpoints
│   ├── multi_rail_api.py   # CBDC & Stablecoin routing
│   ├── deals_api.py        # Treasury deals CRUD & workflow
│   ├── pricing.py          # Customer-specific pricing quotes
│   ├── rules_api.py        # Dynamic pricing rules management
│   ├── chat_api.py         # AI chat assistant
│   └── admin_api.py        # Reference table administration
├── services/               # Business logic
│   ├── smart_routing_engine.py   # Core FX routing logic
│   ├── deals_service.py          # Deal lifecycle management
│   ├── pricing_service.py        # Pricing calculations
│   ├── fx_provider.py            # Provider integration
│   └── rules_engine/             # Dynamic rules evaluation
│       ├── engine.py             # Rule execution engine
│       ├── evaluator.py          # Condition evaluation
│       ├── loader.py             # Rule config loading
│       └── models.py             # Rule data models
└── models/                 # Pydantic models
```

### Frontend Structure (`fx-ui/src/`)

```
src/
├── App.jsx                 # Main application, tab navigation, state management
├── services/api.js         # Axios API client, all backend endpoints
└── components/
    ├── FXRulesManager.jsx  # Dynamic pricing rules UI
    ├── AdminPanel.jsx      # Reference table management
    ├── RatesTable.jsx      # Treasury rates display
    ├── ProvidersTable.jsx  # FX provider configuration
    ├── CustomerTiersTable.jsx # Customer tier management
    └── PricingTable.jsx    # Pricing segment display
```

### Configuration Files (`../config/`)

- `treasury_rates.json` - FX rates with bid/ask/position
- `customer_tiers.json` - Customer tier pricing (PLATINUM, GOLD, etc.)
- `fx_providers.json` - FX provider configurations
- `pricing_segments.json` - Customer segment definitions
- `pricing_tiers.json` - Amount-based tier adjustments
- `rules/` - Dynamic pricing rules (JSON)

### Data Flow

1. **Pricing Request** → `pricing.py` → `pricing_service.py` → `rules_engine/` → applies segment/tier/currency adjustments
2. **Route Calculation** → `routing_api.py` / `multi_rail_api.py` → `smart_routing_engine.py` → scores providers by objective
3. **Deal Workflow** → `deals_api.py` → `deals_service.py` → DRAFT → PENDING_APPROVAL → ACTIVE → EXPIRED/FULLY_UTILIZED/CANCELLED lifecycle

## API Base Path

All API endpoints are prefixed with `/api/v1/fx/`

Key endpoints:
- `POST /routing/recommend` - Get best route recommendation
- `POST /multi-rail/route` - Multi-rail route comparison
- `POST /pricing/quote` - Customer-specific price quote
- `GET/POST /deals` - Deal management (sorted by newest first)
- `POST /deals/{id}/submit` - Submit deal for approval
- `POST /deals/{id}/approve` - Approve a pending deal
- `DELETE /deals/{id}` - Cancel a deal (requires `cancelled_by` and `cancellation_reason`)
- `GET/POST /rules/` - Dynamic rules CRUD

## Environment Variables

### Backend
- `ANTHROPIC_API_KEY` - Required for chat functionality

### Frontend (`fx-ui/.env`)
- `VITE_API_BASE_URL` - Backend API URL (default: `http://127.0.0.1:8000`)

## Testing

Tests are organized by API module in `../tests/api/`:
- `test_01_routing_api.py` through `test_12_integration.py`
- `test_chat_api.py` - Chat functionality tests

Base test utilities in `../tests/base/test_base.py` provide common fixtures.

## Key Concepts

- **Rails**: FIAT (traditional), CBDC (e-INR, e-CNY, etc.), STABLECOIN (USDC, USDT)
- **mBridge**: Cross-border CBDC settlement network (near-instant settlement)
- **Routing Objectives**: BEST_RATE, OPTIMUM, FASTEST_EXECUTION, MAX_STP
- **Customer Tiers**: PLATINUM → RETAIL with different markup discounts
- **Rules Engine**: JSON-based dynamic rules for provider selection and margin adjustments
- **Deal Statuses**: DRAFT, PENDING_APPROVAL, ACTIVE, EXPIRED, FULLY_UTILIZED, CANCELLED, REJECTED
- **Deal Actions**:
  - Submit (DRAFT → PENDING_APPROVAL)
  - Approve (PENDING_APPROVAL → ACTIVE)
  - Cancel (DRAFT/PENDING_APPROVAL/ACTIVE → CANCELLED, requires reason)

## Deployment

### Vercel (Frontend)

Configured via `vercel.json`:
- Framework: Vite
- Build command: `npm run build`
- Output directory: `dist/`
- SPA rewrites: All routes → `/index.html`

**Set in Vercel dashboard:**
```
VITE_API_BASE_URL=https://your-render-backend-url.onrender.com
```

### Render (Backend - parent directory)

Configured via `../render.yaml`:
- Docker-based deployment
- Health check: `/api/v1/fx/health`

### Deployment Flow

1. Push to repo
2. Render auto-deploys backend from Dockerfile
3. Vercel auto-deploys frontend
4. Ensure `VITE_API_BASE_URL` points to Render backend
