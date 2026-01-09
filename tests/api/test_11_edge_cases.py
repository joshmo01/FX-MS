"""
Test Suite: Edge Cases
Boundary values, large amounts, special characters, limits
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class EdgeCaseTests(APITestBase):
    """Edge case tests for boundary conditions"""

    def __init__(self):
        super().__init__("Edge Case Tests")

    def get_test_cases(self):
        now = datetime.utcnow()
        valid_from = now.isoformat()
        valid_until = (now + timedelta(days=7)).isoformat()

        return [
            # Very Large Amount - Route
            TestCase(
                test_id=generate_test_id("EDGE", 1),
                name="Route - Very Large Amount",
                description="Test routing with 100 million USD",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={"source": "USD", "target": "INR", "amount": 100000000},
                expected_status=200
            ),

            # Very Small Amount
            TestCase(
                test_id=generate_test_id("EDGE", 2),
                name="Route - Very Small Amount",
                description="Test with 1 USD",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={"source": "USD", "target": "INR", "amount": 1},
                expected_status=200
            ),

            # Decimal Precision
            TestCase(
                test_id=generate_test_id("EDGE", 3),
                name="Quote - Decimal Precision",
                description="Test with precise decimal amount",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "USD",
                    "target_currency": "INR",
                    "amount": 12345.67,
                    "customer_id": "TEST-EDGE-001",
                    "segment": "RETAIL",
                    "direction": "SELL"
                },
                expected_status=200
            ),

            # Special Characters in Notes
            TestCase(
                test_id=generate_test_id("EDGE", 4),
                name="Create Deal - Special Characters",
                description="Notes with special characters",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={
                    "currency_pair": "USDINR",
                    "side": "SELL",
                    "buy_rate": 84.40,
                    "sell_rate": 84.60,
                    "amount": 100000,
                    "valid_from": valid_from,
                    "valid_until": valid_until,
                    "customer_tier": "GOLD",
                    "notes": "Test: @#$%^&*()[]{}",
                    "created_by": "TEST_USER"
                },
                expected_status=200
            ),

            # Max Pagination (API validates page_size, returns 422 for excessive values)
            TestCase(
                test_id=generate_test_id("EDGE", 5),
                name="List Deals - Large Page Size Validation",
                description="Request with excessive page size returns 422",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"page": 1, "page_size": 1000},
                expected_status=422
            ),

            # High Page Number
            TestCase(
                test_id=generate_test_id("EDGE", 6),
                name="List Deals - High Page Number",
                description="Request page beyond data range",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"page": 99999, "page_size": 10},
                expected_status=200
            ),

            # Very High Rate
            TestCase(
                test_id=generate_test_id("EDGE", 7),
                name="Create Deal - High Rate",
                description="Deal with high rate value",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={
                    "currency_pair": "USDINR",
                    "side": "SELL",
                    "buy_rate": 999.99,
                    "sell_rate": 1000.00,
                    "amount": 100000,
                    "valid_from": valid_from,
                    "valid_until": valid_until,
                    "customer_tier": "GOLD",
                    "created_by": "TEST_USER"
                },
                expected_status=200
            ),

            # Quick Route Lookups
            TestCase(
                test_id=generate_test_id("EDGE", 8),
                name="Route - CBDC to CBDC",
                description="mBridge eligible CBDC pair",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={"source": "e-CNY", "target": "e-THB", "amount": 100000},
                expected_status=200
            ),

            # Empty String Filters
            TestCase(
                test_id=generate_test_id("EDGE", 9),
                name="List Rules - No Filter",
                description="List rules without filter",
                endpoint="/api/v1/fx/rules/",
                method="GET",
                expected_status=200
            ),

            # Large Corporate Quote
            TestCase(
                test_id=generate_test_id("EDGE", 10),
                name="Quote - Very Large Amount",
                description="Institutional size quote",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "USD",
                    "target_currency": "INR",
                    "amount": 50000000,
                    "customer_id": "INST-EDGE-001",
                    "segment": "INSTITUTIONAL",
                    "direction": "SELL"
                },
                expected_status=200
            ),
        ]


async def main():
    tests = EdgeCaseTests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
