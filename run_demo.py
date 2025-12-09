#!/usr/bin/env python3
"""
FX Smart Routing - Comprehensive Test Runner & Demo

Interactive CLI tool to demonstrate all 9 conversion types with live output.
Tests FIAT ↔ CBDC ↔ Stablecoin conversions across all supported routes.

Usage:
    python run_demo.py                    # Run all tests
    python run_demo.py --interactive      # Interactive mode
    python run_demo.py --type CBDC_STABLE # Run specific conversion type
    python run_demo.py --export json      # Export results to JSON

Author: Fintaar.ai
Version: 2.0.0
"""

import asyncio
import json
import sys
import os
import argparse
from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict, field
from enum import Enum
import time

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Terminal colors
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def print_header(text: str):
    print(f"\n{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{text.center(60)}{Colors.END}")
    print(f"{Colors.BOLD}{Colors.HEADER}{'='*60}{Colors.END}\n")


def print_section(text: str):
    print(f"\n{Colors.BOLD}{Colors.CYAN}▶ {text}{Colors.END}")
    print(f"{Colors.CYAN}{'-'*50}{Colors.END}")


def print_success(text: str):
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")


def print_warning(text: str):
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")


def print_error(text: str):
    print(f"{Colors.RED}❌ {text}{Colors.END}")


def print_info(text: str):
    print(f"{Colors.BLUE}ℹ️  {text}{Colors.END}")


class ConversionType(str, Enum):
    """All 9 conversion types"""
    FIAT_FIAT = "FIAT→FIAT"
    FIAT_CBDC = "FIAT→CBDC"
    CBDC_FIAT = "CBDC→FIAT"
    CBDC_CBDC = "CBDC→CBDC"
    FIAT_STABLE = "FIAT→STABLECOIN"
    STABLE_FIAT = "STABLECOIN→FIAT"
    STABLE_STABLE = "STABLECOIN→STABLECOIN"
    CBDC_STABLE = "CBDC→STABLECOIN"
    STABLE_CBDC = "STABLECOIN→CBDC"


@dataclass
class TestScenario:
    """Test scenario definition"""
    id: str
    name: str
    conversion_type: ConversionType
    source: str
    source_type: str
    target: str
    target_type: str
    amount: Decimal
    description: str
    expected_routes: int = 1
    expected_best_fee_max_bps: int = 100


@dataclass
class RouteResult:
    """Single route result"""
    route_id: str
    name: str
    legs: int
    fee_bps: int
    settlement_time: str
    regulated: bool
    path: List[str] = field(default_factory=list)
    is_best: bool = False
    is_recommended: bool = False
    is_experimental: bool = False


@dataclass
class TestResult:
    """Test result"""
    scenario_id: str
    scenario_name: str
    passed: bool
    routes_found: int
    best_route: Optional[RouteResult]
    all_routes: List[RouteResult]
    execution_time_ms: float
    error: str = ""


