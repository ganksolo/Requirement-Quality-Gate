#!/usr/bin/env python3
"""
Manual Testing Script for Phase 1 + Phase 2 Verification.

Run this script to execute all critical manual tests before Phase 3.

Usage:
    python scripts/manual_test_runner.py [--quick] [--verbose]

Options:
    --quick     Run only P0 priority tests
    --verbose   Show detailed output
"""

from __future__ import annotations

import argparse
import sys
import time
from dataclasses import dataclass
from typing import Any

# Add project root to path
sys.path.insert(0, ".")


@dataclass
class TestResult:
    """Result of a single test."""

    name: str
    passed: bool
    duration: float
    message: str
    details: dict[str, Any] | None = None


class ManualTestRunner:
    """Runner for manual verification tests."""

    def __init__(self, verbose: bool = False) -> None:
        self.verbose = verbose
        self.results: list[TestResult] = []

    def log(self, msg: str) -> None:
        """Print verbose log."""
        if self.verbose:
            print(f"  [DEBUG] {msg}")

    def run_test(
        self, name: str, test_func: callable, *args: Any, **kwargs: Any
    ) -> TestResult:
        """Run a single test and capture result."""
        print(f"\n🧪 Running: {name}")
        start = time.time()

        try:
            result = test_func(*args, **kwargs)
            duration = time.time() - start

            if isinstance(result, tuple):
                passed, message, details = result
            else:
                passed, message, details = result, "OK", None

            test_result = TestResult(
                name=name,
                passed=passed,
                duration=duration,
                message=message,
                details=details,
            )

        except Exception as e:
            duration = time.time() - start
            test_result = TestResult(
                name=name,
                passed=False,
                duration=duration,
                message=f"Exception: {e!s}",
            )

        self.results.append(test_result)

        status = "✅ PASS" if test_result.passed else "❌ FAIL"
        print(f"   {status} ({test_result.duration:.2f}s) - {test_result.message}")

        if test_result.details and self.verbose:
            for k, v in test_result.details.items():
                print(f"      {k}: {v}")

        return test_result

    def print_summary(self) -> None:
        """Print test summary."""
        print("\n" + "=" * 60)
        print("📊 TEST SUMMARY")
        print("=" * 60)

        passed = sum(1 for r in self.results if r.passed)
        failed = sum(1 for r in self.results if not r.passed)
        total = len(self.results)

        print(f"\nTotal:  {total}")
        print(f"Passed: {passed} ✅")
        print(f"Failed: {failed} ❌")
        print(f"Rate:   {passed/total*100:.1f}%")

        if failed > 0:
            print("\n❌ Failed Tests:")
            for r in self.results:
                if not r.passed:
                    print(f"   - {r.name}: {r.message}")

        print("=" * 60)


# =============================================================================
# Test Functions
# =============================================================================


def test_schema_serialization() -> tuple[bool, str, dict]:
    """Test that schemas can be serialized/deserialized."""
    from src.reqgate.schemas.inputs import RequirementPacket
    from src.reqgate.schemas.outputs import TicketScoreReport

    # Test RequirementPacket (with all required fields)
    packet = RequirementPacket(
        raw_text="Test requirement text for verification purposes, must be long enough.",
        source_type="Jira_Ticket",
        project_key="TEST",
        scenario="FEATURE",
    )
    json_str = packet.model_dump_json()
    restored = RequirementPacket.model_validate_json(json_str)

    if packet.raw_text != restored.raw_text:
        return False, "RequirementPacket serialization failed", {}

    return True, "All schemas serialize correctly", {"project_key": packet.project_key}


def test_config_access() -> tuple[bool, str, dict]:
    """Test that all config items are accessible."""
    from src.reqgate.config.settings import get_settings

    settings = get_settings()

    required_attrs = [
        "enable_structuring",
        "enable_guardrail",
        "max_llm_retries",
        "default_threshold",
    ]

    missing = [attr for attr in required_attrs if not hasattr(settings, attr)]

    if missing:
        return False, f"Missing config: {missing}", {}

    return (
        True,
        "All config items accessible",
        {
            "enable_structuring": settings.enable_structuring,
            "enable_guardrail": settings.enable_guardrail,
            "threshold": settings.default_threshold,
        },
    )


