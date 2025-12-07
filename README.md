# FX Currency Conversion Microservice

A high-performance microservice for real-time currency conversion with Refinitiv (Reuters) integration.

## Features

- **Real-time Exchange Rates** - Live rates from Refinitiv with automatic fallback
- **Bid/Ask Spreads** - Proper handling of buy/sell directions
- **Multi-Currency Support** - 10 currencies, 8+ currency pairs
- **Rate Caching** - Intelligent 30-second caching to reduce API calls
- **Quote Generation** - Get quotes before committing to conversion
- **Reference Data** - Currencies and pairs configuration via JSON

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    API Layer (FastAPI)                       │
│  POST /api/v1/fx/convert    GET /api/v1/fx/rate/{base}/{qt} │
│  POST /api/v1/fx/quote      GET /api/v1/fx/currencies       │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                  Conversion Service                          │
│  - Amount validation    - Rate calculation                   │
│  - Currency lookup      - Spread application                 │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                   FX Rate Service                            │
│  - Provider failover    - Rate caching                       │
│  - Health monitoring    - Cross-rate calculation             │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
        ┌──────────┐   ┌──────────┐   ┌──────────┐
        │ Refinitiv│   │ Bloomberg│   │   ECB    │
        │ (Primary)│   │(Secondary│   │(Fallback)│
        └──────────┘   └──────────┘   └──────────┘
```

## Quick Start

### Prerequisites

- Python 3.11+
- Refinitiv API credentials (optional - mock provider available)

### Installation

```bash
cd fx_microservice

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Copy environment configuration
cp .env.example .env

# Run the service
uvicorn app.main:app --reload
```

### Docker

```bash
docker build -t fx-conversion-service .
docker run -p 8000:8000 --env-file .env fx-conversion-service
```

## API Reference

### Base URL: `http://localhost:8000/api/v1/fx`

### 1. Convert Currency - POST `/convert`

```json
{
  "source_currency": "USD",
  "target_currency": "INR",
  "amount": 1000.00,
  "direction": "SELL",
  "client_reference": "TXN-2025-001"
}
```

### 2. Get Quote - POST `/quote`

### 3. Get Rate - GET `/rate/{base}/{quote}`

### 4. List Currencies - GET `/currencies`

### 5. Health Check - GET `/health`

## Project Structure

```
fx_microservice/
├── app/
│   ├── api/conversion.py      # API endpoints
│   ├── core/config.py         # Configuration
│   ├── data/*.json            # Reference data
│   ├── models/schemas.py      # Pydantic models
│   ├── services/
│   │   ├── conversion_service.py
│   │   └── fx_provider.py
│   └── main.py
├── Dockerfile
├── requirements.txt
└── .env.example
```

## License

Proprietary - Fintaar.ai
