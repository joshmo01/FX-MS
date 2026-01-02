"""
Test Suite: Integration Tests
End-to-end flows spanning multiple APIs
"""
import asyncio
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class IntegrationTests(APITestBase):
    """Integration tests for cross-API workflows"""

    def __init__(self):
        super().__init__("Integration Tests")

    def get_test_cases(self):
        now = datetime.utcnow()
        valid_from = now.isoformat()
        valid_until = (now + timedelta(days=7)).isoformat()

        return [
            # Flow 1: Check health across all services
            TestCase(
                test_id=generate_test_id("INTG", 1),
                name="Health Check Flow - Main Service",
                description="Verify main FX service is healthy",
                endpoint="/api/v1/fx/health",
                method="GET",
                expected_status=200,
                expected_fields=["status"]
            ),
            TestCase(
                test_id=generate_test_id("INTG", 2),
                name="Health Check Flow - Pricing",
                description="Verify pricing service is healthy",
                endpoint="/api/v1/fx/pricing/health",
                method="GET",
                expected_status=200,
                expected_fields=["status"]
            ),
            TestCase(
                test_id=generate_test_id("INTG", 3),
                name="Health Check Flow - Rules",
                description="Verify rules service is healthy",
                endpoint="/api/v1/fx/rules/health",
                method="GET",
                expected_status=200,
                expected_fields=["status"]
            ),

            # Flow 2: Pricing quote then routing
            TestCase(
                test_id=generate_test_id("INTG", 4),
                name="Quote-Route Flow - Get Quote",
                description="Get pricing quote for USD-INR",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "USD",
                    "target_currency": "INR",
                    "amount": 100000,
                    "customer_id": "INTG-TEST-001",
                    "segment": "LARGE_CORPORATE",
                    "direction": "SELL"
                },
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("INTG", 5),
                name="Quote-Route Flow - Get Route",
                description="Get optimal route for same conversion",
                endpoint="/api/v1/fx/routing/recommend",
                method="POST",
                params={
                    "pair": "USDINR",
                    "amount": 100000,
                    "side": "SELL",
                    "customer_tier": "LARGE_CORPORATE",
                    "objective": "OPTIMUM"
                },
                expected_status=200
            ),

            # Flow 3: Deal lifecycle
            TestCase(
                test_id=generate_test_id("INTG", 6),
                name="Deal Lifecycle - Create",
                description="Create a new deal",
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
                    "notes": "Integration test deal",
                    "created_by": "INTG_TEST"
                },
                expected_status=200,
                expected_fields=["deal_id"]
            ),
            TestCase(
                test_id=generate_test_id("INTG", 7),
                name="Deal Lifecycle - List",
                description="List deals to verify creation",
                endpoint="/api/v1/fx/deals",
                method="GET",
                params={"status": "DRAFT"},
                expected_status=200,
                expected_fields=["deals", "total"]
            ),

            # Flow 4: Multi-rail exploration
            TestCase(
                test_id=generate_test_id("INTG", 8),
                name="Multi-Rail Flow - Get CBDCs",
                description="List available CBDCs",
                endpoint="/api/v1/fx/multi-rail/cbdc",
                method="GET",
                expected_status=200,
                expected_fields=["cbdc", "count"]
            ),
            TestCase(
                test_id=generate_test_id("INTG", 9),
                name="Multi-Rail Flow - Get Stablecoins",
                description="List available stablecoins",
                endpoint="/api/v1/fx/multi-rail/stablecoins",
                method="GET",
                expected_status=200,
                expected_fields=["stablecoins", "count"]
            ),
            TestCase(
                test_id=generate_test_id("INTG", 10),
                name="Multi-Rail Flow - Calculate Route",
                description="Calculate multi-rail route",
                endpoint="/api/v1/fx/multi-rail/route",
                method="POST",
                params={"source": "USD", "target": "INR", "amount": 100000},
                expected_status=200,
                expected_fields=["source", "target", "routes"]
            ),

            # Flow 5: Rules and pricing integration
            TestCase(
                test_id=generate_test_id("INTG", 11),
                name="Rules-Pricing Flow - List Rules",
                description="List pricing rules",
                endpoint="/api/v1/fx/rules/",
                method="GET",
                params={"rule_type": "MARGIN_ADJUSTMENT"},
                expected_status=200
            ),
            TestCase(
                test_id=generate_test_id("INTG", 12),
                name="Rules-Pricing Flow - Get Quote",
                description="Get quote (rules applied automatically)",
                endpoint="/api/v1/fx/pricing/quote",
                method="POST",
                body={
                    "source_currency": "EUR",
                    "target_currency": "INR",
                    "amount": 250000,
                    "customer_id": "INTG-RULES-001",
                    "segment": "MID_MARKET",
                    "direction": "SELL"
                },
                expected_status=200
            ),
        ]


async def main():
    tests = IntegrationTests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
