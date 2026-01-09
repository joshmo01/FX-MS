import json
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime

class SmartRoutingEngine:
    def __init__(self):
        self.config_path = Path("config")
        self.treasury_rates = self._load_config("treasury_rates.json")
        self.customer_tiers = self._load_config("customer_tiers.json")
        self.fx_providers = self._load_config("fx_providers.json")
    
    def _load_config(self, filename: str) -> dict:
        try:
            with open(self.config_path / filename) as f:
                return json.load(f)
        except FileNotFoundError:
            return {}

    def reload_config(self):
        """Reload all configuration files"""
        self.treasury_rates = self._load_config("treasury_rates.json")
        self.customer_tiers = self._load_config("customer_tiers.json")
        self.fx_providers = self._load_config("fx_providers.json")
        print("SmartRoutingEngine: Configuration reloaded successfully")

    def get_treasury_rate(self, pair: str) -> Optional[dict]:
        return self.treasury_rates.get("rates", {}).get(pair.upper())
    
    def get_customer_tier(self, tier_id: str) -> Optional[dict]:
        return self.customer_tiers.get("tiers", {}).get(tier_id.upper())
    
    def get_provider(self, provider_id: str) -> Optional[dict]:
        return self.fx_providers.get("providers", {}).get(provider_id.upper())
    
    def get_volume_markup(self, amount_usd: float) -> int:
        for tier in self.customer_tiers.get("volume_pricing", []):
            max_usd = tier.get("max_usd") or float("inf")
            if tier["min_usd"] <= amount_usd < max_usd:
                return tier["additional_markup_bps"]
        return 0
    
    def calculate_effective_rate(self, pair: str, side: str, amount: float, 
                                  customer_tier: str = "RETAIL") -> dict:
        rate_info = self.get_treasury_rate(pair)
        if not rate_info:
            return {"error": f"Pair {pair} not found"}
        
        tier_info = self.get_customer_tier(customer_tier)
        if not tier_info:
            tier_info = self.get_customer_tier("RETAIL")
        
        # Base rate
        base_rate = rate_info["bid"] if side.upper() == "SELL" else rate_info["ask"]
        
        # Position adjustment
        position = rate_info.get("position", "NEUTRAL")
        pos_adj = self.treasury_rates.get("position_adjustments", {}).get(position, {})
        adj_key = "sell_adjustment_bps" if side.upper() == "SELL" else "buy_adjustment_bps"
        position_adj_bps = pos_adj.get(adj_key, 0)
        
        # Tier discount
        spread_reduction = tier_info.get("spread_reduction_bps", 0)
        
        # Volume markup
        volume_markup = self.get_volume_markup(amount)
        
        # Total adjustment
        total_adj_bps = position_adj_bps - spread_reduction + volume_markup
        
        # Calculate effective rate
        adjustment_factor = 1 + (total_adj_bps / 10000)
        if side.upper() == "SELL":
            effective_rate = base_rate * adjustment_factor
        else:
            effective_rate = base_rate * adjustment_factor
        
        return {
            "pair": pair,
            "side": side,
            "base_rate": base_rate,
            "mid_rate": rate_info["mid"],
            "effective_rate": round(effective_rate, 6),
            "customer_tier": customer_tier,
            "adjustments": {
                "position_bps": position_adj_bps,
                "tier_discount_bps": -spread_reduction,
                "volume_markup_bps": volume_markup,
                "total_bps": total_adj_bps
            },
            "treasury_position": position
        }
    
    def score_provider(self, provider_id: str, objective: str = "OPTIMUM") -> float:
        provider = self.get_provider(provider_id)
        if not provider:
            return 0.0
        
        weights = self.fx_providers.get("routing_objectives", {}).get(objective, {})
        if not weights:
            weights = {"rate_weight": 0.4, "reliability_weight": 0.25, "speed_weight": 0.2, "stp_weight": 0.15}
        
        # Normalize metrics
        reliability = provider.get("reliability_score", 0.9)
        speed = 1 - (provider.get("avg_latency_ms", 100) / 500)  # Lower is better
        rate_score = 1 - (provider.get("markup_bps", 10) / 50)   # Lower markup is better
        stp_score = 0.9 if provider.get("type") == "INTERNAL" else 0.7
        
        score = (
            weights.get("rate_weight", 0.4) * rate_score +
            weights.get("reliability_weight", 0.25) * reliability +
            weights.get("speed_weight", 0.2) * speed +
            weights.get("stp_weight", 0.15) * stp_score
        )
        
        return round(score, 4)
    
    def recommend_route(self, pair: str, amount: float, side: str = "BUY",
                        customer_tier: str = "RETAIL", objective: str = "OPTIMUM",
                        customer_segment: str = None, **kwargs) -> dict:
        # Get all providers supporting this pair
        all_supporting_providers = []
        for pid, pinfo in self.fx_providers.get("providers", {}).items():
            if pair.upper() in pinfo.get("supported_pairs", []):
                all_supporting_providers.append(pid)

        # Determine currency category
        base_currency = pair[:3] if len(pair) >= 6 else "USD"
        quote_currency = pair[3:] if len(pair) >= 6 else "INR"
        currency_category = self._get_currency_category(quote_currency)

        # Build provider context for rules engine
        from app.services.rules_engine import ProviderContext, RulesEngine, RuleType

        provider_context = ProviderContext(
            currency_pair=pair.upper(),
            base_currency=base_currency,
            quote_currency=quote_currency,
            currency_category=currency_category,
            amount=amount,
            direction=side,
            customer_tier=customer_tier,
            customer_segment=customer_segment,
            routing_objective=objective,
            available_providers=all_supporting_providers,
            custom_attributes=kwargs,
            timestamp=datetime.utcnow()
        )

        # Evaluate provider selection rules
        engine = RulesEngine()
        rule_result = engine.evaluate(RuleType.PROVIDER_SELECTION, provider_context)

        # Apply rule-based provider filtering and objective override
        if rule_result.matched:
            provider_actions = rule_result.actions.provider_selection

            # Override routing objective if specified
            if provider_actions.routing_objective_override:
                objective = provider_actions.routing_objective_override

            # Filter providers based on preferred/excluded lists
            if provider_actions.preferred_providers:
                # Use only preferred providers that are available
                eligible_provider_ids = [
                    p for p in provider_actions.preferred_providers
                    if p in all_supporting_providers
                ]
                if not eligible_provider_ids:
                    # Fallback if no preferred providers available
                    eligible_provider_ids = all_supporting_providers
            else:
                eligible_provider_ids = all_supporting_providers

            # Apply exclusions
            if provider_actions.excluded_providers:
                eligible_provider_ids = [
                    p for p in eligible_provider_ids
                    if p not in provider_actions.excluded_providers
                ]

            # Handle force_provider
            if provider_actions.force_provider and eligible_provider_ids:
                eligible_provider_ids = [eligible_provider_ids[0]]

            rule_applied_id = rule_result.winning_rule.rule_id
            rule_applied_name = rule_result.winning_rule.rule_name
        else:
            # No rule matched - use all supporting providers
            eligible_provider_ids = all_supporting_providers
            rule_applied_id = None
            rule_applied_name = None

        # Score and build provider details
        eligible_providers = []
        for pid in eligible_provider_ids:
            pinfo = self.fx_providers.get("providers", {}).get(pid)
            if pinfo:
                score = self.score_provider(pid, objective)
                eligible_providers.append({
                    "provider_id": pid,
                    "name": pinfo["name"],
                    "type": pinfo["type"],
                    "score": score,
                    "markup_bps": pinfo.get("markup_bps", 0),
                    "latency_ms": pinfo.get("avg_latency_ms", 100),
                    "reliability": pinfo.get("reliability_score", 0.9)
                })

        # Sort by score
        eligible_providers.sort(key=lambda x: x["score"], reverse=True)

        # Get effective rate
        rate_info = self.calculate_effective_rate(pair, side, amount, customer_tier)

        # Check STP eligibility
        tier_info = self.get_customer_tier(customer_tier)
        stp_threshold = tier_info.get("stp_threshold_usd", 50000) if tier_info else 50000
        stp_eligible = amount <= stp_threshold

        return {
            "pair": pair,
            "amount": amount,
            "side": side,
            "customer_tier": customer_tier,
            "objective": objective,
            "rate_info": rate_info,
            "stp_eligible": stp_eligible,
            "recommended_provider": eligible_providers[0] if eligible_providers else None,
            "alternative_providers": eligible_providers[1:3] if len(eligible_providers) > 1 else [],
            "all_providers": eligible_providers,
            "rule_applied_id": rule_applied_id,
            "rule_applied_name": rule_applied_name,
            "timestamp": datetime.utcnow().isoformat()
        }

    def _get_currency_category(self, currency: str) -> str:
        """Helper to determine currency category"""
        g10 = ["USD", "EUR", "JPY", "GBP", "CHF", "AUD", "NZD", "CAD", "SEK", "NOK"]
        minor = ["SGD", "HKD", "DKK", "PLN", "CZK", "HUF"]
        exotic = ["TRY", "ZAR", "MXN", "BRL", "ARS", "RUB"]

        if currency in g10:
            return "G10"
        elif currency in minor:
            return "MINOR"
        elif currency in exotic:
            return "EXOTIC"
        else:
            return "RESTRICTED"


# Singleton instance
routing_engine = SmartRoutingEngine()
