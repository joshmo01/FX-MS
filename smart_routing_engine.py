"""
FX Smart Routing Engine

Intelligent routing engine that evaluates multiple factors to determine
the optimal route for FX transactions.

Factors considered:
1. Currency Pair - Direct vs Cross rates
2. Treasury Rates - Internal rates and position management
3. FX Providers - Multiple provider comparison
4. Triangulation - Cross-currency optimization
5. Customer Details - Tier-based pricing and preferences
"""
import json
import uuid
import logging
from datetime import datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional, List, Dict, Tuple
from pathlib import Path
import time

from app.models.routing_models import (
    SmartRoutingRequest,
    SmartRoutingResponse,
    CustomerContext,
    CustomerTier,
    RoutingObjective,
    ProviderType,
    RouteType,
    TreasuryPosition,
    Direction,
    ProviderRate,
    RouteLeg,
    RouteOption,
    TreasuryInfo,
    TriangulationInfo,
)

logger = logging.getLogger(__name__)


class SmartRoutingEngine:
    """
    FX Smart Routing Engine
    
    Evaluates all available routes and providers to recommend
    the optimal execution path based on configurable objectives.
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self._load_configurations()
        
        # Mock base rates for demonstration
        self._market_rates = {
            "USDINR": Decimal("84.50"),
            "EURINR": Decimal("89.20"),
            "GBPINR": Decimal("106.50"),
            "EURUSD": Decimal("1.0557"),
            "GBPUSD": Decimal("1.2604"),
            "USDJPY": Decimal("154.80"),
            "AEDINR": Decimal("23.01"),
            "SGDINR": Decimal("62.85"),
        }
    
    def _load_configurations(self):
        """Load all configuration files"""
        # Routing config
        with open(self.config_dir / "routing_config.json") as f:
            self.routing_config = json.load(f)
        
        # Providers
        with open(self.config_dir / "fx_providers.json") as f:
            self.providers_config = json.load(f)
        
        # Customer tiers
        with open(self.config_dir / "customer_tiers.json") as f:
            self.customer_config = json.load(f)
        
        # Treasury rates
        with open(self.config_dir / "treasury_rates.json") as f:
            self.treasury_config = json.load(f)
    
    async def get_smart_route(
        self, 
        request: SmartRoutingRequest
    ) -> SmartRoutingResponse:
        """
        Main entry point for smart routing recommendation.
        
        Args:
            request: Smart routing request with all parameters
            
        Returns:
            SmartRoutingResponse with recommended and alternative routes
        """
        start_time = time.time()
        request_id = f"RT-{uuid.uuid4().hex[:12].upper()}"
        
        # 1. Resolve customer context
        customer = request.customer or CustomerContext(
            customer_id="GUEST",
            tier=CustomerTier.RETAIL
        )
        tier_config = self.customer_config["customer_tiers"][customer.tier.value]
        
        # 2. Get objective weights
        weights = self.routing_config["routing_objectives"][request.objective.value]["priority_weights"]
        
        # 3. Get treasury info
        treasury_info = self._get_treasury_info(
            request.source_currency,
            request.target_currency,
            request.amount,
            request.direction
        )
        
        # 4. Evaluate triangulation
        triangulation_info = self._evaluate_triangulation(
            request.source_currency,
            request.target_currency,
            request.amount
        )
        
        # 5. Get rates from all eligible providers
        provider_rates = await self._get_provider_rates(
            request.source_currency,
            request.target_currency,
            request.amount,
            customer,
            tier_config
        )
        
        # 6. Build all possible routes
        routes = self._build_routes(
            request,
            provider_rates,
            customer,
            tier_config,
            treasury_info,
            triangulation_info
        )
        
        # 7. Score and rank routes
        scored_routes = self._score_routes(routes, weights, request)
        scored_routes.sort(key=lambda r: r.overall_score, reverse=True)
        
        # 8. Determine STP eligibility
        stp_eligible, requires_approval, approval_reason = self._check_stp_eligibility(
            request,
            scored_routes[0] if scored_routes else None,
            tier_config
        )
        
        # 9. Build response
        response = SmartRoutingResponse(
            request_id=request_id,
            timestamp=datetime.utcnow(),
            source_currency=request.source_currency,
            target_currency=request.target_currency,
            amount=request.amount,
            direction=request.direction,
            objective=request.objective,
            customer_tier=customer.tier,
            customer_discounts_applied=self._get_customer_discounts(customer, tier_config),
            treasury=treasury_info,
            triangulation=triangulation_info,
            recommended_route=scored_routes[0] if scored_routes else None,
            alternative_routes=scored_routes[1:5] if len(scored_routes) > 1 else [],
            best_rate=min(r.customer_rate for r in scored_routes) if scored_routes else Decimal("0"),
            best_rate_provider=min(scored_routes, key=lambda r: r.customer_rate).provider_name if scored_routes else "",
            fastest_settlement_hours=min(r.settlement_hours for r in scored_routes) if scored_routes else 0,
            fastest_provider=min(scored_routes, key=lambda r: r.settlement_hours).provider_name if scored_routes else "",
            stp_eligible=stp_eligible,
            requires_approval=requires_approval,
            approval_reason=approval_reason,
            warnings=self._generate_warnings(request, scored_routes, treasury_info)
        )
        
        execution_time = (time.time() - start_time) * 1000
        logger.info(f"Smart routing completed in {execution_time:.2f}ms, {len(scored_routes)} routes evaluated")
        
        return response
    
    def _get_treasury_info(
        self,
        source: str,
        target: str,
        amount: Decimal,
        direction: Direction
    ) -> TreasuryInfo:
        """Get treasury position and internal rate info"""
        pair = f"{source}{target}"
        treasury_rates = self.treasury_config.get("treasury_rates", {})
        
        if pair not in treasury_rates:
            # Try inverse
            inverse_pair = f"{target}{source}"
            if inverse_pair in treasury_rates:
                rate_info = treasury_rates[inverse_pair]
                return TreasuryInfo(
                    treasury_rate=Decimal("1") / Decimal(str(rate_info["mid"])),
                    position=TreasuryPosition(rate_info["position"]),
                    exposure_pct=(rate_info["current_exposure_usd"] / rate_info["max_exposure_usd"]) * 100,
                    position_adjustment_bps=self._get_position_adjustment(rate_info["position"], direction),
                    can_execute_internally=True
                )
            return TreasuryInfo(can_execute_internally=False)
        
        rate_info = treasury_rates[pair]
        exposure_pct = (rate_info["current_exposure_usd"] / rate_info["max_exposure_usd"]) * 100
        
        return TreasuryInfo(
            treasury_rate=Decimal(str(rate_info["mid"])),
            position=TreasuryPosition(rate_info["position"]),
            exposure_pct=exposure_pct,
            position_adjustment_bps=self._get_position_adjustment(rate_info["position"], direction),
            can_execute_internally=exposure_pct < 90
        )
    
    def _get_position_adjustment(self, position: str, direction: Direction) -> int:
        """Get rate adjustment based on treasury position"""
        rules = self.treasury_config["treasury_rules"]["position_adjustment"]
        pos_rules = rules.get(position, rules["NEUTRAL"])
        
        if direction == Direction.SELL:
            return pos_rules["sell_rate_adjustment_bps"]
        return pos_rules["buy_rate_adjustment_bps"]
    
    def _evaluate_triangulation(
        self,
        source: str,
        target: str,
        amount: Decimal
    ) -> TriangulationInfo:
        """Evaluate if triangulation provides better rate"""
        pair = f"{source}{target}"
        
        # Get direct rate
        direct_rate = self._get_market_rate(source, target)
        if direct_rate is None:
            # No direct rate, triangulation required
            pass
        
        # Try triangulation via bridge currencies
        bridge_currencies = self.routing_config["triangulation"]["bridge_currencies"]
        best_triangulated = None
        best_bridge = None
        
        for bridge in bridge_currencies:
            if bridge == source or bridge == target:
                continue
            
            leg1_rate = self._get_market_rate(source, bridge)
            leg2_rate = self._get_market_rate(bridge, target)
            
            if leg1_rate and leg2_rate:
                triangulated_rate = leg1_rate * leg2_rate
                
                if best_triangulated is None or triangulated_rate < best_triangulated:
                    best_triangulated = triangulated_rate
                    best_bridge = bridge
        
        if direct_rate and best_triangulated:
            savings_bps = int((direct_rate - best_triangulated) / direct_rate * 10000)
            min_savings = self.routing_config["triangulation"]["min_savings_bps"]
            
            return TriangulationInfo(
                is_triangulated=False,
                bridge_currency=best_bridge,
                direct_rate=direct_rate,
                triangulated_rate=best_triangulated,
                savings_bps=savings_bps,
                recommended=savings_bps >= min_savings
            )
        
        if best_triangulated and not direct_rate:
            return TriangulationInfo(
                is_triangulated=True,
                bridge_currency=best_bridge,
                direct_rate=None,
                triangulated_rate=best_triangulated,
                savings_bps=None,
                recommended=True
            )
        
        return TriangulationInfo(
            is_triangulated=False,
            recommended=False
        )
    
    def _get_market_rate(self, source: str, target: str) -> Optional[Decimal]:
        """Get market rate for a currency pair"""
        pair = f"{source}{target}"
        if pair in self._market_rates:
            return self._market_rates[pair]
        
        inverse = f"{target}{source}"
        if inverse in self._market_rates:
            return Decimal("1") / self._market_rates[inverse]
        
        return None
    
    async def _get_provider_rates(
        self,
        source: str,
        target: str,
        amount: Decimal,
        customer: CustomerContext,
        tier_config: Dict
    ) -> List[ProviderRate]:
        """Get rates from all eligible providers"""
        rates = []
        pair = f"{source}{target}"
        allowed_providers = tier_config.get("providers_allowed", [])
        blocked_providers = customer.blocked_providers or []
        
        for provider_id, provider in self.providers_config["providers"].items():
            # Check if provider is active and allowed
            if not provider["is_active"]:
                continue
            
            if provider_id in blocked_providers:
                continue
            
            if allowed_providers and provider_id not in allowed_providers:
                continue
            
            # Check if provider supports this pair
            supported = provider["supported_pairs"]
            if supported != ["*"] and pair not in supported:
                # Check inverse
                inverse = f"{target}{source}"
                if inverse not in supported:
                    continue
            
            # Check amount limits
            amount_usd = float(amount)  # Simplified - should convert to USD
            min_amount = provider.get("min_amount_usd", 0)
            max_amount = provider.get("max_amount_usd", float("inf"))
            
            if amount_usd < min_amount or amount_usd > max_amount:
                continue
            
            # Get rate (mock - would call provider API in production)
            base_rate = self._get_market_rate(source, target)
            if not base_rate:
                continue
            
            # Apply provider markup
            markup_bps = provider.get("markup_bps", 0)
            spread_bps = 25  # Default spread
            
            # Calculate bid/ask
            spread_pct = Decimal(spread_bps) / Decimal("10000")
            markup_pct = Decimal(markup_bps) / Decimal("10000")
            
            half_spread = base_rate * spread_pct / 2
            bid_rate = base_rate - half_spread
            ask_rate = base_rate + half_spread + (base_rate * markup_pct)
            
            now = datetime.utcnow()
            
            rates.append(ProviderRate(
                provider_id=provider_id,
                provider_name=provider["name"],
                provider_type=ProviderType(provider["type"]),
                bid_rate=bid_rate.quantize(Decimal("0.0001")),
                ask_rate=ask_rate.quantize(Decimal("0.0001")),
                mid_rate=base_rate.quantize(Decimal("0.0001")),
                spread_bps=spread_bps,
                markup_bps=markup_bps,
                final_rate=ask_rate.quantize(Decimal("0.0001")),
                settlement_hours=provider.get("settlement_hours", 24),
                stp_enabled=provider["capabilities"].get("stp_enabled", False),
                reliability_score=provider.get("reliability_score", 0.9),
                timestamp=now,
                valid_until=now + timedelta(seconds=30)
            ))
        
        return rates
    
    def _build_routes(
        self,
        request: SmartRoutingRequest,
        provider_rates: List[ProviderRate],
        customer: CustomerContext,
        tier_config: Dict,
        treasury_info: TreasuryInfo,
        triangulation_info: TriangulationInfo
    ) -> List[RouteOption]:
        """Build all possible route options"""
        routes = []
        
        # Customer discounts
        markup_discount_pct = tier_config.get("markup_discount_pct", 0) / 100
        spread_reduction_bps = tier_config.get("spread_reduction_bps", 0)
        volume_adjustment = self._get_volume_adjustment(request.amount)
        tenure_discount = self._get_tenure_discount(customer.tenure_years or 0)
        
        for rate in provider_rates:
            # Apply customer discounts to rate
            adjusted_markup = int(rate.markup_bps * (1 - markup_discount_pct))
            adjusted_spread = max(0, rate.spread_bps - spread_reduction_bps)
            total_adjustment = adjusted_markup + adjusted_spread + volume_adjustment - tenure_discount
            
            # Calculate customer rate
            adjustment_pct = Decimal(total_adjustment) / Decimal("10000")
            
            if request.direction == Direction.SELL:
                customer_rate = rate.bid_rate * (1 - adjustment_pct / 2)
            else:
                customer_rate = rate.ask_rate * (1 + adjustment_pct / 2)
            
            target_amount = request.amount * customer_rate
            
            route = RouteOption(
                route_id=f"R-{uuid.uuid4().hex[:8].upper()}",
                route_type=RouteType.DIRECT,
                provider_id=rate.provider_id,
                provider_name=rate.provider_name,
                legs=[RouteLeg(
                    leg_number=1,
                    source_currency=request.source_currency,
                    target_currency=request.target_currency,
                    provider_id=rate.provider_id,
                    rate=customer_rate,
                    amount_in=request.amount,
                    amount_out=target_amount
                )],
                effective_rate=rate.mid_rate,
                total_spread_bps=adjusted_spread,
                total_markup_bps=adjusted_markup,
                customer_rate=customer_rate.quantize(Decimal("0.0001")),
                source_amount=request.amount,
                target_amount=target_amount.quantize(Decimal("0.01")),
                rate_score=0,  # Will be calculated in scoring
                reliability_score=rate.reliability_score * 100,
                speed_score=0,  # Will be calculated
                stp_score=100 if rate.stp_enabled else 0,
                overall_score=0,  # Will be calculated
                settlement_hours=rate.settlement_hours,
                stp_enabled=rate.stp_enabled,
                requires_manual_review=not rate.stp_enabled or float(request.amount) > tier_config.get("stp_threshold_usd", 0),
                cost_breakdown={
                    "base_spread_bps": Decimal(str(rate.spread_bps)),
                    "provider_markup_bps": Decimal(str(rate.markup_bps)),
                    "customer_discount_bps": Decimal(str(int(rate.markup_bps * markup_discount_pct))),
                    "spread_reduction_bps": Decimal(str(spread_reduction_bps)),
                    "volume_adjustment_bps": Decimal(str(volume_adjustment)),
                    "tenure_discount_bps": Decimal(str(tenure_discount)),
                    "final_cost_bps": Decimal(str(total_adjustment))
                }
            )
            routes.append(route)
        
        return routes
    
    def _score_routes(
        self,
        routes: List[RouteOption],
        weights: Dict[str, float],
        request: SmartRoutingRequest
    ) -> List[RouteOption]:
        """Score routes based on objective weights"""
        if not routes:
            return routes
        
        # Find min/max for normalization
        rates = [float(r.customer_rate) for r in routes]
        min_rate, max_rate = min(rates), max(rates)
        rate_range = max_rate - min_rate if max_rate != min_rate else 1
        
        settlements = [r.settlement_hours for r in routes]
        min_settle, max_settle = min(settlements), max(settlements)
        settle_range = max_settle - min_settle if max_settle != min_settle else 1
        
        for route in routes:
            # Rate score (lower is better, invert for scoring)
            if request.direction == Direction.SELL:
                # For selling, higher rate is better
                route.rate_score = ((float(route.customer_rate) - min_rate) / rate_range) * 100
            else:
                # For buying, lower rate is better
                route.rate_score = (1 - (float(route.customer_rate) - min_rate) / rate_range) * 100
            
            # Speed score (lower settlement is better)
            route.speed_score = (1 - (route.settlement_hours - min_settle) / settle_range) * 100
            
            # Calculate weighted overall score
            route.overall_score = (
                weights.get("rate", 0.4) * route.rate_score +
                weights.get("provider_reliability", 0.25) * route.reliability_score +
                weights.get("settlement_speed", 0.2) * route.speed_score +
                weights.get("stp_capability", 0.15) * route.stp_score
            )
        
        return routes
    
    def _get_volume_adjustment(self, amount: Decimal) -> int:
        """Get volume-based pricing adjustment"""
        volume_tiers = self.customer_config["volume_based_pricing"]["tiers"]
        amount_float = float(amount)
        
        for tier in volume_tiers:
            max_val = tier["max_usd"] or float("inf")
            if tier["min_usd"] <= amount_float < max_val:
                return tier["additional_markup_bps"]
        
        return 0
    
    def _get_tenure_discount(self, tenure_years: int) -> int:
        """Get tenure-based discount"""
        tenure_discounts = self.customer_config["relationship_pricing"]["tenure_discount"]
        
        if tenure_years >= 10:
            return tenure_discounts["10_years"]
        elif tenure_years >= 5:
            return tenure_discounts["5_years"]
        elif tenure_years >= 2:
            return tenure_discounts["2_years"]
        elif tenure_years >= 1:
            return tenure_discounts["1_year"]
        return 0
    
    def _get_customer_discounts(
        self,
        customer: CustomerContext,
        tier_config: Dict
    ) -> Dict:
        """Get summary of customer discounts applied"""
        return {
            "tier": customer.tier.value,
            "markup_discount_pct": tier_config.get("markup_discount_pct", 0),
            "spread_reduction_bps": tier_config.get("spread_reduction_bps", 0),
            "volume_adjustment_bps": self._get_volume_adjustment(Decimal("0")),
            "tenure_discount_bps": self._get_tenure_discount(customer.tenure_years or 0)
        }
    
    def _check_stp_eligibility(
        self,
        request: SmartRoutingRequest,
        route: Optional[RouteOption],
        tier_config: Dict
    ) -> Tuple[bool, bool, Optional[str]]:
        """Check if transaction is STP eligible"""
        if not route:
            return False, True, "No valid route found"
        
        if not route.stp_enabled:
            return False, True, f"Provider {route.provider_name} does not support STP"
        
        stp_threshold = tier_config.get("stp_threshold_usd", 0)
        if float(request.amount) > stp_threshold:
            return False, True, f"Amount exceeds STP threshold of USD {stp_threshold:,.0f}"
        
        if request.require_stp and not route.stp_enabled:
            return False, True, "STP required but not available for this route"
        
        return True, False, None
    
    def _generate_warnings(
        self,
        request: SmartRoutingRequest,
        routes: List[RouteOption],
        treasury_info: TreasuryInfo
    ) -> List[str]:
        """Generate warnings for the routing decision"""
        warnings = []
        
        if treasury_info.exposure_pct and treasury_info.exposure_pct > 70:
            warnings.append(f"Treasury exposure at {treasury_info.exposure_pct:.1f}% - approaching limit")
        
        if len(routes) < 2:
            warnings.append("Limited provider options available for this currency pair")
        
        if routes and routes[0].settlement_hours > 24:
            warnings.append(f"Settlement may take up to {routes[0].settlement_hours} hours")
        
        return warnings


# Singleton instance
_routing_engine: Optional[SmartRoutingEngine] = None


def get_routing_engine(config_dir: str = "config") -> SmartRoutingEngine:
    """Get or create Smart Routing Engine singleton"""
    global _routing_engine
    if _routing_engine is None:
        _routing_engine = SmartRoutingEngine(config_dir=config_dir)
    return _routing_engine
