"""
Master Test Runner for FX-MS API Tests
Executes all test suites and generates aggregate report

Usage:
    python tests/run_all_tests.py              # Run all tests
    python tests/run_all_tests.py --list       # List available suites
    python tests/run_all_tests.py --suite routing pricing  # Run specific suites
"""
import asyncio
import argparse
import sys
import time
from datetime import datetime
from pathlib import Path
from dataclasses import asdict

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from tests.base.test_utils import (
    save_results,
    print_summary,
    ensure_results_dir,
    create_aggregate_report
)

# Import all test suites
from tests.api.test_01_routing_api import RoutingAPITests
from tests.api.test_02_multi_rail_api import MultiRailAPITests
from tests.api.test_03_deals_api import DealsAPITests
from tests.api.test_04_deals_workflow_api import DealsWorkflowAPITests
from tests.api.test_05_pricing_api import PricingAPITests
from tests.api.test_06_rules_api import RulesAPITests
from tests.api.test_07_universal_api import UniversalAPITests
from tests.api.test_08_bridge_api import BridgeAPITests
from tests.api.test_09_health_api import HealthAPITests
from tests.api.test_10_negative_tests import NegativeTests
from tests.api.test_11_edge_cases import EdgeCaseTests
from tests.api.test_12_integration import IntegrationTests


# All available test suites
ALL_TEST_SUITES = [
    ("routing", RoutingAPITests),
    ("multi-rail", MultiRailAPITests),
    ("deals", DealsAPITests),
    ("deals-workflow", DealsWorkflowAPITests),
    ("pricing", PricingAPITests),
    ("rules", RulesAPITests),
    ("universal", UniversalAPITests),
    ("bridge", BridgeAPITests),
    ("health", HealthAPITests),
    ("negative", NegativeTests),
    ("edge-cases", EdgeCaseTests),
    ("integration", IntegrationTests),
]


async def run_suite(suite_class) -> dict:
    """Run a single test suite and return results"""
    suite = suite_class()
    result = await suite.run_all_tests()
    return result.__dict__ if hasattr(result, '__dict__') else asdict(result)


async def run_all_tests(suite_names: list = None):
    """Run all or selected test suites"""

    # Filter suites if specific ones requested
    if suite_names:
        suites_to_run = [
            (name, cls) for name, cls in ALL_TEST_SUITES
            if any(s.lower() in name.lower() for s in suite_names)
        ]
        if not suites_to_run:
            print(f"No matching suites found for: {suite_names}")
            print("Available suites:")
            for name, _ in ALL_TEST_SUITES:
                print(f"  - {name}")
            return 1
    else:
        suites_to_run = ALL_TEST_SUITES

    print("\n" + "=" * 80)
    print("   FX-MS API TEST SUITE - COMPREHENSIVE TEST RUN")
    print("   Started: " + datetime.now().isoformat())
    print("   Suites to run: " + str(len(suites_to_run)))
    print("=" * 80)

    all_results = []
    total_start = time.time()

    for name, suite_class in suites_to_run:
        print(f"\n>>> Running: {name}")
        result = await run_suite(suite_class)
        all_results.append(result)

        # Save individual suite result
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        save_results(result, f"{name.replace('-', '_')}_{timestamp}.json")

    total_time = (time.time() - total_start) * 1000

    # Create and save aggregate report
    aggregate = create_aggregate_report(all_results)
    aggregate["total_execution_time_ms"] = round(total_time, 2)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    save_results(aggregate, f"aggregate_report_{timestamp}.json")

    # Print final summary
    print("\n" + "=" * 80)
    print("   AGGREGATE TEST SUMMARY")
    print("=" * 80)
    print(f"   Total Suites Run:    {aggregate['total_suites']}")
    print(f"   Total Tests:         {aggregate['total_tests']}")
    print(f"   Passed:              {aggregate['overall_passed']} [PASS]")
    print(f"   Failed:              {aggregate['overall_failed']} [FAIL]")
    print(f"   Errors:              {aggregate['overall_errors']} [ERR]")
    print(f"   Skipped:             {aggregate['overall_skipped']} [SKIP]")
    print(f"   Overall Pass Rate:   {aggregate['overall_pass_rate']}")
    print(f"   Total Time:          {total_time:.2f}ms")
    print("=" * 80)

    print("\n   SUITE BREAKDOWN:")
    print("-" * 80)
    for suite in aggregate["suites"]:
        status = "[OK]" if suite["failed"] == 0 and suite.get("errors", 0) == 0 else "[!!]"
        print(f"   {status} {suite['suite_name']}: {suite['passed']}/{suite['tests']} ({suite['pass_rate']})")

    if aggregate["failed_tests"]:
        print("\n   FAILED TESTS:")
        print("-" * 80)
        for ft in aggregate["failed_tests"][:15]:  # Show first 15
            print(f"   [X] {ft['suite']} :: {ft['test_name']}")
            if ft.get('error'):
                print(f"       {ft['error'][:80]}...")

    print("=" * 80)
    print(f"   Completed: {datetime.now().isoformat()}")
    print("=" * 80 + "\n")

    # Return exit code
    return 0 if (aggregate['overall_failed'] == 0 and aggregate['overall_errors'] == 0) else 1


def list_suites():
    """List all available test suites"""
    print("\nAvailable Test Suites:")
    print("-" * 50)
    for name, cls in ALL_TEST_SUITES:
        suite = cls()
        test_count = len(suite.get_test_cases())
        print(f"  {name:20} ({test_count} tests) - {suite.suite_name}")
    print()


def main():
    """CLI entry point"""
    parser = argparse.ArgumentParser(
        description="FX-MS API Test Runner",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python tests/run_all_tests.py              # Run all tests
  python tests/run_all_tests.py --list       # List available suites
  python tests/run_all_tests.py -s routing   # Run routing tests only
  python tests/run_all_tests.py -s routing pricing deals  # Run multiple suites
        """
    )
    parser.add_argument(
        "--suite", "-s",
        help="Run specific suite(s) by name",
        nargs="+",
        metavar="NAME"
    )
    parser.add_argument(
        "--list", "-l",
        action="store_true",
        help="List available test suites"
    )

    args = parser.parse_args()

    if args.list:
        list_suites()
        return 0

    return asyncio.run(run_all_tests(args.suite))


if __name__ == "__main__":
    sys.exit(main())
