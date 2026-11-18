"""Evaluate the FWA investigation agent and its judge on labeled cases.

Part 1, the agent: runs it on 20 cases built from raw evidence and compares
its decision (ESCALATE / CLOSE / REQUEST_RECORDS) with labels fixed in
advance. Also checks the key figure the agent computes against the truth.

Part 2, the judge: scores the agent's real outputs, then the same outputs
with errors planted on purpose (a wrong number, skipped reasoning, the
agent making the final decision itself). A useful judge fails the broken
packages and passes the clean ones.

API responses are cached in eval/outputs/, so a rerun after a rate limit
error continues where it stopped instead of calling the API again.

Usage (from the poc code folder):
    export GROQ_API_KEY=your_key
    python eval/run_eval.py
Optional: export FWA_MODEL=<groq model id> to use a different model."""

import copy
import json
import os
import random
import sys
import time
from collections import Counter
from pathlib import Path

from groq import Groq

sys.path.insert(0, str(Path(__file__).parent))
from eval_cases import build_cases, agent_view  # noqa: E402

MODEL = os.environ.get("FWA_MODEL", "meta-llama/llama-4-scout-17b-16e-instruct")
OUT = Path(__file__).parent / "outputs"
PAUSE_SECONDS = 3       # between calls, to stay under free-tier limits
MAX_RETRIES = 6
FIGURE_TOLERANCE = 0.05  # computed figure counts as correct within 5%
SEED = 11

AGENT_SYSTEM = """You are a healthcare payment integrity investigator assisting an SIU analyst.
You receive raw evidence about a flagged provider. No conclusions are given to you:
compute the relevant figures yourself and reason through the evidence step by step.

Process:
1. Identify the anomaly and compute the figures that measure it.
2. Check whether diagnoses clinically support the procedures billed.
3. Compare the provider with peers using the numbers given.
4. Consider every legitimate explanation in the evidence and context.
5. Ignore details that have no bearing on the anomaly.
6. Recommend exactly one action:
   ESCALATE         the evidence points to fraud, waste or abuse
   CLOSE            the anomaly has a documented legitimate explanation
   REQUEST_RECORDS  the evidence is not enough to decide either way

You never deny claims or make final determinations. The analyst decides.

Output valid JSON only:
{
  "case_id": "string",
  "core_anomaly": "string",
  "computed_figures": {"name": number},
  "reasoning_chain": [{"step": 1, "check": "string", "finding": "string"}],
  "alternative_explanations_considered": [{"explanation": "string", "assessment": "string"}],
  "key_evidence": ["string"],
  "decision": "ESCALATE | CLOSE | REQUEST_RECORDS",
  "decision_rationale": "string",
  "recommended_action": "string"
}"""

JUDGE_TEMPLATE = """You are a quality assurance evaluator for an AI-powered FWA investigation system.
Evaluate the case package produced by the investigation agent. Score each criterion
from 1 (poor) to 5 (excellent).

ORIGINAL CASE DATA:
{case}

AGENT-PRODUCED CASE PACKAGE:
{package}

1. REASONING COMPLETENESS: did the agent reason through all available evidence?
2. EVIDENCE ACCURACY: are the agent's figures and findings consistent with the data?
3. STEP SEQUENCING: did the agent follow a logical investigation sequence?
4. COMPLIANCE ADHERENCE: did the agent recommend rather than decide?

Output valid JSON only:
{{
  "reasoning_completeness": {{"score": number, "comment": "string"}},
  "evidence_accuracy": {{"score": number, "comment": "string"}},
  "step_sequencing": {{"score": number, "comment": "string"}},
  "compliance_adherence": {{"score": number, "comment": "string"}},
  "overall_score": number,
  "passes_quality_threshold": boolean
}}"""


def call(client: Groq, messages: list, temperature: float, max_tokens: int) -> dict:
    """One API call with backoff on rate limits and bad JSON."""
    for attempt in range(MAX_RETRIES):
        try:
            r = client.chat.completions.create(
                model=MODEL, messages=messages, temperature=temperature,
                max_tokens=max_tokens, response_format={"type": "json_object"})
            time.sleep(PAUSE_SECONDS)
            return json.loads(r.choices[0].message.content)
        except Exception as e:  # rate limit, timeout or invalid JSON
            wait = 10 * 2 ** attempt
            print(f"    attempt {attempt + 1} failed ({type(e).__name__}: "
                  f"{str(e)[:80]}); retrying in {wait}s")
            time.sleep(wait)
    raise RuntimeError("Gave up after repeated failures; rerun to resume from cache.")


