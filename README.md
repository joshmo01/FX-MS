# 🌐 FX Smart Routing Engine v2.0

## Universal FX Routing Across Fiat, CBDC & Stablecoin

> **Intelligent payment routing** across traditional banking rails, Central Bank Digital Currencies (CBDCs), and Stablecoins with **atomic swap** support.

[![Version](https://img.shields.io/badge/version-2.0.0-blue.svg)](https://github.com/joshmo01/FX-MS)
[![Python](https://img.shields.io/badge/python-3.10+-green.svg)](https://www.python.org/downloads/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 🌟 Key Features

### Multi-Rail Support
| Rail Type | Currencies | Settlement | Status |
|-----------|------------|------------|--------|
| **💵 Fiat** | USD, EUR, GBP, INR, SGD, AED, CNY, HKD, THB, JPY | 4h - 3 days | ✅ Production |
| **🏛️ CBDC** | e-INR, e-CNY, e-HKD, e-THB, e-AED, e-SGD | 5s - 30s | 🔬 Pilot |
| **🪙 Stablecoin** | USDC, USDT, EURC, PYUSD, XSGD | 30s - 1h | ✅ Production |

### 📊 Complete Conversion Matrix (9 Types)

```
                    ┌─────────────────────────────────────────────┐
                    │         UNIVERSAL CONVERSION MATRIX          │
                    └─────────────────────────────────────────────┘

     ┌─────────┐           ┌─────────┐           ┌─────────────┐
     │  FIAT   │◄─────────►│  CBDC   │◄─────────►│ STABLECOIN  │
     │         │           │         │           │             │
     │ USD,EUR │           │ e-INR   │           │ USDC, USDT  │
     │ INR,SGD │           │ e-CNY   │           │ EURC, XSGD  │
     │ GBP,AED │           │ e-AED   │           │ PYUSD       │
     └────┬────┘           └────┬────┘           └──────┬──────┘
          │                     │                       │
          │     ┌───────────────┴───────────────┐      │
          │     │         mBridge               │      │
          │     │    (Atomic PvP 15 sec)        │      │
          │     │  e-CNY ↔ e-HKD ↔ e-THB ↔ e-AED│      │
          │     └───────────────────────────────┘      │
          │                                            │
          │          ⚛️ ATOMIC SWAPS (5 min)          │
          └────────────── Hybrid Routes ───────────────┘
```

| # | Type | Path | Fee Range | Best Settlement |
|---|------|------|-----------|-----------------|
| 1 | **FIAT → FIAT** | SWIFT / Local | 15-25 bps | 4-24h |
| 2 | **FIAT → CBDC** | FX + Mint | 0-20 bps | 5 sec |
| 3 | **CBDC → FIAT** | Redeem + FX | 0-20 bps | 5 sec |
| 4 | **CBDC → CBDC** | mBridge PvP | 13-40 bps | 15 sec |
| 5 | **FIAT → STABLE** | On-ramp | 0-50 bps | 1h |
| 6 | **STABLE → FIAT** | Off-ramp | 0-50 bps | 1-24h |
| 7 | **STABLE → STABLE** | DEX/CEX | 20-50 bps | 30s |
| 8 | **CBDC → STABLE** | Bridge/Atomic | 15-75 bps | 5m |
| 9 | **STABLE → CBDC** | Bridge/Atomic | 15-65 bps | 5m |

### ⚛️ Atomic Swap Technology

**Trustless CBDC ↔ Stablecoin exchange** using Hash Time-Locked Contracts (HTLCs):

- No intermediaries required
- Lowest fees (15 bps)
- Near-instant settlement (5 min)
- Cryptographic guarantees

**Supported Pairs (Experimental)**:
- e-INR ↔ USDC
- e-SGD ↔ XSGD
- e-CNY ↔ USDT (Planned)
- e-AED ↔ USDC (Planned)

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- pip or pipenv

### Installation

```bash
# Clone repository
git clone https://github.com/joshmo01/FX-MS.git
cd FX-MS

# Install dependencies
pip install -r requirements.txt

# Or use make
make install
```

### Running the Server

```bash
# Development mode
make run

# Or directly
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Run Demo

```bash
# Quick demo (key scenarios)
make demo

# Full demo (all 30+ scenarios)  
make demo-full

# Atomic swap focused
make demo-atomic

# CBDC routes only
make demo-cbdc

# Stablecoin routes only
make demo-stable
```

---

## 📡 API Reference

### Base URL
```
http://localhost:8000/api/v1/fx
```

### Smart Routing (Fiat)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/routing/recommend` | Get best route recommendation |
| POST | `/routing/compare` | Compare all fiat routes |
| GET | `/routing/objectives` | List routing objectives |
| GET | `/routing/providers` | List FX providers |
| GET | `/routing/customer-tiers` | List customer tiers |
| GET | `/routing/treasury/positions` | Get treasury positions |

### Multi-Rail Routing
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/multi-rail/route` | Get multi-rail route |
| GET | `/multi-rail/compare/{source}/{target}` | Quick comparison |
| GET | `/multi-rail/cbdc` | List available CBDCs |
| GET | `/multi-rail/stablecoins` | List stablecoins |
| GET | `/multi-rail/rails` | List available rails |
| GET | `/multi-rail/on-off-ramps` | List ramp providers |

### Universal Conversion
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/universal/convert` | Universal conversion |
| POST | `/bridge/route` | CBDC↔Stablecoin bridge |
| GET | `/bridge/cbdc-to-stable/{cbdc}/{stable}` | CBDC to Stable routes |
| GET | `/bridge/stable-to-cbdc/{stable}/{cbdc}` | Stable to CBDC routes |

### Example Request

```bash
curl -X POST http://localhost:8000/api/v1/fx/universal/convert \
  -H "Content-Type: application/json" \
  -d '{
    "source_currency": "USD",
    "source_type": "FIAT",
    "target_currency": "e-INR",
    "target_type": "CBDC",
    "amount": 10000,
    "customer_tier": "GOLD"
  }'
```

---

## 🏗️ Architecture

```
fx_smart_routing/
├── app/
│   ├── api/                          # API Routers
│   │   ├── routing_api.py            # Fiat routing
│   │   ├── multi_rail_api.py         # Multi-rail routing
│   │   └── universal_api.py          # Universal conversion
│   ├── services/                     # Business Logic
│   │   ├── smart_routing_engine.py   # Fiat engine
│   │   ├── multi_rail_engine.py      # Multi-rail engine
│   │   ├── universal_conversion_engine.py  # Universal
│   │   └── cbdc_stable_bridge.py     # CBDC↔Stable bridge
│   ├── models/                       # Pydantic Models
│   │   ├── routing_models.py
│   │   └── multi_rail_models.py
│   └── static/                       # React Components
│       └── UniversalRouteExplorer.jsx
├── config/                           # Configuration
│   ├── routing_config.json           # Routing objectives
│   ├── fx_providers.json             # 7 FX providers
│   ├── customer_tiers.json           # 5 customer tiers
│   ├── treasury_rates.json           # Treasury positions
│   ├── digital_currencies.json       # 6 CBDCs, 5 Stables
│   └── digital_rails.json            # Rails & On/Off ramps
├── tests/                            # Test Suite
│   ├── test_all_conversions.py       # Comprehensive tests
│   └── test_universal_conversion.py
├── demo_all_routes.py                # Demo runner
├── Dockerfile
├── Makefile
├── requirements.txt
└── setup.py
```

---

## ⚙️ Configuration

### Routing Objectives

| Objective | Rate | Reliability | Speed | STP |
|-----------|------|-------------|-------|-----|
| BEST_RATE | 70% | 15% | 10% | 5% |
| OPTIMUM | 40% | 25% | 20% | 15% |
| FASTEST_EXECUTION | 20% | 25% | 45% | 10% |
| MAX_STP | 25% | 20% | 15% | 40% |

### Customer Tiers

| Tier | Markup Discount | Spread Reduction | Max Transaction |
|------|-----------------|------------------|-----------------|
| **Platinum** | 50% | 10 bps | $50M |
| **Gold** | 30% | 5 bps | $10M |
| **Silver** | 15% | 2 bps | $1M |
| **Bronze** | 5% | 0 bps | $100K |
| **Retail** | 0% | 0 bps | $25K |

### FX Providers (7 Configured)

| Provider | Type | STP | Settlement | Reliability |
|----------|------|-----|------------|-------------|
| Treasury Internal | INTERNAL | ✅ | 4h | 99% |
| Bank of America | CORRESPONDENT | ✅ | 24h | 97% |
| Citibank | CORRESPONDENT | ✅ | 24h | 96% |
| HDFC Bank | LOCAL | ✅ | 4h | 95% |
| ICICI Bank | LOCAL | ✅ | 4h | 94% |
| Wise | FINTECH | ✅ | 12h | 93% |
| Alpha FX Dealers | DEALER | ❌ | 48h | 88% |

---

## 🐳 Docker

```bash
# Build image
docker build -t fx-smart-routing:latest .

# Run container
docker run -p 8000:8000 fx-smart-routing:latest

# Using make
make docker
make docker-run
```

### Docker Compose

```yaml
version: '3.8'
services:
  fx-routing:
    build: .
    ports:
      - "8000:8000"
    environment:
      - LOG_LEVEL=INFO
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## 🧪 Testing

```bash
# Run all tests
make test

# With coverage
make test-cov

# Run demo tests
python tests/test_all_conversions.py

# Specific conversion test
python -m pytest tests/test_universal_conversion.py -v
```

---

## 📊 Route Examples

### Example 1: USD → e-INR (Fiat to CBDC)

```json
{
  "request": {
    "source": "USD",
    "source_type": "FIAT",
    "target": "e-INR", 
    "target_type": "CBDC",
    "amount": 10000
  },
  "best_route": {
    "name": "FX + Direct CBDC Mint",
    "legs": 2,
    "fee_bps": 20,
    "settlement": "4 hours",
    "target_amount": "₹8,43,200"
  }
}
```

### Example 2: e-CNY → e-AED (mBridge)

```json
{
  "request": {
    "source": "e-CNY",
    "target": "e-AED",
    "amount": 500000
  },
  "best_route": {
    "name": "mBridge PvP Settlement",
    "legs": 1,
    "fee_bps": 13,
    "settlement": "15 seconds",
    "highlight": "Atomic cross-border settlement"
  }
}
```

### Example 3: e-INR ↔ USDC (Atomic Swap)

```json
{
  "request": {
    "source": "e-INR",
    "target": "USDC",
    "amount": 50000
  },
  "best_route": {
    "name": "Atomic Swap (HTLC)",
    "legs": 1,
    "fee_bps": 15,
    "settlement": "5 minutes",
    "status": "EXPERIMENTAL",
    "benefits": [
      "No intermediaries",
      "Trustless execution",
      "Lowest fees"
    ]
  }
}
```

---

## 📚 Documentation

| Resource | URL |
|----------|-----|
| **API Docs** | http://localhost:8000/docs |
| **ReDoc** | http://localhost:8000/redoc |
| **Health** | http://localhost:8000/health |
| **API Info** | http://localhost:8000/api |

---

## 🗺️ Roadmap

- [x] 9 conversion types support
- [x] mBridge integration
- [x] Atomic swap framework
- [x] Multi-provider routing
- [x] Customer tier pricing
- [ ] Real-time rate feeds (Refinitiv, Bloomberg)
- [ ] Production atomic swap deployment
- [ ] Project Nexus integration
- [ ] Additional CBDC corridors
- [ ] AI-powered route optimization

---

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

---

## 📄 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🏢 About Fintaar.ai

**Fintaar.ai** specializes in AI-powered solutions for financial services:
- Voice AI Agents
- Conversational AI
- Payment Processing
- Collections Systems
- CBDC/Stablecoin Integration

**Contact**: engineering@fintaar.ai

---

<p align="center">
  <strong>Built with ❤️ by Fintaar.ai</strong>
</p>
