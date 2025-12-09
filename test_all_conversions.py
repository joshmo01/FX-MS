"""
Comprehensive Test Harness for FX Smart Routing Engine

Tests all 9 conversion types:
1. FIAT → FIAT
2. FIAT → CBDC
3. CBDC → FIAT
4. CBDC → CBDC
5. FIAT → STABLECOIN
6. STABLECOIN → FIAT
7. STABLECOIN → STABLECOIN
8. CBDC → STABLECOIN
9. STABLECOIN → CBDC

Author: Fintaar.ai
"""
import asyncio
import json
from decimal import Decimal
from datetime import datetime
from typing import Dict, List, Any
from dataclasses import dataclass, asdict
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.services.universal_conversion_engine import UniversalConversionEngine, ConversionType
from app.services.cbdc_stable_bridge import CBDCStableBridge, get_bridge_engine


@dataclass
class TestCase:
    """Test case definition"""
    name: str
    source: str
    source_type: str
    target: str
    target_type: str
    amount: Decimal
    expected_routes: int  # Minimum expected routes
    description: str


@dataclass 
class TestResult:
    """Test result"""
    test_name: str
    passed: bool
    routes_found: int
    best_route: str
    best_fee_bps: int
    best_settlement: str
    execution_time_ms: float
    error: str = ""
    details: Dict[str, Any] = None


