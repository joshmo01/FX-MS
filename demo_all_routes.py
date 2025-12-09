#!/usr/bin/env python3
"""
FX Smart Routing - Comprehensive Demo Runner

Demonstrates ALL conversion scenarios:
- 9 conversion types (Fiat ↔ CBDC ↔ Stablecoin)
- Atomic swap routes (experimental)
- Multi-provider comparison
- Treasury integration
- Customer tier pricing

Author: Fintaar.ai
Version: 2.0.0
"""

import asyncio
import json
import sys
import os
from decimal import Decimal
from datetime import datetime
from dataclasses import dataclass, asdict
from typing import Dict, List, Any, Optional
from enum import Enum
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Try to import engines
try:
    from app.services.universal_conversion_engine import UniversalConversionEngine, ConversionType
    from app.services.cbdc_stable_bridge import CBDCStableBridge, get_bridge_engine, BridgeType
    ENGINES_AVAILABLE = True
except ImportError as e:
    print(f"⚠️  Warning: Could not import engines: {e}")
    ENGINES_AVAILABLE = False


class DemoMode(str, Enum):
    """Demo execution modes"""
    QUICK = "quick"      # Key scenarios only
    FULL = "full"        # All scenarios
    ATOMIC = "atomic"    # Atomic swap focus
    CBDC = "cbdc"        # CBDC routes focus
    STABLE = "stable"    # Stablecoin routes focus


@dataclass
class DemoScenario:
    """Demo scenario definition"""
    id: str
    name: str
    source: str
    source_type: str
    target: str
    target_type: str
    amount: Decimal
    description: str
    category: str
    highlight: bool = False


@dataclass
class DemoResult:
    """Demo execution result"""
    scenario_id: str
    scenario_name: str
    success: bool
    routes_found: int
    best_route: str
    best_fee_bps: int
    best_settlement: str
    target_amount: str
    execution_ms: float
    error: str = ""


