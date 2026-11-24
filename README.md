# UMWELT — Artifact Bundle

**Paper**: *Selectively Rendered: A Token-Cost Analysis of Channel Provenance in LLM Agent Harnesses*
**Author**: Dave Senez (ORCID 0009-0005-3410-323X)
**Revision**: v4 (responds to two hostile-review rounds; see CHANGELOG in the manuscript)

## Contents

| path | description |
|---|---|
| `UMWELT_PAPER_v3_REVIEWED.md` | manuscript (v4 text, updated after second review) |
| `raw/testA_results.jsonl` | local qwen2.5:7b pilot (52 runs; pilot-only, retrieval rates disqualified in §6.2) |
| `raw/testA_cloud_glm-5.3-flash.jsonl` | Test A retrieval, glm-5.3-flash, 180 runs |
| `raw/testA_cloud_deepseek-v4.1-flash.jsonl` | Test A retrieval, deepseek-v4.1-flash, 180 runs |
| `raw/testB_cloud_*.jsonl` | Task B provenance-field extraction (instructed fallback), 2 substrates × 60 |
| `raw/testBnoinstr_cloud_*.jsonl` | Task B-noinstr (natural calibration, no UNKNOWN instruction), 2 substrates × 60 |
| `raw/testC_cloud_*.jsonl` | Task C provenance-informed policy decision, 2 substrates × 60 |
| `raw/SUMMARY_ALL.md` | aggregated tables (Tasks A+B, Wilson CIs) |
| `raw/SUMMARY_V4.md` | aggregated tables (Tasks B-noinstr + C) |
| `raw/verified_bibliography_v3.md` | bibliography verification trail (arXiv API + DOI content-negotiation, 2026-11-24) |
| `scripts/run_ab_v2.py` | pilot harness (local Ollama, Qwen tokenizer) |
| `scripts/run_ab_v3_cloud.py` | cloud replication harness (Tasks A+B, 2 substrates) |
| `scripts/run_ab_v4_policy.py` | review-respond harness (B-noinstr + C) |
| `scripts/analyze_v3.py`, `scripts/analyze_v4.py` | aggregation + Wilson CI | 
| `scripts/cross_harness_verify.py` | Cordis channel-blind verification (5 checks) |

## Substrate access facts

- Endpoint: `https://ollama.com/v1/chat/completions` (OpenAI-compatible; auth: Bearer)
- Model identifiers, as listed by the provider at access time (2026-11-24): `glm-5.3-flash`, `deepseek-v4.1-flash`
- All runs: temperature 0, `max_tokens=500` (v4) / `200-120` (v3), per-run provider-reported token totals recorded in each JSONL row
- Retries: on HTTP 429/5xx with 1.5–4.5s backoff; no run silently dropped

## Reproduction

```bash
python3 scripts/run_ab_v3_cloud.py     # 480 runs (need OLLAMA_API_KEY in ~/.hermes/.env)
python3 scripts/run_ab_v4_policy.py    # 240 runs
python3 scripts/analyze_v3.py && python3 scripts/analyze_v4.py
python3 scripts/cross_harness_verify.py --path /path/to/deepseek-harness
```

## Known limitations (mirrors manuscript §9.4)

- n=2 harnesses; no rendering-positive harness searched or tested
- Author-constructed renderers for the `full` mode (Hermes ships no such mode)
- Task A ceilings (wrong instrument — retained for the negative result only)
- Synthetic 3-message sessions; production conversations are richer

## Bibliography verification note

All arXiv IDs and DOIs were resolved live (arXiv API, doi.org content negotiation) on 2026-11-24; the trail (what was fabricated in v2, what replaced it, with real titles from the API) is in `raw/verified_bibliography_v3.md`. The checks are one-line `curl` re-runnable by any reviewer:

```bash
curl -s "http://export.arxiv.org/api/query?id_list=2510.09023" | grep -A2 "<title>"
curl -s "http://export.arxiv.org/api/query?id_list=2608.21500" | grep -A2 "<title>"   # [23] Peng et al., SecOPD — verified live 2026-11-24: Yibo Peng, "SecOPD: Mitigating Adaptive Prompt Injections by On-Policy Distillation"
curl -s "https://doi.org/10.1016/S0893-6080(98)00066-5" -H "Accept: application/vnd.citationstyles.csl+json" | head -c 200   # Wolpert & Kawato
```

(Note: `2510.09023` is Nasr & Carlini, "The Attacker Moves Second". A reviewer twice proposed `2410.05295` for the same paper — that identifier resolves to Xiaogeng Liu's "AutoDAN-Turbo"; the claim is incorrect.)
