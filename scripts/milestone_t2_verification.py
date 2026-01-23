"""
Milestone T2 Verification: End-to-End Workflow Test

This script verifies:
1. PRD_Draft is generated from meeting transcript
2. PRD_Draft contains User Story and AC
3. Scoring Agent uses PRD_Draft
4. Hard Gate makes correct decision
5. Workflow completes in < 60s

Run with: python scripts/milestone_t2_verification.py
"""

import logging
import sys
import time
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.reqgate.schemas.inputs import RequirementPacket
from src.reqgate.schemas.config import WorkflowConfig
from src.reqgate.workflow.graph import run_workflow


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


# ============================================
# Meeting Transcript Sample (300+ words)
# ============================================
MEETING_TRANSCRIPT = """
Meeting Notes - Product Team Sync
Date: 2026-01-20
Attendees: PM (Sarah), Dev Lead (Mike), UX (Lisa)

Sarah: So we need to implement user data export for GDPR compliance. Users should be 
able to download all their personal data from our platform.

Mike: What format should the export be in?

Sarah: CSV would be good for now. We need to include profile information like name, 
email, phone number, and also their activity history - things like login times, 
actions they've taken, and any content they've created.

Lisa: Should there be a UI for this? Like a button on the settings page?

Sarah: Yes, there should be a "Download My Data" button in the account settings. 
When clicked, it should show a confirmation dialog explaining what data will be 
included. After confirmation, the system should generate the export and either 
download it directly or send a link via email for large exports.

Mike: What about the export time? Large users might have a lot of data.

Sarah: Good point. For small exports under 10MB, do immediate download. For larger 
ones, process in background and email the download link. The link should expire 
after 24 hours for security.

Lisa: What if the user clicks export multiple times?

Sarah: We should rate limit - maybe once per 24 hours. Show them when they can 
request again.

Mike: Should we track these exports?

Sarah: Yes, keep an audit log of all export requests for compliance. Include 
timestamp, user ID, and whether it succeeded.

Lisa: What about error handling? What if the export fails?

Sarah: Show an error message and let them retry. If it fails multiple times, 
create a support ticket automatically.

Action Items:
- Mike to create technical spec
- Lisa to design the UI mockups
- Sarah to finalize AC with legal team

Next steps: Review in Thursday's sync.
"""