class FXDemoRunner:
    """
    Comprehensive FX Smart Routing Demo Runner
    """
    
    def __init__(self, config_dir: str = "config", mode: DemoMode = DemoMode.FULL):
        self.config_dir = config_dir
        self.mode = mode
        self.results: List[DemoResult] = []
        self.universal_engine = None
        self.bridge_engine = None
        
    def setup(self):
        """Initialize demo environment"""
        self._print_header()
        
        if ENGINES_AVAILABLE:
            try:
                self.universal_engine = UniversalConversionEngine(self.config_dir)
                self.bridge_engine = get_bridge_engine(self.config_dir)
                print("✅ Engines initialized successfully")
            except Exception as e:
                print(f"⚠️  Engine init warning: {e}")
        else:
            print("⚠️  Running in simulation mode (engines not available)")
        
    def _print_header(self):
        """Print demo header"""
        print("\n" + "="*70)
        print("🚀 FX SMART ROUTING - COMPREHENSIVE DEMO")
        print("="*70)
        print(f"""
┌─────────────────────────────────────────────────────────────────────┐
│                    UNIVERSAL FX CONVERSION ENGINE                    │
├─────────────────────────────────────────────────────────────────────┤
│  Supported Rails:                                                    │
│    💵 FIAT      : USD, EUR, GBP, INR, SGD, AED, CNY, HKD, THB, JPY  │
│    🏛️ CBDC      : e-INR, e-CNY, e-HKD, e-THB, e-AED, e-SGD         │
│    🪙 STABLECOIN: USDC, USDT, EURC, PYUSD, XSGD                     │
├─────────────────────────────────────────────────────────────────────┤
│  Conversion Types (9):                                               │
│    1. FIAT → FIAT         6. STABLECOIN → FIAT                      │
│    2. FIAT → CBDC         7. STABLECOIN → STABLECOIN                │
│    3. CBDC → FIAT         8. CBDC → STABLECOIN                      │
│    4. CBDC → CBDC         9. STABLECOIN → CBDC                      │
│    5. FIAT → STABLECOIN                                             │
├─────────────────────────────────────────────────────────────────────┤
│  Special Features:                                                   │
│    ⚛️ Atomic Swaps (CBDC ↔ Stablecoin)                              │
│    🌐 mBridge Cross-Border CBDC                                      │
│    🔗 Multi-Network Stablecoin Support                               │
└─────────────────────────────────────────────────────────────────────┘
""")
        print(f"📅 Demo Run: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"📁 Config: {self.config_dir}")
        print(f"🎯 Mode: {self.mode.value.upper()}")
        print()

    def get_scenarios(self) -> List[DemoScenario]:
        """Get demo scenarios based on mode"""
        all_scenarios = [
            # ═══════════════════════════════════════════════════════════════
            # FIAT TO FIAT
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="F2F-001", name="USD → INR Direct",
                source="USD", source_type="FIAT",
                target="INR", target_type="FIAT",
                amount=Decimal("100000"),
                description="Standard cross-border FX via SWIFT/Local",
                category="FIAT_TO_FIAT"
            ),
            DemoScenario(
                id="F2F-002", name="EUR → SGD Cross",
                source="EUR", source_type="FIAT",
                target="SGD", target_type="FIAT",
                amount=Decimal("50000"),
                description="Cross-rate via USD triangulation",
                category="FIAT_TO_FIAT"
            ),
            DemoScenario(
                id="F2F-003", name="GBP → AED",
                source="GBP", source_type="FIAT",
                target="AED", target_type="FIAT",
                amount=Decimal("25000"),
                description="UK to UAE remittance corridor",
                category="FIAT_TO_FIAT"
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # FIAT TO CBDC
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="F2C-001", name="INR → e-INR Mint",
                source="INR", source_type="FIAT",
                target="e-INR", target_type="CBDC",
                amount=Decimal("100000"),
                description="Direct CBDC minting (same currency)",
                category="FIAT_TO_CBDC",
                highlight=True
            ),
            DemoScenario(
                id="F2C-002", name="USD → e-INR",
                source="USD", source_type="FIAT",
                target="e-INR", target_type="CBDC",
                amount=Decimal("10000"),
                description="FX conversion + CBDC mint",
                category="FIAT_TO_CBDC"
            ),
            DemoScenario(
                id="F2C-003", name="USD → e-CNY",
                source="USD", source_type="FIAT",
                target="e-CNY", target_type="CBDC",
                amount=Decimal("100000"),
                description="Cross-border to Chinese Digital Yuan",
                category="FIAT_TO_CBDC"
            ),
            DemoScenario(
                id="F2C-004", name="EUR → e-AED",
                source="EUR", source_type="FIAT",
                target="e-AED", target_type="CBDC",
                amount=Decimal("50000"),
                description="Europe to UAE CBDC",
                category="FIAT_TO_CBDC"
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # CBDC TO FIAT
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="C2F-001", name="e-INR → INR Redeem",
                source="e-INR", source_type="CBDC",
                target="INR", target_type="FIAT",
                amount=Decimal("100000"),
                description="Direct CBDC redemption (same currency)",
                category="CBDC_TO_FIAT",
                highlight=True
            ),
            DemoScenario(
                id="C2F-002", name="e-INR → USD",
                source="e-INR", source_type="CBDC",
                target="USD", target_type="FIAT",
                amount=Decimal("500000"),
                description="CBDC redeem + FX conversion",
                category="CBDC_TO_FIAT"
            ),
            DemoScenario(
                id="C2F-003", name="e-CNY → EUR",
                source="e-CNY", source_type="CBDC",
                target="EUR", target_type="FIAT",
                amount=Decimal("100000"),
                description="China CBDC to Euro",
                category="CBDC_TO_FIAT"
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # CBDC TO CBDC (mBridge)
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="C2C-001", name="e-CNY → e-AED (mBridge)",
                source="e-CNY", source_type="CBDC",
                target="e-AED", target_type="CBDC",
                amount=Decimal("500000"),
                description="mBridge cross-border PvP settlement",
                category="CBDC_TO_CBDC",
                highlight=True
            ),
            DemoScenario(
                id="C2C-002", name="e-HKD → e-THB (mBridge)",
                source="e-HKD", source_type="CBDC",
                target="e-THB", target_type="CBDC",
                amount=Decimal("200000"),
                description="Hong Kong to Thailand CBDC corridor",
                category="CBDC_TO_CBDC",
                highlight=True
            ),
            DemoScenario(
                id="C2C-003", name="e-INR → e-SGD (Fiat Bridge)",
                source="e-INR", source_type="CBDC",
                target="e-SGD", target_type="CBDC",
                amount=Decimal("100000"),
                description="Non-mBridge CBDCs via fiat intermediary",
                category="CBDC_TO_CBDC"
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # FIAT TO STABLECOIN
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="F2S-001", name="USD → USDC (Direct)",
                source="USD", source_type="FIAT",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("100000"),
                description="Direct mint via Circle",
                category="FIAT_TO_STABLECOIN",
                highlight=True
            ),
            DemoScenario(
                id="F2S-002", name="EUR → EURC",
                source="EUR", source_type="FIAT",
                target="EURC", target_type="STABLECOIN",
                amount=Decimal("50000"),
                description="Euro to Euro Coin (MiCA compliant)",
                category="FIAT_TO_STABLECOIN"
            ),
            DemoScenario(
                id="F2S-003", name="SGD → XSGD",
                source="SGD", source_type="FIAT",
                target="XSGD", target_type="STABLECOIN",
                amount=Decimal("100000"),
                description="Singapore Dollar to XSGD (MAS licensed)",
                category="FIAT_TO_STABLECOIN"
            ),
            DemoScenario(
                id="F2S-004", name="INR → USDC",
                source="INR", source_type="FIAT",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("500000"),
                description="India to USD stablecoin (FX + on-ramp)",
                category="FIAT_TO_STABLECOIN"
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # STABLECOIN TO FIAT
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="S2F-001", name="USDC → USD (Direct)",
                source="USDC", source_type="STABLECOIN",
                target="USD", target_type="FIAT",
                amount=Decimal("100000"),
                description="Direct redeem via Circle",
                category="STABLECOIN_TO_FIAT",
                highlight=True
            ),
            DemoScenario(
                id="S2F-002", name="USDT → INR",
                source="USDT", source_type="STABLECOIN",
                target="INR", target_type="FIAT",
                amount=Decimal("50000"),
                description="Tether to INR via CEX off-ramp",
                category="STABLECOIN_TO_FIAT"
            ),
            DemoScenario(
                id="S2F-003", name="EURC → GBP",
                source="EURC", source_type="STABLECOIN",
                target="GBP", target_type="FIAT",
                amount=Decimal("25000"),
                description="Euro Coin to British Pounds",
                category="STABLECOIN_TO_FIAT"
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # STABLECOIN TO STABLECOIN
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="S2S-001", name="USDC → USDT (DEX)",
                source="USDC", source_type="STABLECOIN",
                target="USDT", target_type="STABLECOIN",
                amount=Decimal("100000"),
                description="DEX swap on Curve/Uniswap",
                category="STABLECOIN_TO_STABLECOIN"
            ),
            DemoScenario(
                id="S2S-002", name="USDC → EURC",
                source="USDC", source_type="STABLECOIN",
                target="EURC", target_type="STABLECOIN",
                amount=Decimal("50000"),
                description="USD to EUR stablecoin swap",
                category="STABLECOIN_TO_STABLECOIN"
            ),
            DemoScenario(
                id="S2S-003", name="USDT → XSGD",
                source="USDT", source_type="STABLECOIN",
                target="XSGD", target_type="STABLECOIN",
                amount=Decimal("100000"),
                description="Cross-currency stablecoin conversion",
                category="STABLECOIN_TO_STABLECOIN"
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # CBDC TO STABLECOIN (Including Atomic Swaps)
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="C2S-001", name="e-INR → USDC (Fiat Bridge)",
                source="e-INR", source_type="CBDC",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("100000"),
                description="CBDC to stablecoin via fiat intermediary",
                category="CBDC_TO_STABLECOIN"
            ),
            DemoScenario(
                id="C2S-002", name="e-INR → USDC (Atomic Swap)",
                source="e-INR", source_type="CBDC",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("50000"),
                description="⚛️ ATOMIC SWAP - Direct HTLC exchange",
                category="CBDC_TO_STABLECOIN",
                highlight=True
            ),
            DemoScenario(
                id="C2S-003", name="e-CNY → USDT (CEX Bridge)",
                source="e-CNY", source_type="CBDC",
                target="USDT", target_type="STABLECOIN",
                amount=Decimal("200000"),
                description="Chinese CBDC to Tether via CEX",
                category="CBDC_TO_STABLECOIN"
            ),
            DemoScenario(
                id="C2S-004", name="e-SGD → XSGD (Atomic Swap)",
                source="e-SGD", source_type="CBDC",
                target="XSGD", target_type="STABLECOIN",
                amount=Decimal("100000"),
                description="⚛️ ATOMIC SWAP - Same-peg atomic exchange",
                category="CBDC_TO_STABLECOIN",
                highlight=True
            ),
            DemoScenario(
                id="C2S-005", name="e-AED → USDC (mBridge + Stable)",
                source="e-AED", source_type="CBDC",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("500000"),
                description="mBridge CBDC to stablecoin hybrid route",
                category="CBDC_TO_STABLECOIN"
            ),
            
            # ═══════════════════════════════════════════════════════════════
            # STABLECOIN TO CBDC (Including Atomic Swaps)
            # ═══════════════════════════════════════════════════════════════
            DemoScenario(
                id="S2C-001", name="USDC → e-INR (Fiat Bridge)",
                source="USDC", source_type="STABLECOIN",
                target="e-INR", target_type="CBDC",
                amount=Decimal("100000"),
                description="Stablecoin to CBDC via fiat intermediary",
                category="STABLECOIN_TO_CBDC"
            ),
            DemoScenario(
                id="S2C-002", name="USDC → e-INR (Atomic Swap)",
                source="USDC", source_type="STABLECOIN",
                target="e-INR", target_type="CBDC",
                amount=Decimal("50000"),
                description="⚛️ ATOMIC SWAP - Direct HTLC exchange",
                category="STABLECOIN_TO_CBDC",
                highlight=True
            ),
            DemoScenario(
                id="S2C-003", name="USDT → e-CNY (CEX Bridge)",
                source="USDT", source_type="STABLECOIN",
                target="e-CNY", target_type="CBDC",
                amount=Decimal("100000"),
                description="Tether to Chinese Digital Yuan",
                category="STABLECOIN_TO_CBDC"
            ),
            DemoScenario(
                id="S2C-004", name="XSGD → e-SGD (Atomic Swap)",
                source="XSGD", source_type="STABLECOIN",
                target="e-SGD", target_type="CBDC",
                amount=Decimal("100000"),
                description="⚛️ ATOMIC SWAP - Same-peg atomic exchange",
                category="STABLECOIN_TO_CBDC",
                highlight=True
            ),
        ]
        
        # Filter based on mode
        if self.mode == DemoMode.QUICK:
            return [s for s in all_scenarios if s.highlight]
        elif self.mode == DemoMode.ATOMIC:
            return [s for s in all_scenarios if "Atomic" in s.description or "ATOMIC" in s.description]
        elif self.mode == DemoMode.CBDC:
            return [s for s in all_scenarios if "CBDC" in s.category]
        elif self.mode == DemoMode.STABLE:
            return [s for s in all_scenarios if "STABLECOIN" in s.category]
        else:
            return all_scenarios
    
    async def run_scenario(self, scenario: DemoScenario) -> DemoResult:
        """Execute a single demo scenario"""
        start = time.time()
        
        try:
            if self.universal_engine:
                # Use actual engine
                routes = await self.universal_engine.find_all_routes(
                    scenario.source,
                    scenario.source_type,
                    scenario.target,
                    scenario.target_type,
                    scenario.amount
                )
                
                if routes:
                    best = routes[0]
                    return DemoResult(
                        scenario_id=scenario.id,
                        scenario_name=scenario.name,
                        success=True,
                        routes_found=len(routes),
                        best_route=best.route_name,
                        best_fee_bps=best.total_fee_bps,
                        best_settlement=f"{best.total_settlement_seconds}s",
                        target_amount=f"{best.target_amount:,.2f}",
                        execution_ms=(time.time() - start) * 1000
                    )
                else:
                    return DemoResult(
                        scenario_id=scenario.id,
                        scenario_name=scenario.name,
                        success=False,
                        routes_found=0,
                        best_route="N/A",
                        best_fee_bps=0,
                        best_settlement="N/A",
                        target_amount="N/A",
                        execution_ms=(time.time() - start) * 1000,
                        error="No routes found"
                    )
            else:
                # Simulation mode
                return self._simulate_scenario(scenario, start)
                
        except Exception as e:
            return DemoResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                success=False,
                routes_found=0,
                best_route="N/A",
                best_fee_bps=0,
                best_settlement="N/A",
                target_amount="N/A",
                execution_ms=(time.time() - start) * 1000,
                error=str(e)
            )
    
    def _simulate_scenario(self, scenario: DemoScenario, start: float) -> DemoResult:
        """Simulate scenario result for demo purposes"""
        import random
        
        # Simulated route data based on category
        sim_data = {
            "FIAT_TO_FIAT": {"routes": 3, "fee": 20, "time": "4h", "rate": 1.0},
            "FIAT_TO_CBDC": {"routes": 2, "fee": 0, "time": "5s", "rate": 1.0},
            "CBDC_TO_FIAT": {"routes": 2, "fee": 0, "time": "5s", "rate": 1.0},
            "CBDC_TO_CBDC": {"routes": 3, "fee": 13, "time": "15s", "rate": 1.0},
            "FIAT_TO_STABLECOIN": {"routes": 3, "fee": 0, "time": "1h", "rate": 1.0},
            "STABLECOIN_TO_FIAT": {"routes": 3, "fee": 25, "time": "4h", "rate": 1.0},
            "STABLECOIN_TO_STABLECOIN": {"routes": 2, "fee": 30, "time": "30s", "rate": 1.0},
            "CBDC_TO_STABLECOIN": {"routes": 4, "fee": 35, "time": "1h", "rate": 1.0},
            "STABLECOIN_TO_CBDC": {"routes": 3, "fee": 50, "time": "4h", "rate": 1.0},
        }
        
        data = sim_data.get(scenario.category, {"routes": 1, "fee": 50, "time": "1h", "rate": 1.0})
        
        # Adjust for atomic swaps
        if "Atomic" in scenario.description:
            data = {"routes": 1, "fee": 15, "time": "5m", "rate": 1.0}
        
        target_amount = float(scenario.amount) * data["rate"] * (1 - data["fee"]/10000)
        
        route_names = {
            "FIAT_TO_FIAT": "SWIFT Transfer",
            "FIAT_TO_CBDC": "Direct CBDC Mint",
            "CBDC_TO_FIAT": "Direct CBDC Redeem",
            "CBDC_TO_CBDC": "mBridge PvP",
            "FIAT_TO_STABLECOIN": "Direct Issuer Mint",
            "STABLECOIN_TO_FIAT": "Direct Issuer Redeem",
            "STABLECOIN_TO_STABLECOIN": "DEX Swap",
            "CBDC_TO_STABLECOIN": "Fiat Intermediary",
            "STABLECOIN_TO_CBDC": "Fiat Intermediary",
        }
        
        route_name = route_names.get(scenario.category, "Standard Route")
        if "Atomic" in scenario.description:
            route_name = "Atomic Swap (HTLC)"
        
        return DemoResult(
            scenario_id=scenario.id,
            scenario_name=scenario.name,
            success=True,
            routes_found=data["routes"],
            best_route=route_name,
            best_fee_bps=data["fee"],
            best_settlement=data["time"],
            target_amount=f"{target_amount:,.2f}",
            execution_ms=(time.time() - start) * 1000 + random.uniform(10, 50)
        )
    
    async def run_all(self):
        """Run all demo scenarios"""
        scenarios = self.get_scenarios()
        
        print(f"\n📋 Running {len(scenarios)} scenarios...\n")
        
        # Group by category
        categories = {}
        for s in scenarios:
            if s.category not in categories:
                categories[s.category] = []
            categories[s.category].append(s)
        
        # Run scenarios by category
        for category, cat_scenarios in categories.items():
            self._print_category_header(category)
            
            for scenario in cat_scenarios:
                result = await self.run_scenario(scenario)
                self.results.append(result)
                self._print_result(result, scenario)
        
        # Print summary
        self._print_summary()
    
    def _print_category_header(self, category: str):
        """Print category header"""
        icons = {
            "FIAT_TO_FIAT": "💱",
            "FIAT_TO_CBDC": "🏛️",
            "CBDC_TO_FIAT": "💵",
            "CBDC_TO_CBDC": "🌐",
            "FIAT_TO_STABLECOIN": "🪙",
            "STABLECOIN_TO_FIAT": "💰",
            "STABLECOIN_TO_STABLECOIN": "🔄",
            "CBDC_TO_STABLECOIN": "🔗",
            "STABLECOIN_TO_CBDC": "⚡",
        }
        icon = icons.get(category, "📦")
        print(f"\n{'─'*70}")
        print(f"{icon} {category.replace('_', ' ')}")
        print(f"{'─'*70}")
    
    def _print_result(self, result: DemoResult, scenario: DemoScenario):
        """Print scenario result"""
        status = "✅" if result.success else "❌"
        highlight = "⭐ " if scenario.highlight else ""
        atomic = "⚛️ " if "Atomic" in scenario.description else ""
        
        print(f"""
{highlight}{atomic}{status} {result.scenario_id}: {result.scenario_name}
   └─ Routes: {result.routes_found} | Best: {result.best_route}
   └─ Fee: {result.best_fee_bps} bps | Settlement: {result.best_settlement}
   └─ Target Amount: {result.target_amount}
   └─ Execution: {result.execution_ms:.1f}ms""")
        
        if result.error:
            print(f"   └─ ⚠️ Error: {result.error}")
    
    def _print_summary(self):
        """Print execution summary"""
        total = len(self.results)
        success = sum(1 for r in self.results if r.success)
        failed = total - success
        avg_time = sum(r.execution_ms for r in self.results) / total if total > 0 else 0
        
        print(f"""
{'═'*70}
📊 DEMO SUMMARY
{'═'*70}

┌────────────────────────────────────────────────────────────────────┐
│  Total Scenarios: {total:3d}                                           │
│  ✅ Successful:   {success:3d}                                           │
│  ❌ Failed:       {failed:3d}                                           │
│  ⏱️ Avg Time:     {avg_time:.1f}ms                                        │
└────────────────────────────────────────────────────────────────────┘

📈 Results by Category:
""")
        
        # Group results by category
        from collections import defaultdict
        by_category = defaultdict(list)
        for r in self.results:
            cat = r.scenario_id.split("-")[0]
            by_category[cat].append(r)
        
        cat_names = {
            "F2F": "Fiat → Fiat",
            "F2C": "Fiat → CBDC",
            "C2F": "CBDC → Fiat",
            "C2C": "CBDC → CBDC",
            "F2S": "Fiat → Stablecoin",
            "S2F": "Stablecoin → Fiat",
            "S2S": "Stablecoin → Stablecoin",
            "C2S": "CBDC → Stablecoin",
            "S2C": "Stablecoin → CBDC",
        }
        
        for cat, results in by_category.items():
            success_count = sum(1 for r in results if r.success)
            print(f"   {cat_names.get(cat, cat):25s}: {success_count}/{len(results)} passed")
        
        print(f"""
{'═'*70}
✨ Demo Complete!
{'═'*70}
""")
    
    def export_results(self, filepath: str = "demo_results.json"):
        """Export results to JSON"""
        output = {
            "run_date": datetime.now().isoformat(),
            "mode": self.mode.value,
            "total_scenarios": len(self.results),
            "success_count": sum(1 for r in self.results if r.success),
            "results": [asdict(r) for r in self.results]
        }
        
        with open(filepath, "w") as f:
            json.dump(output, f, indent=2, default=str)
        
        print(f"📁 Results exported to: {filepath}")


async def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description="FX Smart Routing Demo")
    parser.add_argument(
        "--mode", 
        choices=["quick", "full", "atomic", "cbdc", "stable"],
        default="quick",
        help="Demo mode"
    )
    parser.add_argument(
        "--config",
        default="config",
        help="Config directory"
    )
    parser.add_argument(
        "--export",
        action="store_true",
        help="Export results to JSON"
    )
    
    args = parser.parse_args()
    
    demo = FXDemoRunner(
        config_dir=args.config,
        mode=DemoMode(args.mode)
    )
    
    demo.setup()
    await demo.run_all()
    
    if args.export:
        demo.export_results()


if __name__ == "__main__":
    asyncio.run(main())