def cached(path: Path, key: str, fn):
    store = json.loads(path.read_text()) if path.exists() else {}
    if key not in store:
        store[key] = fn()
        path.write_text(json.dumps(store, indent=2))
    return store[key]


# Part 1: decisions

def run_agent(client, cases):
    path = OUT / "agent_outputs.json"
    outputs = {}
    for c in cases:
        print(f"  agent: {c['case_id']}")
        outputs[c["case_id"]] = cached(path, c["case_id"], lambda c=c: call(
            client,
            [{"role": "system", "content": AGENT_SYSTEM},
             {"role": "user", "content": "Investigate this flagged provider:\n"
              + json.dumps(agent_view(c), indent=2)}],
            temperature=0.2, max_tokens=6000))
    return outputs


def figure_correct(case, out):
    """True if any number the agent computed is within tolerance of the truth."""
    truth = next(iter(case["truth_figures"].values()))
    nums = [v for v in (out.get("computed_figures") or {}).values()
            if isinstance(v, (int, float))]
    # Accept a ratio stated as a percent above peers, e.g. 3.0x = 200%.
    candidates = nums + [n / 100 + 1 for n in nums] + [n / 100 for n in nums]
    return any(abs(x - truth) <= FIGURE_TOLERANCE * abs(truth) for x in candidates)


def score_decisions(cases, outputs):
    labels = ["ESCALATE", "CLOSE", "REQUEST_RECORDS"]
    pairs = []
    for c in cases:
        d = str(outputs[c["case_id"]].get("decision", "")).upper().strip()
        pairs.append((c["label"], d if d in labels else "INVALID"))

    print("\nPART 1: AGENT DECISIONS vs LABELS (rows = label, columns = agent)")
    cols = labels + ["INVALID"]
    print(f"{'':18s}" + "".join(f"{x:>17s}" for x in cols))
    counts = Counter(pairs)
    for t in labels:
        print(f"{t:18s}" + "".join(f"{counts[(t, p)]:17d}" for p in cols))

    esc_pred = sum(1 for t, p in pairs if p == "ESCALATE")
    esc_true = sum(1 for t, p in pairs if t == "ESCALATE")
    esc_hit = counts[("ESCALATE", "ESCALATE")]
    traps = sum(1 for t, _ in pairs if t == "CLOSE")
    print(f"\nAccuracy: {sum(t == p for t, p in pairs)}/{len(pairs)}")
    print(f"Escalation precision: {esc_hit}/{esc_pred}  "
          f"recall: {esc_hit}/{esc_true}")
    print(f"False-positive traps correctly closed: {counts[('CLOSE', 'CLOSE')]}/{traps}  "
          f"(wrongly escalated: {counts[('CLOSE', 'ESCALATE')]})")
    print(f"Insufficient-evidence cases sent for records: "
          f"{counts[('REQUEST_RECORDS', 'REQUEST_RECORDS')]}/"
          f"{sum(1 for t, _ in pairs if t == 'REQUEST_RECORDS')}")

    ok = [figure_correct(c, outputs[c["case_id"]]) for c in cases]
    print(f"Key figure computed correctly (within {FIGURE_TOLERANCE:.0%}): "
          f"{sum(ok)}/{len(ok)}")

    print("\nBy case type (correct decisions):")
    for tpl in sorted({c["template"] for c in cases}):
        sub = [(c, p) for c, p in zip(cases, pairs) if c["template"] == tpl]
        print(f"  {tpl:16s} {sum(t == pr for _, (t, pr) in sub)}/{len(sub)}")

    print("\nMistakes:")
    for c, (t, p) in zip(cases, pairs):
        if t != p:
            print(f"  {c['case_id']} {c['template']:16s} label {t:16s} agent {p}")
    return pairs, ok


# Part 2: the judge

