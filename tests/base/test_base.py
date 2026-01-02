"""
Base Test Infrastructure for FX-MS API Tests
"""
import asyncio
import json
import time
from dataclasses import dataclass, asdict, field
from datetime import datetime
from typing import List, Dict, Any, Optional, Callable
from enum import Enum
import httpx


class TestStatus(str, Enum):
    PASSED = "PASSED"
    FAILED = "FAILED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


@dataclass
class TestCase:
    """Test case definition"""
    test_id: str
    name: str
    description: str
    endpoint: str
    method: str = "GET"
    params: Dict[str, Any] = field(default_factory=dict)
    body: Dict[str, Any] = field(default_factory=dict)
    headers: Dict[str, str] = field(default_factory=dict)
    expected_status: int = 200
    expected_fields: List[str] = field(default_factory=list)
    validation_func: Optional[Callable] = None
    tags: List[str] = field(default_factory=list)


@dataclass
class TestResult:
    """Test result"""
    test_id: str
    test_name: str
    status: TestStatus
    endpoint: str
    method: str
    http_status: int
    execution_time_ms: float
    response_size_bytes: int = 0
    error_message: str = ""
    response_data: Dict[str, Any] = field(default_factory=dict)
    assertions_passed: int = 0
    assertions_failed: int = 0
    timestamp: str = field(default_factory=lambda: datetime.utcnow().isoformat())


@dataclass
class TestSuiteResult:
    """Results for entire test suite"""
    suite_name: str
    timestamp: str
    total_tests: int
    passed: int
    failed: int
    skipped: int
    errors: int
    total_execution_time_ms: float
    pass_rate: str
    results: List[Dict[str, Any]] = field(default_factory=list)
    environment: Dict[str, str] = field(default_factory=dict)


