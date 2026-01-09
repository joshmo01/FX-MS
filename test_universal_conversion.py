"""
Comprehensive Test Harness for Universal FX Conversion Engine

Tests all 9 conversion types with various scenarios.
"""
import asyncio
import json
from decimal import Decimal
from datetime import datetime
from typing import List, Dict
from dataclasses import dataclass, asdict

# Import the engine
import sys
sys.path.insert(0, '.')

from app.services.universal_conversion_engine import (
    get_universal_engine,
    UniversalConversionEngine,
    ConversionType,
    ConversionRoute
)


@dataclass
class TestCase:
    """Test case definition"""
    name: str
    source_currency: str
    source_type: str
    target_currency: str
    target_type: str
    amount: Decimal
    expected_conversion_type: str
    min_routes_expected: int = 1


@dataclass
class TestResult:
    """Test result"""
    test_name: str
    passed: bool
    conversion_type: str
    routes_found: int
    best_route: str
    best_fee_bps: int
    best_settlement: str
    error: str = None


def format_time(seconds: int) -> str:
    """Format seconds to human readable"""
    if seconds < 60:
        return f"{seconds}s"
    elif seconds < 3600:
        return f"{seconds // 60}m"
    elif seconds < 86400:
        return f"{seconds / 3600:.1f}h"
    else:
        return f"{seconds / 86400:.1f}d"


async def run_test(engine: UniversalConversionEngine, test: TestCase) -> TestResult:
    """Run a single test case"""
    try:
        routes = await engine.find_all_routes(
            source_currency=test.source_currency,
            source_type=test.source_type,
            target_currency=test.target_currency,
            target_type=test.target_type,
            amount=test.amount
        )
        
        if len(routes) < test.min_routes_expected:
            return TestResult(
                test_name=test.name,
                passed=False,
                conversion_type=test.expected_conversion_type,
                routes_found=len(routes),
                best_route="N/A",
                best_fee_bps=0,
                best_settlement="N/A",
                error=f"Expected at least {test.min_routes_expected} routes, got {len(routes)}"
            )
        
        best = routes[0]  # Already sorted by score
        
        return TestResult(
            test_name=test.name,
            passed=True,
            conversion_type=best.conversion_type.value,
            routes_found=len(routes),
            best_route=best.route_name,
            best_fee_bps=best.total_fee_bps,
            best_settlement=format_time(best.total_settlement_seconds)
        )
        
    except Exception as e:
        return TestResult(
            test_name=test.name,
            passed=False,
            conversion_type=test.expected_conversion_type,
            routes_found=0,
            best_route="N/A",
            best_fee_bps=0,
            best_settlement="N/A",
            error=str(e)
        )


