"""
CBDC ↔ Stablecoin Bridge Engine

Advanced conversion paths between CBDCs and Stablecoins including:
- Atomic swap protocols (future-ready)
- Hybrid bridge routes
- DEX liquidity aggregation
- Multi-path optimization

Author: Fintaar.ai
Version: 1.0.0
"""
import json
import uuid
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Tuple, Any
from pathlib import Path
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class BridgeType(str, Enum):
    """Types of bridges between CBDC and Stablecoin"""
    FIAT_INTERMEDIARY = "FIAT_INTERMEDIARY"      # CBDC → Fiat → Stablecoin
    DEX_BRIDGE = "DEX_BRIDGE"                     # Via decentralized exchange
    CEX_BRIDGE = "CEX_BRIDGE"                     # Via centralized exchange
    ATOMIC_SWAP = "ATOMIC_SWAP"                   # Direct atomic swap (experimental)
    HYBRID_MBRIDGE = "HYBRID_MBRIDGE"             # mBridge + Stablecoin
    LIQUIDITY_POOL = "LIQUIDITY_POOL"             # Via DeFi liquidity pools


class BridgeStatus(str, Enum):
    """Status of bridge route"""
    ACTIVE = "ACTIVE"
    PILOT = "PILOT"
    EXPERIMENTAL = "EXPERIMENTAL"
    PLANNED = "PLANNED"


@dataclass
class BridgeLeg:
    """Single leg in a bridge route"""
    leg_id: str
    sequence: int
    from_asset: str
    from_type: str  # CBDC, STABLECOIN, FIAT
    to_asset: str
    to_type: str
    provider: str
    protocol: str
    network: Optional[str]
    rate: Decimal
    amount_in: Decimal
    amount_out: Decimal
    fee_bps: int
    gas_cost_usd: Decimal
    settlement_seconds: int
    requires_kyc: bool
    compliance_check: str
    description: str


@dataclass
class BridgeRoute:
    """Complete bridge route"""
    route_id: str
    route_name: str
    bridge_type: BridgeType
    status: BridgeStatus
    legs: List[BridgeLeg]
    
    # Source/Target
    source_asset: str
    source_type: str
    source_amount: Decimal
    target_asset: str
    target_type: str
    target_amount: Decimal
    
    # Economics
    effective_rate: Decimal
    total_fee_bps: int
    total_gas_usd: Decimal
    slippage_tolerance_bps: int
    
    # Settlement
    total_settlement_seconds: int
    settlement_finality: str  # INSTANT, PROBABILISTIC, DEFERRED
    
    # Risk scores (0-100)
    liquidity_score: int
    counterparty_score: int
    smart_contract_score: int
    regulatory_score: int
    overall_score: float
    
    # Compliance
    kyc_required: bool
    travel_rule_applies: bool
    sanctions_check: bool
    jurisdictions: List[str]
    
    # Limits
    min_amount: Decimal
    max_amount: Decimal
    daily_limit: Optional[Decimal]
    
    # Warnings
    warnings: List[str] = field(default_factory=list)
    benefits: List[str] = field(default_factory=list)


