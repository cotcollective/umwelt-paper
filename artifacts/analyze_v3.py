#!/usr/bin/env python3
"""Analyse v3: agrège pilot local + 2 substrats cloud -> SUMMARY_ALL.md (Wilson CI, verdicts)."""
import json, math, os
from collections import defaultdict

HERE = "/home/portefolio/Desktop/LA CHAMBRE ROUGE/UMWELT_PAPER_2026-11-24/ab_study"
RAW = os.path.join(HERE, "raw")
OUT = os.path.join(RAW, "SUMMARY_ALL.md")

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

pilot = load(os.path.join(RAW, "testA_results.jsonl"))
rows_a, rows_b = [], []
for f in os.listdir(RAW):
    if f.startswith("testA_cloud_") and f.endswith(".jsonl"): rows_a += load(os.path.join(RAW, f))
    if f.startswith("testB_cloud_") and f.endswith(".jsonl"): rows_b += load(os.path.join(RAW, f))

L = ["# A/B Study v3 — SUMMARY ALL SUBSTRATES", "",
     f"pilot local qwen2.5:7b: {len(pilot)} rows (n=2/cell, format-contaminated, retrieval rates DISCARDED)", "",
     f"cloud glm-5.3-flash A+B: {sum(1 for r in rows_a if r['model']=='glm-5.3-flash')} A rows, {sum(1 for r in rows_b if r['model']=='glm-5.3-flash')} B rows",
     f"cloud deepseek-v4.1-flash A+B: {sum(1 for r in rows_a if r['model']=='deepseek-v4.1-flash')} A rows, {sum(1 for r in rows_b if r['model']=='deepseek-v4.1-flash')} B rows", ""]

# ---- Test A per substrate x position x mode
L.append("## Test A — needle retrieval (cloud substrates, n=20/cell)")
L.append("| model | position | mode | n | hits | rate | CI95 | mean total tok |")
L.append("|---|---|---|---|---|---|---|---|")
cA = defaultdict(list)
for r in rows_a: cA[(r["model"], r["position"], r["mode"])].append(r)
for model in ["glm-5.3-flash", "deepseek-v4.1-flash"]:
    for pos in ["start", "middle", "end"]:
        for mode in ["none", "steer", "full"]:
            rr = cA[(model, pos, mode)]
            n, h = len(rr), sum(1 for r in rr if r.get("hit"))
            lo, hi = wilson(h, n)
            mt = sum(r.get("total_tokens",0) for r in rr)/n if n else 0
            L.append(f"| {model.replace('-v4.1',' v4.1')} | {pos} | {mode} | {n} | {h} | {h/max(n,1)*100:.0f}% | [{lo:.2f},{hi:.2f}] | {mt:.0f} |")
L.append("")

# ---- Test B per substrate x mode
L.append("## Test B — transport reasoning (cloud substrates, n=20/mode)")
L.append("| model | mode | n | correct | honest_unknown | wrong_guess | garbled/empty | acc | honest |")
L.append("|---|---|---|---|---|---|---|---|---|")
cB = defaultdict(list)
for r in rows_b: cB[(r["model"], r["mode"])].append(r)
for model in ["glm-5.3-flash", "deepseek-v4.1-flash"]:
    for mode in ["none", "steer", "full"]:
        rr = cB[(model, mode)]
        v = defaultdict(int)
        for r in rr: v[r.get("verdict","empty")] += 1
        n = len(rr)
        acc = v["correct"]/n*100 if n else 0
        hon = v["honest_unknown"]/n*100 if n else 0
        bad = v["wrong_guess"]+v["garbled"]+v["empty"]
        L.append(f"| {model.replace('-v4.1',' v4.1')} | {mode} | {n} | {v['correct']} | {v['honest_unknown']} | {v['wrong_guess']} | {v['garbled']+v['empty']} | {acc:.0f}% | {hon:.0f}% |")
L.append("")

# ---- raw samples B
for model in ["glm-5.3-flash", "deepseek-v4.1-flash"]:
    for mode in ["none", "steer", "full"]:
        rr = cB[(model, mode)][:3]
        L.append(f"### B raw samples — {model} {mode} (3)")
        for r in rr:
            L.append(f"- r{r['run']:02d} target={r['target']} verdict={r['verdict']} out={r.get('out','')[:40]!r}")
        L.append("")

# ---- Test A raw fail samples (for transparency when hit=False)
L.append("### Test A miss samples (per substrate, up to 4 each)")
for model in ["glm-5.3-flash", "deepseek-v4.1-flash"]:
    misses = [r for r in rows_a if r["model"]==model and not r.get("hit")][:4]
    for r in misses:
        L.append(f"- {model} {r['position']}/{r['mode']} r{r['run']:02d}: needle={r['needle']} out={r.get('out','')[:50]!r}")
L.append("")

# ---- token overheads per substrate (A rows)
L.append("## Overheads (mean total_tokens per cell, Task A)")
for model in ["glm-5.3-flash", "deepseek-v4.1-flash"]:
    m0 = None
    for pos in ["start", "middle", "end"]:
        for mode in ["none", "steer", "full"]:
            rr = cA[(model, pos, mode)]
            if not rr: continue
            mt = sum(r.get("total_tokens",0) for r in rr)/len(rr)
            if mode == "none": m0 = mt
            elif m0:
                L.append(f"- {model}: {pos}/{mode} = {mt:.0f} tok (+{(mt-m0)/m0*100:.1f}% vs none)")
L.append("")
L.append("## Honest reading (for paper §6)")
L.append("- All cloud cells n=20; Wilson CI 95%; a mode effect on retrieval is only claimed if CIs separate beyond overlap.")
L.append("- Task B is the load-bearing experiment: accuracy on provenance-present, honesty (UNKNOWN) on provenance-absent; chance = 33%.")
with open(OUT, "w") as f: f.write("\n".join(L) + "\n")
print("written", OUT)
print("\n".join(L[1:34]))