async def run_all_tests():
    """Run all test cases"""
    print("\n" + "=" * 80)
    print("🧪 UNIVERSAL FX CONVERSION ENGINE - COMPREHENSIVE TEST HARNESS")
    print("=" * 80)
    print(f"Started: {datetime.now().isoformat()}")
    print()
    
    engine = get_universal_engine()
    
    # Define all test cases
    test_cases: List[TestCase] = [
        # =====================================================================
        # FIAT ↔ FIAT Tests
        # =====================================================================
        TestCase(
            name="FIAT→FIAT: USD to INR (Direct)",
            source_currency="USD", source_type="FIAT",
            target_currency="INR", target_type="FIAT",
            amount=Decimal("10000"),
            expected_conversion_type="FIAT_TO_FIAT",
            min_routes_expected=2
        ),
        TestCase(
            name="FIAT→FIAT: EUR to USD",
            source_currency="EUR", source_type="FIAT",
            target_currency="USD", target_type="FIAT",
            amount=Decimal("5000"),
            expected_conversion_type="FIAT_TO_FIAT",
            min_routes_expected=1
        ),
        
        # =====================================================================
        # FIAT ↔ CBDC Tests
        # =====================================================================
        TestCase(
            name="FIAT→CBDC: INR to e-INR (Direct Mint)",
            source_currency="INR", source_type="FIAT",
            target_currency="e-INR", target_type="CBDC",
            amount=Decimal("100000"),
            expected_conversion_type="FIAT_TO_CBDC",
            min_routes_expected=1
        ),
        TestCase(
            name="FIAT→CBDC: USD to e-INR (FX then Mint)",
            source_currency="USD", source_type="FIAT",
            target_currency="e-INR", target_type="CBDC",
            amount=Decimal("10000"),
            expected_conversion_type="FIAT_TO_CBDC",
            min_routes_expected=1
        ),
        TestCase(
            name="CBDC→FIAT: e-INR to INR (Direct Redeem)",
            source_currency="e-INR", source_type="CBDC",
            target_currency="INR", target_type="FIAT",
            amount=Decimal("100000"),
            expected_conversion_type="CBDC_TO_FIAT",
            min_routes_expected=1
        ),
        TestCase(
            name="CBDC→FIAT: e-INR to USD (Redeem then FX)",
            source_currency="e-INR", source_type="CBDC",
            target_currency="USD", target_type="FIAT",
            amount=Decimal("100000"),
            expected_conversion_type="CBDC_TO_FIAT",
            min_routes_expected=1
        ),
        
        # =====================================================================
        # CBDC ↔ CBDC Tests
        # =====================================================================
        TestCase(
            name="CBDC→CBDC: e-CNY to e-AED (mBridge)",
            source_currency="e-CNY", source_type="CBDC",
            target_currency="e-AED", target_type="CBDC",
            amount=Decimal("50000"),
            expected_conversion_type="CBDC_TO_CBDC",
            min_routes_expected=1
        ),
        TestCase(
            name="CBDC→CBDC: e-HKD to e-THB (mBridge)",
            source_currency="e-HKD", source_type="CBDC",
            target_currency="e-THB", target_type="CBDC",
            amount=Decimal("100000"),
            expected_conversion_type="CBDC_TO_CBDC",
            min_routes_expected=1
        ),
        
        # =====================================================================
        # FIAT ↔ STABLECOIN Tests
        # =====================================================================
        TestCase(
            name="FIAT→STABLE: USD to USDC",
            source_currency="USD", source_type="FIAT",
            target_currency="USDC", target_type="STABLECOIN",
            amount=Decimal("10000"),
            expected_conversion_type="FIAT_TO_STABLECOIN",
            min_routes_expected=1
        ),
        TestCase(
            name="FIAT→STABLE: EUR to EURC",
            source_currency="EUR", source_type="FIAT",
            target_currency="EURC", target_type="STABLECOIN",
            amount=Decimal("5000"),
            expected_conversion_type="FIAT_TO_STABLECOIN",
            min_routes_expected=1
        ),
        TestCase(
            name="STABLE→FIAT: USDC to USD",
            source_currency="USDC", source_type="STABLECOIN",
            target_currency="USD", target_type="FIAT",
            amount=Decimal("10000"),
            expected_conversion_type="STABLECOIN_TO_FIAT",
            min_routes_expected=1
        ),
        TestCase(
            name="STABLE→FIAT: USDT to INR",
            source_currency="USDT", source_type="STABLECOIN",
            target_currency="INR", target_type="FIAT",
            amount=Decimal("5000"),
            expected_conversion_type="STABLECOIN_TO_FIAT",
            min_routes_expected=1
        ),
        
        # =====================================================================
        # STABLECOIN ↔ STABLECOIN Tests
        # =====================================================================
        TestCase(
            name="STABLE→STABLE: USDC to USDT (DEX/CEX)",
            source_currency="USDC", source_type="STABLECOIN",
            target_currency="USDT", target_type="STABLECOIN",
            amount=Decimal("10000"),
            expected_conversion_type="STABLECOIN_TO_STABLECOIN",
            min_routes_expected=2
        ),
        TestCase(
            name="STABLE→STABLE: USDT to EURC",
            source_currency="USDT", source_type="STABLECOIN",
            target_currency="EURC", target_type="STABLECOIN",
            amount=Decimal("5000"),
            expected_conversion_type="STABLECOIN_TO_STABLECOIN",
            min_routes_expected=1
        ),
        
        # =====================================================================
        # CBDC ↔ STABLECOIN Tests (NEW!)
        # =====================================================================
        TestCase(
            name="CBDC→STABLE: e-INR to USDC",
            source_currency="e-INR", source_type="CBDC",
            target_currency="USDC", target_type="STABLECOIN",
            amount=Decimal("100000"),
            expected_conversion_type="CBDC_TO_STABLECOIN",
            min_routes_expected=1
        ),
        TestCase(
            name="CBDC→STABLE: e-CNY to USDT",
            source_currency="e-CNY", source_type="CBDC",
            target_currency="USDT", target_type="STABLECOIN",
            amount=Decimal("50000"),
            expected_conversion_type="CBDC_TO_STABLECOIN",
            min_routes_expected=1
        ),
        TestCase(
            name="CBDC→STABLE: e-SGD to XSGD",
            source_currency="e-SGD", source_type="CBDC",
            target_currency="XSGD", target_type="STABLECOIN",
            amount=Decimal("10000"),
            expected_conversion_type="CBDC_TO_STABLECOIN",
            min_routes_expected=1
        ),
        TestCase(
            name="STABLE→CBDC: USDC to e-INR",
            source_currency="USDC", source_type="STABLECOIN",
            target_currency="e-INR", target_type="CBDC",
            amount=Decimal("10000"),
            expected_conversion_type="STABLECOIN_TO_CBDC",
            min_routes_expected=1
        ),
        TestCase(
            name="STABLE→CBDC: USDT to e-CNY",
            source_currency="USDT", source_type="STABLECOIN",
            target_currency="e-CNY", target_type="CBDC",
            amount=Decimal("5000"),
            expected_conversion_type="STABLECOIN_TO_CBDC",
            min_routes_expected=1
        ),
        TestCase(
            name="STABLE→CBDC: XSGD to e-SGD",
            source_currency="XSGD", source_type="STABLECOIN",
            target_currency="e-SGD", target_type="CBDC",
            amount=Decimal("10000"),
            expected_conversion_type="STABLECOIN_TO_CBDC",
            min_routes_expected=1
        ),
    ]
    
    # Run all tests
    results: List[TestResult] = []
    passed = 0
    failed = 0
    
    # Group tests by conversion type
    current_type = ""
    
    for test in test_cases:
        if test.expected_conversion_type != current_type:
            current_type = test.expected_conversion_type
            print(f"\n{'─' * 60}")
            print(f"📋 {current_type.replace('_', ' ')}")
            print(f"{'─' * 60}")
        
        result = await run_test(engine, test)
        results.append(result)
        
        if result.passed:
            passed += 1
            status = "✅ PASS"
        else:
            failed += 1
            status = "❌ FAIL"
        
        print(f"\n{status} {result.test_name}")
        print(f"   Routes: {result.routes_found} | Best: {result.best_route}")
        print(f"   Fee: {result.best_fee_bps} bps | Settlement: {result.best_settlement}")
        
        if result.error:
            print(f"   ⚠️  Error: {result.error}")
    
    # Summary
    print("\n" + "=" * 80)
    print("📊 TEST SUMMARY")
    print("=" * 80)
    print(f"Total Tests: {len(results)}")
    print(f"✅ Passed: {passed}")
    print(f"❌ Failed: {failed}")
    print(f"Pass Rate: {passed / len(results) * 100:.1f}%")
    
    # Conversion type summary
    print("\n📈 RESULTS BY CONVERSION TYPE:")
    print("-" * 60)
    
    type_results = {}
    for result in results:
        ct = result.conversion_type
        if ct not in type_results:
            type_results[ct] = {"passed": 0, "failed": 0}
        if result.passed:
            type_results[ct]["passed"] += 1
        else:
            type_results[ct]["failed"] += 1
    
    for ct, counts in type_results.items():
        total = counts["passed"] + counts["failed"]
        pct = counts["passed"] / total * 100
        status = "✅" if counts["failed"] == 0 else "⚠️"
        print(f"{status} {ct}: {counts['passed']}/{total} ({pct:.0f}%)")
    
    print("\n" + "=" * 80)
    print(f"Completed: {datetime.now().isoformat()}")
    print("=" * 80)
    
    return results


