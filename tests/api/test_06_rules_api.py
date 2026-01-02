"""
Test Suite: Rules Management API
Endpoint: /api/v1/fx/rules
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class RulesAPITests(APITestBase):
    """Tests for Rules Management API endpoints"""

    def __init__(self):
        super().__init__("Rules Management API Tests")

    def get_test_cases(self):
        return [
            # Health Check
            TestCase(
                test_id=generate_test_id("RULES", 1),
                name="Rules Health Check",
                description="Verify rules engine is healthy",
                endpoint="/api/v1/fx/rules/health",
                method="GET",
                expected_status=200,
                expected_fields=["status"]
            ),

            # List All Rules (with trailing slash)
            TestCase(
                test_id=generate_test_id("RULES", 2),
                name="List All Rules",
                description="Retrieve all rules without filters",
                endpoint="/api/v1/fx/rules/",
                method="GET",
                expected_status=200
            ),

            # List Rules - Filter by Type (PROVIDER_SELECTION)
            TestCase(
                test_id=generate_test_id("RULES", 3),
                name="List Rules - Provider Selection Rules",
                description="Get provider selection rules",
                endpoint="/api/v1/fx/rules/",
                method="GET",
                params={"rule_type": "PROVIDER_SELECTION"},
                expected_status=200
            ),

            # List Rules - Filter by Margin Rules
            TestCase(
                test_id=generate_test_id("RULES", 4),
                name="List Rules - Margin Rules",
                description="Get margin adjustment rules",
                endpoint="/api/v1/fx/rules/",
                method="GET",
                params={"rule_type": "MARGIN_ADJUSTMENT"},
                expected_status=200
            ),

            # List Rules - Enabled Only
            TestCase(
                test_id=generate_test_id("RULES", 5),
                name="List Rules - Enabled Only",
                description="Get only enabled rules",
                endpoint="/api/v1/fx/rules/",
                method="GET",
                params={"enabled": True},
                expected_status=200
            ),

            # Create Rule - Invalid body schema returns 422
            # Note: Rule schema requires rule_id, rule_name, valid_from, conditions (with operator/criteria), actions, metadata
            TestCase(
                test_id=generate_test_id("RULES", 6),
                name="Create Rule - Schema Validation",
                description="Create rule with simplified body returns 422 (missing required fields)",
                endpoint="/api/v1/fx/rules/",
                method="POST",
                body={
                    "name": "Test Provider Score Rule",
                    "description": "Test rule for API testing",
                    "rule_type": "PROVIDER_SELECTION",
                    "priority": 100,
                    "enabled": True,
                    "conditions": {
                        "provider_id": {"eq": "BANK_A"}
                    },
                    "actions": {
                        "score_adjustment": 5
                    }
                },
                expected_status=422
            ),

            # Create Rule - Margin Adjustment (schema validation)
            TestCase(
                test_id=generate_test_id("RULES", 7),
                name="Create Rule - Margin Schema Validation",
                description="Create margin rule with simplified body returns 422",
                endpoint="/api/v1/fx/rules/",
                method="POST",
                body={
                    "name": "Test Margin Rule",
                    "description": "Margin rule for API testing",
                    "rule_type": "MARGIN_ADJUSTMENT",
                    "priority": 50,
                    "enabled": True,
                    "conditions": {
                        "segment": {"eq": "RETAIL"},
                        "amount": {"gte": 100000}
                    },
                    "actions": {
                        "margin_adjustment_bps": -5
                    }
                },
                expected_status=422
            ),

            # Validate Rule - Schema validation
            TestCase(
                test_id=generate_test_id("RULES", 8),
                name="Validate Rule - Schema Validation",
                description="Validate rule with simplified body returns 422",
                endpoint="/api/v1/fx/rules/validate",
                method="POST",
                body={
                    "name": "Validation Test Rule",
                    "rule_type": "PROVIDER_SELECTION",
                    "priority": 10,
                    "conditions": {
                        "currency_pair": {"eq": "USDINR"}
                    },
                    "actions": {
                        "score_adjustment": 10
                    }
                },
                expected_status=422
            ),

            # Reload Rules
            TestCase(
                test_id=generate_test_id("RULES", 9),
                name="Reload Rules",
                description="Force reload rules from configuration",
                endpoint="/api/v1/fx/rules/reload",
                method="POST",
                expected_status=200
            ),

            # Get Recent Audit
            TestCase(
                test_id=generate_test_id("RULES", 10),
                name="Get Recent Audit Logs",
                description="Get recent rule execution audit logs",
                endpoint="/api/v1/fx/rules/audit/recent",
                method="GET",
                expected_status=200
            ),

            # Get Rule - Invalid ID
            TestCase(
                test_id=generate_test_id("RULES", 11),
                name="Get Rule - Invalid ID",
                description="Get non-existent rule",
                endpoint="/api/v1/fx/rules/INVALID-RULE-ID",
                method="GET",
                expected_status=404
            ),

            # Delete Rule - Invalid ID
            TestCase(
                test_id=generate_test_id("RULES", 12),
                name="Delete Rule - Invalid ID",
                description="Delete non-existent rule",
                endpoint="/api/v1/fx/rules/INVALID-RULE-ID",
                method="DELETE",
                expected_status=404
            ),

            # Toggle Rule - Invalid ID
            TestCase(
                test_id=generate_test_id("RULES", 13),
                name="Toggle Rule - Invalid ID",
                description="Toggle non-existent rule",
                endpoint="/api/v1/fx/rules/INVALID-RULE-ID/toggle",
                method="POST",
                expected_status=404
            ),
        ]


async def main():
    tests = RulesAPITests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
