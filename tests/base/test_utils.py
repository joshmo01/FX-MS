"""
Test Utilities for FX-MS API Tests
"""
import json
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Any


def ensure_results_dir() -> Path:
    """Ensure test_results directory exists"""
    # Get the project root (where tests/ is located)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    results_dir = project_root / "test_results"
    results_dir.mkdir(exist_ok=True)
    return results_dir


def save_results(suite_result: Dict[str, Any], filename: str = None) -> Path:
    """Save test results to JSON file"""
    results_dir = ensure_results_dir()

    if filename is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        suite_name = suite_result.get("suite_name", "test").replace(" ", "_").lower()
        filename = f"{suite_name}_{timestamp}.json"

    filepath = results_dir / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(suite_result, f, indent=2, default=str)

    print(f"\n   Results saved to: {filepath}")
    return filepath


def print_summary(suite_result: Dict[str, Any]):
    """Print test summary to console"""
    print(f"\n{'='*70}")
    print(f"   TEST SUMMARY: {suite_result['suite_name']}")
    print(f"{'='*70}")
    print(f"   Total Tests:    {suite_result['total_tests']}")
    print(f"   Passed:         {suite_result['passed']} [PASS]")
    print(f"   Failed:         {suite_result['failed']} [FAIL]")
    print(f"   Errors:         {suite_result['errors']} [ERR]")
    print(f"   Skipped:        {suite_result['skipped']} [SKIP]")
    print(f"   Pass Rate:      {suite_result['pass_rate']}")
    print(f"   Execution Time: {suite_result['total_execution_time_ms']:.2f}ms")
    print(f"{'='*70}")


def generate_test_id(prefix: str, number: int) -> str:
    """Generate standardized test ID"""
    return f"{prefix}-{number:03d}"


def load_results(filepath: str) -> Dict[str, Any]:
    """Load test results from JSON file"""
    with open(filepath, "r", encoding="utf-8") as f:
        return json.load(f)


def get_latest_results(suite_name: str = None) -> Path:
    """Get path to the latest results file for a suite"""
    results_dir = ensure_results_dir()

    if suite_name:
        pattern = f"{suite_name.replace(' ', '_').lower()}_*.json"
    else:
        pattern = "*.json"

    files = list(results_dir.glob(pattern))
    if not files:
        return None

    return max(files, key=lambda f: f.stat().st_mtime)


def print_failed_tests(suite_result: Dict[str, Any]):
    """Print details of failed tests"""
    failed = [r for r in suite_result.get("results", [])
              if r.get("status") in ["FAILED", "ERROR"]]

    if not failed:
        print("\n   No failed tests!")
        return

    print(f"\n   FAILED TESTS ({len(failed)}):")
    print("-" * 70)

    for test in failed:
        print(f"\n   [{test['status']}] {test['test_id']}: {test['test_name']}")
        print(f"         Endpoint: {test['method']} {test['endpoint']}")
        print(f"         HTTP Status: {test['http_status']}")
        if test.get('error_message'):
            print(f"         Error: {test['error_message'][:200]}")


def create_aggregate_report(suite_results: list) -> Dict[str, Any]:
    """Create aggregate report from multiple suite results"""
    total_tests = sum(r.get("total_tests", 0) for r in suite_results)
    total_passed = sum(r.get("passed", 0) for r in suite_results)
    total_failed = sum(r.get("failed", 0) for r in suite_results)
    total_errors = sum(r.get("errors", 0) for r in suite_results)
    total_skipped = sum(r.get("skipped", 0) for r in suite_results)

    failed_tests = []
    for result in suite_results:
        for test_result in result.get("results", []):
            if test_result.get("status") in ["FAILED", "ERROR"]:
                failed_tests.append({
                    "suite": result.get("suite_name"),
                    "test_id": test_result.get("test_id"),
                    "test_name": test_result.get("test_name"),
                    "error": test_result.get("error_message", "")[:200]
                })

    return {
        "report_timestamp": datetime.utcnow().isoformat(),
        "total_suites": len(suite_results),
        "total_tests": total_tests,
        "overall_passed": total_passed,
        "overall_failed": total_failed,
        "overall_errors": total_errors,
        "overall_skipped": total_skipped,
        "overall_pass_rate": f"{(total_passed/total_tests*100):.1f}%" if total_tests > 0 else "0%",
        "suites": [
            {
                "suite_name": r.get("suite_name"),
                "tests": r.get("total_tests"),
                "passed": r.get("passed"),
                "failed": r.get("failed"),
                "errors": r.get("errors"),
                "pass_rate": r.get("pass_rate")
            }
            for r in suite_results
        ],
        "failed_tests": failed_tests
    }
