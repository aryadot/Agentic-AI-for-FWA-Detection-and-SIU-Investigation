"""
FWA Investigation Agent

"""

import os
import json
from groq import Groq

INVESTIGATION_SYSTEM_PROMPT = """You are an expert healthcare payment integrity investigator AI assistant.
Your role is to autonomously investigate flagged claims and produce structured, 
investigation-ready case packages for SIU analysts.

You reason step by step through billing evidence, following this exact process:
1. Identify the core anomaly that triggered the flag
2. Evaluate whether the diagnosis codes clinically support the procedures billed
3. Assess billing volume against peer benchmarks and identify deviations
4. Check prior authorization compliance
5. Consider ALL alternative explanations that could legitimately explain the anomaly
6. Weigh the evidence for and against each explanation
7. Assign a confidence level: HIGH, MEDIUM, or LOW suspicion
8. Provide a clear recommended next action for the SIU analyst

CRITICAL RULES:
- You NEVER make denial decisions. You produce investigative arguments only.
- You ALWAYS consider alternative explanations before reaching a finding.
- You ALWAYS document your reasoning chain step by step.
- The human SIU analyst makes all final decisions.
- Your output must be clear, professional, and auditable.

Output your response as a valid JSON object with this exact structure:
{
  "case_id": "string",
  "case_name": "string", 
  "core_anomaly": "string - one sentence describing what was flagged",
  "reasoning_chain": [
    {
      "step": 1,
      "check": "string - what you are evaluating",
      "finding": "string - what you found",
      "significance": "string - why this matters"
    }
  ],
  "alternative_explanations_considered": [
    {
      "explanation": "string",
      "assessment": "string - does this explanation resolve the anomaly or not and why"
    }
  ],
  "key_evidence": ["string", "string"],
  "confidence_level": "HIGH | MEDIUM | LOW",
  "confidence_rationale": "string",
  "recommended_action": "string - specific next step for the SIU analyst",
  "compliance_note": "This case package is for investigative purposes only. All denial or referral decisions require human SIU analyst review."
}"""


def build_investigation_prompt(case: dict) -> str:
    """Build a structured prompt from case data for the investigation agent."""
    
    provider = case["provider"]
    claim = case["flagged_claim"]
    billing = case["billing_history"]
    coding = case["coding_analysis"]
    peers = case["peer_comparison"]
    
    prompt = f"""Investigate the following flagged healthcare claim and produce a structured case package.

CASE ID: {case['case_id']}
CASE NAME: {case['case_name']}

PROVIDER INFORMATION:
- Name: {provider['name']}
- Specialty: {provider['specialty']}  
- Location: {provider['location']}
- Years Billing: {provider['years_billing']}
- Prior Investigation History: {provider['prior_investigation_flag']}

FLAGGED CLAIM:
- Procedure Code: {claim['procedure_code']} - {claim['procedure_description']}
- Diagnosis Code: {claim['diagnosis_code']} - {claim['diagnosis_description']}
- Amount Billed: ${claim['billed_amount']:,.2f}
- Date of Service: {claim['date_of_service']}
- Prior Authorization Required: {claim['prior_authorization_required']}
- Prior Authorization Obtained: {claim['prior_authorization_obtained']}

BILLING PATTERN ANALYSIS:
- Peer Deviation: {billing['peer_deviation_percent']}% above peer average
- Volume Spike: {billing['billing_volume_spike_percent']}% increase since {billing.get('spike_start_date', 'N/A')}
- Provider Billing Average: ${billing.get('avg_billed_per_procedure', billing.get('avg_billed_per_visit', billing.get('avg_billed_per_session', 0))):,.2f}
- Peer Average: ${billing.get('peer_avg_billed_per_procedure', billing.get('peer_avg_billed_per_visit', billing.get('peer_avg_billed_per_session', 0))):,.2f}

CODING ANALYSIS:
- Diagnosis Supports Procedure: {coding['diagnosis_supports_procedure']}
- Clinical Assessment: {coding['clinical_note']}

PEER COMPARISON:
- Specialty Group: {peers['specialty']}
- Geography: {peers['geography']}
- Peers Analyzed: {peers['peers_analyzed']}
- Provider Percentile: {peers['provider_percentile']}th percentile"""

    if "staffing_data" in case:
        staffing = case["staffing_data"]
        prompt += f"""

STAFFING DATA (Critical for Volume Analysis):
- Licensed Clinicians on Staff: {staffing['licensed_clinicians_on_staff']}
- Sessions Billed Per Day: {billing['avg_daily_sessions_billed']}
- Sessions Per Clinician Required: {staffing['sessions_per_clinician_required']}
- Session Duration: {staffing['session_duration_minutes']} minutes
- Required Clinical Hours Per Clinician Per Day: {staffing['required_hours_per_clinician_per_day']} hours
- Documentation Time Per Session: {staffing['documentation_time_per_session_minutes']} minutes
- Total Hours Required Per Clinician (sessions + documentation): {staffing['total_hours_required_per_clinician']} hours
- Standard Working Day: {staffing['hours_in_working_day']} hours
- Physically Possible: {staffing['physically_possible']}"""

    if "documentation_review" in case:
        docs = case["documentation_review"]
        prompt += f"""

DOCUMENTATION REVIEW:
- Sessions with Complete Notes: {docs['sessions_with_complete_notes']}
- Sessions with Missing Notes: {docs['sessions_with_missing_notes']}
- Note Completion Rate: {docs['note_completion_rate_percent']}%"""

    if "contextual_factors" in case:
        ctx = case["contextual_factors"]
        prompt += f"""

CONTEXTUAL FACTORS:
- Rural Designation: {ctx.get('rural_designation', 'N/A')}
- Patient Acuity: {ctx.get('patient_acuity_index', 'N/A')}
- Practice Type: {'Solo Practice' if ctx.get('solo_practice') else 'Group Practice'}
- Additional Context: {ctx.get('note', 'N/A')}"""

    prompt += """

Now investigate this case. Reason through each piece of evidence step by step.
Consider all alternative explanations seriously before reaching a finding.
Remember: you produce an investigative argument, not a decision.
Output valid JSON only."""

    return prompt


