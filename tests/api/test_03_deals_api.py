"""
Test Suite: Treasury Deals API - CRUD Operations
Endpoint: /api/v1/fx/deals
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class DealsAPITests(APITestBase):
    """Tests for Treasury Deals CRUD operations"""

    def __init__(self):
        super().__init__("Treasury Deals API Tests")

    def get_test_cases(self):
        now = datetime.utcnow()
        valid_from = now.isoformat()
        valid_until = (now + timedelta(days=7)).isoformat()

        return [
            # List Deals
            TestCase(
                test_id=generate_test_id("DEAL", 1),
                name="List All Deals",
                description="Get all deals without filters",
                endpoint="/api/v1/fx/deals",
                method="GET",
                expected_status=200,
                expected_fields=["deals", "total", "page", "page_size"]
            ),

            # List Deals with Status Filter
            TestCase(
                test_id=generate_test_id("DEAL", 2),
                name="List Deals - Filter by ACTIVE Status",
                description="Get deals filtered by ACTIVE status",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"status": "ACTIVE"},
                expected_status=200,
                expected_fields=["deals", "total"]
            ),

            # List Deals with DRAFT Status
            TestCase(
                test_id=generate_test_id("DEAL", 3),
                name="List Deals - Filter by DRAFT Status",
                description="Get deals filtered by DRAFT status",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"status": "DRAFT"},
                expected_status=200
            ),

            # List Deals with Currency Pair Filter
            TestCase(
                test_id=generate_test_id("DEAL", 4),
                name="List Deals - Filter by Currency Pair",
                description="Get deals for USDINR",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"currency_pair": "USDINR"},
                expected_status=200
            ),

            # List Deals - Pagination
            TestCase(
                test_id=generate_test_id("DEAL", 5),
                name="List Deals - Pagination",
                description="Test pagination parameters",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"page": 1, "page_size": 5},
                expected_status=200
            ),

            # Create Deal - Valid
            TestCase(
                test_id=generate_test_id("DEAL", 6),
                name="Create Deal - Valid USDINR",
                description="Create a new deal in DRAFT status",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={
                    "currency_pair": "USDINR",
                    "side": "SELL",
                    "buy_rate": 84.40,
                    "sell_rate": 84.60,
                    "amount": 1000000,
                    "valid_from": valid_from,
                    "valid_until": valid_until,
                    "customer_tier": "GOLD",
                    "min_amount": 10000,
                    "max_amount_per_txn": 500000,
                    "notes": "Test deal from API test suite",
                    "created_by": "TEST_USER"
                },
                expected_status=200,
                expected_fields=["deal_id", "currency_pair", "status"]
            ),

            # Create Deal - EURINR
            TestCase(
                test_id=generate_test_id("DEAL", 7),
                name="Create Deal - Valid EURINR",
                description="Create a new EUR/INR deal",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={
                    "currency_pair": "EURINR",
                    "side": "BUY",
                    "buy_rate": 91.20,
                    "sell_rate": 91.50,
                    "amount": 500000,
                    "valid_from": valid_from,
                    "valid_until": valid_until,
                    "customer_tier": "PLATINUM",
                    "min_amount": 5000,
                    "max_amount_per_txn": 250000,
                    "notes": "EUR deal test",
                    "created_by": "TEST_USER"
                },
                expected_status=200
            ),

            # Get Active Deals
            TestCase(
                test_id=generate_test_id("DEAL", 8),
                name="Get Active Deals - USDINR",
                description="Get active deals for USDINR pair",
                endpoint="/api/v1/fx/deals/active",
                method="GET",
                params={"currency_pair": "USDINR"},
                expected_status=200
            ),

            # Get Active Deals - EURINR
            TestCase(
                test_id=generate_test_id("DEAL", 9),
                name="Get Active Deals - EURINR",
                description="Get active deals for EURINR pair",
                endpoint="/api/v1/fx/deals/active",
                method="GET",
                params={"currency_pair": "EURINR"},
                expected_status=200
            ),

            # Best Rate - SELL
            TestCase(
                test_id=generate_test_id("DEAL", 10),
                name="Get Best Rate - USDINR SELL",
                description="Get best available rate for SELL",
                endpoint="/api/v1/fx/deals/best-rate",
                method="GET",
                params={
                    "currency_pair": "USDINR",
                    "side": "SELL",
                    "amount": 50000,
                    "customer_tier": "GOLD",
                    "treasury_rate": 84.50
                },
                expected_status=200
            ),

            # Best Rate - BUY
            TestCase(
                test_id=generate_test_id("DEAL", 11),
                name="Get Best Rate - USDINR BUY",
                description="Get best available rate for BUY",
                endpoint="/api/v1/fx/deals/best-rate",
                method="GET",
                params={
                    "currency_pair": "USDINR",
                    "side": "BUY",
                    "amount": 100000,
                    "customer_tier": "PLATINUM",
                    "treasury_rate": 84.45
                },
                expected_status=200
            ),

            # Create Deal - Missing Required Field
            TestCase(
                test_id=generate_test_id("DEAL", 12),
                name="Create Deal - Missing Currency Pair",
                description="Should fail validation",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={
                    "side": "SELL",
                    "buy_rate": 84.40,
                    "sell_rate": 84.60,
                    "amount": 1000000,
                    "valid_from": valid_from,
                    "valid_until": valid_until,
                    "created_by": "TEST_USER"
                },
                expected_status=422
            ),

            # Create Deal - Negative Amount
            TestCase(
                test_id=generate_test_id("DEAL", 13),
                name="Create Deal - Negative Amount",
                description="Should fail with negative amount",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={
                    "currency_pair": "USDINR",
                    "side": "SELL",
                    "buy_rate": 84.40,
                    "sell_rate": 84.60,
                    "amount": -1000,
                    "valid_from": valid_from,
                    "valid_until": valid_until,
                    "created_by": "TEST_USER"
                },
                expected_status=422
            ),

            # Get Deal - Invalid ID
            TestCase(
                test_id=generate_test_id("DEAL", 14),
                name="Get Deal - Invalid ID",
                description="Get deal with non-existent ID",
                endpoint="/api/v1/fx/deals/INVALID-DEAL-ID-12345",
                method="GET",
                expected_status=404
            ),

            # Delete Deal - Invalid ID (API returns 422 for non-existent IDs)
            TestCase(
                test_id=generate_test_id("DEAL", 15),
                name="Delete Deal - Invalid ID",
                description="Delete deal with non-existent ID (returns 422)",
                endpoint="/api/v1/fx/deals/INVALID-DEAL-ID-12345",
                method="DELETE",
                expected_status=422
            ),
        ]


async def main():
    tests = DealsAPITests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
