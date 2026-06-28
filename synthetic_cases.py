"""
Synthetic Claims Data for FWA Investigation POC
Three cases grounded in real documented fraud patterns from:
- DOJ National Health Care Fraud Takedown, June 2026
- HHS/CMS Common Types of Health Care Fraud Fact Sheet
- Recent Healthcare Fraud Settlements (2024)
"""

CASES = [
    {
        "case_id": "FWA-2026-001",
        "case_name": "Wound Allograft Overbilling",
        "fraud_type": "Billing for medically unnecessary services / diagnosis-procedure mismatch",
        "source_reference": "Pattern consistent with DOJ June 2026 National Fraud Takedown - Wound Allograft Schemes",
        "provider": {
            "name": "Coastal Dermatology Associates",
            "npi": "1234567890",
            "specialty": "Dermatology",
            "location": "Miami, FL",
            "years_billing": 3,
            "prior_investigation_flag": False
        },
        "flagged_claim": {
            "procedure_code": "Q4121",
            "procedure_description": "Amniotic wound allograft application",
            "diagnosis_code": "S00.01XA",
            "diagnosis_description": "Superficial abrasion of scalp, initial encounter",
            "billed_amount": 14500.00,
            "units_billed": 10,
            "date_of_service": "2026-05-15",
            "prior_authorization_obtained": False,
            "prior_authorization_required": True
        },
        "billing_history": {
            "allograft_procedures_last_90_days": 312,
            "peer_average_allograft_procedures_last_90_days": 104,
            "peer_deviation_percent": 200,
            "billing_volume_spike_percent": 280,
            "spike_start_date": "2026-02-01",
            "avg_billed_per_procedure": 14200.00,
            "peer_avg_billed_per_procedure": 3100.00
        },
        "coding_analysis": {
            "diagnosis_supports_procedure": False,
            "clinical_note": "Amniotic allografts are indicated for chronic non-healing wounds such as diabetic ulcers and venous leg ulcers. Superficial abrasions (S00.01XA) are minor injuries that heal without intervention and do not meet clinical criteria for allograft application.",
            "upcoding_flag": True
        },
        "peer_comparison": {
            "specialty": "Dermatology",
            "geography": "Miami-Dade County, FL",
            "peers_analyzed": 47,
            "provider_percentile": 99
        }
    },

    {
        "case_id": "FWA-2026-002",
        "case_name": "Complex E&M Upcoding - False Positive",
        "fraud_type": "Suspected upcoding - high complexity evaluation and management codes",
        "source_reference": "Pattern consistent with Bluestone Physician Services $14.9M settlement - E&M upcoding",
        "provider": {
            "name": "Northside Internal Medicine Group",
            "npi": "9876543210",
            "specialty": "Internal Medicine",
            "location": "Rural Appalachian Kentucky",
            "years_billing": 12,
            "prior_investigation_flag": False
        },
        "flagged_claim": {
            "procedure_code": "99205",
            "procedure_description": "Office visit - new patient, high medical decision complexity",
            "diagnosis_code": "E11.65",
            "diagnosis_description": "Type 2 diabetes with hyperglycemia, with multiple comorbidities",
            "billed_amount": 320.00,
            "units_billed": 1,
            "date_of_service": "2026-05-20",
            "prior_authorization_obtained": True,
            "prior_authorization_required": True
        },
        "billing_history": {
            "high_complexity_em_percent": 78,
            "peer_average_high_complexity_em_percent": 35,
            "peer_deviation_percent": 123,
            "billing_volume_spike_percent": 0,
            "spike_start_date": None,
            "avg_billed_per_visit": 298.00,
            "peer_avg_billed_per_visit": 187.00
        },
        "coding_analysis": {
            "diagnosis_supports_procedure": True,
            "clinical_note": "Patient population consists of 84% Medicare beneficiaries with multiple chronic conditions including Type 2 diabetes, COPD, heart failure, and CKD. High complexity E&M coding is clinically appropriate for patients presenting with 3 or more chronic conditions requiring active management. Diagnosis codes submitted across the flagged claims are consistent with the complexity level billed.",
            "upcoding_flag": False
        },
        "peer_comparison": {
            "specialty": "Internal Medicine",
            "geography": "Rural Appalachian Kentucky",
            "peers_analyzed": 12,
            "provider_percentile": 91
        },
        "contextual_factors": {
            "rural_designation": "Health Professional Shortage Area (HPSA)",
            "patient_acuity_index": "High - 84% Medicare, avg 4.2 chronic conditions per patient",
            "solo_practice": True,
            "note": "Rural HPSA designation with limited peer providers. High acuity patient population is documented and consistent with elevated complexity billing."
        }
    },

    {
        "case_id": "FWA-2026-003",
        "case_name": "Behavioral Health Session Volume Anomaly",
        "fraud_type": "Billing for services not rendered / physically impossible session volume",
        "source_reference": "Pattern consistent with DOJ June 2026 Takedown - behavioral health billing fraud ($49M Virginia scheme)",
        "provider": {
            "name": "ClearMind Behavioral Health Clinic",
            "npi": "5556667770",
            "specialty": "Outpatient Behavioral Health",
            "location": "Richmond, VA",
            "years_billing": 2,
            "prior_investigation_flag": False
        },
        "flagged_claim": {
            "procedure_code": "90837",
            "procedure_description": "Individual psychotherapy, 60 minutes",
            "diagnosis_code": "F32.1",
            "diagnosis_description": "Major depressive disorder, single episode, moderate",
            "billed_amount": 175.00,
            "units_billed": 45,
            "date_of_service": "2026-05-10",
            "prior_authorization_obtained": True,
            "prior_authorization_required": False
        },
        "billing_history": {
            "avg_daily_sessions_billed": 45,
            "peer_average_daily_sessions": 12,
            "peer_deviation_percent": 275,
            "billing_volume_spike_percent": 310,
            "spike_start_date": "2026-01-15",
            "avg_billed_per_session": 175.00,
            "peer_avg_billed_per_session": 162.00
        },
        "staffing_data": {
            "licensed_clinicians_on_staff": 3,
            "sessions_per_clinician_required": 15,
            "session_duration_minutes": 60,
            "required_hours_per_clinician_per_day": 15,
            "documentation_time_per_session_minutes": 15,
            "total_hours_required_per_clinician": 18.75,
            "hours_in_working_day": 8,
            "physically_possible": False
        },
        "coding_analysis": {
            "diagnosis_supports_procedure": True,
            "clinical_note": "Diagnosis codes are clinically appropriate for individual psychotherapy. The anomaly is in session volume, not coding accuracy.",
            "upcoding_flag": False,
            "volume_fraud_flag": True
        },
        "documentation_review": {
            "sessions_with_complete_notes": 18,
            "sessions_with_missing_notes": 27,
            "note_completion_rate_percent": 40
        },
        "peer_comparison": {
            "specialty": "Outpatient Behavioral Health",
            "geography": "Richmond, VA Metro",
            "peers_analyzed": 23,
            "provider_percentile": 99
        }
    }
]
