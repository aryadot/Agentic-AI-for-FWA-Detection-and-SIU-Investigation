"""Labeled evaluation cases for the FWA investigation agent.

Every case gives the agent raw evidence only: counts, peer counts, staffing,
codes and context. No pre-computed conclusions (no "diagnosis supports
procedure", "upcoding flag", "peer deviation percent" or "percentile"), so
the agent has to do the reasoning itself.

Each case carries a label fixed in advance:
  ESCALATE         evidence points to fraud
  CLOSE            the anomaly is real but has a legitimate explanation
  REQUEST_RECORDS  suspicious, but the evidence is not enough either way

and the figures the agent should compute, for an arithmetic check.
Cases are generated from templates with a fixed seed, not written by an
LLM, and some include irrelevant details as distractors. Provider names
and NPIs are fictional."""

import random

SEED = 7
DISTRACTORS = [
    "Practice changed billing software vendors two years ago.",
    "Provider relocated to a new office within the same city last year.",
    "Practice added online appointment scheduling this year.",
    "Provider's malpractice insurance carrier changed last year.",
    "Front desk staff turnover was high this year.",
]


def _provider(rng, i, specialty, location):
    return {
        "name": f"Provider {i:02d} ({specialty})",
        "npi": f"9{rng.randint(100000000, 999999999)}",  # fictional
        "specialty": specialty,
        "location": location,
        "years_billing": rng.randint(2, 15),
    }


def skin_substitute(rng, i, label):
    """Skin substitute (allograft) billing. Fraud when applied to minor
    wounds; legitimate at a wound clinic treating chronic ulcers."""
    peer = rng.randint(80, 120)
    if label == "ESCALATE":
        dx = ("S00.01XA", "Superficial abrasion of scalp, initial encounter")
        specialty, count = "Dermatology", int(peer * rng.uniform(2.5, 3.5))
        context = "General dermatology practice; no wound care program."
    elif label == "CLOSE":
        dx = ("L97.512", "Non-pressure chronic ulcer of right foot, fat layer exposed")
        specialty, count = "Wound Care", int(peer * rng.uniform(2.5, 3.5))
        context = ("Hospital-affiliated wound care center; receives referrals for "
                   "diabetic foot ulcers from four endocrinology practices. "
                   "Documented failure of 4+ weeks of standard care before application.")
    else:
        dx = ("L97.512", "Non-pressure chronic ulcer of right foot, fat layer exposed")
        specialty, count = "Podiatry", int(peer * rng.uniform(2.0, 2.6))
        context = ("Diagnoses are consistent with the procedure. Records showing "
                   "whether standard care was tried first were not provided.")
    return {
        "provider": _provider(rng, i, specialty, "Miami-Dade County, FL"),
        "claim": {"procedure": "Q4121 Skin substitute (amniotic allograft), per sq cm",
                  "diagnosis": f"{dx[0]} {dx[1]}",
                  "prior_authorization_required": True,
                  "prior_authorization_obtained": label != "ESCALATE"},
        "evidence": {"skin_substitute_procedures_last_90_days": count,
                     "peer_mean_procedures_last_90_days": peer,
                     "peers_in_comparison": rng.randint(30, 60)},
        "context": context,
        "truth_figures": {"volume_ratio_to_peers": round(count / peer, 2)},
    }


def therapy_hours(rng, i, label):
    """Psychotherapy session volume vs clinician capacity."""
    duration, doc_min, workday = 60, 15, 8
    if label == "ESCALATE":
        clinicians = rng.randint(2, 4)
        sessions = clinicians * rng.randint(13, 16)
    elif label == "CLOSE":
        clinicians = rng.randint(7, 10)
        sessions = clinicians * rng.randint(5, 6)
    else:
        clinicians = rng.randint(4, 6)
        sessions = clinicians * 7  # 8.75 hours: over a day, but not by much
    hours = sessions / clinicians * (duration + doc_min) / 60
    return {
        "provider": _provider(rng, i, "Outpatient Behavioral Health", "Richmond, VA"),
        "claim": {"procedure": "90837 Psychotherapy, 60 minutes",
                  "diagnosis": "F32.1 Major depressive disorder, single episode, moderate",
                  "prior_authorization_required": False,
                  "prior_authorization_obtained": False},
        "evidence": {"average_sessions_billed_per_day": sessions,
                     "licensed_clinicians_on_staff": clinicians,
                     "session_length_minutes": duration,
                     "documentation_minutes_per_session": doc_min,
                     "standard_workday_hours": workday,
                     "peer_mean_sessions_per_day": rng.randint(10, 14)},
        "context": ("Clinic hours and clinician schedules were not provided."
                    if label == "REQUEST_RECORDS" else "Clinic open weekdays, 8 hours."),
        "truth_figures": {"hours_per_clinician_per_day": round(hours, 2)},
    }


