"""
Test Suite: Health Endpoints
All service health check endpoints
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tests.base.test_base import APITestBase, TestCase
from tests.base.test_utils import save_results, print_summary, generate_test_id


class HealthAPITests(APITestBase):
    """Tests for all health check endpoints"""

    def __init__(self):
        super().__init__("Health Endpoints Tests")

    def get_test_cases(self):
        return [
            # Root Health
            TestCase(
                test_id=generate_test_id("HEALTH", 1),
                name="Root Endpoint",
                description="Check root endpoint returns service info",
                endpoint="/",
                method="GET",
                expected_status=200,
                expected_fields=["service", "version"]
            ),

            # Main FX Health
            TestCase(
                test_id=generate_test_id("HEALTH", 2),
                name="FX Service Health",
                description="Main FX service health check",
                endpoint="/api/v1/fx/health",
                method="GET",
                expected_status=200,
                expected_fields=["status"]
            ),

            # Pricing Health
            TestCase(
                test_id=generate_test_id("HEALTH", 3),
                name="Pricing Service Health",
                description="Pricing service health",
                endpoint="/api/v1/fx/pricing/health",
                method="GET",
                expected_status=200,
                expected_fields=["status"]
            ),

            # Rules Health
            TestCase(
                test_id=generate_test_id("HEALTH", 4),
                name="Rules Engine Health",
                description="Rules engine service health",
                endpoint="/api/v1/fx/rules/health",
                method="GET",
                expected_status=200,
                expected_fields=["status"]
            ),

            # Universal Health - API NOT REGISTERED
            TestCase(
                test_id=generate_test_id("HEALTH", 5),
                name="Universal Service Health (NOT REGISTERED)",
                description="Universal API not registered - expects 404",
                endpoint="/api/v1/fx/universal/health",
                method="GET",
                expected_status=404
            ),

            # Bridge Health - API NOT REGISTERED
            TestCase(
                test_id=generate_test_id("HEALTH", 6),
                name="Bridge Service Health (NOT REGISTERED)",
                description="Bridge API not registered - expects 404",
                endpoint="/api/v1/fx/bridge/health",
                method="GET",
                expected_status=404
            ),
        ]


async def main():
    tests = HealthAPITests()
    suite_result = await tests.run_all_tests()

    print_summary(suite_result.__dict__)
    save_results(suite_result.__dict__)

    return 0 if suite_result.failed == 0 and suite_result.errors == 0 else 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