def run_investigation_agent(case: dict) -> dict:
    """
    Run the FWA investigation agent on a single case.
    Client is created fresh inside this function so it always
    picks up the API key set in the notebook Cell 1.
    """
    
    print(f"\n{'='*60}")
    print(f"INVESTIGATING: {case['case_id']} - {case['case_name']}")
    print(f"{'='*60}")
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found.\n"
            "In Cell 1 of the notebook add:\n"
            "os.environ['GROQ_API_KEY'] = 'your_key_here'\n"
            "Then restart and run all cells again."
        )
    
    groq_client = Groq(api_key=api_key)
    prompt = build_investigation_prompt(case)
    
    response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "system", "content": INVESTIGATION_SYSTEM_PROMPT},
            {"role": "user", "content": prompt}
        ],
        temperature=0.2,
        max_tokens=2000,
        response_format={"type": "json_object"}
    )
    
    raw_output = response.choices[0].message.content
    result = json.loads(raw_output)
    
    print(f"Confidence Level: {result.get('confidence_level', 'N/A')}")
    print(f"Recommended Action: {result.get('recommended_action', 'N/A')}")
    
    return result


def run_judge_evaluation(case: dict, agent_output: dict) -> dict:
    """
    LLM-as-Judge evaluation layer.
    Client is created fresh inside this function so it always
    picks up the API key set in the notebook Cell 1.
    """
    
    print(f"\nRunning Judge Evaluation for {case['case_id']}...")
    
    api_key = os.environ.get("GROQ_API_KEY")
    if not api_key:
        raise EnvironmentError(
            "GROQ_API_KEY not found.\n"
            "In Cell 1 of the notebook add:\n"
            "os.environ['GROQ_API_KEY'] = 'your_key_here'\n"
            "Then restart and run all cells again."
        )
    
    groq_client = Groq(api_key=api_key)
    
    judge_prompt = f"""You are a quality assurance evaluator for an AI-powered FWA investigation system.
    
Evaluate the following case package produced by the investigation agent against four criteria.
Score each criterion from 1 to 5, where 5 is excellent and 1 is poor.

ORIGINAL CASE DATA:
{json.dumps(case, indent=2)}

AGENT-PRODUCED CASE PACKAGE:
{json.dumps(agent_output, indent=2)}

Evaluate against these four criteria:

1. REASONING COMPLETENESS (1-5): Did the agent reason through all available evidence?
2. EVIDENCE ACCURACY (1-5): Are the agent's findings consistent with the data provided?
3. STEP SEQUENCING (1-5): Did the agent follow a logical investigation sequence?
4. COMPLIANCE ADHERENCE (1-5): Did the agent recommend rather than decide?

Output valid JSON only with this structure:
{{
  "case_id": "string",
  "reasoning_completeness": {{"score": number, "comment": "string"}},
  "evidence_accuracy": {{"score": number, "comment": "string"}},
  "step_sequencing": {{"score": number, "comment": "string"}},
  "compliance_adherence": {{"score": number, "comment": "string"}},
  "overall_score": number,
  "passes_quality_threshold": boolean,
  "quality_note": "string"
}}"""

    response = groq_client.chat.completions.create(
        model="meta-llama/llama-4-scout-17b-16e-instruct",
        messages=[
            {"role": "user", "content": judge_prompt}
        ],
        temperature=0.1,
        max_tokens=800,
        response_format={"type": "json_object"}
    )
    
    judge_result = json.loads(response.choices[0].message.content)
    print(f"Judge Overall Score: {judge_result.get('overall_score', 'N/A')}/5")
    print(f"Passes Quality Threshold: {judge_result.get('passes_quality_threshold', 'N/A')}")
    
    return judge_result
