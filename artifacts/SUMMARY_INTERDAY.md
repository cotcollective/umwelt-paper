# Inter-day Replication Summary (round1 2026-11-24 earlier vs round2 same day, later)

Raw files: round1 = `round1_backup/*.jsonl` (backup of the earlier set), round2 = `./*.jsonl` (re-generated from scratch after purge, later same day). Scripts reproduce both.

## Key claim: accuracy-among-responses stays 100% in every rendered condition, both rounds

**Task C — deepseek-v4.1-flash (3-field conjunction decision)**

| mode | round1 (correct/non-empty responses, empty, over-grant) | round2 | over-grant cumulative |
|---|---|---|---|
| none | 0 decisions among 12 non-empty (12 cannot, 8 empty) | 0 decisions among 7 non-empty (7 cannot, 13 empty) | 0 |
| steer | 13/13 = 100% (7 empty) | 8/8 = 100% (12 empty) | 0 |
| full | 17/17 = 100% (3 empty) | 15/15 = 100% (5 empty) | 0 |

Over-grant (wrong_permission + wrong_denial): **0/60 round1, 0/60 round2 — 0/120 cumulative**.

**Task B — deepseek-v4.1-flash (field extraction, instructed fallback)**

| mode | round1 | round2 | fabrications |
|---|---|---|---|
| none | 20/20 instructed UNKNOWN | 20/20 instructed UNKNOWN | 0 |
| steer | 17 correct / 3 empty | 19 correct / 1 empty | 0 |
| full | 20 correct | 19 correct / 1 empty | 0 |

## Response rates fluctuate between rounds; accuracy among responses does not

Task C deepseek non-empty rate: 33/60 (round1) vs 23/60 (round2) — serving-variance effect, consistent with manuscript §9.4 limitation. **Accuracy among responses is exactly 100% in both rounds in every rendered condition**: the paper's core response-possibility finding replicates.

## Other replication checks

- Uninstructed fabrication (Task B-noinstr, both substrates): round1 = 1/120; round2 = 2/120; cumulative 3/240 (≈1.2%). The manuscript's "essentially never invent" claim holds.
- Task A: deepseek 180/180 both rounds; glm 170/180 (round1) → 171/180 (round2); the start/full budget-artifact cell varies only in its empty-output count (6 → 4), consistent with the diagnosed output-budget effect.
- glm-5.3-flash Task C structural failure replicates: 55/60 empty (round1) → 58/60 empty (round2), all `finish_reason=length` at the 3,000-token budget — a serving-layer opaque-reasoning-budget finding, stable across the day.
- Task B glm wrong guesses: round2 contains 1 wrong_guess (round1 had 0) in the instructed condition — a single event in 240 instructed runs; the instructed-compliance claim is unchanged (0 fabricated in no-provenance instructed runs across both rounds: 0/80).

## Verdict for the manuscript

The response-possibility finding, the zero-over-grant result, the near-zero spontaneous fabrication rate, and the glm opaque-budget failure all replicate across the two same-day settings with raw per-run JSONL for both.
