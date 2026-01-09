from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/fx/multi-rail", tags=["Multi-Rail Routing"])

CBDC = [
    {"code": "e-INR", "name": "Digital Rupee", "issuer": "RBI", "country": "India", "mbridge": False, "settlement_sec": 5},
    {"code": "e-CNY", "name": "Digital Yuan", "issuer": "PBoC", "country": "China", "mbridge": True, "settlement_sec": 3},
    {"code": "e-HKD", "name": "Digital HKD", "issuer": "HKMA", "country": "Hong Kong", "mbridge": True, "settlement_sec": 5},
    {"code": "e-THB", "name": "Digital Baht", "issuer": "BoT", "country": "Thailand", "mbridge": True, "settlement_sec": 5},
    {"code": "e-AED", "name": "Digital Dirham", "issuer": "CBUAE", "country": "UAE", "mbridge": True, "settlement_sec": 5},
    {"code": "e-SGD", "name": "Digital SGD", "issuer": "MAS", "country": "Singapore", "mbridge": False, "settlement_sec": 10},
]

STABLECOINS = [
    {"code": "USDC", "name": "USD Coin", "issuer": "Circle", "peg": "USD", "regulated": True, "liquidity": 95},
    {"code": "USDT", "name": "Tether", "issuer": "Tether", "peg": "USD", "regulated": False, "liquidity": 100},
    {"code": "EURC", "name": "Euro Coin", "issuer": "Circle", "peg": "EUR", "regulated": True, "liquidity": 60},
    {"code": "PYUSD", "name": "PayPal USD", "issuer": "Paxos", "peg": "USD", "regulated": True, "liquidity": 50},
    {"code": "XSGD", "name": "StraitsX SGD", "issuer": "StraitsX", "peg": "SGD", "regulated": True, "liquidity": 40},
]

CONVERSION_TYPES = [
    {"id": "F2F", "name": "Fiat to Fiat", "fee_bps": "8-25", "settlement": "4h-3d", "status": "Production"},
    {"id": "F2C", "name": "Fiat to CBDC", "fee_bps": "0-20", "settlement": "5s-4h", "status": "Production"},
    {"id": "C2F", "name": "CBDC to Fiat", "fee_bps": "0-20", "settlement": "5s-4h", "status": "Production"},
    {"id": "C2C", "name": "CBDC to CBDC", "fee_bps": "13-40", "settlement": "15s-8h", "status": "Pilot"},
    {"id": "F2S", "name": "Fiat to Stablecoin", "fee_bps": "0-50", "settlement": "1-4h", "status": "Production"},
    {"id": "S2F", "name": "Stablecoin to Fiat", "fee_bps": "0-50", "settlement": "1-24h", "status": "Production"},
    {"id": "S2S", "name": "Stablecoin to Stablecoin", "fee_bps": "20-30", "settlement": "30s-5m", "status": "Production"},
    {"id": "C2S", "name": "CBDC to Stablecoin", "fee_bps": "15-75", "settlement": "5m-4h", "status": "Experimental"},
    {"id": "S2C", "name": "Stablecoin to CBDC", "fee_bps": "15-65", "settlement": "5m-4h", "status": "Experimental"},
]

ATOMIC_SWAPS = [
    {"pair": "e-INR/USDC", "status": "Experimental", "risk": "Medium", "fee_bps": 15, "settlement": "5 min"},
    {"pair": "e-SGD/XSGD", "status": "Pilot", "risk": "Low", "fee_bps": 15, "settlement": "5 min"},
    {"pair": "e-CNY/USDT", "status": "Planned", "risk": "High", "fee_bps": 15, "settlement": "5 min"},
    {"pair": "e-AED/USDC", "status": "Planned", "risk": "Medium", "fee_bps": 15, "settlement": "5 min"},
]

@router.get("/cbdc")
def get_cbdc():
    return {"cbdc": CBDC, "count": len(CBDC)}

@router.get("/stablecoins")
def get_stablecoins():
    return {"stablecoins": STABLECOINS, "count": len(STABLECOINS)}

@router.get("/conversion-types")
def get_conversion_types():
    return {"conversion_types": CONVERSION_TYPES, "count": len(CONVERSION_TYPES)}

@router.get("/atomic-swaps")
def get_atomic_swaps():
    return {"atomic_swaps": ATOMIC_SWAPS, "protocol": "HTLC", "status": "Experimental"}

@router.get("/rails")
def get_rails():
    return {
        "rails": [
            {"id": "CBDC_DOMESTIC", "name": "Domestic CBDC", "settlement": "5s", "fee_bps": 0},
            {"id": "MBRIDGE", "name": "mBridge PvP", "settlement": "10s", "fee_bps": 13, "participants": ["e-CNY", "e-HKD", "e-THB", "e-AED"]},
            {"id": "PROJECT_NEXUS", "name": "Project Nexus", "settlement": "60s", "fee_bps": 35},
            {"id": "STABLECOIN_BRIDGE", "name": "Stablecoin Bridge", "settlement": "5-180s", "fee_bps": 50},
        ]
    }

@router.post("/route")
def calculate_route(source: str, target: str, amount: float = 10000):
    source_upper = source.upper()
    target_upper = target.upper()
    
    # Determine currency types
    def get_type(code):
        if code.startswith("E-"):
            return "CBDC"
        if code in ["USDC", "USDT", "EURC", "PYUSD", "XSGD"]:
            return "STABLECOIN"
        return "FIAT"
    
    source_type = get_type(source_upper)
    target_type = get_type(target_upper)
    
    # Build conversion type
    type_map = {"FIAT": "F", "CBDC": "C", "STABLECOIN": "S"}
    conv_type = f"{type_map[source_type]}2{type_map[target_type]}"
    
    # Find matching conversion
    conv_info = next((c for c in CONVERSION_TYPES if c["id"] == conv_type), None)
    
    # Build route
    routes = []
    if conv_type == "C2C":
        # Check mBridge eligibility
        source_cbdc = next((c for c in CBDC if c["code"] == source_upper), None)
        target_cbdc = next((c for c in CBDC if c["code"] == target_upper), None)
        if source_cbdc and target_cbdc and source_cbdc.get("mbridge") and target_cbdc.get("mbridge"):
            routes.append({"route": "mBridge PvP", "fee_bps": 13, "settlement": "10s", "recommended": True})
        routes.append({"route": "Fiat Bridge", "fee_bps": 40, "settlement": "8h", "recommended": False})
    elif conv_type in ["C2S", "S2C"]:
        routes.append({"route": "Atomic Swap (HTLC)", "fee_bps": 15, "settlement": "5m", "experimental": True})
        routes.append({"route": "Fiat Intermediary", "fee_bps": 50, "settlement": "4h", "recommended": True})
    else:
        fee = 20
        routes.append({"route": "Direct", "fee_bps": fee, "settlement": "1h", "recommended": True})
    
    return {
        "source": source_upper,
        "target": target_upper,
        "amount": amount,
        "conversion_type": conv_type,
        "conversion_info": conv_info,
        "routes": routes,
        "best_route": routes[0] if routes else None
    }