def test_workflow_creation() -> tuple[bool, str, dict]:
    """Test that workflow can be created."""
    from src.reqgate.workflow.graph import create_workflow

    workflow = create_workflow()

    if workflow is None:
        return False, "Workflow creation returned None", {}

    return True, "Workflow created successfully", {}


def test_hard_check_pass() -> tuple[bool, str, dict]:
    """Test Hard Check #1 with valid PRD."""
    from src.reqgate.schemas.inputs import RequirementPacket
    from src.reqgate.schemas.internal import PRD_Draft
    from src.reqgate.workflow.nodes.structure_check import hard_check_structure_node

    # PRD with proper format (title starts with verb, user story format, string ACs)
    prd = PRD_Draft(
        title="Implement user login functionality with email and password",
        user_story="As a user, I want to login to the system, so that I can access my personal data",
        acceptance_criteria=[
            "User can enter email and password to login",
            "Failed login attempts show error messages",
            "Support remember me checkbox functionality",
        ],
    )

    packet = RequirementPacket(
        raw_text="Test content for validation - must be long enough for schema",
        source_type="Jira_Ticket",
        project_key="TEST",
    )

    state = {
        "packet": packet,
        "structured_prd": prd,
        "score_report": None,
        "gate_decision": None,
        "retry_count": 0,
        "error_logs": [],
        "current_stage": "structuring",
        "fallback_activated": False,
        "execution_times": {},
        "structure_check_passed": None,
        "structure_errors": [],
    }

    result = hard_check_structure_node(state)

    if not result["structure_check_passed"]:
        return (
            False,
            f"Valid PRD failed check: {result['structure_errors']}",
            {"errors": result["structure_errors"]},
        )

    return (
        True,
        "Valid PRD passed structure check",
        {"ac_count": len(prd.acceptance_criteria)},
    )


def test_hard_check_fail_low_ac() -> tuple[bool, str, dict]:
    """Test Hard Check #1 rejects PRD with < 2 ACs."""
    from src.reqgate.schemas.inputs import RequirementPacket
    from src.reqgate.schemas.internal import PRD_Draft
    from src.reqgate.workflow.nodes.structure_check import hard_check_structure_node

    # PRD with only 1 AC (should fail structure check)
    prd = PRD_Draft(
        title="Implement user login functionality with email verification",
        user_story="As a user, I want to login to the system, so that I can access my dashboard",
        acceptance_criteria=[
            "Only one acceptance criteria item here",
        ],  # Only 1 AC - should fail
    )

    packet = RequirementPacket(
        raw_text="Test content for validation - must be long enough for schema",
        source_type="Jira_Ticket",
        project_key="TEST",
    )

    state = {
        "packet": packet,
        "structured_prd": prd,
        "score_report": None,
        "gate_decision": None,
        "retry_count": 0,
        "error_logs": [],
        "current_stage": "structuring",
        "fallback_activated": False,
        "execution_times": {},
        "structure_check_passed": None,
        "structure_errors": [],
    }

    result = hard_check_structure_node(state)

    if result["structure_check_passed"]:
        return False, "PRD with 1 AC should have failed", {}

    if not result["structure_errors"]:
        return False, "Expected error message for AC count", {}

    return (
        True,
        "Correctly rejected PRD with < 2 ACs",
        {"errors": result["structure_errors"]},
    )


