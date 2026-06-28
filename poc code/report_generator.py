"""
HTML Report Generator
Renders investigation case packages as a clean visual report
for the video walkthrough demonstration.
"""

def get_confidence_color(level: str) -> str:
    colors = {
        "HIGH": "#dc2626",
        "MEDIUM": "#d97706", 
        "LOW": "#16a34a"
    }
    return colors.get(level, "#6b7280")


def get_confidence_label(level: str) -> str:
    labels = {
        "HIGH": "HIGH SUSPICION — Escalate to Full Investigation",
        "MEDIUM": "MEDIUM SUSPICION — Targeted Follow-Up Required",
        "LOW": "LOW SUSPICION — Recommend Closing Flag"
    }
    return labels.get(level, level)


def get_score_color(score: float) -> str:
    if score >= 4:
        return "#16a34a"
    elif score >= 3:
        return "#d97706"
    return "#dc2626"


def generate_html_report(results: list) -> str:
    """Generate a clean HTML report from all case package results."""
    
    cases_html = ""
    
    for item in results:
        case = item["case"]
        agent = item["agent_output"]
        judge = item["judge_output"]
        
        confidence_color = get_confidence_color(agent.get("confidence_level", ""))
        confidence_label = get_confidence_label(agent.get("confidence_level", ""))
        
        reasoning_steps_html = ""
        for step in agent.get("reasoning_chain", []):
            reasoning_steps_html += f"""
            <div class="reasoning-step">
                <div class="step-header">
                    <span class="step-number">Step {step.get('step', '')}</span>
                    <span class="step-check">{step.get('check', '')}</span>
                </div>
                <div class="step-finding"><strong>Finding:</strong> {step.get('finding', '')}</div>
                <div class="step-significance"><strong>Significance:</strong> {step.get('significance', '')}</div>
            </div>"""
        
        alternatives_html = ""
        for alt in agent.get("alternative_explanations_considered", []):
            alternatives_html += f"""
            <div class="alternative">
                <div class="alt-explanation"><strong>Explanation considered:</strong> {alt.get('explanation', '')}</div>
                <div class="alt-assessment"><strong>Assessment:</strong> {alt.get('assessment', '')}</div>
            </div>"""
        
        evidence_html = ""
        for ev in agent.get("key_evidence", []):
            evidence_html += f'<li>{ev}</li>'
        
        judge_html = ""
        for criterion in ["reasoning_completeness", "evidence_accuracy", "step_sequencing", "compliance_adherence"]:
            if criterion in judge:
                score = judge[criterion].get("score", 0)
                comment = judge[criterion].get("comment", "")
                label = criterion.replace("_", " ").title()
                score_color = get_score_color(score)
                judge_html += f"""
                <div class="judge-criterion">
                    <div class="criterion-header">
                        <span class="criterion-label">{label}</span>
                        <span class="criterion-score" style="color: {score_color};">{score}/5</span>
                    </div>
                    <div class="criterion-comment">{comment}</div>
                </div>"""
        
        passes = judge.get("passes_quality_threshold", False)
        pass_color = "#16a34a" if passes else "#dc2626"
        pass_label = "PASSES QUALITY THRESHOLD" if passes else "REQUIRES REVIEW BEFORE DELIVERY"
        
        cases_html += f"""
        <div class="case-card">
            <div class="case-header">
                <div class="case-id">{case['case_id']}</div>
                <div class="case-name">{case['case_name']}</div>
                <div class="case-type">{case['fraud_type']}</div>
            </div>
            
            <div class="provider-info">
                <h3>Provider Information</h3>
                <div class="info-grid">
                    <div><strong>Provider:</strong> {case['provider']['name']}</div>
                    <div><strong>Specialty:</strong> {case['provider']['specialty']}</div>
                    <div><strong>Location:</strong> {case['provider']['location']}</div>
                    <div><strong>Prior Investigation:</strong> {case['provider']['prior_investigation_flag']}</div>
                </div>
            </div>

            <div class="core-anomaly">
                <h3>Core Anomaly Identified</h3>
                <p>{agent.get('core_anomaly', '')}</p>
            </div>

            <div class="reasoning-section">
                <h3>Investigation Reasoning Chain</h3>
                {reasoning_steps_html}
            </div>

            <div class="alternatives-section">
                <h3>Alternative Explanations Considered</h3>
                {alternatives_html}
            </div>

            <div class="evidence-section">
                <h3>Key Evidence</h3>
                <ul>{evidence_html}</ul>
            </div>

            <div class="confidence-section" style="border-left: 5px solid {confidence_color};">
                <div class="confidence-level" style="color: {confidence_color};">
                    {agent.get('confidence_level', '')} SUSPICION
                </div>
                <div class="confidence-label">{confidence_label}</div>
                <div class="confidence-rationale">{agent.get('confidence_rationale', '')}</div>
            </div>

            <div class="recommendation-section">
                <h3>Recommended Action for SIU Analyst</h3>
                <p class="recommendation">{agent.get('recommended_action', '')}</p>
                <p class="compliance-note">{agent.get('compliance_note', '')}</p>
            </div>

            <div class="judge-section">
                <h3>Quality Evaluation — LLM-as-Judge</h3>
                <div class="judge-pass" style="color: {pass_color}; border-color: {pass_color};">
                    {pass_label} | Overall Score: {judge.get('overall_score', 'N/A')}/5
                </div>
                <p class="quality-note">{judge.get('quality_note', '')}</p>
                {judge_html}
            </div>
        </div>"""
    
    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FWA Investigation Agent — Case Packages</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: #f1f5f9;
            color: #1e293b;
            line-height: 1.6;
        }}
        
        .header {{
            background: #1e293b;
            color: white;
            padding: 32px 40px;
            margin-bottom: 32px;
        }}
        
        .header h1 {{
            font-size: 24px;
            font-weight: 700;
            margin-bottom: 8px;
        }}
        
        .header p {{
            color: #94a3b8;
            font-size: 14px;
        }}
        
        .system-note {{
            background: #dbeafe;
            border: 1px solid #3b82f6;
            border-radius: 8px;
            padding: 16px 24px;
            margin: 0 40px 32px;
            font-size: 14px;
            color: #1d4ed8;
        }}
        
        .cases-container {{
            max-width: 1100px;
            margin: 0 auto;
            padding: 0 40px 60px;
            display: flex;
            flex-direction: column;
            gap: 48px;
        }}
        
        .case-card {{
            background: white;
            border-radius: 12px;
            box-shadow: 0 2px 12px rgba(0,0,0,0.08);
            overflow: hidden;
        }}
        
        .case-header {{
            background: #1e293b;
            color: white;
            padding: 24px 28px;
        }}
        
        .case-id {{
            font-size: 12px;
            color: #94a3b8;
            font-family: monospace;
            margin-bottom: 4px;
        }}
        
        .case-name {{
            font-size: 20px;
            font-weight: 700;
            margin-bottom: 6px;
        }}
        
        .case-type {{
            font-size: 13px;
            color: #cbd5e1;
        }}
        
        .case-card > div:not(.case-header) {{
            padding: 20px 28px;
            border-bottom: 1px solid #f1f5f9;
        }}
        
        .case-card h3 {{
            font-size: 13px;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #64748b;
            margin-bottom: 12px;
        }}
        
        .info-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 8px;
            font-size: 14px;
        }}
        
        .core-anomaly p {{
            font-size: 15px;
            color: #334155;
            background: #fef9c3;
            padding: 12px 16px;
            border-radius: 6px;
            border-left: 4px solid #eab308;
        }}
        
        .reasoning-step {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 14px 16px;
            margin-bottom: 10px;
            border-left: 3px solid #3b82f6;
        }}
        
        .step-header {{
            display: flex;
            align-items: center;
            gap: 10px;
            margin-bottom: 8px;
        }}
        
        .step-number {{
            background: #3b82f6;
            color: white;
            font-size: 11px;
            font-weight: 700;
            padding: 2px 8px;
            border-radius: 4px;
        }}
        
        .step-check {{
            font-weight: 600;
            font-size: 14px;
            color: #1e293b;
        }}
        
        .step-finding, .step-significance {{
            font-size: 13px;
            color: #475569;
            margin-top: 4px;
        }}
        
        .alternative {{
            background: #f8fafc;
            border-radius: 8px;
            padding: 12px 16px;
            margin-bottom: 8px;
            font-size: 13px;
            color: #475569;
            border-left: 3px solid #8b5cf6;
        }}
        
        .alt-explanation {{ margin-bottom: 6px; }}
        
        .evidence-section ul {{
            list-style: none;
            display: flex;
            flex-direction: column;
            gap: 8px;
        }}
        
        .evidence-section li {{
            font-size: 13px;
            color: #334155;
            padding: 8px 12px;
            background: #f8fafc;
            border-radius: 6px;
            padding-left: 20px;
            position: relative;
        }}
        
        .evidence-section li::before {{
            content: "→";
            position: absolute;
            left: 6px;
            color: #64748b;
        }}
        
        .confidence-section {{
            padding: 20px 28px;
            background: #f8fafc;
        }}
        
        .confidence-level {{
            font-size: 22px;
            font-weight: 800;
            margin-bottom: 4px;
        }}
        
        .confidence-label {{
            font-size: 14px;
            font-weight: 600;
            color: #334155;
            margin-bottom: 10px;
        }}
        
        .confidence-rationale {{
            font-size: 13px;
            color: #475569;
        }}
        
        .recommendation {{
            font-size: 15px;
            color: #1e293b;
            background: #f0fdf4;
            padding: 14px 16px;
            border-radius: 8px;
            border-left: 4px solid #16a34a;
            margin-bottom: 12px;
        }}
        
        .compliance-note {{
            font-size: 12px;
            color: #64748b;
            font-style: italic;
        }}
        
        .judge-pass {{
            font-size: 13px;
            font-weight: 700;
            padding: 8px 14px;
            border: 2px solid;
            border-radius: 6px;
            display: inline-block;
            margin-bottom: 10px;
        }}
        
        .quality-note {{
            font-size: 13px;
            color: #475569;
            margin-bottom: 14px;
        }}
        
        .judge-criterion {{
            background: #f8fafc;
            border-radius: 6px;
            padding: 10px 14px;
            margin-bottom: 8px;
        }}
        
        .criterion-header {{
            display: flex;
            justify-content: space-between;
            margin-bottom: 4px;
        }}
        
        .criterion-label {{
            font-size: 13px;
            font-weight: 600;
            color: #334155;
        }}
        
        .criterion-score {{
            font-size: 14px;
            font-weight: 800;
        }}
        
        .criterion-comment {{
            font-size: 12px;
            color: #64748b;
        }}
        
        .footer {{
            text-align: center;
            padding: 32px;
            color: #94a3b8;
            font-size: 12px;
        }}
    </style>
</head>
<body>

<div class="header">
    <h1>FWA Investigation Agent — Case Packages</h1>
    <p>Agentic AI Pre-Investigation Triage | Proof of Concept | Cotiviti Assessment</p>
    <p style="margin-top:8px;">Model: Llama 4 Scout via Groq | Evaluation: LLM-as-Judge | Cases grounded in DOJ 2026 National Fraud Takedown patterns</p>
</div>

<div class="system-note">
    <strong>System Note:</strong> These case packages are produced by an autonomous investigation agent and delivered to the SIU analyst in place of a raw risk score. The agent reasons through billing evidence, considers alternative explanations, and recommends a next action. All denial and referral decisions remain with the human SIU analyst. This system is compliant with AMA June 2026 policy on AI in coverage determinations.
</div>

<div class="cases-container">
    {cases_html}
</div>

<div class="footer">
    <p>FWA Investigation Agent POC | Aryamani Boruah | Cotiviti Agentic AI Research Intern Assessment | June 2026</p>
    <p>Synthetic cases based on documented fraud patterns. Not real provider data.</p>
</div>

</body>
</html>"""
    
    return html
