"""
Test Suite: FX Pricing API
Endpoint: /api/v1/fx/pricing
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class PricingAPITests(APITestBase):
    """Tests for FX Pricing API endpoints"""

    def __init__(self):
        super().__init__("FX Pricing API Tests")

    def get_test_cases(self):
        return [
            # Health Check
            TestCase(
                test_id=generate_test_id("PRICE", 1),
                name="Pricing Health Check",
                description="Verify pricing service is healthy",
                endpoint="/api/v1/fx/pricing/health",
                method="GET",
                expected_status=200,
                expected_fields=["status"]
            ),

            # Segments
            TestCase(
                test_id=generate_test_id("PRICE", 2),
                name="Get All Segments",
                description="Retrieve all customer pricing segments",
                endpoint="/api/v1/fx/pricing/segments",
                method="GET",
                expected_status=200
            ),

            # Tiers
            TestCase(
                test_id=generate_test_id("PRICE", 3),
                name="Get All Tiers",
                description="Retrieve amount-based pricing tiers",
                endpoint="/api/v1/fx/pricing/tiers",
                method="GET",
                expected_status=200
            ),

            # Categories
            TestCase(
                test_id=generate_test_id("PRICE", 4),
                name="Get Currency Categories",
                description="Retrieve currency category definitions",
                endpoint="/api/v1/fx/pricing/categories",
                method="GET",
                expected_status=200
            ),

            # Quote - Retail USD to INR
            TestCase(
                test_id=generate_test_id("PRICE", 5),
                name="Get Quote - Retail USD to INR",
                description="Standard retail quote for USD/INR",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "USD",
                    "target_currency": "INR",
                    "amount": 10000,
                    "customer_id": "CUST-TEST-001",
                    "segment": "RETAIL",
                    "direction": "SELL"
                },
                expected_status=200
            ),

            # Quote - Mid Market
            TestCase(
                test_id=generate_test_id("PRICE", 6),
                name="Get Quote - Mid Market EUR to INR",
                description="Mid-market quote for EUR/INR",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "EUR",
                    "target_currency": "INR",
                    "amount": 100000,
                    "customer_id": "CUST-TEST-002",
                    "segment": "MID_MARKET",
                    "direction": "SELL"
                },
                expected_status=200
            ),

            # Quote - Large Corporate
            TestCase(
                test_id=generate_test_id("PRICE", 7),
                name="Get Quote - Large Corporate",
                description="Large corporate quote with volume discount",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "USD",
                    "target_currency": "INR",
                    "amount": 1000000,
                    "customer_id": "CORP-TEST-001",
                    "segment": "LARGE_CORPORATE",
                    "direction": "SELL"
                },
                expected_status=200
            ),

            # Quote - Institutional
            TestCase(
                test_id=generate_test_id("PRICE", 8),
                name="Get Quote - Institutional",
                description="Institutional quote for large amount",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "EUR",
                    "target_currency": "INR",
                    "amount": 5000000,
                    "customer_id": "INST-TEST-001",
                    "segment": "INSTITUTIONAL",
                    "direction": "SELL"
                },
                expected_status=200
            ),

            # Quote with Negotiated Discount
            TestCase(
                test_id=generate_test_id("PRICE", 9),
                name="Get Quote - With Negotiated Discount",
                description="Quote with pre-negotiated discount",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "USD",
                    "target_currency": "INR",
                    "amount": 500000,
                    "customer_id": "CORP-PREM-001",
                    "segment": "LARGE_CORPORATE",
                    "direction": "SELL",
                    "negotiated_discount_bps": 10
                },
                expected_status=200
            ),

            # Margin Info - USD/INR
            TestCase(
                test_id=generate_test_id("PRICE", 10),
                name="Get Margin Info - USD/INR",
                description="Get margin breakdown for USD/INR",
                endpoint="/api/v1/fx/pricing/margin/USD/INR",
                method="GET",
                params={"segment": "MID_MARKET", "amount": 100000},
                expected_status=200
            ),

            # Margin Info - EUR/INR
            TestCase(
                test_id=generate_test_id("PRICE", 11),
                name="Get Margin Info - EUR/INR",
                description="Get margin breakdown for EUR/INR",
                endpoint="/api/v1/fx/pricing/margin/EUR/INR",
                method="GET",
                params={"segment": "RETAIL", "amount": 50000},
                expected_status=200
            ),

            # Quote - BUY Direction
            TestCase(
                test_id=generate_test_id("PRICE", 12),
                name="Get Quote - BUY Direction",
                description="Quote for BUY direction",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "INR",
                    "target_currency": "USD",
                    "amount": 500000,
                    "customer_id": "CUST-TEST-003",
                    "segment": "MID_MARKET",
                    "direction": "BUY"
                },
                expected_status=200
            ),
        ]


async def main():
    tests = PricingAPITests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