def em_upcoding(rng, i, label):
    """Share of office visits billed at the highest complexity level."""
    peer_share = rng.randint(30, 38)
    if label == "ESCALATE":
        share = rng.randint(70, 82)
        acuity = {"average_chronic_conditions_per_patient": round(rng.uniform(0.8, 1.3), 1),
                  "average_patient_risk_score": round(rng.uniform(0.7, 0.9), 2)}
        context = "Urban practice; patient panel younger and healthier than peers."
    elif label == "CLOSE":
        share = rng.randint(70, 82)
        acuity = {"average_chronic_conditions_per_patient": round(rng.uniform(3.8, 4.6), 1),
                  "average_patient_risk_score": round(rng.uniform(1.9, 2.4), 2)}
        context = ("Rural Health Professional Shortage Area; solo practice serving "
                   "mostly elderly patients with multiple chronic conditions.")
    else:
        share = rng.randint(55, 62)
        acuity = {}
        context = "Patient acuity data was not provided."
    return {
        "provider": _provider(rng, i, "Internal Medicine", "Kentucky"),
        "claim": {"procedure": "99215 Office visit, established patient, high complexity",
                  "diagnosis": "E11.65 Type 2 diabetes with hyperglycemia",
                  "prior_authorization_required": False,
                  "prior_authorization_obtained": False},
        "evidence": {"share_of_visits_at_highest_level_percent": share,
                     "peer_mean_share_at_highest_level_percent": peer_share, **acuity},
        "context": context,
        "truth_figures": {"share_ratio_to_peers": round(share / peer_share, 2)},
    }


def billing_spike(rng, i, label):
    """Sudden rise in monthly billing."""
    before = rng.randint(40000, 60000)
    after = int(before * rng.uniform(2.8, 3.4))
    if label == "ESCALATE":
        staff_before = staff_after = rng.randint(3, 5)
        context = ("No new clinicians, locations or services. 40% of new patients "
                   "live more than 100 miles away.")
    elif label == "CLOSE":
        staff_before = rng.randint(3, 4)
        staff_after = staff_before * 3
        context = ("Practice merged with a neighboring group; clinicians and their "
                   "existing patient panels transferred at the time of the increase.")
    else:
        staff_before, staff_after = rng.randint(3, 5), None
        context = "Current staffing and any changes to the practice were not provided."
    ev = {"monthly_billed_before_usd": before, "monthly_billed_after_usd": after,
          "clinicians_before": staff_before}
    if staff_after is not None:
        ev["clinicians_after"] = staff_after
    return {
        "provider": _provider(rng, i, "Physical Therapy", "Houston, TX"),
        "claim": {"procedure": "97110 Therapeutic exercise, each 15 minutes",
                  "diagnosis": "M54.50 Low back pain",
                  "prior_authorization_required": False,
                  "prior_authorization_obtained": False},
        "evidence": ev,
        "context": context,
        "truth_figures": {"billing_ratio_after_to_before": round(after / before, 2)},
    }


TEMPLATES = {
    "skin_substitute": skin_substitute,
    "therapy_hours": therapy_hours,
    "em_upcoding": em_upcoding,
    "billing_spike": billing_spike,
}

# 8 fraud, 7 false-positive traps, 5 insufficient evidence.
PLAN = [
    ("skin_substitute", "ESCALATE"), ("skin_substitute", "ESCALATE"),
    ("skin_substitute", "CLOSE"), ("skin_substitute", "CLOSE"),
    ("skin_substitute", "REQUEST_RECORDS"),
    ("therapy_hours", "ESCALATE"), ("therapy_hours", "ESCALATE"),
    ("therapy_hours", "CLOSE"), ("therapy_hours", "CLOSE"),
    ("therapy_hours", "REQUEST_RECORDS"),
    ("em_upcoding", "ESCALATE"), ("em_upcoding", "ESCALATE"),
    ("em_upcoding", "CLOSE"), ("em_upcoding", "CLOSE"),
    ("em_upcoding", "REQUEST_RECORDS"),
    ("billing_spike", "ESCALATE"), ("billing_spike", "ESCALATE"),
    ("billing_spike", "CLOSE"),
    ("billing_spike", "REQUEST_RECORDS"), ("billing_spike", "REQUEST_RECORDS"),
]


def build_cases() -> list[dict]:
    rng = random.Random(SEED)
    cases = []
    for i, (template, label) in enumerate(PLAN, start=1):
        case = TEMPLATES[template](rng, i, label)
        if rng.random() < 0.5:
            case["context"] += " " + rng.choice(DISTRACTORS)
        case.update({"case_id": f"EVAL-{i:02d}", "template": template, "label": label})
        cases.append(case)
    rng.shuffle(cases)  # so labels are not in a predictable order
    return cases


def agent_view(case: dict) -> dict:
    """What the agent sees: everything except the label and the truth."""
    return {k: v for k, v in case.items()
            if k not in ("label", "template", "truth_figures")}


if __name__ == "__main__":
    from collections import Counter
    cases = build_cases()
    print(f"{len(cases)} cases")
    print(Counter(c["label"] for c in cases))
    print(Counter((c["template"], c["label"]) for c in cases))
