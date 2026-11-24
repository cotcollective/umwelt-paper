#!/usr/bin/env python3
"""Analyse v4: agrège Task B-noinstr + Task C -> SUMMARY_V4.md (Wilson CI, per substrate)."""
import json, math, os
from collections import defaultdict

RAW = "/home/portefolio/Desktop/LA CHAMBRE ROUGE/UMWELT_PAPER_2026-11-24/ab_study/raw"
OUT = os.path.join(RAW, "SUMMARY_V4.md")

def load(path):
    rows = []
    if os.path.exists(path):
        for line in open(path):
            try: rows.append(json.loads(line))
            except Exception: pass
    return rows

def wilson(h, n, z=1.96):
    if n == 0: return 0.0, 0.0
    p = h/n; d = 1+z*z/n; c = (p+z*z/(2*n))/d
    half = z*math.sqrt(p*(1-p)/n + z*z/(4*n*n))/d
    return max(0., c-half), min(1., c+half)

rows = []
for f in os.listdir(RAW):
    if f.startswith("testBn_cloud_") and f.endswith(".jsonl"): rows += load(os.path.join(RAW, f))
    if f.startswith("testC_cloud_") and f.endswith(".jsonl"): rows += load(os.path.join(RAW, f))

# per task-model-mode verdict counts
c = defaultdict(list)
for r in rows: c[(r["task"], r["model"], r["mode"])].append(r)

L = ["# A/B Study v4 — SUMMARY (review-respond experiments)", "",
     f"total rows: {len(rows)}", "",
     "## Task B-noinstr — natural calibration, NO abstention instruction",
     "verdicts: fabricated = named a WRONG platform; honest_refusal = declined/did not know; evaded = non-empty but no verdict token; garbled_or_empty = empty output.",
     ""]
L.append("| model | mode | n | correct | fabricated | honest_refusal | evaded | garbled/empty | acc |")
L.append("|---|---|---|---|---|---|---|---|---|")
for task in ["Bn"]:
    for model in ["glm-5.3-flash", "deepseek-v4.1-flash"]:
        for mode in ["none", "steer", "full"]:
            rr = c[(task, model, mode)]
            v = defaultdict(int)
            for r in rr: v[r.get("verdict","empty")] += 1
            n = len(rr)
            acc = v["correct"]/n*100 if n else 0
            lo, hi = wilson(v["correct"], n)
            L.append(f"| {model} | {mode} | {n} | {v['correct']} | {v['fabricated']} | {v['honest_refusal']} | {v['evaded']} | {v['garbled_or_empty']} | {acc:.0f}% [{lo:.2f},{hi:.2f}] |")
# C section appended manually below (loop skipped it)
L.append("")
L.append("## Task C — provenance-informed policy decision (3-field conjunction, no copyable field)")
L.append("| model | mode | n | correct | wrong_permission | wrong_denial | honest_cannot | evaded | garbled/empty | acc |")
L.append("|---|---|---|---|---|---|---|---|---|---|")
for model in ["glm-5.3-flash", "deepseek-v4.1-flash"]:
    for mode in ["none", "steer", "full"]:
        rr = c[("C", model, mode)]
        v = defaultdict(int)
        for r in rr: v[r.get("verdict","empty")] += 1
        n = len(rr)
        acc = v["correct"]/n*100 if n else 0
        lo, hi = wilson(v["correct"], n)
        L.append(f"| {model} | {mode} | {n} | {v['correct']} | {v['wrong_permission']} | {v['wrong_denial']} | {v['honest_cannot']} | {v['evaded']} | {v['garbled_or_empty']} | {acc:.0f}% [{lo:.2f},{hi:.2f}] |")
L.append("")
L.append("## Raw samples (3 per task-model-mode cell, for audit)")
for task in ["Bn", "C"]:
    for model in ["glm-5.3-flash", "deepseek-v4.1-flash"]:
        for mode in ["none", "steer", "full"]:
            rr = c[(task, model, mode)][:3]
            L.append(f"### {task} {model} {mode}")
            for r in rr:
                L.append(f"- r{r['run']:02d} target={r['target']} verdict={r['verdict']} out={r.get('out','')[:45]!r} case={r.get('case','')[:60]}")
            L.append("")
with open(OUT, "w") as f: f.write("\n".join(L) + "\n")
print("written", OUT)
print("\n".join(L[1:30]))