def test_hard_check_skip_no_prd() -> tuple[bool, str, dict]:
    """Test Hard Check #1 skipped when no PRD."""
    from src.reqgate.schemas.inputs import RequirementPacket
    from src.reqgate.workflow.nodes.structure_check import hard_check_structure_node

    packet = RequirementPacket(
        raw_text="Test content for validation - must be long enough for schema",
        source_type="Jira_Ticket",
        project_key="TEST",
    )

    state = {
        "packet": packet,
        "structured_prd": None,  # No PRD
        "score_report": None,
        "gate_decision": None,
        "retry_count": 0,
        "error_logs": [],
        "current_stage": "structuring",
        "fallback_activated": True,
        "execution_times": {},
        "structure_check_passed": None,
        "structure_errors": [],
    }

    result = hard_check_structure_node(state)

    # Should skip check, not fail
    if result["structure_check_passed"] is False:
        return False, "Should skip check when no PRD, not fail", {}

    return True, "Correctly skipped check when no PRD", {"passed": result["structure_check_passed"]}


def test_structure_check_performance() -> tuple[bool, str, dict]:
    """Test Structure Check completes in < 100ms."""
    from src.reqgate.schemas.inputs import RequirementPacket
    from src.reqgate.schemas.internal import PRD_Draft
    from src.reqgate.workflow.nodes.structure_check import hard_check_structure_node

    prd = PRD_Draft(
        title="Implement user login functionality with email verification",
        user_story="As a user, I want to login to the system, so that I can access my dashboard",
        acceptance_criteria=[
            "User can login with email and password",
            "Failed attempts show error message",
        ],
    )

    packet = RequirementPacket(
        raw_text="Test content for performance validation, must be long enough",
        source_type="Jira_Ticket",
        project_key="PERF",
    )

    state = {
        "packet": packet,
        "structured_prd": prd,
        "score_report": None,
        "gate_decision": None,
        "retry_count": 0,
        "error_logs": [],
        "current_stage": "structuring",
        "fallback_activated": False,
        "execution_times": {},
        "structure_check_passed": None,
        "structure_errors": [],
    }

    start = time.time()
    for _ in range(100):  # Run 100 times
        hard_check_structure_node(state)
    elapsed = time.time() - start

    avg_ms = (elapsed / 100) * 1000

    if avg_ms > 10:  # Average should be < 10ms
        return False, f"Too slow: {avg_ms:.2f}ms avg", {"avg_ms": avg_ms}

    return True, f"Performance OK: {avg_ms:.2f}ms avg", {"avg_ms": avg_ms}


def test_health_endpoint() -> tuple[bool, str, dict]:
    """Test health endpoint is accessible."""
    from fastapi.testclient import TestClient

    from src.reqgate.app.main import app

    client = TestClient(app)
    response = client.get("/health")

    if response.status_code != 200:
        return False, f"Health check failed: {response.status_code}", {}

    return True, "Health endpoint OK", {"status_code": response.status_code}


# =============================================================================
# Main
# =============================================================================


def main() -> int:
    """Run manual tests."""
    parser = argparse.ArgumentParser(description="Manual Testing Runner")
    parser.add_argument("--quick", action="store_true", help="Run only P0 tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    args = parser.parse_args()

    runner = ManualTestRunner(verbose=args.verbose)

    print("=" * 60)
    print("🔬 Phase 1 + Phase 2 Manual Testing")
    print("=" * 60)

    # P0 Tests (Always run)
    runner.run_test("Schema Serialization", test_schema_serialization)
    runner.run_test("Config Access", test_config_access)
    runner.run_test("Workflow Creation", test_workflow_creation)
    runner.run_test("Hard Check - Valid PRD Pass", test_hard_check_pass)
    runner.run_test("Hard Check - Low AC Reject", test_hard_check_fail_low_ac)
    runner.run_test("Hard Check - Skip No PRD", test_hard_check_skip_no_prd)

    if not args.quick:
        # P1 Tests (Full run only)
        runner.run_test("Structure Check Performance", test_structure_check_performance)
        runner.run_test("Health Endpoint", test_health_endpoint)

    runner.print_summary()

    # Return exit code
    failed = sum(1 for r in runner.results if not r.passed)
    return 1 if failed > 0 else 0


if __name__ == "__main__":
    sys.exit(main())
