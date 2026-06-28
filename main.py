"""
FWA Investigation Agent — Main Runner
Run this script to process all three synthetic cases and generate the HTML report.

Usage:
    Set GROQ_API_KEY environment variable, then run:
    python main.py
"""

import json
import os
from synthetic_cases import CASES
from investigation_agent import run_investigation_agent, run_judge_evaluation
from report_generator import generate_html_report


def main():
    print("\n" + "="*60)
    print("FWA INVESTIGATION AGENT — PROOF OF CONCEPT")
    print("Agentic AI Pre-Investigation Triage for SIU Teams")
    print("Model: Llama 4 Scout via Groq")
    print("="*60)
    print(f"\nProcessing {len(CASES)} synthetic cases...")
    print("Cases grounded in DOJ June 2026 National Fraud Takedown patterns\n")

    if not os.environ.get("GROQ_API_KEY"):
        print("ERROR: GROQ_API_KEY environment variable not set.")
        print("Set your Groq API key: export GROQ_API_KEY=your_key_here")
        return

    results = []

    for case in CASES:
        # Step 1: Run investigation agent
        agent_output = run_investigation_agent(case)

        # Step 2: Run judge evaluation
        judge_output = run_judge_evaluation(case, agent_output)

        results.append({
            "case": case,
            "agent_output": agent_output,
            "judge_output": judge_output
        })

    # Step 3: Save raw JSON results
    with open("results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("\n\nRaw results saved to results.json")

    # Step 4: Generate HTML report
    html = generate_html_report(results)
    with open("fwa_investigation_report.html", "w") as f:
        f.write(html)
    print("HTML report generated: fwa_investigation_report.html")

    # Step 5: Print summary
    print("\n" + "="*60)
    print("SUMMARY")
    print("="*60)
    for item in results:
        case_id = item["case"]["case_id"]
        case_name = item["case"]["case_name"]
        confidence = item["agent_output"].get("confidence_level", "N/A")
        recommendation = item["agent_output"].get("recommended_action", "N/A")[:80]
        judge_score = item["judge_output"].get("overall_score", "N/A")
        passes = item["judge_output"].get("passes_quality_threshold", False)

        print(f"\n{case_id} — {case_name}")
        print(f"  Confidence: {confidence}")
        print(f"  Recommendation: {recommendation}...")
        print(f"  Judge Score: {judge_score}/5 | Passes QA: {passes}")

    print("\n" + "="*60)
    print("DEMONSTRATION COMPLETE")
    print("Open fwa_investigation_report.html to view case packages")
    print("="*60)


if __name__ == "__main__":
    main()