async def demo_single_conversion():
    """Demo a single complex conversion"""
    print("\n" + "=" * 80)
    print("🔄 DEMO: CBDC to STABLECOIN Conversion")
    print("=" * 80)
    
    engine = get_universal_engine()
    
    # e-INR → USDC
    routes = await engine.find_all_routes(
        source_currency="e-INR",
        source_type="CBDC",
        target_currency="USDC",
        target_type="STABLECOIN",
        amount=Decimal("100000")
    )
    
    print(f"\n📍 Conversion: e-INR (CBDC) → USDC (STABLECOIN)")
    print(f"   Amount: ₹100,000")
    print(f"   Routes Found: {len(routes)}")
    
    for i, route in enumerate(routes):
        print(f"\n   {'🏆 ' if i == 0 else '   '}Route {i+1}: {route.route_name}")
        print(f"      Method: {route.route_method}")
        print(f"      Legs: {len(route.legs)}")
        
        for leg in route.legs:
            print(f"         {leg.leg_number}. {leg.from_currency} → {leg.to_currency}")
            print(f"            Provider: {leg.provider}")
            print(f"            Rate: {leg.rate}")
            print(f"            Fee: {leg.fee_bps} bps")
            print(f"            Time: {format_time(leg.settlement_seconds)}")
            if leg.network:
                print(f"            Network: {leg.network}")
        
        print(f"      ─────────────────────────────")
        print(f"      Target Amount: {route.target_amount} USDC")
        print(f"      Effective Rate: {route.effective_rate}")
        print(f"      Total Fee: {route.total_fee_bps} bps (${route.total_fee_usd})")
        print(f"      Settlement: {format_time(route.total_settlement_seconds)}")
        print(f"      Score: {route.overall_score:.1f}/100")


async def main():
    """Main entry point"""
    print("\n🚀 Starting Universal FX Conversion Engine Tests...")
    
    # Run demo first
    await demo_single_conversion()
    
    # Then run all tests
    results = await run_all_tests()
    
    # Return exit code based on results
    failed = sum(1 for r in results if not r.passed)
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