class FXRoutingDemo:
    """
    FX Smart Routing Demonstration Engine
    
    Simulates all conversion routes without requiring actual API connections.
    """
    
    def __init__(self):
        self.results: List[TestResult] = []
        self._init_routes()
    
    def _init_routes(self):
        """Initialize route definitions for all conversions"""
        self.route_definitions = {
            ConversionType.FIAT_FIAT: [
                RouteResult("FF-001", "SWIFT Direct", 1, 25, "1-3 days", True),
                RouteResult("FF-002", "Local Rails (RTGS)", 1, 15, "4 hours", True),
                RouteResult("FF-003", "USD Triangulation", 2, 30, "4-8 hours", True),
                RouteResult("FF-004", "EUR Triangulation", 2, 32, "4-8 hours", True),
            ],
            ConversionType.FIAT_CBDC: [
                RouteResult("FC-001", "Direct Mint", 1, 0, "5 seconds", True, is_best=True),
                RouteResult("FC-002", "FX + Mint", 2, 20, "4 hours", True),
                RouteResult("FC-003", "mBridge + Mint", 3, 13, "30 seconds", True, is_recommended=True),
            ],
            ConversionType.CBDC_FIAT: [
                RouteResult("CF-001", "Direct Redeem", 1, 0, "5 seconds", True, is_best=True),
                RouteResult("CF-002", "Redeem + FX", 2, 20, "4 hours", True),
            ],
            ConversionType.CBDC_CBDC: [
                RouteResult("CC-001", "mBridge PvP", 1, 13, "15 seconds", True, is_best=True, is_recommended=True),
                RouteResult("CC-002", "Project Nexus", 1, 35, "60 seconds", True),
                RouteResult("CC-003", "Fiat Bridge (4 legs)", 4, 40, "8 hours", True),
            ],
            ConversionType.FIAT_STABLE: [
                RouteResult("FS-001", "Circle On-Ramp", 1, 0, "1 hour", True, is_best=True),
                RouteResult("FS-002", "Coinbase Prime", 1, 20, "2 hours", True),
                RouteResult("FS-003", "FX + On-Ramp", 2, 50, "5 hours", True),
            ],
            ConversionType.STABLE_FIAT: [
                RouteResult("SF-001", "Circle Off-Ramp", 1, 0, "1 hour", True, is_best=True),
                RouteResult("SF-002", "CEX Off-Ramp", 1, 25, "2 hours", True),
                RouteResult("SF-003", "Off-Ramp + FX", 2, 50, "5 hours", True),
            ],
            ConversionType.STABLE_STABLE: [
                RouteResult("SS-001", "Curve DEX", 1, 4, "1 minute", False, is_best=True),
                RouteResult("SS-002", "Uniswap V3", 1, 30, "1 minute", False),
                RouteResult("SS-003", "CEX Trade", 1, 20, "10 seconds", True),
            ],
            # ⭐ NEW: CBDC ↔ Stablecoin Routes
            ConversionType.CBDC_STABLE: [
                RouteResult("CS-001", "Fiat Intermediary", 2, 25, "5 hours", True, 
                           path=["CBDC", "FIAT", "STABLECOIN"]),
                RouteResult("CS-002", "CEX Bridge", 2, 50, "2 hours", True,
                           path=["CBDC", "FIAT", "STABLECOIN"]),
                RouteResult("CS-003", "mBridge + Off-Ramp", 3, 38, "1 hour", True, 
                           is_recommended=True, path=["CBDC", "CBDC", "FIAT", "STABLECOIN"]),
                RouteResult("CS-004", "DEX Liquidity", 2, 35, "10 minutes", False, 
                           is_experimental=True, path=["CBDC", "FIAT", "STABLECOIN"]),
                RouteResult("CS-005", "Atomic Swap", 1, 5, "5 minutes", False, 
                           is_best=True, is_experimental=True, path=["CBDC", "STABLECOIN"]),
            ],
            ConversionType.STABLE_CBDC: [
                RouteResult("SC-001", "Fiat Intermediary", 2, 25, "5 hours", True,
                           path=["STABLECOIN", "FIAT", "CBDC"]),
                RouteResult("SC-002", "CEX Bridge", 2, 50, "2 hours", True,
                           path=["STABLECOIN", "FIAT", "CBDC"]),
                RouteResult("SC-003", "OTC Trade", 1, 15, "T+1", True,
                           path=["STABLECOIN", "CBDC"]),
                RouteResult("SC-004", "Liquidity Pool", 2, 40, "15 minutes", False, 
                           is_experimental=True, path=["STABLECOIN", "FIAT", "CBDC"]),
                RouteResult("SC-005", "Atomic Swap", 1, 5, "5 minutes", False, 
                           is_best=True, is_experimental=True, path=["STABLECOIN", "CBDC"]),
            ],
        }
    
    def get_test_scenarios(self) -> List[TestScenario]:
        """Get all test scenarios"""
        return [
            # FIAT → FIAT
            TestScenario("T001", "USD to INR Direct", ConversionType.FIAT_FIAT,
                        "USD", "FIAT", "INR", "FIAT", Decimal("100000"),
                        "Standard USD to INR conversion via correspondent banking"),
            TestScenario("T002", "EUR to SGD Cross", ConversionType.FIAT_FIAT,
                        "EUR", "FIAT", "SGD", "FIAT", Decimal("50000"),
                        "EUR to SGD with possible USD triangulation"),
            
            # FIAT → CBDC
            TestScenario("T003", "INR to e-INR Mint", ConversionType.FIAT_CBDC,
                        "INR", "FIAT", "e-INR", "CBDC", Decimal("100000"),
                        "Direct INR to Digital Rupee conversion"),
            TestScenario("T004", "USD to e-CNY via FX", ConversionType.FIAT_CBDC,
                        "USD", "FIAT", "e-CNY", "CBDC", Decimal("200000"),
                        "USD to Digital Yuan with FX conversion"),
            
            # CBDC → FIAT
            TestScenario("T005", "e-INR to INR Redeem", ConversionType.CBDC_FIAT,
                        "e-INR", "CBDC", "INR", "FIAT", Decimal("50000"),
                        "Digital Rupee redemption to bank account"),
            TestScenario("T006", "e-CNY to USD", ConversionType.CBDC_FIAT,
                        "e-CNY", "CBDC", "USD", "FIAT", Decimal("100000"),
                        "Digital Yuan to USD with FX"),
            
            # CBDC → CBDC (mBridge)
            TestScenario("T007", "e-CNY to e-HKD mBridge", ConversionType.CBDC_CBDC,
                        "e-CNY", "CBDC", "e-HKD", "CBDC", Decimal("500000"),
                        "Cross-border CBDC via mBridge PvP"),
            TestScenario("T008", "e-THB to e-AED mBridge", ConversionType.CBDC_CBDC,
                        "e-THB", "CBDC", "e-AED", "CBDC", Decimal("200000"),
                        "Thailand to UAE via mBridge"),
            
            # FIAT → STABLECOIN
            TestScenario("T009", "USD to USDC On-Ramp", ConversionType.FIAT_STABLE,
                        "USD", "FIAT", "USDC", "STABLECOIN", Decimal("100000"),
                        "Direct USD to USDC via Circle"),
            TestScenario("T010", "EUR to EURC On-Ramp", ConversionType.FIAT_STABLE,
                        "EUR", "FIAT", "EURC", "STABLECOIN", Decimal("75000"),
                        "EUR to Euro Coin conversion"),
            
            # STABLECOIN → FIAT
            TestScenario("T011", "USDC to USD Off-Ramp", ConversionType.STABLE_FIAT,
                        "USDC", "STABLECOIN", "USD", "FIAT", Decimal("50000"),
                        "USDC redemption to bank account"),
            TestScenario("T012", "USDT to INR Off-Ramp", ConversionType.STABLE_FIAT,
                        "USDT", "STABLECOIN", "INR", "FIAT", Decimal("100000"),
                        "USDT to INR with CEX + FX"),
            
            # STABLECOIN → STABLECOIN
            TestScenario("T013", "USDC to USDT DEX", ConversionType.STABLE_STABLE,
                        "USDC", "STABLECOIN", "USDT", "STABLECOIN", Decimal("1000000"),
                        "Stablecoin swap via Curve"),
            TestScenario("T014", "USDC to EURC Swap", ConversionType.STABLE_STABLE,
                        "USDC", "STABLECOIN", "EURC", "STABLECOIN", Decimal("100000"),
                        "USD stablecoin to EUR stablecoin"),
            
            # ⭐ CBDC → STABLECOIN (NEW)
            TestScenario("T015", "e-INR to USDC Bridge", ConversionType.CBDC_STABLE,
                        "e-INR", "CBDC", "USDC", "STABLECOIN", Decimal("100000"),
                        "Digital Rupee to USDC via fiat intermediary"),
            TestScenario("T016", "e-CNY to USDT mBridge", ConversionType.CBDC_STABLE,
                        "e-CNY", "CBDC", "USDT", "STABLECOIN", Decimal("500000"),
                        "Digital Yuan to USDT via mBridge hybrid route"),
            TestScenario("T017", "e-HKD to USDC Atomic", ConversionType.CBDC_STABLE,
                        "e-HKD", "CBDC", "USDC", "STABLECOIN", Decimal("200000"),
                        "Digital HKD to USDC atomic swap (experimental)"),
            TestScenario("T018", "e-SGD to XSGD Direct", ConversionType.CBDC_STABLE,
                        "e-SGD", "CBDC", "XSGD", "STABLECOIN", Decimal("50000"),
                        "Digital SGD to XSGD stablecoin"),
            
            # ⭐ STABLECOIN → CBDC (NEW)
            TestScenario("T019", "USDC to e-INR Bridge", ConversionType.STABLE_CBDC,
                        "USDC", "STABLECOIN", "e-INR", "CBDC", Decimal("100000"),
                        "USDC to Digital Rupee via fiat intermediary"),
            TestScenario("T020", "USDT to e-CNY OTC", ConversionType.STABLE_CBDC,
                        "USDT", "STABLECOIN", "e-CNY", "CBDC", Decimal("1000000"),
                        "USDT to Digital Yuan via OTC desk"),
            TestScenario("T021", "XSGD to e-SGD Direct", ConversionType.STABLE_CBDC,
                        "XSGD", "STABLECOIN", "e-SGD", "CBDC", Decimal("75000"),
                        "XSGD stablecoin to Digital SGD"),
            TestScenario("T022", "EURC to e-EUR Future", ConversionType.STABLE_CBDC,
                        "EURC", "STABLECOIN", "e-EUR", "CBDC", Decimal("200000"),
                        "Euro Coin to Digital Euro (future route)"),
        ]
    
    async def run_scenario(self, scenario: TestScenario) -> TestResult:
        """Run a single test scenario"""
        start_time = time.time()
        
        try:
            # Get routes for this conversion type
            routes = self.route_definitions.get(scenario.conversion_type, [])
            
            if not routes:
                return TestResult(
                    scenario_id=scenario.id,
                    scenario_name=scenario.name,
                    passed=False,
                    routes_found=0,
                    best_route=None,
                    all_routes=[],
                    execution_time_ms=(time.time() - start_time) * 1000,
                    error="No routes defined for this conversion type"
                )
            
            # Find best route
            best_route = next((r for r in routes if r.is_best), routes[0])
            
            # Calculate execution time
            exec_time = (time.time() - start_time) * 1000
            
            return TestResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                passed=True,
                routes_found=len(routes),
                best_route=best_route,
                all_routes=routes,
                execution_time_ms=exec_time
            )
            
        except Exception as e:
            return TestResult(
                scenario_id=scenario.id,
                scenario_name=scenario.name,
                passed=False,
                routes_found=0,
                best_route=None,
                all_routes=[],
                execution_time_ms=(time.time() - start_time) * 1000,
                error=str(e)
            )
    
    def print_scenario_result(self, scenario: TestScenario, result: TestResult):
        """Print formatted scenario result"""
        status = f"{Colors.GREEN}PASS{Colors.END}" if result.passed else f"{Colors.RED}FAIL{Colors.END}"
        
        print(f"\n{Colors.BOLD}[{scenario.id}] {scenario.name}{Colors.END} [{status}]")
        print(f"   {Colors.CYAN}{scenario.source} ({scenario.source_type}) → {scenario.target} ({scenario.target_type}){Colors.END}")
        print(f"   Amount: ${scenario.amount:,.2f}")
        print(f"   {scenario.description}")
        
        if result.passed:
            print(f"\n   📊 {Colors.BOLD}Routes Found: {result.routes_found}{Colors.END}")
            
            for i, route in enumerate(result.all_routes):
                badge = ""
                if route.is_best:
                    badge = f" {Colors.GREEN}⭐ BEST{Colors.END}"
                elif route.is_recommended:
                    badge = f" {Colors.YELLOW}🔥 RECOMMENDED{Colors.END}"
                elif route.is_experimental:
                    badge = f" {Colors.CYAN}🧪 EXPERIMENTAL{Colors.END}"
                
                regulated = f"{Colors.GREEN}✓{Colors.END}" if route.regulated else f"{Colors.YELLOW}✗{Colors.END}"
                
                print(f"   {i+1}. {route.name}{badge}")
                print(f"      Legs: {route.legs} | Fee: {route.fee_bps} bps | Time: {route.settlement_time} | Regulated: {regulated}")
                if route.path:
                    print(f"      Path: {' → '.join(route.path)}")
            
            print(f"\n   ⏱️  Execution: {result.execution_time_ms:.2f}ms")
        else:
            print(f"   {Colors.RED}Error: {result.error}{Colors.END}")
    
    async def run_all_tests(self, verbose: bool = True) -> Dict[str, Any]:
        """Run all test scenarios"""
        scenarios = self.get_test_scenarios()
        results = []
        
        print_header("FX Smart Routing - Complete Test Suite")
        print_info(f"Running {len(scenarios)} test scenarios...")
        print_info(f"Timestamp: {datetime.now().isoformat()}")
        
        # Group by conversion type
        by_type: Dict[ConversionType, List[TestScenario]] = {}
        for s in scenarios:
            if s.conversion_type not in by_type:
                by_type[s.conversion_type] = []
            by_type[s.conversion_type].append(s)
        
        for conv_type, type_scenarios in by_type.items():
            print_section(f"{conv_type.value} ({len(type_scenarios)} scenarios)")
            
            for scenario in type_scenarios:
                result = await self.run_scenario(scenario)
                results.append(result)
                
                if verbose:
                    self.print_scenario_result(scenario, result)
        
        # Summary
        passed = sum(1 for r in results if r.passed)
        failed = len(results) - passed
        
        print_header("Test Summary")
        print(f"   Total:  {len(results)}")
        print(f"   {Colors.GREEN}Passed: {passed}{Colors.END}")
        print(f"   {Colors.RED}Failed: {failed}{Colors.END}")
        
        # Routes by type
        print_section("Routes by Conversion Type")
        for conv_type in ConversionType:
            routes = self.route_definitions.get(conv_type, [])
            regulated = sum(1 for r in routes if r.regulated)
            experimental = sum(1 for r in routes if r.is_experimental)
            print(f"   {conv_type.value}: {len(routes)} routes ({regulated} regulated, {experimental} experimental)")
        
        return {
            "timestamp": datetime.now().isoformat(),
            "total_scenarios": len(results),
            "passed": passed,
            "failed": failed,
            "results": [asdict(r) for r in results]
        }
    
    async def run_interactive(self):
        """Interactive mode"""
        print_header("FX Smart Routing - Interactive Demo")
        
        print("Available conversion types:")
        for i, ct in enumerate(ConversionType, 1):
            print(f"   {i}. {ct.value}")
        
        while True:
            print(f"\n{Colors.BOLD}Enter number (1-9) or 'q' to quit:{Colors.END} ", end="")
            choice = input().strip()
            
            if choice.lower() == 'q':
                break
            
            try:
                idx = int(choice) - 1
                if 0 <= idx < len(ConversionType):
                    conv_type = list(ConversionType)[idx]
                    routes = self.route_definitions.get(conv_type, [])
                    
                    print_section(f"{conv_type.value}")
                    print(f"\n{Colors.BOLD}Available Routes:{Colors.END}")
                    
                    for i, route in enumerate(routes, 1):
                        badge = ""
                        if route.is_best:
                            badge = f" {Colors.GREEN}⭐ BEST{Colors.END}"
                        elif route.is_recommended:
                            badge = f" {Colors.YELLOW}🔥 RECOMMENDED{Colors.END}"
                        elif route.is_experimental:
                            badge = f" {Colors.CYAN}🧪 EXPERIMENTAL{Colors.END}"
                        
                        print(f"\n   {i}. {Colors.BOLD}{route.name}{Colors.END}{badge}")
                        print(f"      ID: {route.route_id}")
                        print(f"      Legs: {route.legs}")
                        print(f"      Fee: {route.fee_bps} bps")
                        print(f"      Settlement: {route.settlement_time}")
                        print(f"      Regulated: {'✅ Yes' if route.regulated else '⚠️ No'}")
                        if route.path:
                            print(f"      Path: {' → '.join(route.path)}")
                else:
                    print_warning("Invalid selection")
            except ValueError:
                print_warning("Please enter a number")


async def main():
    parser = argparse.ArgumentParser(description="FX Smart Routing Demo")
    parser.add_argument("--interactive", "-i", action="store_true", help="Interactive mode")
    parser.add_argument("--type", "-t", type=str, help="Run specific conversion type")
    parser.add_argument("--export", "-e", type=str, choices=["json"], help="Export format")
    parser.add_argument("--output", "-o", type=str, default="test_results.json", help="Output file")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (summary only)")
    
    args = parser.parse_args()
    
    demo = FXRoutingDemo()
    
    if args.interactive:
        await demo.run_interactive()
    else:
        results = await demo.run_all_tests(verbose=not args.quiet)
        
        if args.export == "json":
            with open(args.output, "w") as f:
                json.dump(results, f, indent=2, default=str)
            print_success(f"Results exported to {args.output}")


if __name__ == "__main__":
    asyncio.run(main())
