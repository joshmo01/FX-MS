"""
Multi-Rail FX Routing Engine

Intelligent routing engine that evaluates multiple rails:
- Traditional Fiat (SWIFT, Local)
- CBDC (Domestic + Cross-border via mBridge)
- Stablecoins (USDC, USDT, etc.)
- Hybrid paths (Fiat→CBDC, Fiat→Stablecoin→Fiat, etc.)
"""
import json
import uuid
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Tuple, Any
from pathlib import Path
import time

from app.models.multi_rail_models import (
    MultiRailRoutingRequest,
    MultiRailRoutingResponse,
    MultiRailRoute,
    RailLeg,
    CurrencyType,
    RailType,
    SettlementType,
    ComplianceLevel,
    RailPreference,
    BlockchainNetwork,
    CBDCRouteInfo,
    StablecoinRouteInfo,
    RailComparison,
)

logger = logging.getLogger(__name__)


class MultiRailRoutingEngine:
    """
    Multi-Rail FX Routing Engine
    
    Evaluates all available rails (Fiat, CBDC, Stablecoin) and their
    combinations to find optimal routes based on cost, speed, and compliance.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._load_configurations()
        
        # Market rates for demonstration
        self._fiat_rates = {
            "USDINR": Decimal("84.50"),
            "EURINR": Decimal("89.20"),
            "GBPINR": Decimal("106.50"),
            "EURUSD": Decimal("1.0557"),
            "USDSGD": Decimal("1.34"),
            "USDCNY": Decimal("7.25"),
            "USDHKD": Decimal("7.82"),
            "USDTHB": Decimal("34.50"),
            "USDAED": Decimal("3.67"),
        }
    
    def _load_configurations(self):
        """Load all configuration files"""
        with open(self.config_dir / "digital_currencies.json") as f:
            self.digital_currencies = json.load(f)
        
        with open(self.config_dir / "digital_rails.json") as f:
            self.digital_rails = json.load(f)
        
        # Load existing configs
        with open(self.config_dir / "fx_providers.json") as f:
            self.fx_providers = json.load(f)
        
        with open(self.config_dir / "customer_tiers.json") as f:
            self.customer_tiers = json.load(f)
    
    async def get_multi_rail_route(
        self,
        request: MultiRailRoutingRequest
    ) -> MultiRailRoutingResponse:
        """
        Get optimal route across all available rails.
        """
        start_time = time.time()
        request_id = f"MR-{uuid.uuid4().hex[:12].upper()}"
        
        # 1. Determine source and target currency types
        source_info = self._get_currency_info(request.source_currency, request.source_type)
        target_info = self._get_currency_info(request.target_currency, request.target_type)
        
        # 2. Find all available routes
        all_routes = []
        rails_evaluated = []
        
        # 2a. Fiat routes
        fiat_routes = await self._evaluate_fiat_routes(request, source_info, target_info)
        all_routes.extend(fiat_routes)
        if fiat_routes:
            rails_evaluated.append("FIAT")
        
        # 2b. CBDC routes
        cbdc_routes = await self._evaluate_cbdc_routes(request, source_info, target_info)
        all_routes.extend(cbdc_routes)
        if cbdc_routes:
            rails_evaluated.append("CBDC")
        
        # 2c. Stablecoin routes
        stable_routes = await self._evaluate_stablecoin_routes(request, source_info, target_info)
        all_routes.extend(stable_routes)
        if stable_routes:
            rails_evaluated.append("STABLECOIN")
        
        # 2d. Hybrid routes (if applicable)
        hybrid_routes = await self._evaluate_hybrid_routes(request, source_info, target_info)
        all_routes.extend(hybrid_routes)
        if hybrid_routes:
            rails_evaluated.append("HYBRID")
        
        # 3. Score and rank routes
        scored_routes = self._score_routes(all_routes, request)
        
        # 4. Select recommended route based on preference
        recommended = self._select_recommended(scored_routes, request.rail_preference)
        
        # 5. Categorize routes
        categorized = self._categorize_routes(scored_routes)
        
        # 6. Build comparison
        comparison = self._build_comparison(scored_routes)
        
        # 7. Get additional info
        cbdc_info = self._get_cbdc_route_info(recommended) if "CBDC" in recommended.route_type else None
        stable_info = self._get_stablecoin_route_info(recommended) if "STABLE" in recommended.route_type else None
        
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Multi-rail routing completed in {execution_time:.2f}ms")
        
        return MultiRailRoutingResponse(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            source_currency=request.source_currency,
            source_type=request.source_type,
            source_amount=request.source_amount,
            target_currency=request.target_currency,
            target_type=request.target_type,
            rails_evaluated=rails_evaluated,
            cbdc_available=len(categorized["cbdc"]) > 0,
            stablecoin_available=len(categorized["stablecoin"]) > 0,
            fiat_available=len(categorized["fiat"]) > 0,
            cbdc_info=cbdc_info,
            stablecoin_info=stable_info,
            recommended_route=recommended,
            cbdc_routes=categorized["cbdc"][:3],
            stablecoin_routes=categorized["stablecoin"][:3],
            fiat_routes=categorized["fiat"][:3],
            best_rate_route=comparison.get("best_rate_route"),
            fastest_route=comparison.get("fastest_route"),
            lowest_cost_route=comparison.get("lowest_cost_route"),
            comparison=comparison,
            compliance_requirements=self._get_compliance_requirements(recommended),
            warnings=self._generate_warnings(request, recommended)
        )
    
    def _get_currency_info(self, currency: str, currency_type: CurrencyType) -> Dict:
        """Get currency information"""
        if currency_type == CurrencyType.CBDC:
            return {
                "code": currency,
                "type": CurrencyType.CBDC,
                "info": self.digital_currencies["cbdc"].get(currency, {})
            }
        elif currency_type == CurrencyType.STABLECOIN:
            return {
                "code": currency,
                "type": CurrencyType.STABLECOIN,
                "info": self.digital_currencies["stablecoins"].get(currency, {})
            }
        else:
            return {
                "code": currency,
                "type": CurrencyType.FIAT,
                "info": {"code": currency}
            }
    
    async def _evaluate_fiat_routes(
        self,
        request: MultiRailRoutingRequest,
        source_info: Dict,
        target_info: Dict
    ) -> List[MultiRailRoute]:
        """Evaluate traditional fiat routes"""
        routes = []
        
        # Only if both source and target are fiat (or can be converted to fiat)
        source_fiat = self._get_fiat_currency(source_info)
        target_fiat = self._get_fiat_currency(target_info)
        
        if not source_fiat or not target_fiat:
            return routes
        
        # Get fiat rate
        rate = self._get_fiat_rate(source_fiat, target_fiat)
        if not rate:
            return routes
        
        # Evaluate fiat providers
        for provider_id, provider in self.fx_providers["providers"].items():
            if not provider["is_active"]:
                continue
            if provider["type"] == "MARKET_DATA":
                continue
            
            # Calculate amounts
            markup_bps = provider.get("markup_bps", 10)
            spread_bps = 25
            total_cost_bps = markup_bps + spread_bps
            
            effective_rate = rate * (1 + Decimal(total_cost_bps) / 10000)
            target_amount = request.source_amount * effective_rate
            
            settlement_hours = provider.get("settlement_hours", 24)
            
            route = MultiRailRoute(
                route_id=f"FIAT-{uuid.uuid4().hex[:8].upper()}",
                route_name=f"Fiat via {provider['name']}",
                route_type="FIAT_DIRECT",
                legs=[RailLeg(
                    leg_number=1,
                    rail_type=RailType.FIAT_SWIFT if settlement_hours > 4 else RailType.FIAT_LOCAL,
                    provider=provider["name"],
                    source_currency=source_fiat,
                    source_type=CurrencyType.FIAT,
                    source_amount=request.source_amount,
                    target_currency=target_fiat,
                    target_type=CurrencyType.FIAT,
                    target_amount=target_amount,
                    exchange_rate=effective_rate,
                    fee_amount=request.source_amount * Decimal(total_cost_bps) / 10000,
                    fee_currency=source_fiat,
                    settlement_type=SettlementType.SAME_DAY if settlement_hours <= 4 else SettlementType.T_PLUS_2,
                    settlement_seconds=settlement_hours * 3600,
                    compliance_level=ComplianceLevel.FULL_KYC
                )],
                total_legs=1,
                source_currency=source_fiat,
                source_type=CurrencyType.FIAT,
                source_amount=request.source_amount,
                target_currency=target_fiat,
                target_type=CurrencyType.FIAT,
                target_amount=target_amount.quantize(Decimal("0.01")),
                effective_rate=effective_rate.quantize(Decimal("0.0001")),
                total_fees_usd=self._to_usd(request.source_amount * Decimal(total_cost_bps) / 10000, source_fiat),
                total_cost_bps=total_cost_bps,
                total_settlement_seconds=settlement_hours * 3600,
                settlement_type=SettlementType.SAME_DAY if settlement_hours <= 4 else SettlementType.T_PLUS_2,
                stp_enabled=provider["capabilities"].get("stp_enabled", False),
                cost_score=0,
                speed_score=0,
                reliability_score=provider.get("reliability_score", 0.9) * 100,
                compliance_score=90,
                overall_score=0,
                compliance_level=ComplianceLevel.FULL_KYC,
                sanctions_screening="PROVIDER"
            )
            routes.append(route)
        
        return routes
    
    async def _evaluate_cbdc_routes(
        self,
        request: MultiRailRoutingRequest,
        source_info: Dict,
        target_info: Dict
    ) -> List[MultiRailRoute]:
        """Evaluate CBDC routes"""
        routes = []
        
        source_fiat = self._get_fiat_currency(source_info)
        target_fiat = self._get_fiat_currency(target_info)
        
        # Check for domestic CBDC route
        source_cbdc = self._get_cbdc_for_fiat(source_fiat)
        target_cbdc = self._get_cbdc_for_fiat(target_fiat)
        
        # Domestic CBDC (same country)
        if source_fiat == target_fiat and target_cbdc:
            cbdc_info = self.digital_currencies["cbdc"][target_cbdc]
            if cbdc_info["is_active"]:
                route = self._build_domestic_cbdc_route(request, source_fiat, target_cbdc, cbdc_info)
                if route:
                    routes.append(route)
        
        # Cross-border CBDC (mBridge)
        if source_cbdc and target_cbdc:
            source_cbdc_info = self.digital_currencies["cbdc"].get(source_cbdc, {})
            target_cbdc_info = self.digital_currencies["cbdc"].get(target_cbdc, {})
            
            if (source_cbdc_info.get("mbridge_participant") and 
                target_cbdc_info.get("mbridge_participant")):
                route = self._build_mbridge_route(request, source_fiat, target_fiat, 
                                                   source_cbdc, target_cbdc)
                if route:
                    routes.append(route)
        
        # Fiat to CBDC route (e.g., USD → e-INR)
        if target_cbdc and source_fiat != target_fiat:
            route = self._build_fiat_to_cbdc_route(request, source_fiat, target_fiat, target_cbdc)
            if route:
                routes.append(route)
        
        return routes
    
    async def _evaluate_stablecoin_routes(
        self,
        request: MultiRailRoutingRequest,
        source_info: Dict,
        target_info: Dict
    ) -> List[MultiRailRoute]:
        """Evaluate stablecoin bridge routes"""
        routes = []
        
        source_fiat = self._get_fiat_currency(source_info)
        target_fiat = self._get_fiat_currency(target_info)
        
        if not source_fiat or not target_fiat:
            return routes
        
        # Find applicable stablecoins
        # USD-pegged stablecoins for USD source/target
        applicable_stables = []
        
        if source_fiat == "USD":
            applicable_stables.extend(["USDC", "USDT"])
        if target_fiat == "USD":
            applicable_stables.extend(["USDC", "USDT"])
        if source_fiat == "EUR" or target_fiat == "EUR":
            applicable_stables.append("EURC")
        if source_fiat == "SGD" or target_fiat == "SGD":
            applicable_stables.append("XSGD")
        
        # Remove duplicates
        applicable_stables = list(set(applicable_stables))
        
        for stable in applicable_stables:
            stable_info = self.digital_currencies["stablecoins"].get(stable)
            if not stable_info or not stable_info["is_active"]:
                continue
            
            # Evaluate different networks
            for network in stable_info["networks"][:2]:  # Top 2 networks
                route = self._build_stablecoin_bridge_route(
                    request, source_fiat, target_fiat, stable, stable_info, network
                )
                if route:
                    routes.append(route)
        
        return routes
    
    async def _evaluate_hybrid_routes(
        self,
        request: MultiRailRoutingRequest,
        source_info: Dict,
        target_info: Dict
    ) -> List[MultiRailRoute]:
        """Evaluate hybrid routes (e.g., Fiat→Stablecoin→CBDC)"""
        routes = []
        # Hybrid routes are experimental - placeholder for future
        return routes
    
    def _build_domestic_cbdc_route(
        self,
        request: MultiRailRoutingRequest,
        fiat: str,
        cbdc: str,
        cbdc_info: Dict
    ) -> Optional[MultiRailRoute]:
        """Build domestic CBDC route (Fiat ↔ CBDC same country)"""
        # This is instant and usually free
        return MultiRailRoute(
            route_id=f"CBDC-DOM-{uuid.uuid4().hex[:8].upper()}",
            route_name=f"Domestic CBDC ({cbdc_info['name']})",
            route_type="CBDC_DOMESTIC",
            legs=[RailLeg(
                leg_number=1,
                rail_type=RailType.CBDC_DOMESTIC,
                provider=cbdc_info["issuer"],
                source_currency=fiat,
                source_type=CurrencyType.FIAT,
                source_amount=request.source_amount,
                target_currency=cbdc,
                target_type=CurrencyType.CBDC,
                target_amount=request.source_amount,  # 1:1 for domestic
                exchange_rate=Decimal("1.0"),
                fee_amount=Decimal("0"),
                fee_currency=fiat,
                settlement_type=SettlementType.INSTANT,
                settlement_seconds=cbdc_info.get("settlement_seconds", 5),
                compliance_level=ComplianceLevel.FULL_KYC
            )],
            total_legs=1,
            source_currency=fiat,
            source_type=CurrencyType.FIAT,
            source_amount=request.source_amount,
            target_currency=cbdc,
            target_type=CurrencyType.CBDC,
            target_amount=request.source_amount,
            effective_rate=Decimal("1.0"),
            total_fees_usd=Decimal("0"),
            total_cost_bps=0,
            total_settlement_seconds=cbdc_info.get("settlement_seconds", 5),
            settlement_type=SettlementType.INSTANT,
            stp_enabled=True,
            cost_score=100,
            speed_score=100,
            reliability_score=99,
            compliance_score=100,
            overall_score=0,
            compliance_level=ComplianceLevel.FULL_KYC,
            sanctions_screening="CENTRAL_BANK"
        )
    
    def _build_mbridge_route(
        self,
        request: MultiRailRoutingRequest,
        source_fiat: str,
        target_fiat: str,
        source_cbdc: str,
        target_cbdc: str
    ) -> Optional[MultiRailRoute]:
        """Build mBridge cross-border CBDC route"""
        mbridge = self.digital_rails["digital_rails"]["MBRIDGE"]
        
        # Get FX rate
        rate = self._get_fiat_rate(source_fiat, target_fiat)
        if not rate:
            return None
        
        # mBridge fees
        fee_bps = mbridge["fee_structure"]["cross_border_bps"] + mbridge["fee_structure"]["fx_spread_bps"]
        effective_rate = rate * (1 + Decimal(fee_bps) / 10000)
        target_amount = request.source_amount * effective_rate
        
        return MultiRailRoute(
            route_id=f"CBDC-MB-{uuid.uuid4().hex[:8].upper()}",
            route_name=f"mBridge ({source_cbdc} → {target_cbdc})",
            route_type="CBDC_MBRIDGE",
            legs=[
                RailLeg(
                    leg_number=1,
                    rail_type=RailType.CBDC_DOMESTIC,
                    provider="Originating Central Bank",
                    source_currency=source_fiat,
                    source_type=CurrencyType.FIAT,
                    source_amount=request.source_amount,
                    target_currency=source_cbdc,
                    target_type=CurrencyType.CBDC,
                    target_amount=request.source_amount,
                    exchange_rate=Decimal("1.0"),
                    fee_amount=Decimal("0"),
                    fee_currency=source_fiat,
                    settlement_type=SettlementType.INSTANT,
                    settlement_seconds=5,
                    compliance_level=ComplianceLevel.CENTRAL_BANK
                ),
                RailLeg(
                    leg_number=2,
                    rail_type=RailType.MBRIDGE,
                    provider="mBridge Platform",
                    source_currency=source_cbdc,
                    source_type=CurrencyType.CBDC,
                    source_amount=request.source_amount,
                    target_currency=target_cbdc,
                    target_type=CurrencyType.CBDC,
                    target_amount=target_amount,
                    exchange_rate=effective_rate,
                    fee_amount=request.source_amount * Decimal(fee_bps) / 10000,
                    fee_currency=source_fiat,
                    settlement_type=SettlementType.ATOMIC,
                    settlement_seconds=10,
                    compliance_level=ComplianceLevel.CENTRAL_BANK
                )
            ],
            total_legs=2,
            source_currency=source_fiat,
            source_type=CurrencyType.FIAT,
            source_amount=request.source_amount,
            target_currency=target_fiat,
            target_type=CurrencyType.FIAT,
            target_amount=target_amount.quantize(Decimal("0.01")),
            effective_rate=effective_rate.quantize(Decimal("0.0001")),
            total_fees_usd=self._to_usd(request.source_amount * Decimal(fee_bps) / 10000, source_fiat),
            total_cost_bps=fee_bps,
            total_settlement_seconds=15,
            settlement_type=SettlementType.ATOMIC,
            stp_enabled=True,
            cost_score=0,
            speed_score=0,
            reliability_score=98,
            compliance_score=100,
            overall_score=0,
            compliance_level=ComplianceLevel.CENTRAL_BANK,
            sanctions_screening="BOTH_JURISDICTIONS"
        )
    
    def _build_fiat_to_cbdc_route(
        self,
        request: MultiRailRoutingRequest,
        source_fiat: str,
        target_fiat: str,
        target_cbdc: str
    ) -> Optional[MultiRailRoute]:
        """Build Fiat → FX → CBDC route"""
        rate = self._get_fiat_rate(source_fiat, target_fiat)
        if not rate:
            return None
        
        cbdc_info = self.digital_currencies["cbdc"].get(target_cbdc, {})
        
        # FX spread + CBDC fee
        fee_bps = 20  # FX spread
        effective_rate = rate * (1 + Decimal(fee_bps) / 10000)
        target_amount = request.source_amount * effective_rate
        
        return MultiRailRoute(
            route_id=f"CBDC-FX-{uuid.uuid4().hex[:8].upper()}",
            route_name=f"FX to CBDC ({source_fiat} → {target_cbdc})",
            route_type="FIAT_TO_CBDC",
            legs=[
                RailLeg(
                    leg_number=1,
                    rail_type=RailType.FIAT_SWIFT,
                    provider="FX Provider",
                    source_currency=source_fiat,
                    source_type=CurrencyType.FIAT,
                    source_amount=request.source_amount,
                    target_currency=target_fiat,
                    target_type=CurrencyType.FIAT,
                    target_amount=target_amount,
                    exchange_rate=effective_rate,
                    fee_amount=request.source_amount * Decimal(fee_bps) / 10000,
                    fee_currency=source_fiat,
                    settlement_type=SettlementType.SAME_DAY,
                    settlement_seconds=14400,
                    compliance_level=ComplianceLevel.FULL_KYC
                ),
                RailLeg(
                    leg_number=2,
                    rail_type=RailType.CBDC_DOMESTIC,
                    provider=cbdc_info.get("issuer", "Central Bank"),
                    source_currency=target_fiat,
                    source_type=CurrencyType.FIAT,
                    source_amount=target_amount,
                    target_currency=target_cbdc,
                    target_type=CurrencyType.CBDC,
                    target_amount=target_amount,
                    exchange_rate=Decimal("1.0"),
                    fee_amount=Decimal("0"),
                    fee_currency=target_fiat,
                    settlement_type=SettlementType.INSTANT,
                    settlement_seconds=5,
                    compliance_level=ComplianceLevel.FULL_KYC
                )
            ],
            total_legs=2,
            source_currency=source_fiat,
            source_type=CurrencyType.FIAT,
            source_amount=request.source_amount,
            target_currency=target_cbdc,
            target_type=CurrencyType.CBDC,
            target_amount=target_amount.quantize(Decimal("0.01")),
            effective_rate=effective_rate.quantize(Decimal("0.0001")),
            total_fees_usd=self._to_usd(request.source_amount * Decimal(fee_bps) / 10000, source_fiat),
            total_cost_bps=fee_bps,
            total_settlement_seconds=14405,
            settlement_type=SettlementType.SAME_DAY,
            stp_enabled=True,
            cost_score=0,
            speed_score=0,
            reliability_score=95,
            compliance_score=95,
            overall_score=0,
            compliance_level=ComplianceLevel.FULL_KYC,
            sanctions_screening="BANK_LEVEL"
        )
    
    def _build_stablecoin_bridge_route(
        self,
        request: MultiRailRoutingRequest,
        source_fiat: str,
        target_fiat: str,
        stable: str,
        stable_info: Dict,
        network: Dict
    ) -> Optional[MultiRailRoute]:
        """Build Fiat → Stablecoin → Fiat bridge route"""
        # Get rates
        source_to_stable_rate = self._get_fiat_rate(source_fiat, stable_info["pegged_currency"])
        stable_to_target_rate = self._get_fiat_rate(stable_info["pegged_currency"], target_fiat)
        
        if not source_to_stable_rate or not stable_to_target_rate:
            return None
        
        # Calculate fees
        on_ramp_bps = 50
        off_ramp_bps = 50
        network_fee_usd = Decimal(str(network["fee_usd"]))
        total_fee_bps = on_ramp_bps + off_ramp_bps
        
        # Calculate amounts
        stable_amount = request.source_amount * source_to_stable_rate * (1 - Decimal(on_ramp_bps) / 10000)
        target_amount = stable_amount * stable_to_target_rate * (1 - Decimal(off_ramp_bps) / 10000)
        
        effective_rate = target_amount / request.source_amount
        
        settlement_seconds = network["settlement_seconds"] + 7200  # Network + off-ramp
        
        return MultiRailRoute(
            route_id=f"STABLE-{stable}-{network['chain'][:3]}-{uuid.uuid4().hex[:6].upper()}",
            route_name=f"Stablecoin Bridge ({stable} on {network['chain']})",
            route_type=f"STABLE_BRIDGE_{stable}",
            legs=[
                RailLeg(
                    leg_number=1,
                    rail_type=RailType.STABLECOIN_BRIDGE,
                    provider="On-Ramp Provider",
                    source_currency=source_fiat,
                    source_type=CurrencyType.FIAT,
                    source_amount=request.source_amount,
                    target_currency=stable,
                    target_type=CurrencyType.STABLECOIN,
                    target_amount=stable_amount,
                    exchange_rate=source_to_stable_rate,
                    fee_amount=request.source_amount * Decimal(on_ramp_bps) / 10000,
                    fee_currency=source_fiat,
                    settlement_type=SettlementType.SAME_DAY,
                    settlement_seconds=3600,
                    blockchain_network=BlockchainNetwork(network["chain"]),
                    compliance_level=ComplianceLevel.FULL_KYC
                ),
                RailLeg(
                    leg_number=2,
                    rail_type=RailType.STABLECOIN_BRIDGE,
                    provider=f"{network['chain']} Network",
                    source_currency=stable,
                    source_type=CurrencyType.STABLECOIN,
                    source_amount=stable_amount,
                    target_currency=stable,
                    target_type=CurrencyType.STABLECOIN,
                    target_amount=stable_amount,
                    exchange_rate=Decimal("1.0"),
                    fee_amount=network_fee_usd,
                    fee_currency="USD",
                    settlement_type=SettlementType.NEAR_INSTANT,
                    settlement_seconds=network["settlement_seconds"],
                    blockchain_network=BlockchainNetwork(network["chain"]),
                    network_fee_usd=network_fee_usd,
                    compliance_level=ComplianceLevel.BASIC_KYC
                ),
                RailLeg(
                    leg_number=3,
                    rail_type=RailType.STABLECOIN_BRIDGE,
                    provider="Off-Ramp Provider",
                    source_currency=stable,
                    source_type=CurrencyType.STABLECOIN,
                    source_amount=stable_amount,
                    target_currency=target_fiat,
                    target_type=CurrencyType.FIAT,
                    target_amount=target_amount,
                    exchange_rate=stable_to_target_rate,
                    fee_amount=stable_amount * Decimal(off_ramp_bps) / 10000,
                    fee_currency=stable_info["pegged_currency"],
                    settlement_type=SettlementType.SAME_DAY,
                    settlement_seconds=3600,
                    blockchain_network=BlockchainNetwork(network["chain"]),
                    compliance_level=ComplianceLevel.FULL_KYC
                )
            ],
            total_legs=3,
            source_currency=source_fiat,
            source_type=CurrencyType.FIAT,
            source_amount=request.source_amount,
            target_currency=target_fiat,
            target_type=CurrencyType.FIAT,
            target_amount=target_amount.quantize(Decimal("0.01")),
            effective_rate=effective_rate.quantize(Decimal("0.0001")),
            total_fees_usd=self._to_usd(request.source_amount * Decimal(total_fee_bps) / 10000, source_fiat) + network_fee_usd,
            total_cost_bps=total_fee_bps,
            total_settlement_seconds=settlement_seconds,
            settlement_type=SettlementType.SAME_DAY,
            stp_enabled=True,
            cost_score=0,
            speed_score=0,
            reliability_score=stable_info.get("liquidity_score", 80),
            compliance_score=85 if stable_info.get("regulatory_status") == "REGULATED_US" else 70,
            overall_score=0,
            compliance_level=ComplianceLevel.FULL_KYC,
            travel_rule_applicable=True,
            sanctions_screening="CHAINALYSIS"
        )
    
    def _score_routes(
        self,
        routes: List[MultiRailRoute],
        request: MultiRailRoutingRequest
    ) -> List[MultiRailRoute]:
        """Score and rank routes"""
        if not routes:
            return routes
        
        # Get min/max for normalization
        costs = [r.total_cost_bps for r in routes]
        min_cost, max_cost = min(costs), max(costs)
        cost_range = max_cost - min_cost if max_cost != min_cost else 1
        
        times = [r.total_settlement_seconds for r in routes]
        min_time, max_time = min(times), max(times)
        time_range = max_time - min_time if max_time != min_time else 1
        
        # Define weights based on preference
        weights = self._get_preference_weights(request.rail_preference)
        
        for route in routes:
            # Cost score (lower is better)
            route.cost_score = (1 - (route.total_cost_bps - min_cost) / cost_range) * 100
            
            # Speed score (lower time is better)
            route.speed_score = (1 - (route.total_settlement_seconds - min_time) / time_range) * 100
            
            # Overall score
            route.overall_score = (
                weights["cost"] * route.cost_score +
                weights["speed"] * route.speed_score +
                weights["reliability"] * route.reliability_score +
                weights["compliance"] * route.compliance_score
            )
        
        routes.sort(key=lambda r: r.overall_score, reverse=True)
        return routes
    
    def _get_preference_weights(self, preference: RailPreference) -> Dict[str, float]:
        """Get scoring weights based on preference"""
        weights = {
            RailPreference.LOWEST_COST: {"cost": 0.50, "speed": 0.15, "reliability": 0.20, "compliance": 0.15},
            RailPreference.FASTEST: {"cost": 0.15, "speed": 0.50, "reliability": 0.20, "compliance": 0.15},
            RailPreference.CBDC_PREFERRED: {"cost": 0.25, "speed": 0.25, "reliability": 0.25, "compliance": 0.25},
            RailPreference.STABLECOIN_PREFERRED: {"cost": 0.35, "speed": 0.30, "reliability": 0.20, "compliance": 0.15},
            RailPreference.FIAT_PREFERRED: {"cost": 0.30, "speed": 0.20, "reliability": 0.30, "compliance": 0.20},
            RailPreference.AUTO: {"cost": 0.30, "speed": 0.25, "reliability": 0.25, "compliance": 0.20},
        }
        return weights.get(preference, weights[RailPreference.AUTO])
    
    def _select_recommended(
        self,
        routes: List[MultiRailRoute],
        preference: RailPreference
    ) -> MultiRailRoute:
        """Select recommended route based on preference"""
        if not routes:
            raise ValueError("No routes available")
        
        # Filter by preference if specific rail requested
        if preference == RailPreference.CBDC_PREFERRED:
            cbdc_routes = [r for r in routes if "CBDC" in r.route_type]
            if cbdc_routes:
                return cbdc_routes[0]
        
        elif preference == RailPreference.STABLECOIN_PREFERRED:
            stable_routes = [r for r in routes if "STABLE" in r.route_type]
            if stable_routes:
                return stable_routes[0]
        
        elif preference == RailPreference.FIAT_PREFERRED:
            fiat_routes = [r for r in routes if "FIAT" in r.route_type]
            if fiat_routes:
                return fiat_routes[0]
        
        # Return highest scored route
        return routes[0]
    
    def _categorize_routes(self, routes: List[MultiRailRoute]) -> Dict[str, List[MultiRailRoute]]:
        """Categorize routes by rail type"""
        return {
            "cbdc": [r for r in routes if "CBDC" in r.route_type],
            "stablecoin": [r for r in routes if "STABLE" in r.route_type],
            "fiat": [r for r in routes if "FIAT" in r.route_type and "CBDC" not in r.route_type],
            "hybrid": [r for r in routes if "HYBRID" in r.route_type]
        }
    
    def _build_comparison(self, routes: List[MultiRailRoute]) -> Dict:
        """Build comparison summary"""
        if not routes:
            return {}
        
        best_rate = min(routes, key=lambda r: r.total_cost_bps)
        fastest = min(routes, key=lambda r: r.total_settlement_seconds)
        lowest_cost = min(routes, key=lambda r: float(r.total_fees_usd))
        
        return {
            "best_rate_route": best_rate.route_id,
            "best_rate_cost_bps": best_rate.total_cost_bps,
            "fastest_route": fastest.route_id,
            "fastest_seconds": fastest.total_settlement_seconds,
            "lowest_cost_route": lowest_cost.route_id,
            "lowest_cost_usd": float(lowest_cost.total_fees_usd),
            "total_routes_evaluated": len(routes)
        }
    
    def _get_cbdc_route_info(self, route: MultiRailRoute) -> Optional[CBDCRouteInfo]:
        """Get CBDC-specific route info"""
        # Extract CBDC code from route
        for leg in route.legs:
            if leg.target_type == CurrencyType.CBDC:
                cbdc_code = leg.target_currency
                cbdc_info = self.digital_currencies["cbdc"].get(cbdc_code, {})
                if cbdc_info:
                    return CBDCRouteInfo(
                        cbdc_code=cbdc_code,
                        cbdc_name=cbdc_info.get("name", cbdc_code),
                        issuing_central_bank=cbdc_info.get("issuer", "Unknown"),
                        is_cross_border="MBRIDGE" in route.route_type,
                        mbridge_route="MBRIDGE" in route.route_type,
                        participating_banks=cbdc_info.get("participating_banks", []),
                        wallet_type=cbdc_info.get("wallet_types", ["TOKEN"])[0],
                        offline_capable=cbdc_info.get("offline_capable", False)
                    )
        return None
    
    def _get_stablecoin_route_info(self, route: MultiRailRoute) -> Optional[StablecoinRouteInfo]:
        """Get stablecoin-specific route info"""
        for leg in route.legs:
            if leg.target_type == CurrencyType.STABLECOIN:
                stable_code = leg.target_currency
                stable_info = self.digital_currencies["stablecoins"].get(stable_code, {})
                if stable_info:
                    return StablecoinRouteInfo(
                        stablecoin_code=stable_code,
                        stablecoin_name=stable_info.get("name", stable_code),
                        issuer=stable_info.get("issuer", "Unknown"),
                        pegged_currency=stable_info.get("pegged_currency", "USD"),
                        network=leg.blockchain_network or BlockchainNetwork.ETHEREUM,
                        network_fee_usd=leg.network_fee_usd or Decimal("0"),
                        on_ramp_provider="Circle" if stable_code == "USDC" else "Exchange",
                        off_ramp_provider="Circle" if stable_code == "USDC" else "Exchange",
                        liquidity_score=stable_info.get("liquidity_score", 50),
                        regulatory_status=stable_info.get("regulatory_status", "UNREGULATED")
                    )
        return None
    
    def _get_compliance_requirements(self, route: MultiRailRoute) -> Dict:
        """Get compliance requirements for a route"""
        return {
            "kyc_level": route.compliance_level.value,
            "travel_rule": route.travel_rule_applicable,
            "sanctions_screening": route.sanctions_screening,
            "reporting_required": True,
            "documentation": ["KYC", "Source of Funds"] if route.compliance_level != ComplianceLevel.BASIC_KYC else ["KYC"]
        }
    
    def _generate_warnings(self, request: MultiRailRoutingRequest, route: MultiRailRoute) -> List[str]:
        """Generate warnings for the route"""
        warnings = []
        
        if route.total_legs > 2:
            warnings.append(f"Route involves {route.total_legs} legs - higher complexity")
        
        if route.travel_rule_applicable:
            warnings.append("Travel Rule compliance required for this route")
        
        if "STABLE" in route.route_type:
            warnings.append("Stablecoin route involves counterparty risk with exchanges")
        
        if route.total_settlement_seconds > 86400:
            warnings.append(f"Settlement may take more than 24 hours")
        
        return warnings
    
    # Helper methods
    def _get_fiat_currency(self, currency_info: Dict) -> Optional[str]:
        """Get fiat currency code"""
        if currency_info["type"] == CurrencyType.FIAT:
            return currency_info["code"]
        elif currency_info["type"] == CurrencyType.CBDC:
            return currency_info["info"].get("fiat_currency")
        elif currency_info["type"] == CurrencyType.STABLECOIN:
            return currency_info["info"].get("pegged_currency")
        return None
    
    def _get_cbdc_for_fiat(self, fiat: str) -> Optional[str]:
        """Get CBDC code for a fiat currency"""
        mapping = {
            "INR": "e-INR",
            "CNY": "e-CNY",
            "HKD": "e-HKD",
            "THB": "e-THB",
            "AED": "e-AED",
            "SGD": "e-SGD"
        }
        return mapping.get(fiat)
    
    def _get_fiat_rate(self, source: str, target: str) -> Optional[Decimal]:
        """Get fiat exchange rate"""
        if source == target:
            return Decimal("1.0")
        
        pair = f"{source}{target}"
        if pair in self._fiat_rates:
            return self._fiat_rates[pair]
        
        inverse = f"{target}{source}"
        if inverse in self._fiat_rates:
            return Decimal("1") / self._fiat_rates[inverse]
        
        # Try cross via USD
        source_usd = self._fiat_rates.get(f"USD{source}") or (Decimal("1") / self._fiat_rates.get(f"{source}USD", Decimal("1")))
        usd_target = self._fiat_rates.get(f"USD{target}") or (Decimal("1") / self._fiat_rates.get(f"{target}USD", Decimal("1")))
        
        if source_usd and usd_target:
            return usd_target / source_usd
        
        return None
    
    def _to_usd(self, amount: Decimal, currency: str) -> Decimal:
        """Convert amount to USD"""
        if currency == "USD":
            return amount
        rate = self._get_fiat_rate(currency, "USD")
        return (amount * rate).quantize(Decimal("0.01")) if rate else amount


# Singleton
_multi_rail_engine: Optional[MultiRailRoutingEngine] = None


def get_multi_rail_engine(config_dir: str = "config") -> MultiRailRoutingEngine:
    """Get or create Multi-Rail Routing Engine singleton"""
    global _multi_rail_engine
    if _multi_rail_engine is None:
        _multi_rail_engine = MultiRailRoutingEngine(config_dir=config_dir)
    return _multi_rail_engine
