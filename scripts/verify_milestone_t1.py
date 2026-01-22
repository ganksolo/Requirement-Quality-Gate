#!/usr/bin/env python3
"""
Milestone T1 Verification Script: The First Reject

This script verifies that the ReqGate system can:
1. Score a bad requirement (missing AC) with total_score < 60
2. Identify MISSING_AC as a blocking issue
3. Return REJECT from Hard Gate

Success Criteria:
- total_score < 60
- blocking_issues contains MISSING_AC category
- Hard Gate returns REJECT
"""

import json
import sys
from datetime import datetime
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reqgate.agents.scoring import ScoringAgent
from src.reqgate.gates.decision import HardGate
from src.reqgate.schemas.inputs import RequirementPacket


def load_bad_sample() -> str:
    """Load the bad requirement sample."""
    sample_path = project_root / "tests" / "samples" / "bad_requirement_missing_ac.txt"
    if not sample_path.exists():
        raise FileNotFoundError(f"Sample file not found: {sample_path}")
    return sample_path.read_text(encoding="utf-8")


def create_requirement_packet(raw_text: str) -> RequirementPacket:
    """Create a RequirementPacket from raw text."""
    return RequirementPacket(
        raw_text=raw_text,
        source_type="Jira_Ticket",
        project_key="TEST",
        priority="P1",
        ticket_type="Feature",
    )


def verify_milestone_t1() -> bool:
    """
    Execute Milestone T1 verification.

    Returns:
        True if all criteria pass, False otherwise
    """
    print("=" * 60)
    print("Milestone T1 Verification: The First Reject")
    print("=" * 60)
    print(f"Time: {datetime.now().isoformat()}")
    print()

    # Step 1: Load bad sample
    print("[1/4] Loading bad requirement sample...")
    try:
        raw_text = load_bad_sample()
        print(f"     Sample loaded ({len(raw_text)} chars)")
    except FileNotFoundError as e:
        print(f"     ERROR: {e}")
        return False

    # Step 2: Create packet
    print("[2/4] Creating RequirementPacket...")
    packet = create_requirement_packet(raw_text)
    print(f"     Packet created: project={packet.project_key}, type={packet.ticket_type}")

    # Step 3: Score with Scoring Agent
    print("[3/4] Scoring with ScoringAgent...")
    print("     (This may take 10-30 seconds for LLM call)")
    try:
        agent = ScoringAgent()
        report = agent.score(packet)
    except Exception as e:
        print(f"     ERROR: Scoring failed - {e}")
        return False

    print()
    print("-" * 40)
    print("Scoring Result:")
    print("-" * 40)
    print(f"Total Score: {report.total_score}")
    print(f"Ready for Review: {report.ready_for_review}")
    print(f"Dimension Scores: {json.dumps(report.dimension_scores, indent=2)}")
    print(f"Blocking Issues ({len(report.blocking_issues)}):")
    for issue in report.blocking_issues:
        print(f"  - [{issue.severity}] {issue.category}: {issue.description}")
    print(f"Non-blocking Issues ({len(report.non_blocking_issues)}):")
    for issue in report.non_blocking_issues:
        print(f"  - [{issue.severity}] {issue.category}: {issue.description}")
    print()
    print("Summary Markdown:")
    print(report.summary_markdown)
    print("-" * 40)
    print()

    # Step 4: Check Hard Gate decision
    print("[4/4] Checking Hard Gate decision...")
    gate = HardGate()
    decision = gate.decide(report, packet.ticket_type)
    print(f"     Gate Decision: {decision}")
    print()

    # Verify success criteria
    print("=" * 60)
    print("Verification Results:")
    print("=" * 60)

    criteria = [
        ("total_score < 60", report.total_score < 60, f"Got {report.total_score}"),
        (
            "blocking_issues contains MISSING_AC",
            any(issue.category == "MISSING_AC" for issue in report.blocking_issues),
            f"Categories: {[issue.category for issue in report.blocking_issues]}",
        ),
        ("Hard Gate returns REJECT", decision == "REJECT", f"Got {decision}"),
    ]

    all_passed = True
    for criterion, passed, detail in criteria:
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"  {status}: {criterion}")
        print(f"          Detail: {detail}")
        if not passed:
            all_passed = False

    print()
    if all_passed:
        print("🎉 MILESTONE T1 VERIFIED SUCCESSFULLY!")
    else:
        print("⚠️  MILESTONE T1 VERIFICATION FAILED")
        print("    Some criteria did not pass. Check the results above.")

    return all_passed


if __name__ == "__main__":
    success = verify_milestone_t1()
    sys.exit(0 if success else 1)