class APITestBase:
    """Base class for all API test suites"""

    BASE_URL = "http://localhost:8000"
    TIMEOUT = 30.0

    def __init__(self, suite_name: str = "FX-MS API Tests"):
        self.suite_name = suite_name
        self.results: List[TestResult] = []
        self.client: Optional[httpx.AsyncClient] = None

    async def setup(self):
        """Initialize HTTP client"""
        self.client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            timeout=self.TIMEOUT
        )
        print(f"\n{'='*70}")
        print(f"   {self.suite_name}")
        print(f"   Started: {datetime.now().isoformat()}")
        print(f"   Target: {self.BASE_URL}")
        print(f"{'='*70}")

    async def teardown(self):
        """Cleanup HTTP client"""
        if self.client:
            await self.client.aclose()

    async def run_test(self, test_case: TestCase) -> TestResult:
        """Execute a single test case"""
        start_time = time.time()

        try:
            # Build request kwargs
            kwargs = {
                "params": test_case.params if test_case.params else None,
                "headers": test_case.headers if test_case.headers else None
            }
            if test_case.method.upper() in ["POST", "PUT", "PATCH"]:
                kwargs["json"] = test_case.body

            # Remove None values
            kwargs = {k: v for k, v in kwargs.items() if v is not None}

            # Execute request
            response = await getattr(self.client, test_case.method.lower())(
                test_case.endpoint, **kwargs
            )

            execution_time = (time.time() - start_time) * 1000
            response_data = {}

            try:
                response_data = response.json()
            except:
                response_data = {"raw": response.text[:500] if response.text else ""}

            # Validate response
            status = TestStatus.PASSED
            error_message = ""
            assertions_passed = 0
            assertions_failed = 0

            # Check HTTP status
            if response.status_code != test_case.expected_status:
                status = TestStatus.FAILED
                error_message = f"Expected status {test_case.expected_status}, got {response.status_code}"
                assertions_failed += 1
            else:
                assertions_passed += 1

            # Check expected fields (only for successful responses)
            if status == TestStatus.PASSED and test_case.expected_fields:
                for field_name in test_case.expected_fields:
                    # Handle nested fields with dot notation
                    if "." in field_name:
                        parts = field_name.split(".")
                        value = response_data
                        found = True
                        for part in parts:
                            if isinstance(value, dict) and part in value:
                                value = value[part]
                            else:
                                found = False
                                break
                        if found:
                            assertions_passed += 1
                        else:
                            assertions_failed += 1
                            status = TestStatus.FAILED
                            error_message += f"\nMissing field: {field_name}"
                    else:
                        if field_name in response_data:
                            assertions_passed += 1
                        else:
                            assertions_failed += 1
                            status = TestStatus.FAILED
                            error_message += f"\nMissing field: {field_name}"

            # Run custom validation if provided
            if status == TestStatus.PASSED and test_case.validation_func:
                try:
                    validation_result = test_case.validation_func(response_data)
                    if validation_result is not True:
                        status = TestStatus.FAILED
                        error_message = f"Custom validation failed: {validation_result}"
                        assertions_failed += 1
                    else:
                        assertions_passed += 1
                except Exception as e:
                    status = TestStatus.FAILED
                    error_message = f"Validation error: {str(e)}"
                    assertions_failed += 1

            return TestResult(
                test_id=test_case.test_id,
                test_name=test_case.name,
                status=status,
                endpoint=test_case.endpoint,
                method=test_case.method,
                http_status=response.status_code,
                execution_time_ms=round(execution_time, 2),
                response_size_bytes=len(response.content),
                error_message=error_message.strip(),
                response_data=response_data,
                assertions_passed=assertions_passed,
                assertions_failed=assertions_failed
            )

        except httpx.ConnectError as e:
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                test_id=test_case.test_id,
                test_name=test_case.name,
                status=TestStatus.ERROR,
                endpoint=test_case.endpoint,
                method=test_case.method,
                http_status=0,
                execution_time_ms=round(execution_time, 2),
                error_message=f"Connection error: Server not running at {self.BASE_URL}"
            )
        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return TestResult(
                test_id=test_case.test_id,
                test_name=test_case.name,
                status=TestStatus.ERROR,
                endpoint=test_case.endpoint,
                method=test_case.method,
                http_status=0,
                execution_time_ms=round(execution_time, 2),
                error_message=str(e)
            )

    def get_test_cases(self) -> List[TestCase]:
        """Override in subclass to define test cases"""
        raise NotImplementedError("Subclass must implement get_test_cases()")

    async def run_all_tests(self) -> TestSuiteResult:
        """Run all test cases in the suite"""
        await self.setup()

        test_cases = self.get_test_cases()
        print(f"\n   Running {len(test_cases)} tests...\n")

        total_start = time.time()

        for test_case in test_cases:
            result = await self.run_test(test_case)
            self.results.append(result)

            # Print result
            status_indicators = {
                TestStatus.PASSED: "[PASS]",
                TestStatus.FAILED: "[FAIL]",
                TestStatus.SKIPPED: "[SKIP]",
                TestStatus.ERROR: "[ERR ]"
            }

            status_str = status_indicators.get(result.status, "[????]")
            print(f"  {status_str} {result.test_name}")
            print(f"         {result.method} {result.endpoint} -> {result.http_status} ({result.execution_time_ms}ms)")

            if result.error_message:
                # Truncate long error messages
                error_display = result.error_message[:100]
                if len(result.error_message) > 100:
                    error_display += "..."
                print(f"         Error: {error_display}")
            print()

        total_time = (time.time() - total_start) * 1000
        await self.teardown()

        # Build summary
        passed = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        skipped = sum(1 for r in self.results if r.status == TestStatus.SKIPPED)
        errors = sum(1 for r in self.results if r.status == TestStatus.ERROR)
        total = len(self.results)

        return TestSuiteResult(
            suite_name=self.suite_name,
            timestamp=datetime.utcnow().isoformat(),
            total_tests=total,
            passed=passed,
            failed=failed,
            skipped=skipped,
            errors=errors,
            total_execution_time_ms=round(total_time, 2),
            pass_rate=f"{(passed/total*100):.1f}%" if total > 0 else "0%",
            results=[asdict(r) for r in self.results],
            environment={
                "base_url": self.BASE_URL,
                "timeout": str(self.TIMEOUT)
            }
        )