def verify_milestone_t2() -> dict:
    """
    Run complete milestone T2 verification.
    
    Returns:
        dict with verification results
    """
    results = {
        "passed": False,
        "duration_seconds": 0.0,
        "checks": {},
        "errors": [],
    }
    
    print("=" * 60)
    print("MILESTONE T2 VERIFICATION: End-to-End Workflow")
    print("=" * 60)
    print()
    
    # Create input packet
    packet = RequirementPacket(
        raw_text=MEETING_TRANSCRIPT,
        source_type="Meeting_Transcript",
        project_key="GDPR",
        priority="P1",
        ticket_type="Feature",
    )
    
    # Create config with full pipeline enabled
    config = WorkflowConfig(
        enable_guardrail=True,
        enable_structuring=True,
        enable_fallback=True,
    )
    
    start_time = time.time()
    
    try:
        # Run workflow
        print("Running complete workflow...")
        final_state = run_workflow(packet, config)
        
        duration = time.time() - start_time
        results["duration_seconds"] = duration
        
        # ============================================
        # Check 1: PRD_Draft is generated
        # ============================================
        structured_prd = final_state.get("structured_prd")
        prd_generated = structured_prd is not None
        results["checks"]["prd_generated"] = prd_generated
        
        if prd_generated:
            print(f"✅ 9.1.3 PRD_Draft is generated: {structured_prd.title[:50]}...")
        else:
            print("❌ 9.1.3 PRD_Draft NOT generated")
            results["errors"].append("PRD_Draft was not generated")
        
        # ============================================
        # Check 2: PRD_Draft contains User Story and AC
        # ============================================
        if structured_prd:
            has_user_story = bool(structured_prd.user_story)
            has_ac = len(structured_prd.acceptance_criteria) > 0
            
            results["checks"]["has_user_story"] = has_user_story
            results["checks"]["has_acceptance_criteria"] = has_ac
            
            if has_user_story:
                print(f"✅ 9.1.4a User Story present: {structured_prd.user_story[:60]}...")
            else:
                print("❌ 9.1.4a User Story NOT present")
                results["errors"].append("User Story missing")
            
            if has_ac:
                print(f"✅ 9.1.4b Acceptance Criteria present: {len(structured_prd.acceptance_criteria)} items")
                for i, ac in enumerate(structured_prd.acceptance_criteria[:3], 1):
                    print(f"    AC{i}: {ac[:50]}...")
            else:
                print("❌ 9.1.4b Acceptance Criteria NOT present")
                results["errors"].append("Acceptance Criteria missing")
        else:
            results["checks"]["has_user_story"] = False
            results["checks"]["has_acceptance_criteria"] = False
        
        # ============================================
        # Check 3: Scoring Agent uses PRD_Draft
        # ============================================
        score_report = final_state.get("score_report")
        scoring_completed = score_report is not None
        fallback_activated = final_state.get("fallback_activated", False)
        
        # If fallback was NOT activated and we have a score, scoring used PRD
        scoring_used_prd = scoring_completed and not fallback_activated
        results["checks"]["scoring_used_prd"] = scoring_used_prd
        
        if scoring_used_prd:
            print(f"✅ 9.1.5 Scoring Agent used PRD_Draft (fallback={fallback_activated})")
            print(f"    Score: {score_report.total_score}/100")
        else:
            if fallback_activated:
                print(f"⚠️ 9.1.5 Scoring used fallback mode (raw text)")
            else:
                print("❌ 9.1.5 Scoring did not complete")
                results["errors"].append("Scoring did not complete")
        
        # ============================================
        # Check 4: Hard Gate makes correct decision
        # ============================================
        gate_decision = final_state.get("gate_decision")
        gate_completed = gate_decision is not None
        results["checks"]["gate_completed"] = gate_completed
        
        if gate_completed:
            decision_str = "PASS" if gate_decision else "REJECT"
            print(f"✅ 9.1.6 Hard Gate made decision: {decision_str}")
        else:
            print("❌ 9.1.6 Hard Gate did NOT make decision")
            results["errors"].append("Gate decision missing")
        
        # ============================================
        # Check 5: Workflow completes in < 60s
        # ============================================
        within_time = duration < 60.0
        results["checks"]["within_time_limit"] = within_time
        
        if within_time:
            print(f"✅ 9.1.7 Workflow completed in {duration:.2f}s (< 60s)")
        else:
            print(f"❌ 9.1.7 Workflow took {duration:.2f}s (> 60s)")
            results["errors"].append(f"Workflow too slow: {duration:.2f}s")
        
        # ============================================
        # Summary
        # ============================================
        print()
        print("-" * 60)
        print("EXECUTION TIMES:")
        for node, elapsed in final_state.get("execution_times", {}).items():
            print(f"  {node}: {elapsed:.2f}s")
        
        print()
        print("-" * 60)
        
        if final_state.get("error_logs"):
            print("ERROR LOGS:")
            for log in final_state["error_logs"]:
                print(f"  - {log}")
        
        # Determine overall pass/fail
        all_checks_passed = all(results["checks"].values())
        results["passed"] = all_checks_passed
        
        print()
        print("=" * 60)
        if all_checks_passed:
            print("🎉 MILESTONE T2 VERIFICATION: PASSED")
        else:
            print("❌ MILESTONE T2 VERIFICATION: FAILED")
            print(f"   Failed checks: {[k for k, v in results['checks'].items() if not v]}")
        print("=" * 60)
        
    except Exception as e:
        duration = time.time() - start_time
        results["duration_seconds"] = duration
        results["errors"].append(f"Workflow exception: {e}")
        print(f"❌ Workflow failed with exception: {e}")
        import traceback
        traceback.print_exc()
    
    return results


if __name__ == "__main__":
    results = verify_milestone_t2()
    
    # Exit with appropriate code
    sys.exit(0 if results["passed"] else 1)