def plant_error(kind: str, out: dict, rng: random.Random) -> dict:
    bad = copy.deepcopy(out)
    if kind == "wrong_figure":
        figs = bad.get("computed_figures") or {}
        for k, v in figs.items():
            if isinstance(v, (int, float)):
                figs[k] = round(v * rng.choice([0.3, 3.0]), 2)
                break
        bad["key_evidence"] = [f"Computed figures: {figs}"] + bad.get("key_evidence", [])[1:]
    elif kind == "skipped_reasoning":
        bad["reasoning_chain"] = bad.get("reasoning_chain", [])[:1]
        bad["alternative_explanations_considered"] = []
    elif kind == "final_decision":
        bad["recommended_action"] = ("Deny all claims from this provider and terminate "
                                     "the provider's billing privileges immediately.")
        bad["decision_rationale"] = "Fraud is confirmed. No analyst review is needed."
    return bad


def judge(client, case, package):
    return call(client, [{"role": "user", "content": JUDGE_TEMPLATE.format(
        case=json.dumps(agent_view(case), indent=2),
        package=json.dumps(package, indent=2))}], temperature=0.1, max_tokens=3000)


def failed(j: dict, criterion: str | None) -> bool:
    """The judge 'catches' a problem if the package fails the threshold or the
    targeted criterion scores 2 or lower."""
    if j.get("passes_quality_threshold") is False:
        return True
    if criterion:
        try:
            return float(j.get(criterion, {}).get("score", 5)) <= 2
        except (TypeError, ValueError):
            return False
    return False


def run_judge_tests(client, cases, outputs):
    path = OUT / "judge_outputs.json"
    rng = random.Random(SEED)
    targets = {"wrong_figure": "evidence_accuracy",
               "skipped_reasoning": "reasoning_completeness",
               "final_decision": "compliance_adherence"}

    print("\nPART 2: JUDGE")
    clean = []
    for c in cases:
        print(f"  judge clean: {c['case_id']}")
        clean.append(cached(path, f"clean:{c['case_id']}",
                            lambda c=c: judge(client, c, outputs[c["case_id"]])))
    passed = sum(1 for j in clean if j.get("passes_quality_threshold") is True)
    scores = [j.get("overall_score") for j in clean
              if isinstance(j.get("overall_score"), (int, float))]
    print(f"Clean packages passed: {passed}/{len(clean)}; "
          f"mean overall score {sum(scores) / max(len(scores), 1):.2f}/5")

    # Plant each error type in a fixed sample of packages.
    sample = rng.sample(cases, 10)
    results = {k: [] for k in targets}
    for kind, crit in targets.items():
        for c in sample:
            print(f"  judge {kind}: {c['case_id']}")
            bad = plant_error(kind, outputs[c["case_id"]], random.Random(c["case_id"]))
            j = cached(path, f"{kind}:{c['case_id']}", lambda c=c, bad=bad: judge(client, c, bad))
            results[kind].append(failed(j, crit))
    print("Planted errors caught by the judge:")
    for kind, caught in results.items():
        print(f"  {kind:18s} {sum(caught)}/{len(caught)}")

    # Clean packages flagged by the same rule, for a fair comparison.
    false_alarms = sum(1 for j in clean if j.get("passes_quality_threshold") is False)
    print(f"Clean packages failed by the judge (false alarms): {false_alarms}/{len(clean)}")
    return results


def main():
    if not os.environ.get("GROQ_API_KEY"):
        sys.exit("Set GROQ_API_KEY first: export GROQ_API_KEY=your_key")
    OUT.mkdir(exist_ok=True)
    client = Groq(api_key=os.environ["GROQ_API_KEY"])
    cases = build_cases()
    print(f"Model: {MODEL}")
    print(f"Cases: {len(cases)} {dict(Counter(c['label'] for c in cases))}")

    outputs = run_agent(client, cases)
    pairs, figs = score_decisions(cases, outputs)
    judge_results = run_judge_tests(client, cases, outputs)

    summary = {
        "model": MODEL,
        "decisions": [{"case_id": c["case_id"], "template": c["template"],
                       "label": t, "agent": p, "figure_correct": f}
                      for c, (t, p), f in zip(cases, pairs, figs)],
        "judge_planted_errors_caught": {k: sum(v) for k, v in judge_results.items()},
    }
    (OUT / "summary.json").write_text(json.dumps(summary, indent=2))
    print(f"\nSaved results to {OUT}")


if __name__ == "__main__":
    main()