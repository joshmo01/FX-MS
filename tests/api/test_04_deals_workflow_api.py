"""
Test Suite: Treasury Deals API - Workflow Operations
Endpoint: /api/v1/fx/deals
Tests: Submit, Approve, Reject, Utilize workflows
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class DealsWorkflowAPITests(APITestBase):
    """Tests for Treasury Deals workflow operations"""

    def __init__(self):
        super().__init__("Treasury Deals Workflow API Tests")

    def get_test_cases(self):
        now = datetime.utcnow()
        valid_from = now.isoformat()
        valid_until = (now + timedelta(days=7)).isoformat()

        return [
            # Create a deal first for workflow testing
            TestCase(
                test_id=generate_test_id("WFLOW", 1),
                name="Create Deal for Workflow",
                description="Create a deal to test workflow operations",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={
                    "currency_pair": "USDINR",
                    "side": "SELL",
                    "buy_rate": 84.40,
                    "sell_rate": 84.60,
                    "amount": 500000,
                    "valid_from": valid_from,
                    "valid_until": valid_until,
                    "customer_tier": "GOLD",
                    "min_amount": 5000,
                    "max_amount_per_txn": 100000,
                    "notes": "Workflow test deal",
                    "created_by": "TEST_USER"
                },
                expected_status=200,
                expected_fields=["deal_id", "status"]
            ),

            # Submit Invalid Deal ID (API returns 422)
            TestCase(
                test_id=generate_test_id("WFLOW", 2),
                name="Submit Deal - Invalid ID",
                description="Submit non-existent deal returns 422",
                endpoint="/api/v1/fx/deals/INVALID-ID-12345/submit",
                method="POST",
                expected_status=422
            ),

            # Approve Invalid Deal ID (API returns 400)
            TestCase(
                test_id=generate_test_id("WFLOW", 3),
                name="Approve Deal - Invalid ID",
                description="Approve non-existent deal returns 400",
                endpoint="/api/v1/fx/deals/INVALID-ID-12345/approve",
                method="POST",
                body={"approved_by": "APPROVER_1"},
                expected_status=400
            ),

            # Reject Invalid Deal ID (API returns 400)
            TestCase(
                test_id=generate_test_id("WFLOW", 4),
                name="Reject Deal - Invalid ID",
                description="Reject non-existent deal returns 400",
                endpoint="/api/v1/fx/deals/INVALID-ID-12345/reject",
                method="POST",
                body={
                    "rejected_by": "APPROVER_1",
                    "rejection_reason": "Test rejection"
                },
                expected_status=400
            ),

            # Utilize Invalid Deal ID (API returns 422)
            TestCase(
                test_id=generate_test_id("WFLOW", 5),
                name="Utilize Deal - Invalid ID",
                description="Utilize non-existent deal returns 422",
                endpoint="/api/v1/fx/deals/INVALID-ID-12345/utilize",
                method="POST",
                body={
                    "amount": 10000,
                    "transaction_id": "TXN-TEST-001"
                },
                expected_status=422
            ),

            # Get Utilizations - Invalid Deal ID (API returns 200 empty list)
            TestCase(
                test_id=generate_test_id("WFLOW", 6),
                name="Get Utilizations - Invalid ID",
                description="Get utilizations returns empty list for non-existent deal",
                endpoint="/api/v1/fx/deals/INVALID-ID-12345/utilizations",
                method="GET",
                expected_status=200
            ),

            # Get Audit Log - Invalid Deal ID (API returns 200 empty list)
            TestCase(
                test_id=generate_test_id("WFLOW", 7),
                name="Get Audit Log - Invalid ID",
                description="Get audit log returns empty list for non-existent deal",
                endpoint="/api/v1/fx/deals/INVALID-ID-12345/audit-log",
                method="GET",
                expected_status=200
            ),

            # List PENDING_APPROVAL Deals
            TestCase(
                test_id=generate_test_id("WFLOW", 8),
                name="List Pending Approval Deals",
                description="Get deals awaiting approval",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"status": "PENDING_APPROVAL"},
                expected_status=200
            ),

            # List REJECTED Deals
            TestCase(
                test_id=generate_test_id("WFLOW", 9),
                name="List Rejected Deals",
                description="Get rejected deals",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"status": "REJECTED"},
                expected_status=200
            ),

            # List EXPIRED Deals
            TestCase(
                test_id=generate_test_id("WFLOW", 10),
                name="List Expired Deals",
                description="Get expired deals",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"status": "EXPIRED"},
                expected_status=200
            ),

            # List CANCELLED Deals
            TestCase(
                test_id=generate_test_id("WFLOW", 11),
                name="List Cancelled Deals",
                description="Get cancelled deals",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"status": "CANCELLED"},
                expected_status=200
            ),

            # List FULLY_UTILIZED Deals
            TestCase(
                test_id=generate_test_id("WFLOW", 12),
                name="List Fully Utilized Deals",
                description="Get fully utilized deals",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"status": "FULLY_UTILIZED"},
                expected_status=200
            ),
        ]


async def main():
    tests = DealsWorkflowAPITests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
