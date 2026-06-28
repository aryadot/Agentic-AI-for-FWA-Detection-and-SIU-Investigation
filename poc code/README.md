# FWA Investigation Agent — Proof of Concept

---

## What The POC Demonstrates

An agentic AI investigation layer that intercepts flagged healthcare claims, autonomously reasons through the billing evidence step by step, and delivers structured investigation-ready case packages to SIU analysts — in place of a raw risk score.

The core problem this addresses: ML detection systems flag suspicious claims and route them to SIU analysts with a risk score. Investigators then manually collect provider history, check coding consistency, evaluate peer comparisons, and document findings — consuming 20 to 30 percent of investigator time on administrative tasks and extending case turnaround to an average of 270 days (4L Fraud Advisory Council, 2025).

This agent automates that initial investigative triage. The SIU analyst receives a pre-built documented argument rather than a blank case to build from scratch. The analyst reads the reasoning, applies judgment, and decides. All denial determinations remain with the human, preserving full compliance with AMA June 2026 policy.

---

## Three Synthetic Cases

Cases are grounded in real documented fraud patterns from the DOJ June 2026 National Health Care Fraud Takedown and HHS/CMS published fraud typologies.

FWA-2026-001 — Wound Allograft Overbilling

A dermatology provider billing amniotic wound allograft procedures against a superficial abrasion diagnosis. Allografts are indicated for chronic non-healing wounds, not minor surface injuries. Billing volume 200 percent above specialty and geography peers, 280 percent volume spike in 90 days, no prior authorization obtained. Grounded in the DOJ June 2026 Takedown where a single allograft scheme generated over $4 billion in false Medicare claims.

Expected outcome: HIGH suspicion. Escalate to full investigation.
FWA-2026-002 — E&M Upcoding False Positive

An internal medicine provider billing 78 percent of visits at the highest complexity level against a peer average of 35 percent. The anomaly is real but the explanation is legitimate. This provider operates in a rural health professional shortage area serving a Medicare population with an average of 4.2 chronic conditions per patient. High complexity coding is clinically appropriate for that patient population. Grounded in the Bluestone Physician Services $14.9 million E&M upcoding settlement.

Expected outcome: LOW suspicion. Close flag, anomaly explained by patient population.
FWA-2026-003 — Behavioral Health Session Volume

A behavioral health clinic billing 45 therapy sessions per day with 3 licensed clinicians on staff. 45 sessions divided by 3 clinicians equals 15 sessions each. At 60 minutes per session plus 15 minutes documentation that is 18.75 hours required per clinician per day against an 8 hour working day. Physically impossible. Documentation completeness rate is 40 percent. Grounded in the DOJ June 2026 Takedown where a behavioral health provider billed over 500 hours of counseling per day.

Expected outcome: HIGH suspicion. Escalate to full investigation.

Case 3 is the strongest demonstration of chain reasoning. The agent works through the arithmetic explicitly: 45 sessions divided by 3 clinicians equals 15 sessions each, at 60 minutes per session plus 15 minutes documentation equals 18.75 hours required per clinician against an 8-hour working day. Physically impossible. The agent identifies this, documents it, and recommends targeted record requests before escalation.

---

## Architecture

```
ML Detection Flag
       │
       ▼
┌─────────────────────────────────────┐
│        FWA Investigation Agent       │
│                                     │
│  1. Receive flagged claim and       │
│     structured provider data        │
│  2. Reason through billing evidence │
│     step by step                    │
│  3. Evaluate diagnosis-procedure    │
│     clinical alignment              │
│  4. Assess peer benchmark deviation │
│  5. Check authorization compliance  │
│  6. Consider alternative            │
│     explanations                    │
│  7. Assign confidence tier          │
│  8. Build structured case package   │
└─────────────────────────────────────┘
       │
       ▼
┌─────────────────────────────────────┐
│      LLM-as-Judge Evaluation        │
│                                     │
│  Quality gate before analyst        │
│  delivery — four criteria:          │
│  - Reasoning completeness           │
│  - Evidence accuracy                │
│  - Step sequencing                  │
│  - Compliance adherence             │
└─────────────────────────────────────┘
       │
       ▼
  SIU Analyst receives
  investigation-ready case package
  Human makes the final decision
```

---

## Evaluation Layer — LLM-as-Judge

Before any case package reaches the SIU analyst it passes through an embedded quality evaluation layer. This addresses a documented risk in production agentic systems — that agents frequently violate operational policies and skip verification steps in ways that conventional task-completion metrics cannot detect (Akshathala et al., 2026).

The judge evaluates each case package across four criteria:

**Reasoning completeness** — did the agent reason through all available evidence including billing patterns, coding consistency, peer comparison, and authorization status.

**Evidence accuracy** — are the agent's findings consistent with the structured data provided and correctly interpreted.

**Step sequencing** — did the agent follow a logical investigation sequence where each step builds appropriately on the previous one.

**Compliance adherence** — did the agent stay within its defined boundary, recommend rather than decide, and preserve human decision authority throughout.

Case packages that fail the quality threshold are flagged for human review rather than passed through. This ensures the SIU analyst receives only case packages that are pre-investigated, reliably reasoned, and auditable under state insurance regulations and AMA June 2026 explainability requirements.

---

## Stack

- **Model:** Llama 4 Scout via Groq API
- **Language:** Python 3.11
- **Data:** Synthetic structured claims data grounded in real fraud patterns
- **Evaluation:** LLM-as-Judge (Akshattala et al., AGENT 2026)
- **Output:** JSON case packages + HTML visual report

---

## Setup

```bash
# Navigate to the project folder
cd fwa_poc

# Install dependencies
pip install -r requirements.txt

# Get a free Groq API key at console.groq.com
# Then open the notebook in VS Code or Jupyter
# Set your key in Cell 1:
# os.environ["GROQ_API_KEY"] = "your_key_here"

# Or run directly via terminal
export GROQ_API_KEY=your_key_here
python main.py
```

---

## Output

Running the POC generates two files:

- `fwa_investigation_report.html` — Visual case packages for all three scenarios, viewable in any browser
- `results.json` — Raw structured JSON output from the agent and judge for all cases

---

## Repository Structure

```
fwa_poc/
├── FWA_Investigation_Agent_POC.ipynb  # Main demonstration notebook
├── synthetic_cases.py                  # Synthetic claims data — three cases
├── investigation_agent.py              # Investigation agent and judge
├── report_generator.py                 # HTML report generator
├── main.py                             # Terminal runner script
├── requirements.txt                    # Dependencies
└── README.md                           # This file
```

---
## Tools Used

Model: Llama 4 Scout via Groq — LLM reasoning agent and LLM-as-Judge evaluation layer
Language: Python 3.11
Synthetic Data: Generated with Claude to represent realistic FWA investigation scenarios grounded in real fraud patterns
Output: Structured JSON case packages rendered as an HTML visual report

## References

- 4L Fraud Advisory Council. (2025). Leveraging AI to evolve SIU performance.
- Akshattala, S., et al. (2026). Beyond task completion: An assessment framework for evaluating agentic AI systems. AGENT '26, ACM.
- American Medical Association. (2026). AMA policy on AI in coverage determinations.
- Anonymous. (2025). INFER: A multi-agent framework for detecting fraud, waste, and abuse in Medicare claims.
- Department of Justice. (2026, June 23). National Health Care Fraud Takedown — 455 defendants, $6.5 billion in alleged fraud.
- FraudOps. (2026). Detection AI and investigation AI are not the same thing.
- HHS/CMS. (2016). Common types of health care fraud fact sheet.

---