class ConversionTestHarness:
    """
    Comprehensive test harness for all conversion scenarios
    """
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = config_dir
        self.results: List[TestResult] = []
        self.universal_engine = None
        self.bridge_engine = None
        
    def setup(self):
        """Initialize engines"""
        print("\n" + "="*60)
        print("🚀 FX Smart Routing - Conversion Test Harness")
        print("="*60)
        print(f"\n📅 Test Run: {datetime.now().isoformat()}")
        print(f"📁 Config Directory: {self.config_dir}")
        
        try:
            self.universal_engine = UniversalConversionEngine(self.config_dir)
            self.bridge_engine = get_bridge_engine(self.config_dir)
            print("✅ Engines initialized successfully")
        except Exception as e:
            print(f"❌ Engine initialization failed: {e}")
            raise
    
    def get_test_cases(self) -> List[TestCase]:
        """Define all test cases"""
        return [
            # =========================================
            # FIAT to FIAT
            # =========================================
            TestCase(
                name="F2F-001: USD to INR Direct",
                source="USD", source_type="FIAT",
                target="INR", target_type="FIAT",
                amount=Decimal("100000"),
                expected_routes=2,
                description="Standard USD to INR conversion"
            ),
            TestCase(
                name="F2F-002: EUR to SGD Cross",
                source="EUR", source_type="FIAT",
                target="SGD", target_type="FIAT",
                amount=Decimal("50000"),
                expected_routes=2,
                description="Cross-rate conversion via USD"
            ),
            
            # =========================================
            # FIAT to CBDC
            # =========================================
            TestCase(
                name="F2C-001: INR to e-INR Mint",
                source="INR", source_type="FIAT",
                target="e-INR", target_type="CBDC",
                amount=Decimal("100000"),
                expected_routes=1,
                description="Direct CBDC minting (same currency)"
            ),
            TestCase(
                name="F2C-002: USD to e-INR",
                source="USD", source_type="FIAT",
                target="e-INR", target_type="CBDC",
                amount=Decimal("10000"),
                expected_routes=1,
                description="FX + CBDC mint path"
            ),
            TestCase(
                name="F2C-003: USD to e-CNY",
                source="USD", source_type="FIAT",
                target="e-CNY", target_type="CBDC",
                amount=Decimal("100000"),
                expected_routes=1,
                description="FX to Chinese CBDC"
            ),
            
            # =========================================
            # CBDC to FIAT
            # =========================================
            TestCase(
                name="C2F-001: e-INR to INR Redeem",
                source="e-INR", source_type="CBDC",
                target="INR", target_type="FIAT",
                amount=Decimal("100000"),
                expected_routes=1,
                description="Direct CBDC redemption"
            ),
            TestCase(
                name="C2F-002: e-INR to USD",
                source="e-INR", source_type="CBDC",
                target="USD", target_type="FIAT",
                amount=Decimal("8450000"),
                expected_routes=1,
                description="CBDC redeem + FX"
            ),
            
            # =========================================
            # CBDC to CBDC
            # =========================================
            TestCase(
                name="C2C-001: e-CNY to e-HKD (mBridge)",
                source="e-CNY", source_type="CBDC",
                target="e-HKD", target_type="CBDC",
                amount=Decimal("1000000"),
                expected_routes=2,
                description="mBridge cross-border CBDC"
            ),
            TestCase(
                name="C2C-002: e-CNY to e-AED (mBridge)",
                source="e-CNY", source_type="CBDC",
                target="e-AED", target_type="CBDC",
                amount=Decimal("500000"),
                expected_routes=2,
                description="mBridge to UAE"
            ),
            TestCase(
                name="C2C-003: e-INR to e-SGD (Non-mBridge)",
                source="e-INR", source_type="CBDC",
                target="e-SGD", target_type="CBDC",
                amount=Decimal("1000000"),
                expected_routes=1,
                description="Fiat bridge path (no mBridge)"
            ),
            
            # =========================================
            # FIAT to STABLECOIN
            # =========================================
            TestCase(
                name="F2S-001: USD to USDC",
                source="USD", source_type="FIAT",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("100000"),
                expected_routes=2,
                description="Direct stablecoin mint"
            ),
            TestCase(
                name="F2S-002: EUR to EURC",
                source="EUR", source_type="FIAT",
                target="EURC", target_type="STABLECOIN",
                amount=Decimal("50000"),
                expected_routes=2,
                description="Euro stablecoin path"
            ),
            TestCase(
                name="F2S-003: INR to USDC",
                source="INR", source_type="FIAT",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("8450000"),
                expected_routes=2,
                description="FX + stablecoin mint"
            ),
            
            # =========================================
            # STABLECOIN to FIAT
            # =========================================
            TestCase(
                name="S2F-001: USDC to USD",
                source="USDC", source_type="STABLECOIN",
                target="USD", target_type="FIAT",
                amount=Decimal("100000"),
                expected_routes=2,
                description="Direct stablecoin redemption"
            ),
            TestCase(
                name="S2F-002: USDC to INR",
                source="USDC", source_type="STABLECOIN",
                target="INR", target_type="FIAT",
                amount=Decimal("100000"),
                expected_routes=2,
                description="Stablecoin + FX"
            ),
            TestCase(
                name="S2F-003: USDT to EUR",
                source="USDT", source_type="STABLECOIN",
                target="EUR", target_type="FIAT",
                amount=Decimal("50000"),
                expected_routes=2,
                description="USDT off-ramp to Euro"
            ),
            
            # =========================================
            # STABLECOIN to STABLECOIN
            # =========================================
            TestCase(
                name="S2S-001: USDC to USDT (Same peg)",
                source="USDC", source_type="STABLECOIN",
                target="USDT", target_type="STABLECOIN",
                amount=Decimal("100000"),
                expected_routes=2,
                description="Same-peg stablecoin swap"
            ),
            TestCase(
                name="S2S-002: USDC to EURC (Cross peg)",
                source="USDC", source_type="STABLECOIN",
                target="EURC", target_type="STABLECOIN",
                amount=Decimal("50000"),
                expected_routes=2,
                description="Cross-currency stablecoin swap"
            ),
            
            # =========================================
            # CBDC to STABLECOIN (NEW!)
            # =========================================
            TestCase(
                name="C2S-001: e-INR to USDC",
                source="e-INR", source_type="CBDC",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("8450000"),
                expected_routes=2,
                description="Indian CBDC to US stablecoin"
            ),
            TestCase(
                name="C2S-002: e-CNY to USDC (mBridge)",
                source="e-CNY", source_type="CBDC",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("725000"),
                expected_routes=3,
                description="Chinese CBDC via mBridge hybrid"
            ),
            TestCase(
                name="C2S-003: e-SGD to XSGD",
                source="e-SGD", source_type="CBDC",
                target="XSGD", target_type="STABLECOIN",
                amount=Decimal("100000"),
                expected_routes=2,
                description="Singapore CBDC to Singapore stablecoin"
            ),
            
            # =========================================
            # STABLECOIN to CBDC (NEW!)
            # =========================================
            TestCase(
                name="S2C-001: USDC to e-INR",
                source="USDC", source_type="STABLECOIN",
                target="e-INR", target_type="CBDC",
                amount=Decimal("100000"),
                expected_routes=2,
                description="US stablecoin to Indian CBDC"
            ),
            TestCase(
                name="S2C-002: USDT to e-CNY",
                source="USDT", source_type="STABLECOIN",
                target="e-CNY", target_type="CBDC",
                amount=Decimal("100000"),
                expected_routes=2,
                description="Tether to Chinese CBDC"
            ),
            TestCase(
                name="S2C-003: XSGD to e-SGD",
                source="XSGD", source_type="STABLECOIN",
                target="e-SGD", target_type="CBDC",
                amount=Decimal("50000"),
                expected_routes=2,
                description="Singapore stablecoin to Singapore CBDC"
            ),
            
            # =========================================
            # Edge Cases
            # =========================================
            TestCase(
                name="EDGE-001: Large Amount CBDC",
                source="e-CNY", source_type="CBDC",
                target="USDC", target_type="STABLECOIN",
                amount=Decimal("10000000"),
                expected_routes=2,
                description="Large institutional conversion"
            ),
            TestCase(
                name="EDGE-002: Small Amount Stablecoin",
                source="USDC", source_type="STABLECOIN",
                target="e-INR", target_type="CBDC",
                amount=Decimal("100"),
                expected_routes=2,
                description="Small retail conversion"
            ),
        ]
    
    async def run_test(self, test: TestCase) -> TestResult:
        """Run a single test case"""
        import time
        start = time.time()
        
        try:
            # Determine which engine to use
            if (test.source_type == "CBDC" and test.target_type == "STABLECOIN"):
                routes = await self.bridge_engine.get_cbdc_to_stable_routes(
                    cbdc=test.source,
                    stablecoin=test.target,
                    amount=test.amount,
                    require_regulated=False  # Include all routes for testing
                )
            elif (test.source_type == "STABLECOIN" and test.target_type == "CBDC"):
                routes = await self.bridge_engine.get_stable_to_cbdc_routes(
                    stablecoin=test.source,
                    cbdc=test.target,
                    amount=test.amount,
                    require_regulated=False
                )
            else:
                routes = await self.universal_engine.convert(
                    source=test.source,
                    source_type=test.source_type,
                    target=test.target,
                    target_type=test.target_type,
                    amount=test.amount
                )
            
            execution_time = (time.time() - start) * 1000
            
            # Determine if test passed
            passed = len(routes) >= test.expected_routes
            
            # Get best route info
            if routes:
                best = routes[0]
                if hasattr(best, 'route_name'):
                    best_route = best.route_name
                    best_fee = best.total_fee_bps
                    best_settlement = f"{best.total_settlement_seconds}s"
                else:
                    best_route = getattr(best, 'route_name', 'Unknown')
                    best_fee = getattr(best, 'total_fee_bps', 0)
                    best_settlement = f"{getattr(best, 'total_settlement_seconds', 0)}s"
            else:
                best_route = "N/A"
                best_fee = 0
                best_settlement = "N/A"
            
            return TestResult(
                test_name=test.name,
                passed=passed,
                routes_found=len(routes),
                best_route=best_route,
                best_fee_bps=best_fee,
                best_settlement=best_settlement,
                execution_time_ms=round(execution_time, 2),
                details={
                    "description": test.description,
                    "source": f"{test.source} ({test.source_type})",
                    "target": f"{test.target} ({test.target_type})",
                    "amount": str(test.amount),
                    "expected_routes": test.expected_routes,
                    "all_routes": [
                        getattr(r, 'route_name', str(r)) for r in routes[:5]
                    ]
                }
            )
            
        except Exception as e:
            execution_time = (time.time() - start) * 1000
            return TestResult(
                test_name=test.name,
                passed=False,
                routes_found=0,
                best_route="ERROR",
                best_fee_bps=0,
                best_settlement="N/A",
                execution_time_ms=round(execution_time, 2),
                error=str(e)
            )
    
    async def run_all_tests(self) -> Dict[str, Any]:
        """Run all test cases"""
        self.setup()
        
        test_cases = self.get_test_cases()
        print(f"\n📋 Running {len(test_cases)} test cases...\n")
        
        # Group tests by conversion type
        conversion_types = {}
        for test in test_cases:
            conv_type = f"{test.source_type}→{test.target_type}"
            if conv_type not in conversion_types:
                conversion_types[conv_type] = []
            conversion_types[conv_type].append(test)
        
        all_results = []
        
        for conv_type, tests in conversion_types.items():
            print(f"\n{'='*60}")
            print(f"📦 {conv_type} Tests ({len(tests)} cases)")
            print("="*60)
            
            for test in tests:
                result = await self.run_test(test)
                all_results.append(result)
                
                # Print result
                status = "✅ PASS" if result.passed else "❌ FAIL"
                print(f"\n{status} {result.test_name}")
                print(f"   Description: {test.description}")
                print(f"   Routes Found: {result.routes_found} (expected: {test.expected_routes}+)")
                if result.routes_found > 0:
                    print(f"   Best Route: {result.best_route}")
                    print(f"   Best Fee: {result.best_fee_bps} bps")
                    print(f"   Settlement: {result.best_settlement}")
                print(f"   Execution: {result.execution_time_ms}ms")
                if result.error:
                    print(f"   Error: {result.error}")
        
        # Summary
        passed = sum(1 for r in all_results if r.passed)
        failed = len(all_results) - passed
        
        print("\n" + "="*60)
        print("📊 TEST SUMMARY")
        print("="*60)
        print(f"Total Tests: {len(all_results)}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Pass Rate: {passed/len(all_results)*100:.1f}%")
        
        # By conversion type
        print("\n📈 Results by Conversion Type:")
        for conv_type in conversion_types.keys():
            type_results = [r for r in all_results if conv_type in r.test_name or 
                          any(conv_type in str(r.details.get('source', '')) + str(r.details.get('target', ''))
                              for _ in [1])]
            # Simpler grouping
            count = len([t for t in test_cases if f"{t.source_type}→{t.target_type}" == conv_type])
            passed_count = sum(1 for i, r in enumerate(all_results) 
                             if f"{test_cases[i].source_type}→{test_cases[i].target_type}" == conv_type 
                             and r.passed)
            print(f"   {conv_type}: {passed_count}/{count}")
        
        # Performance stats
        avg_time = sum(r.execution_time_ms for r in all_results) / len(all_results)
        max_time = max(r.execution_time_ms for r in all_results)
        print(f"\n⏱️  Avg Execution Time: {avg_time:.2f}ms")
        print(f"⏱️  Max Execution Time: {max_time:.2f}ms")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_tests": len(all_results),
            "passed": passed,
            "failed": failed,
            "pass_rate": f"{passed/len(all_results)*100:.1f}%",
            "results": [asdict(r) if hasattr(r, '__dataclass_fields__') else r for r in all_results]
        }
    
    def generate_report(self, results: Dict[str, Any], output_file: str = "test_report.json"):
        """Generate JSON test report"""
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        print(f"\n📄 Report saved to: {output_file}")


async def main():
    """Main entry point"""
    harness = ConversionTestHarness(config_dir="config")
    results = await harness.run_all_tests()
    harness.generate_report(results, "test_report.json")
    
    # Return exit code based on results
    if results["failed"] > 0:
        print(f"\n⚠️  {results['failed']} tests failed!")
        return 1
    else:
        print("\n✅ All tests passed!")
        return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