class CBDCStableBridge:
    """
    CBDC ↔ Stablecoin Bridge Engine
    
    Provides optimal routes for converting between CBDCs and Stablecoins
    with support for multiple bridge types and compliance requirements.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._load_configurations()
        self._init_bridge_providers()
        self._init_liquidity_pools()
    
    def _load_configurations(self):
        """Load configuration files"""
        with open(self.config_dir / "digital_currencies.json") as f:
            self.digital_currencies = json.load(f)
        
        with open(self.config_dir / "digital_rails.json") as f:
            self.digital_rails = json.load(f)
    
    def _init_bridge_providers(self):
        """Initialize bridge provider configurations"""
        self.bridge_providers = {
            "CIRCLE": {
                "name": "Circle",
                "supported_stables": ["USDC", "EURC"],
                "supported_cbdc_pilots": ["e-SGD"],  # Project Guardian
                "fee_bps": 0,
                "settlement_seconds": 3600,
                "kyc_level": "INSTITUTIONAL",
                "regulated": True,
                "networks": ["ETHEREUM", "SOLANA", "POLYGON", "AVALANCHE"]
            },
            "COINBASE_PRIME": {
                "name": "Coinbase Prime",
                "supported_stables": ["USDC", "USDT", "PYUSD"],
                "supported_cbdc_pilots": [],
                "fee_bps": 25,
                "settlement_seconds": 7200,
                "kyc_level": "INSTITUTIONAL",
                "regulated": True,
                "networks": ["ETHEREUM", "SOLANA", "POLYGON"]
            },
            "UNISWAP": {
                "name": "Uniswap V3",
                "type": "DEX",
                "supported_stables": ["USDC", "USDT", "DAI", "EURC"],
                "fee_bps": 30,
                "settlement_seconds": 60,
                "kyc_level": "NONE",
                "regulated": False,
                "networks": ["ETHEREUM", "POLYGON", "ARBITRUM", "OPTIMISM"]
            },
            "CURVE": {
                "name": "Curve Finance",
                "type": "DEX",
                "supported_stables": ["USDC", "USDT", "DAI", "FRAX"],
                "fee_bps": 4,  # Very low for stablecoin swaps
                "settlement_seconds": 60,
                "kyc_level": "NONE",
                "regulated": False,
                "networks": ["ETHEREUM", "POLYGON", "ARBITRUM"]
            },
            "STRAITSX": {
                "name": "StraitsX",
                "supported_stables": ["XSGD", "XIDR"],
                "supported_cbdc_pilots": ["e-SGD"],
                "fee_bps": 10,
                "settlement_seconds": 3600,
                "kyc_level": "FULL_KYC",
                "regulated": True,
                "networks": ["ETHEREUM", "POLYGON"]
            },
            "RBI_PILOT": {
                "name": "RBI CBDC Pilot",
                "supported_stables": [],  # No direct stablecoin support yet
                "supported_cbdc": ["e-INR"],
                "fee_bps": 0,
                "settlement_seconds": 5,
                "kyc_level": "AADHAAR_EKYC",
                "regulated": True,
                "networks": ["R3_CORDA"]
            }
        }
    
    def _init_liquidity_pools(self):
        """Initialize DeFi liquidity pool data"""
        self.liquidity_pools = {
            "USDC-USDT": {
                "dex": "Curve",
                "pool": "3pool",
                "tvl_usd": 500_000_000,
                "daily_volume": 50_000_000,
                "fee_bps": 4,
                "slippage_1m": 1,  # bps for $1M trade
                "networks": ["ETHEREUM", "POLYGON"]
            },
            "USDC-EURC": {
                "dex": "Uniswap",
                "pool": "USDC-EURC 0.01%",
                "tvl_usd": 50_000_000,
                "daily_volume": 5_000_000,
                "fee_bps": 10,
                "slippage_1m": 5,
                "networks": ["ETHEREUM"]
            },
            "USDC-XSGD": {
                "dex": "StraitsX/Uniswap",
                "pool": "USDC-XSGD",
                "tvl_usd": 10_000_000,
                "daily_volume": 1_000_000,
                "fee_bps": 30,
                "slippage_1m": 20,
                "networks": ["ETHEREUM", "POLYGON"]
            }
        }
    
    # =========================================================================
    # CBDC TO STABLECOIN ROUTES
    # =========================================================================
    
    async def get_cbdc_to_stable_routes(
        self,
        cbdc: str,
        stablecoin: str,
        amount: Decimal,
        preferred_network: Optional[str] = None,
        max_slippage_bps: int = 50,
        require_regulated: bool = True
    ) -> List[BridgeRoute]:
        """
        Get all available routes for CBDC → Stablecoin conversion
        
        Args:
            cbdc: Source CBDC (e.g., "e-INR", "e-CNY")
            stablecoin: Target stablecoin (e.g., "USDC", "USDT")
            amount: Amount in source CBDC
            preferred_network: Preferred blockchain network
            max_slippage_bps: Maximum acceptable slippage
            require_regulated: Only return regulated routes
        
        Returns:
            List of BridgeRoute sorted by overall_score
        """
        routes = []
        
        cbdc_info = self.digital_currencies["cbdc"].get(cbdc)
        stable_info = self.digital_currencies["stablecoins"].get(stablecoin)
        
        if not cbdc_info or not stable_info:
            return routes
        
        # Get underlying fiat currencies
        cbdc_fiat = self._get_cbdc_fiat(cbdc)
        stable_peg = stable_info["pegged_currency"]
        
        # Route 1: Standard Fiat Intermediary (most common)
        routes.extend(await self._build_fiat_intermediary_route(
            cbdc, stablecoin, amount, cbdc_fiat, stable_peg,
            cbdc_info, stable_info, preferred_network
        ))
        
        # Route 2: CEX Bridge (faster, higher fees)
        routes.extend(await self._build_cex_bridge_route(
            cbdc, stablecoin, amount, cbdc_fiat, stable_peg,
            cbdc_info, stable_info, preferred_network
        ))
        
        # Route 3: Hybrid mBridge (for supported CBDCs)
        if cbdc in ["e-CNY", "e-HKD", "e-THB", "e-AED"]:
            routes.extend(await self._build_hybrid_mbridge_route(
                cbdc, stablecoin, amount, cbdc_info, stable_info
            ))
        
        # Route 4: Atomic Swap (experimental)
        if not require_regulated:
            routes.extend(await self._build_atomic_swap_route(
                cbdc, stablecoin, amount, cbdc_info, stable_info
            ))
        
        # Filter and sort
        if require_regulated:
            routes = [r for r in routes if r.regulatory_score >= 70]
        
        routes = [r for r in routes if r.slippage_tolerance_bps <= max_slippage_bps]
        
        # Calculate overall scores and sort
        for route in routes:
            route.overall_score = self._calculate_route_score(route)
        
        return sorted(routes, key=lambda r: r.overall_score, reverse=True)
    
    async def _build_fiat_intermediary_route(
        self, cbdc: str, stablecoin: str, amount: Decimal,
        cbdc_fiat: str, stable_peg: str,
        cbdc_info: dict, stable_info: dict,
        preferred_network: Optional[str]
    ) -> List[BridgeRoute]:
        """Build standard CBDC → Fiat → Stablecoin route"""
        routes = []
        
        # Get FX rate if needed
        fx_rate = self._get_fx_rate(cbdc_fiat, stable_peg)
        fx_fee = 0 if cbdc_fiat == stable_peg else 15
        
        # Calculate amounts through the path
        fiat_amount = amount  # CBDC → Fiat is 1:1
        pegged_fiat_amount = fiat_amount * fx_rate * (1 - Decimal(fx_fee) / 10000)
        
        # On-ramp fee for stablecoin minting
        on_ramp_fee = 25 if stable_info.get("regulatory_status") == "REGULATED_US" else 50
        stable_amount = pegged_fiat_amount * (1 - Decimal(on_ramp_fee) / 10000)
        
        networks = stable_info.get("networks", [])
        if preferred_network:
            networks = [n for n in networks if n["chain"] == preferred_network] or networks[:1]
        
        for network in networks[:2]:
            legs = []
            
            # Leg 1: CBDC Redemption
            legs.append(BridgeLeg(
                leg_id=f"L1-{uuid.uuid4().hex[:6]}",
                sequence=1,
                from_asset=cbdc,
                from_type="CBDC",
                to_asset=cbdc_fiat,
                to_type="FIAT",
                provider=cbdc_info.get("issuer", "Central Bank"),
                protocol=cbdc_info.get("technology", "DLT"),
                network=cbdc_info.get("technology"),
                rate=Decimal("1.0"),
                amount_in=amount,
                amount_out=fiat_amount,
                fee_bps=0,
                gas_cost_usd=Decimal("0"),
                settlement_seconds=cbdc_info.get("settlement_seconds", 5),
                requires_kyc=True,
                compliance_check="CENTRAL_BANK_VALIDATED",
                description=f"Redeem {cbdc} to {cbdc_fiat}"
            ))
            
            # Leg 2: FX Conversion (if different currencies)
            if cbdc_fiat != stable_peg:
                legs.append(BridgeLeg(
                    leg_id=f"L2-{uuid.uuid4().hex[:6]}",
                    sequence=2,
                    from_asset=cbdc_fiat,
                    from_type="FIAT",
                    to_asset=stable_peg,
                    to_type="FIAT",
                    provider="FX Provider",
                    protocol="SWIFT/LOCAL",
                    network=None,
                    rate=fx_rate,
                    amount_in=fiat_amount,
                    amount_out=pegged_fiat_amount,
                    fee_bps=fx_fee,
                    gas_cost_usd=Decimal("0"),
                    settlement_seconds=14400,  # 4 hours
                    requires_kyc=True,
                    compliance_check="BANK_KYC",
                    description=f"FX {cbdc_fiat} → {stable_peg}"
                ))
            
            # Leg 3: Stablecoin Minting
            legs.append(BridgeLeg(
                leg_id=f"L3-{uuid.uuid4().hex[:6]}",
                sequence=len(legs) + 1,
                from_asset=stable_peg,
                from_type="FIAT",
                to_asset=stablecoin,
                to_type="STABLECOIN",
                provider=stable_info.get("issuer", "Issuer"),
                protocol="ON_RAMP",
                network=network["chain"],
                rate=Decimal("1.0"),
                amount_in=pegged_fiat_amount if cbdc_fiat != stable_peg else fiat_amount,
                amount_out=stable_amount,
                fee_bps=on_ramp_fee,
                gas_cost_usd=Decimal(str(network.get("avg_fee_usd", 0.5))),
                settlement_seconds=network.get("settlement_seconds", 60) + 1800,
                requires_kyc=True,
                compliance_check="EXCHANGE_KYC",
                description=f"Mint {stablecoin} on {network['chain']}"
            ))
            
            total_fee = fx_fee + on_ramp_fee
            total_settlement = sum(leg.settlement_seconds for leg in legs)
            
            routes.append(BridgeRoute(
                route_id=f"C2S-FI-{cbdc[:3]}-{stablecoin}-{network['chain'][:3]}-{uuid.uuid4().hex[:4]}",
                route_name=f"Fiat Bridge: {cbdc} → {stablecoin} ({network['chain']})",
                bridge_type=BridgeType.FIAT_INTERMEDIARY,
                status=BridgeStatus.ACTIVE,
                legs=legs,
                source_asset=cbdc,
                source_type="CBDC",
                source_amount=amount,
                target_asset=stablecoin,
                target_type="STABLECOIN",
                target_amount=stable_amount.quantize(Decimal("0.01")),
                effective_rate=(stable_amount / amount).quantize(Decimal("0.000001")),
                total_fee_bps=total_fee,
                total_gas_usd=Decimal(str(network.get("avg_fee_usd", 0.5))),
                slippage_tolerance_bps=10,
                total_settlement_seconds=total_settlement,
                settlement_finality="DEFERRED",
                liquidity_score=95,
                counterparty_score=90,
                smart_contract_score=85,
                regulatory_score=95,
                overall_score=0,
                kyc_required=True,
                travel_rule_applies=True,
                sanctions_check=True,
                jurisdictions=[cbdc_info.get("country", ""), stable_info.get("jurisdictions", ["US"])[0]],
                min_amount=Decimal("100"),
                max_amount=Decimal("10000000"),
                daily_limit=Decimal("50000000"),
                warnings=["FX settlement may take 4+ hours"] if cbdc_fiat != stable_peg else [],
                benefits=[
                    "Fully regulated path",
                    "Bank-grade compliance",
                    "No smart contract risk"
                ]
            ))
        
        return routes
    
    async def _build_cex_bridge_route(
        self, cbdc: str, stablecoin: str, amount: Decimal,
        cbdc_fiat: str, stable_peg: str,
        cbdc_info: dict, stable_info: dict,
        preferred_network: Optional[str]
    ) -> List[BridgeRoute]:
        """Build CEX-based bridge route (faster but higher fees)"""
        routes = []
        
        fx_rate = self._get_fx_rate(cbdc_fiat, stable_peg)
        
        # CEX typically charges higher fees but faster
        cex_fee = 50  # bps
        on_ramp_fee = 25
        total_fee = cex_fee + on_ramp_fee
        
        fiat_amount = amount
        stable_amount = fiat_amount * fx_rate * (1 - Decimal(total_fee) / 10000)
        
        network = stable_info.get("networks", [{"chain": "ETHEREUM"}])[0]
        
        legs = [
            BridgeLeg(
                leg_id=f"CEX-L1-{uuid.uuid4().hex[:6]}",
                sequence=1,
                from_asset=cbdc,
                from_type="CBDC",
                to_asset=cbdc_fiat,
                to_type="FIAT",
                provider=cbdc_info.get("issuer", "Central Bank"),
                protocol=cbdc_info.get("technology", "DLT"),
                network=None,
                rate=Decimal("1.0"),
                amount_in=amount,
                amount_out=fiat_amount,
                fee_bps=0,
                gas_cost_usd=Decimal("0"),
                settlement_seconds=5,
                requires_kyc=True,
                compliance_check="CENTRAL_BANK_VALIDATED",
                description=f"Redeem {cbdc}"
            ),
            BridgeLeg(
                leg_id=f"CEX-L2-{uuid.uuid4().hex[:6]}",
                sequence=2,
                from_asset=cbdc_fiat,
                from_type="FIAT",
                to_asset=stablecoin,
                to_type="STABLECOIN",
                provider="Coinbase Prime",
                protocol="CEX_TRADE",
                network=network["chain"],
                rate=fx_rate * (1 - Decimal(total_fee) / 10000),
                amount_in=fiat_amount,
                amount_out=stable_amount,
                fee_bps=total_fee,
                gas_cost_usd=Decimal("0.50"),
                settlement_seconds=7200,  # 2 hours
                requires_kyc=True,
                compliance_check="EXCHANGE_KYC",
                description=f"CEX trade {cbdc_fiat} → {stablecoin}"
            )
        ]
        
        routes.append(BridgeRoute(
            route_id=f"C2S-CEX-{cbdc[:3]}-{stablecoin}-{uuid.uuid4().hex[:4]}",
            route_name=f"CEX Bridge: {cbdc} → {stablecoin}",
            bridge_type=BridgeType.CEX_BRIDGE,
            status=BridgeStatus.ACTIVE,
            legs=legs,
            source_asset=cbdc,
            source_type="CBDC",
            source_amount=amount,
            target_asset=stablecoin,
            target_type="STABLECOIN",
            target_amount=stable_amount.quantize(Decimal("0.01")),
            effective_rate=(stable_amount / amount).quantize(Decimal("0.000001")),
            total_fee_bps=total_fee,
            total_gas_usd=Decimal("0.50"),
            slippage_tolerance_bps=20,
            total_settlement_seconds=7205,
            settlement_finality="DEFERRED",
            liquidity_score=90,
            counterparty_score=85,
            smart_contract_score=95,  # CEX, not smart contract
            regulatory_score=90,
            overall_score=0,
            kyc_required=True,
            travel_rule_applies=True,
            sanctions_check=True,
            jurisdictions=[cbdc_info.get("country", ""), "US"],
            min_amount=Decimal("1000"),
            max_amount=Decimal("5000000"),
            daily_limit=Decimal("25000000"),
            warnings=["CEX custody risk", "Higher fees than direct path"],
            benefits=["Faster than bank settlement", "Single counterparty", "Deep liquidity"]
        ))
        
        return routes
    
    async def _build_hybrid_mbridge_route(
        self, cbdc: str, stablecoin: str, amount: Decimal,
        cbdc_info: dict, stable_info: dict
    ) -> List[BridgeRoute]:
        """Build hybrid route using mBridge for cross-border then stablecoin"""
        routes = []
        
        # mBridge participants can convert to USD-pegged CBDC equivalent
        # then to stablecoin
        
        if stablecoin not in ["USDC", "USDT"]:
            return routes  # Only USD stablecoins for now
        
        # e-CNY → mBridge → e-HKD → HKD → USDC path
        mbridge_fee = 13  # bps
        fx_fee = 10
        on_ramp_fee = 25
        total_fee = mbridge_fee + fx_fee + on_ramp_fee
        
        cbdc_fiat = self._get_cbdc_fiat(cbdc)
        fx_rate = self._get_fx_rate(cbdc_fiat, "USD")
        
        stable_amount = amount * fx_rate * (1 - Decimal(total_fee) / 10000)
        
        legs = [
            BridgeLeg(
                leg_id=f"MB-L1-{uuid.uuid4().hex[:6]}",
                sequence=1,
                from_asset=cbdc,
                from_type="CBDC",
                to_asset="e-HKD",
                to_type="CBDC",
                provider="mBridge",
                protocol="MBRIDGE_PVP",
                network="MBRIDGE",
                rate=self._get_fx_rate(cbdc_fiat, "HKD"),
                amount_in=amount,
                amount_out=amount * self._get_fx_rate(cbdc_fiat, "HKD"),
                fee_bps=mbridge_fee,
                gas_cost_usd=Decimal("0"),
                settlement_seconds=15,
                requires_kyc=True,
                compliance_check="CENTRAL_BANK_VALIDATED",
                description=f"mBridge: {cbdc} → e-HKD"
            ),
            BridgeLeg(
                leg_id=f"MB-L2-{uuid.uuid4().hex[:6]}",
                sequence=2,
                from_asset="e-HKD",
                from_type="CBDC",
                to_asset="HKD",
                to_type="FIAT",
                provider="HKMA",
                protocol="CBDC_REDEEM",
                network=None,
                rate=Decimal("1.0"),
                amount_in=amount * self._get_fx_rate(cbdc_fiat, "HKD"),
                amount_out=amount * self._get_fx_rate(cbdc_fiat, "HKD"),
                fee_bps=0,
                gas_cost_usd=Decimal("0"),
                settlement_seconds=5,
                requires_kyc=True,
                compliance_check="CENTRAL_BANK_VALIDATED",
                description="Redeem e-HKD to HKD"
            ),
            BridgeLeg(
                leg_id=f"MB-L3-{uuid.uuid4().hex[:6]}",
                sequence=3,
                from_asset="HKD",
                from_type="FIAT",
                to_asset=stablecoin,
                to_type="STABLECOIN",
                provider="Circle",
                protocol="ON_RAMP",
                network="ETHEREUM",
                rate=Decimal("1") / Decimal("7.82"),  # HKD to USD
                amount_in=amount * self._get_fx_rate(cbdc_fiat, "HKD"),
                amount_out=stable_amount,
                fee_bps=on_ramp_fee + fx_fee,
                gas_cost_usd=Decimal("1.00"),
                settlement_seconds=3600,
                requires_kyc=True,
                compliance_check="EXCHANGE_KYC",
                description=f"Mint {stablecoin}"
            )
        ]
        
        routes.append(BridgeRoute(
            route_id=f"C2S-MB-{cbdc[:3]}-{stablecoin}-{uuid.uuid4().hex[:4]}",
            route_name=f"mBridge Hybrid: {cbdc} → {stablecoin}",
            bridge_type=BridgeType.HYBRID_MBRIDGE,
            status=BridgeStatus.PILOT,
            legs=legs,
            source_asset=cbdc,
            source_type="CBDC",
            source_amount=amount,
            target_asset=stablecoin,
            target_type="STABLECOIN",
            target_amount=stable_amount.quantize(Decimal("0.01")),
            effective_rate=(stable_amount / amount).quantize(Decimal("0.000001")),
            total_fee_bps=total_fee,
            total_gas_usd=Decimal("1.00"),
            slippage_tolerance_bps=15,
            total_settlement_seconds=3620,
            settlement_finality="INSTANT",  # mBridge is atomic
            liquidity_score=85,
            counterparty_score=95,
            smart_contract_score=90,
            regulatory_score=98,  # Central bank backed
            overall_score=0,
            kyc_required=True,
            travel_rule_applies=False,  # CB-to-CB doesn't need travel rule
            sanctions_check=True,
            jurisdictions=[cbdc_info.get("country", ""), "HK", "US"],
            min_amount=Decimal("100000"),  # mBridge has high minimums
            max_amount=Decimal("100000000"),
            daily_limit=None,
            warnings=["Pilot phase - limited availability", "High minimum amount"],
            benefits=[
                "Central bank grade security",
                "Atomic PvP settlement",
                "No correspondent bank delays",
                "Multi-jurisdiction compliance"
            ]
        ))
        
        return routes
    
    async def _build_atomic_swap_route(
        self, cbdc: str, stablecoin: str, amount: Decimal,
        cbdc_info: dict, stable_info: dict
    ) -> List[BridgeRoute]:
        """Build experimental atomic swap route (future)"""
        routes = []
        
        # This is a future-ready implementation for when
        # CBDCs support atomic swaps with stablecoins
        
        cbdc_fiat = self._get_cbdc_fiat(cbdc)
        stable_peg = stable_info.get("pegged_currency", "USD")
        fx_rate = self._get_fx_rate(cbdc_fiat, stable_peg)
        
        atomic_fee = 5  # Very low for atomic swaps
        stable_amount = amount * fx_rate * (1 - Decimal(atomic_fee) / 10000)
        
        legs = [
            BridgeLeg(
                leg_id=f"AS-L1-{uuid.uuid4().hex[:6]}",
                sequence=1,
                from_asset=cbdc,
                from_type="CBDC",
                to_asset=stablecoin,
                to_type="STABLECOIN",
                provider="CBDC-Stable Bridge (Experimental)",
                protocol="HTLC_ATOMIC_SWAP",
                network="CROSS_CHAIN",
                rate=fx_rate,
                amount_in=amount,
                amount_out=stable_amount,
                fee_bps=atomic_fee,
                gas_cost_usd=Decimal("2.00"),  # Cross-chain gas
                settlement_seconds=300,  # 5 minutes
                requires_kyc=False,
                compliance_check="SMART_CONTRACT",
                description=f"Atomic swap {cbdc} ↔ {stablecoin}"
            )
        ]
        
        routes.append(BridgeRoute(
            route_id=f"C2S-AS-{cbdc[:3]}-{stablecoin}-{uuid.uuid4().hex[:4]}",
            route_name=f"Atomic Swap: {cbdc} ↔ {stablecoin} (Experimental)",
            bridge_type=BridgeType.ATOMIC_SWAP,
            status=BridgeStatus.EXPERIMENTAL,
            legs=legs,
            source_asset=cbdc,
            source_type="CBDC",
            source_amount=amount,
            target_asset=stablecoin,
            target_type="STABLECOIN",
            target_amount=stable_amount.quantize(Decimal("0.01")),
            effective_rate=(stable_amount / amount).quantize(Decimal("0.000001")),
            total_fee_bps=atomic_fee,
            total_gas_usd=Decimal("2.00"),
            slippage_tolerance_bps=5,
            total_settlement_seconds=300,
            settlement_finality="INSTANT",
            liquidity_score=60,  # Limited liquidity
            counterparty_score=70,
            smart_contract_score=65,  # New tech risk
            regulatory_score=40,  # Not yet regulated
            overall_score=0,
            kyc_required=False,
            travel_rule_applies=False,
            sanctions_check=False,
            jurisdictions=["GLOBAL"],
            min_amount=Decimal("100"),
            max_amount=Decimal("100000"),  # Limited
            daily_limit=Decimal("1000000"),
            warnings=[
                "EXPERIMENTAL - Use at own risk",
                "Smart contract risk",
                "Not regulated",
                "Limited liquidity"
            ],
            benefits=[
                "Lowest fees",
                "Fastest settlement",
                "No intermediaries",
                "Trustless execution"
            ]
        ))
        
        return routes
    
    # =========================================================================
    # STABLECOIN TO CBDC ROUTES
    # =========================================================================
    
    async def get_stable_to_cbdc_routes(
        self,
        stablecoin: str,
        cbdc: str,
        amount: Decimal,
        source_network: Optional[str] = None,
        require_regulated: bool = True
    ) -> List[BridgeRoute]:
        """
        Get all available routes for Stablecoin → CBDC conversion
        
        Args:
            stablecoin: Source stablecoin (e.g., "USDC", "USDT")
            cbdc: Target CBDC (e.g., "e-INR", "e-CNY")
            amount: Amount in source stablecoin
            source_network: Network where stablecoin is held
            require_regulated: Only return regulated routes
        
        Returns:
            List of BridgeRoute sorted by overall_score
        """
        routes = []
        
        stable_info = self.digital_currencies["stablecoins"].get(stablecoin)
        cbdc_info = self.digital_currencies["cbdc"].get(cbdc)
        
        if not stable_info or not cbdc_info:
            return routes
        
        stable_peg = stable_info["pegged_currency"]
        cbdc_fiat = self._get_cbdc_fiat(cbdc)
        
        # Route 1: Standard off-ramp path
        routes.extend(await self._build_stable_to_cbdc_fiat_route(
            stablecoin, cbdc, amount, stable_peg, cbdc_fiat,
            stable_info, cbdc_info, source_network
        ))
        
        # Route 2: CEX Bridge
        routes.extend(await self._build_stable_to_cbdc_cex_route(
            stablecoin, cbdc, amount, stable_peg, cbdc_fiat,
            stable_info, cbdc_info
        ))
        
        # Route 3: P2P/OTC Route (for large amounts)
        if amount >= Decimal("100000"):
            routes.extend(await self._build_stable_to_cbdc_otc_route(
                stablecoin, cbdc, amount, stable_peg, cbdc_fiat,
                stable_info, cbdc_info
            ))
        
        # Filter and sort
        if require_regulated:
            routes = [r for r in routes if r.regulatory_score >= 70]
        
        for route in routes:
            route.overall_score = self._calculate_route_score(route)
        
        return sorted(routes, key=lambda r: r.overall_score, reverse=True)
    
    async def _build_stable_to_cbdc_fiat_route(
        self, stablecoin: str, cbdc: str, amount: Decimal,
        stable_peg: str, cbdc_fiat: str,
        stable_info: dict, cbdc_info: dict,
        source_network: Optional[str]
    ) -> List[BridgeRoute]:
        """Build Stablecoin → Fiat → CBDC route"""
        routes = []
        
        fx_rate = self._get_fx_rate(stable_peg, cbdc_fiat)
        
        off_ramp_fee = 25
        fx_fee = 0 if stable_peg == cbdc_fiat else 15
        total_fee = off_ramp_fee + fx_fee
        
        fiat_amount = amount * (1 - Decimal(off_ramp_fee) / 10000)
        cbdc_amount = fiat_amount * fx_rate * (1 - Decimal(fx_fee) / 10000)
        
        network = source_network or stable_info.get("networks", [{"chain": "ETHEREUM"}])[0]["chain"]
        
        legs = [
            BridgeLeg(
                leg_id=f"S2C-L1-{uuid.uuid4().hex[:6]}",
                sequence=1,
                from_asset=stablecoin,
                from_type="STABLECOIN",
                to_asset=stable_peg,
                to_type="FIAT",
                provider=stable_info.get("issuer", "Issuer"),
                protocol="OFF_RAMP",
                network=network,
                rate=Decimal("1.0"),
                amount_in=amount,
                amount_out=fiat_amount,
                fee_bps=off_ramp_fee,
                gas_cost_usd=Decimal("0.50"),
                settlement_seconds=3600,
                requires_kyc=True,
                compliance_check="EXCHANGE_KYC",
                description=f"Redeem {stablecoin} to {stable_peg}"
            )
        ]
        
        if stable_peg != cbdc_fiat:
            legs.append(BridgeLeg(
                leg_id=f"S2C-L2-{uuid.uuid4().hex[:6]}",
                sequence=2,
                from_asset=stable_peg,
                from_type="FIAT",
                to_asset=cbdc_fiat,
                to_type="FIAT",
                provider="FX Provider",
                protocol="SWIFT/LOCAL",
                network=None,
                rate=fx_rate,
                amount_in=fiat_amount,
                amount_out=fiat_amount * fx_rate,
                fee_bps=fx_fee,
                gas_cost_usd=Decimal("0"),
                settlement_seconds=14400,
                requires_kyc=True,
                compliance_check="BANK_KYC",
                description=f"FX {stable_peg} → {cbdc_fiat}"
            ))
        
        legs.append(BridgeLeg(
            leg_id=f"S2C-L3-{uuid.uuid4().hex[:6]}",
            sequence=len(legs) + 1,
            from_asset=cbdc_fiat,
            from_type="FIAT",
            to_asset=cbdc,
            to_type="CBDC",
            provider=cbdc_info.get("issuer", "Central Bank"),
            protocol="CBDC_MINT",
            network=cbdc_info.get("technology"),
            rate=Decimal("1.0"),
            amount_in=fiat_amount * fx_rate if stable_peg != cbdc_fiat else fiat_amount,
            amount_out=cbdc_amount,
            fee_bps=0,
            gas_cost_usd=Decimal("0"),
            settlement_seconds=cbdc_info.get("settlement_seconds", 5),
            requires_kyc=True,
            compliance_check="CENTRAL_BANK_VALIDATED",
            description=f"Mint {cbdc}"
        ))
        
        total_settlement = sum(leg.settlement_seconds for leg in legs)
        
        routes.append(BridgeRoute(
            route_id=f"S2C-FI-{stablecoin}-{cbdc[:3]}-{uuid.uuid4().hex[:4]}",
            route_name=f"Fiat Bridge: {stablecoin} → {cbdc}",
            bridge_type=BridgeType.FIAT_INTERMEDIARY,
            status=BridgeStatus.ACTIVE,
            legs=legs,
            source_asset=stablecoin,
            source_type="STABLECOIN",
            source_amount=amount,
            target_asset=cbdc,
            target_type="CBDC",
            target_amount=cbdc_amount.quantize(Decimal("0.01")),
            effective_rate=(cbdc_amount / amount).quantize(Decimal("0.0001")),
            total_fee_bps=total_fee,
            total_gas_usd=Decimal("0.50"),
            slippage_tolerance_bps=10,
            total_settlement_seconds=total_settlement,
            settlement_finality="DEFERRED",
            liquidity_score=95,
            counterparty_score=90,
            smart_contract_score=85,
            regulatory_score=95,
            overall_score=0,
            kyc_required=True,
            travel_rule_applies=True,
            sanctions_check=True,
            jurisdictions=[stable_info.get("jurisdictions", ["US"])[0], cbdc_info.get("country", "")],
            min_amount=Decimal("100"),
            max_amount=cbdc_info.get("transaction_limits", {}).get("max_transaction", Decimal("10000000")),
            daily_limit=cbdc_info.get("transaction_limits", {}).get("daily_limit"),
            warnings=["FX settlement may take 4+ hours"] if stable_peg != cbdc_fiat else [],
            benefits=["Fully regulated", "Central bank guarantee", "No smart contract risk"]
        ))
        
        return routes
    
    async def _build_stable_to_cbdc_cex_route(
        self, stablecoin: str, cbdc: str, amount: Decimal,
        stable_peg: str, cbdc_fiat: str,
        stable_info: dict, cbdc_info: dict
    ) -> List[BridgeRoute]:
        """Build CEX-based Stablecoin → CBDC route"""
        routes = []
        
        fx_rate = self._get_fx_rate(stable_peg, cbdc_fiat)
        cex_fee = 50
        
        cbdc_amount = amount * fx_rate * (1 - Decimal(cex_fee) / 10000)
        
        legs = [
            BridgeLeg(
                leg_id=f"S2C-CEX-L1-{uuid.uuid4().hex[:6]}",
                sequence=1,
                from_asset=stablecoin,
                from_type="STABLECOIN",
                to_asset=cbdc_fiat,
                to_type="FIAT",
                provider="Coinbase Prime",
                protocol="CEX_OFFRAMP",
                network="ETHEREUM",
                rate=fx_rate,
                amount_in=amount,
                amount_out=amount * fx_rate * (1 - Decimal(cex_fee) / 10000),
                fee_bps=cex_fee,
                gas_cost_usd=Decimal("0.50"),
                settlement_seconds=7200,
                requires_kyc=True,
                compliance_check="EXCHANGE_KYC",
                description=f"CEX: {stablecoin} → {cbdc_fiat}"
            ),
            BridgeLeg(
                leg_id=f"S2C-CEX-L2-{uuid.uuid4().hex[:6]}",
                sequence=2,
                from_asset=cbdc_fiat,
                from_type="FIAT",
                to_asset=cbdc,
                to_type="CBDC",
                provider=cbdc_info.get("issuer", "Central Bank"),
                protocol="CBDC_MINT",
                network=cbdc_info.get("technology"),
                rate=Decimal("1.0"),
                amount_in=cbdc_amount,
                amount_out=cbdc_amount,
                fee_bps=0,
                gas_cost_usd=Decimal("0"),
                settlement_seconds=5,
                requires_kyc=True,
                compliance_check="CENTRAL_BANK_VALIDATED",
                description=f"Mint {cbdc}"
            )
        ]
        
        routes.append(BridgeRoute(
            route_id=f"S2C-CEX-{stablecoin}-{cbdc[:3]}-{uuid.uuid4().hex[:4]}",
            route_name=f"CEX Bridge: {stablecoin} → {cbdc}",
            bridge_type=BridgeType.CEX_BRIDGE,
            status=BridgeStatus.ACTIVE,
            legs=legs,
            source_asset=stablecoin,
            source_type="STABLECOIN",
            source_amount=amount,
            target_asset=cbdc,
            target_type="CBDC",
            target_amount=cbdc_amount.quantize(Decimal("0.01")),
            effective_rate=(cbdc_amount / amount).quantize(Decimal("0.0001")),
            total_fee_bps=cex_fee,
            total_gas_usd=Decimal("0.50"),
            slippage_tolerance_bps=20,
            total_settlement_seconds=7205,
            settlement_finality="DEFERRED",
            liquidity_score=90,
            counterparty_score=85,
            smart_contract_score=95,
            regulatory_score=90,
            overall_score=0,
            kyc_required=True,
            travel_rule_applies=True,
            sanctions_check=True,
            jurisdictions=["US", cbdc_info.get("country", "")],
            min_amount=Decimal("1000"),
            max_amount=Decimal("5000000"),
            daily_limit=Decimal("25000000"),
            warnings=["CEX custody risk"],
            benefits=["Faster than bank", "Single counterparty"]
        ))
        
        return routes
    
    async def _build_stable_to_cbdc_otc_route(
        self, stablecoin: str, cbdc: str, amount: Decimal,
        stable_peg: str, cbdc_fiat: str,
        stable_info: dict, cbdc_info: dict
    ) -> List[BridgeRoute]:
        """Build OTC route for large amounts"""
        routes = []
        
        fx_rate = self._get_fx_rate(stable_peg, cbdc_fiat)
        otc_fee = 15  # Lower fees for large OTC trades
        
        cbdc_amount = amount * fx_rate * (1 - Decimal(otc_fee) / 10000)
        
        legs = [
            BridgeLeg(
                leg_id=f"S2C-OTC-L1-{uuid.uuid4().hex[:6]}",
                sequence=1,
                from_asset=stablecoin,
                from_type="STABLECOIN",
                to_asset=cbdc,
                to_type="CBDC",
                provider="OTC Desk (Cumberland/Circle Trade)",
                protocol="OTC_TRADE",
                network="BILATERAL",
                rate=fx_rate * (1 - Decimal(otc_fee) / 10000),
                amount_in=amount,
                amount_out=cbdc_amount,
                fee_bps=otc_fee,
                gas_cost_usd=Decimal("0"),
                settlement_seconds=86400,  # T+1
                requires_kyc=True,
                compliance_check="INSTITUTIONAL_KYC",
                description=f"OTC: {stablecoin} → {cbdc}"
            )
        ]
        
        routes.append(BridgeRoute(
            route_id=f"S2C-OTC-{stablecoin}-{cbdc[:3]}-{uuid.uuid4().hex[:4]}",
            route_name=f"OTC Trade: {stablecoin} → {cbdc}",
            bridge_type=BridgeType.FIAT_INTERMEDIARY,
            status=BridgeStatus.ACTIVE,
            legs=legs,
            source_asset=stablecoin,
            source_type="STABLECOIN",
            source_amount=amount,
            target_asset=cbdc,
            target_type="CBDC",
            target_amount=cbdc_amount.quantize(Decimal("0.01")),
            effective_rate=(cbdc_amount / amount).quantize(Decimal("0.0001")),
            total_fee_bps=otc_fee,
            total_gas_usd=Decimal("0"),
            slippage_tolerance_bps=5,
            total_settlement_seconds=86400,
            settlement_finality="DEFERRED",
            liquidity_score=98,
            counterparty_score=95,
            smart_contract_score=100,  # No smart contract
            regulatory_score=95,
            overall_score=0,
            kyc_required=True,
            travel_rule_applies=True,
            sanctions_check=True,
            jurisdictions=["US", cbdc_info.get("country", "")],
            min_amount=Decimal("100000"),
            max_amount=Decimal("500000000"),
            daily_limit=None,
            warnings=["T+1 settlement", "Requires institutional account"],
            benefits=["Lowest fees for large amounts", "No slippage", "White-glove service"]
        ))
        
        return routes
    
    # =========================================================================
    # HELPER METHODS
    # =========================================================================
    
    def _get_cbdc_fiat(self, cbdc: str) -> str:
        """Get underlying fiat currency for CBDC"""
        mapping = {
            "e-INR": "INR",
            "e-CNY": "CNY",
            "e-HKD": "HKD",
            "e-THB": "THB",
            "e-AED": "AED",
            "e-SGD": "SGD",
            "e-EUR": "EUR",
            "e-USD": "USD",
        }
        return mapping.get(cbdc, cbdc.replace("e-", ""))
    
    def _get_fx_rate(self, source: str, target: str) -> Decimal:
        """Get FX rate between fiat currencies"""
        if source == target:
            return Decimal("1.0")
        
        rates = {
            "USDINR": Decimal("84.50"),
            "USDCNY": Decimal("7.25"),
            "USDHKD": Decimal("7.82"),
            "USDTHB": Decimal("34.50"),
            "USDAED": Decimal("3.67"),
            "USDSGD": Decimal("1.345"),
            "EURUSD": Decimal("1.056"),
            "GBPUSD": Decimal("1.26"),
        }
        
        key = f"{source}{target}"
        if key in rates:
            return rates[key]
        
        inv_key = f"{target}{source}"
        if inv_key in rates:
            return (Decimal("1") / rates[inv_key]).quantize(Decimal("0.0001"))
        
        # Try via USD
        if source != "USD" and target != "USD":
            source_to_usd = self._get_fx_rate(source, "USD")
            usd_to_target = self._get_fx_rate("USD", target)
            if source_to_usd and usd_to_target:
                return (source_to_usd * usd_to_target).quantize(Decimal("0.0001"))
        
        return Decimal("1.0")
    
    def _calculate_route_score(self, route: BridgeRoute) -> float:
        """Calculate overall route score"""
        # Weighted scoring
        weights = {
            "cost": 0.35,
            "speed": 0.25,
            "liquidity": 0.15,
            "regulatory": 0.15,
            "reliability": 0.10
        }
        
        # Normalize cost score (lower fees = higher score)
        cost_score = max(0, 100 - route.total_fee_bps)
        
        # Normalize speed score (faster = higher score)
        speed_score = max(0, 100 - (route.total_settlement_seconds / 3600))
        
        overall = (
            cost_score * weights["cost"] +
            speed_score * weights["speed"] +
            route.liquidity_score * weights["liquidity"] +
            route.regulatory_score * weights["regulatory"] +
            route.counterparty_score * weights["reliability"]
        )
        
        return round(overall, 2)
    
    # =========================================================================
    # CONVERSION MATRIX
    # =========================================================================
    
    async def get_all_routes(
        self,
        source: str,
        source_type: str,
        target: str,
        target_type: str,
        amount: Decimal
    ) -> List[BridgeRoute]:
        """
        Universal router - get routes for any conversion type
        
        Args:
            source: Source asset code
            source_type: FIAT, CBDC, or STABLECOIN
            target: Target asset code
            target_type: FIAT, CBDC, or STABLECOIN
            amount: Amount in source asset
        
        Returns:
            List of BridgeRoute sorted by score
        """
        if source_type == "CBDC" and target_type == "STABLECOIN":
            return await self.get_cbdc_to_stable_routes(source, target, amount)
        
        elif source_type == "STABLECOIN" and target_type == "CBDC":
            return await self.get_stable_to_cbdc_routes(source, target, amount)
        
        # For other types, delegate to universal engine
        return []
    
    def get_supported_pairs(self) -> Dict[str, List[str]]:
        """Get all supported CBDC ↔ Stablecoin pairs"""
        cbdcs = list(self.digital_currencies.get("cbdc", {}).keys())
        stables = list(self.digital_currencies.get("stablecoins", {}).keys())
        
        return {
            "cbdc_to_stablecoin": [
                f"{cbdc} → {stable}"
                for cbdc in cbdcs
                for stable in stables
            ],
            "stablecoin_to_cbdc": [
                f"{stable} → {cbdc}"
                for stable in stables
                for cbdc in cbdcs
            ]
        }


# Singleton instance
_bridge_instance: Optional[CBDCStableBridge] = None


def get_bridge_engine(config_dir: str = "config") -> CBDCStableBridge:
    """Get or create bridge engine instance"""
    global _bridge_instance
    if _bridge_instance is None:
        _bridge_instance = CBDCStableBridge(config_dir)
    return _bridge_instance
