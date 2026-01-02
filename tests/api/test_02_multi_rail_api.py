"""
Test Suite: Multi-Rail API
Endpoint: /api/v1/fx/multi-rail
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class MultiRailAPITests(APITestBase):
    """Tests for Multi-Rail API endpoints"""

    def __init__(self):
        super().__init__("Multi-Rail API Tests")

    def get_test_cases(self):
        return [
            # CBDCs
            TestCase(
                test_id=generate_test_id("MRAIL", 1),
                name="Get All CBDCs",
                description="Retrieve all available CBDCs",
                endpoint="/api/v1/fx/multi-rail/cbdc",
                method="GET",
                expected_status=200,
                expected_fields=["cbdc", "count"]
            ),

            # Stablecoins
            TestCase(
                test_id=generate_test_id("MRAIL", 2),
                name="Get All Stablecoins",
                description="Retrieve all available stablecoins",
                endpoint="/api/v1/fx/multi-rail/stablecoins",
                method="GET",
                expected_status=200,
                expected_fields=["stablecoins", "count"]
            ),

            # Conversion Types
            TestCase(
                test_id=generate_test_id("MRAIL", 3),
                name="Get Conversion Types",
                description="Retrieve all conversion types",
                endpoint="/api/v1/fx/multi-rail/conversion-types",
                method="GET",
                expected_status=200,
                expected_fields=["conversion_types", "count"]
            ),

            # Atomic Swaps
            TestCase(
                test_id=generate_test_id("MRAIL", 4),
                name="Get Atomic Swaps",
                description="Retrieve atomic swap information",
                endpoint="/api/v1/fx/multi-rail/atomic-swaps",
                method="GET",
                expected_status=200,
                expected_fields=["atomic_swaps", "protocol"]
            ),

            # Rails
            TestCase(
                test_id=generate_test_id("MRAIL", 5),
                name="Get All Rails",
                description="Retrieve all available payment/settlement rails",
                endpoint="/api/v1/fx/multi-rail/rails",
                method="GET",
                expected_status=200,
                expected_fields=["rails"]
            ),

            # Route Calculation - Fiat to Fiat (uses query params)
            TestCase(
                test_id=generate_test_id("MRAIL", 6),
                name="Route - Fiat to Fiat (USD-INR)",
                description="Calculate multi-rail route for fiat conversion",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={
                    "source": "USD",
                    "target": "INR",
                    "amount": 100000
                },
                expected_status=200,
                expected_fields=["source", "target", "conversion_type", "routes"]
            ),

            # Route Calculation - Fiat to CBDC
            TestCase(
                test_id=generate_test_id("MRAIL", 7),
                name="Route - Fiat to CBDC",
                description="Calculate route from fiat to CBDC",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={
                    "source": "USD",
                    "target": "e-CNY",
                    "amount": 50000
                },
                expected_status=200,
                expected_fields=["source", "target", "conversion_type"]
            ),

            # Route Calculation - CBDC to CBDC
            TestCase(
                test_id=generate_test_id("MRAIL", 8),
                name="Route - CBDC to CBDC (mBridge)",
                description="Calculate route for CBDC to CBDC via mBridge",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={
                    "source": "e-CNY",
                    "target": "e-HKD",
                    "amount": 100000
                },
                expected_status=200,
                expected_fields=["conversion_type", "routes"]
            ),

            # Route Calculation - Fiat to Stablecoin
            TestCase(
                test_id=generate_test_id("MRAIL", 9),
                name="Route - Fiat to Stablecoin",
                description="Calculate route from fiat to stablecoin",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={
                    "source": "USD",
                    "target": "USDC",
                    "amount": 25000
                },
                expected_status=200
            ),

            # Route Calculation - Stablecoin to Stablecoin
            TestCase(
                test_id=generate_test_id("MRAIL", 10),
                name="Route - Stablecoin to Stablecoin",
                description="Calculate route for stablecoin swap",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={
                    "source": "USDT",
                    "target": "USDC",
                    "amount": 50000
                },
                expected_status=200
            ),

            # Route Calculation - CBDC to Stablecoin
            TestCase(
                test_id=generate_test_id("MRAIL", 11),
                name="Route - CBDC to Stablecoin",
                description="Calculate route for CBDC to stablecoin",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={
                    "source": "e-INR",
                    "target": "USDC",
                    "amount": 100000
                },
                expected_status=200
            ),

            # Route Calculation - Large Amount
            TestCase(
                test_id=generate_test_id("MRAIL", 12),
                name="Route - Large Institutional Amount",
                description="Calculate route for large amount",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={
                    "source": "EUR",
                    "target": "INR",
                    "amount": 5000000
                },
                expected_status=200
            ),
        ]


async def main():
    tests = MultiRailAPITests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
