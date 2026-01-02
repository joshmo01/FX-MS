"""
Test Suite: Negative Tests
Invalid inputs, error handling, 400/404/422 responses
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class NegativeTests(APITestBase):
    """Negative test cases for error handling validation"""

    def __init__(self):
        super().__init__("Negative Tests")

    def get_test_cases(self):
        return [
            # Invalid Endpoints
            TestCase(
                test_id=generate_test_id("NEG", 1),
                name="Invalid Endpoint - 404",
                description="Request to non-existent endpoint",
                endpoint="/api/v1/fx/nonexistent",
                method="GET",
                expected_status=404
            ),

            # Invalid Deal ID
            TestCase(
                test_id=generate_test_id("NEG", 2),
                name="Get Deal - Invalid ID",
                description="Get deal with non-existent ID",
                endpoint="/api/v1/fx/deals/INVALID-DEAL-ID-12345",
                method="GET",
                expected_status=404
            ),

            # Empty POST Body for Deal
            TestCase(
                test_id=generate_test_id("NEG", 3),
                name="Create Deal - Empty Body",
                description="Create deal with empty request body",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={},
                expected_status=422
            ),

            # Missing Required Field
            TestCase(
                test_id=generate_test_id("NEG", 4),
                name="Create Deal - Missing Currency Pair",
                description="Create deal without currency_pair",
                endpoint="/api/v1/fx/deals",
                method="POST",
                body={
                    "side": "SELL",
                    "buy_rate": 84.40,
                    "sell_rate": 84.60,
                    "amount": 1000000,
                    "created_by": "TEST"
                },
                expected_status=422
            ),

            # Invalid Rule ID
            TestCase(
                test_id=generate_test_id("NEG", 5),
                name="Get Rule - Non-existent ID",
                description="Get rule with non-existent ID",
                endpoint="/api/v1/fx/rules/non-existent-rule-id",
                method="GET",
                expected_status=404
            ),

            # Delete Rule - Invalid ID
            TestCase(
                test_id=generate_test_id("NEG", 6),
                name="Delete Rule - Invalid ID",
                description="Delete non-existent rule",
                endpoint="/api/v1/fx/rules/INVALID-RULE-ID",
                method="DELETE",
                expected_status=404
            ),

            # Invalid Method
            TestCase(
                test_id=generate_test_id("NEG", 7),
                name="Health - Invalid Method (DELETE)",
                description="DELETE to GET-only endpoint",
                endpoint="/api/v1/fx/health",
                method="DELETE",
                expected_status=405
            ),

            # Update Non-existent Deal (API returns 422)
            TestCase(
                test_id=generate_test_id("NEG", 8),
                name="Update Deal - Non-existent ID",
                description="Update deal that doesn't exist returns 422",
                endpoint="/api/v1/fx/deals/NON-EXISTENT-DEAL-ID",
                method="PUT",
                body={"notes": "Updated notes"},
                expected_status=422
            ),

            # Submit Non-existent Deal (API returns 422)
            TestCase(
                test_id=generate_test_id("NEG", 9),
                name="Submit Deal - Invalid ID",
                description="Submit non-existent deal returns 422",
                endpoint="/api/v1/fx/deals/INVALID-ID-12345/submit",
                method="POST",
                expected_status=422
            ),

            # Approve Non-existent Deal (API returns 400)
            TestCase(
                test_id=generate_test_id("NEG", 10),
                name="Approve Deal - Invalid ID",
                description="Approve non-existent deal returns 400",
                endpoint="/api/v1/fx/deals/INVALID-ID-12345/approve",
                method="POST",
                body={"approved_by": "APPROVER_1"},
                expected_status=400
            ),

            # Toggle Rule - Invalid ID
            TestCase(
                test_id=generate_test_id("NEG", 11),
                name="Toggle Rule - Invalid ID",
                description="Toggle non-existent rule",
                endpoint="/api/v1/fx/rules/INVALID-RULE-ID/toggle",
                method="POST",
                expected_status=404
            ),

            # Empty Rule Body
            TestCase(
                test_id=generate_test_id("NEG", 12),
                name="Create Rule - Empty Body",
                description="Create rule with empty body",
                endpoint="/api/v1/fx/rules/",
                method="POST",
                body={},
                expected_status=422
            ),
        ]


async def main():
    tests = NegativeTests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
