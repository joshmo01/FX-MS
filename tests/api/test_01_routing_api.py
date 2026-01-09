"""
Test Suite: Smart Routing API
Endpoint: /api/v1/fx/routing
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class RoutingAPITests(APITestBase):
    """Tests for Smart Routing API endpoints"""

    def __init__(self):
        super().__init__("Smart Routing API Tests")

    def get_test_cases(self):
        return [
            # Treasury Rates
            TestCase(
                test_id=generate_test_id("ROUTE", 1),
                name="Get All Treasury Rates",
                description="Retrieve all treasury rates",
                endpoint="/api/v1/fx/routing/treasury-rates",
                method="GET",
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("ROUTE", 2),
                name="Get Treasury Rate - USDINR",
                description="Get specific treasury rate for USDINR",
                endpoint="/api/v1/fx/routing/treasury-rates/USDINR",
                method="GET",
                expected_status=200
            ),

            # Customer Tiers
            TestCase(
                test_id=generate_test_id("ROUTE", 3),
                name="Get All Customer Tiers",
                description="Retrieve all customer tier configurations",
                endpoint="/api/v1/fx/routing/customer-tiers",
                method="GET",
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("ROUTE", 4),
                name="Get Customer Tier - PLATINUM",
                description="Get PLATINUM tier details",
                endpoint="/api/v1/fx/routing/customer-tiers/PLATINUM",
                method="GET",
                expected_status=200
            ),

            # Providers
            TestCase(
                test_id=generate_test_id("ROUTE", 5),
                name="Get All Providers",
                description="Retrieve all FX providers",
                endpoint="/api/v1/fx/routing/providers",
                method="GET",
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("ROUTE", 6),
                name="Get Provider - BANK_A",
                description="Get specific provider details",
                endpoint="/api/v1/fx/routing/providers/BANK_A",
                method="GET",
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("ROUTE", 7),
                name="Get Provider Score",
                description="Get provider score with objective",
                endpoint="/api/v1/fx/routing/providers/BANK_A/score",
                method="GET",
                params={"objective": "OPTIMUM"},
                expected_status=200
            ),

            # Effective Rate
            TestCase(
                test_id=generate_test_id("ROUTE", 8),
                name="Get Effective Rate - USDINR BUY",
                description="Calculate effective rate for USDINR BUY",
                endpoint="/api/v1/fx/routing/effective-rate/USDINR",
                method="GET",
                params={"side": "BUY", "amount": 100000, "customer_tier": "GOLD"},
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("ROUTE", 9),
                name="Get Effective Rate - USDINR SELL",
                description="Calculate effective rate for USDINR SELL",
                endpoint="/api/v1/fx/routing/effective-rate/USDINR",
                method="GET",
                params={"side": "SELL", "amount": 50000, "customer_tier": "RETAIL"},
                expected_status=200
            ),

            # Route Recommendation
            TestCase(
                test_id=generate_test_id("ROUTE", 10),
                name="Recommend Route - Basic",
                description="Get route recommendation with default params",
                endpoint="/api/v1/fx/routing/recommend",
                method="POST",
                params={
                    "pair": "USDINR",
                    "amount": 100000,
                    "side": "SELL",
                    "customer_tier": "GOLD",
                    "objective": "OPTIMUM"
                },
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("ROUTE", 11),
                name="Recommend Route - Large Amount",
                description="Get route for large institutional amount",
                endpoint="/api/v1/fx/routing/recommend",
                method="POST",
                params={
                    "pair": "USDINR",
                    "amount": 10000000,
                    "side": "BUY",
                    "customer_tier": "PLATINUM",
                    "objective": "CHEAPEST"
                },
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("ROUTE", 12),
                name="Recommend Route - FASTEST Objective",
                description="Get fastest route recommendation",
                endpoint="/api/v1/fx/routing/recommend",
                method="POST",
                params={
                    "pair": "EURINR",
                    "amount": 50000,
                    "side": "SELL",
                    "customer_tier": "RETAIL",
                    "objective": "FASTEST"
                },
                expected_status=200
            ),

            # Routing Objectives
            TestCase(
                test_id=generate_test_id("ROUTE", 13),
                name="Get Routing Objectives",
                description="Retrieve available routing objectives",
                endpoint="/api/v1/fx/routing/objectives",
                method="GET",
                expected_status=200
            ),

            # Additional Route Tests
            TestCase(
                test_id=generate_test_id("ROUTE", 14),
                name="Recommend Route - GBP to INR",
                description="Get route recommendation for GBP to INR",
                endpoint="/api/v1/fx/routing/recommend",
                method="POST",
                params={
                    "pair": "GBPINR",
                    "amount": 25000,
                    "side": "BUY",
                    "customer_tier": "GOLD",
                    "objective": "OPTIMUM"
                },
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("ROUTE", 15),
                name="Recommend Route - SAFEST Objective",
                description="Get safest route recommendation",
                endpoint="/api/v1/fx/routing/recommend",
                method="POST",
                params={
                    "pair": "USDINR",
                    "amount": 500000,
                    "side": "SELL",
                    "customer_tier": "INSTITUTIONAL",
                    "objective": "SAFEST"
                },
                expected_status=200
            ),
        ]


async def main():
    tests = RoutingAPITests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
