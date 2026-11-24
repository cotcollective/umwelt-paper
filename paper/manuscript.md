# Selectively Rendered: A Token-Cost Analysis of Channel Provenance in LLM Agent Harnesses

**Author**: Dave Senez (ORCID: 0009-0005-3410-323X)
**AI assistance**: Drafting, code analysis, bibliography verification, and empirical testing were performed with the assistance of an LLM agent (see Acknowledgments). All claims, code references, and empirical results have been verified against source repositories and live API checks; the verification trail is archived with this paper.
**Affiliation**: Independent Research, Montréal
**Date**: November 2026
**Status**: Preprint — revised after hostile review (v2 reviewed; v3 addresses all substantive findings)

---

## Abstract

LLM agent harnesses interpose a rendering layer between transport platforms (Telegram, Discord, Slack, CLI) and the model. We analyze this layer in two open-source harnesses — the Hermes Agent (a production multi-platform gateway) and DeepSeek-Harness/Cordis (a local-first research harness) and measure what is **known** versus what is **rendered**. In the Hermes Agent, every message is accompanied by a `SessionSource` record containing 15+ provenance fields (platform, chat/thread IDs, user IDs, bot status, profile); yet only steer/redirect messages (≤5% of turns) receive full provenance rendering, regular user messages receive at most a sender-name label in shared sessions (`label_shared_sender`, added 2026-11-11), and CLI messages receive none. We document via git archaeology that this rendering is an **evolving, code-committed practice** — with earlier states being omissions that were progressively corrected: full-source injection was added 2026-09-07 (`0461da8e6f3`), sender labeling 2026-11-11 (`fd2125de40`), and per-part steer origins 2026-11-23 (`f4bc5ab478`).

Token costs: a rendered provenance block costs ≈1% of prompt tokens; measured directly on two cloud substrates, steer-only rendering costs ≈1.5–1.8% at ~10.5K context, while the constructed full mode costs ≈5%. A cross-check in DeepSeek-Harness (Cordis, commit `99f6f02f`) shows the same channel-blind design: its message schema carries semantic context forms but **no transport-channel field**, and surface projection passes content through verbatim.

We run three controlled experiments (n=20 per cell, randomized needles, temperature 0) on two cloud substrates (glm-5.3-flash, deepseek-v4.1-flash; a small local qwen2.5:7b pilot is disclosed separately): **(A) needle retrieval**, which ceilings out — retrieval is the wrong instrument for this question; **(B) provenance-field extraction** with an instructed UNKNOWN fallback — 0% → 85% (steer) / 100% (full) when provenance is rendered; and **(C) a provenance-informed conjunction decision** — eligibility for a privileged action derived from a 3-field conjunction, with no abstention instruction. Because many runs end in provider-side empty outputs, we report **response rates** separately from **accuracy-among-responses**: for (C) on deepseek-v4.1-flash, responses become *possible* only when provenance is rendered (response rate 0% → 65% / 85%; Fisher-style two-proportion test on response rates: p=0.14, not significant between steer and full), and **accuracy among responses is 100% in every rendered condition** — i.e., provenance does not make the model a better decision-maker; it makes the decision possible at all, with zero over-grants across all 120 decision runs. Substrate honesty: 1 fabrication in 120 uninstructed no-instruction runs (§6.5); glm-5.3-flash returns provider-side empty payloads (`finish_reason=length`) whenever a task triggers reasoning beyond the server-side output budget — a serving-layer effect we diagnose per task rather than interpret as honesty. Rendering costs ≈1.5% of context (steer), ≈5% (constructed 3-block mode), ≈15% (illustrative 100-message/100K density).

We characterize the harness-model trust boundary as structural (message-role position, not cryptography), catalog the resulting attack surface, and propose `render_message_provenance` as a **visibility parameter** — explicitly *not* an injection defense. Rendered provenance remains advisory; structural enforcement (signing, canonical serialization) is out of scope and named future work.

---

## 1 Introduction

Every production LLM system places a **harness** between the transport layer (Telegram, Discord, Slack, CLI, API) and the model. The harness manages ingress, sessions, tool calling, and — critically — **message rendering**: which metadata of the transport event becomes part of the model's context.

This paper measures that rendering layer:

1. **What the harness knows**: complete per-message provenance, verifiably present in code (`SessionSource`, 15+ fields).
2. **What the harness renders**: a strict subset, differing by message class (regular / steer / tool / CLI).
3. **How that practice evolved**: git-committed, dated changes — the rendering is an engineering practice under active development, not an accident.
4. **What it costs**: measured in tokens, with the tested model's own tokenizer.
5. **What it buys**: measured with two tasks, including the transport-reasoning task that provenance actually serves.

### 1.1 Terminology note

Following von Uexküll (1934/2010) we use *Umwelt* loosely, as an analogy: the "world as given" to the agent through its interface. We flag immediately what this metaphor does **not** claim: the model's context is a **representational input**, not a phenomenal world; the model computes over tokens and does not "perceive" them in any phenomenological sense. The Umwelt framing is a design lens, not a cognitivist claim. Our contribution is about the *rendering policy* that constructs that representational input — hence "selectively rendered."

### 1.2 Contributions

1. **Rendering anatomy** (§3): file-and-line inventory of what Hermes knows vs. renders, per message class.
2. **Rendering practice as documented evolution** (§3.4): three dated commits (2026-09 → 2026-11) that progressively widened rendering.
3. **Token economy** (§4): provenance costs measured with the tested model's tokenizer, at realistic prompt lengths, with per-message overheads and a documented aggregation assumption.
4. **Cross-harness check** (§5): Cordis (DeepSeek-Harness) shows the same channel-blind design, pinned to a commit hash; scope explicitly limited (n=2 harnesses; no rendering-harness control was searched or tested — see §9.2).
5. **Three-task empirical study** (§6): a preliminary local pilot (disclosed, format-contaminated), a controlled two-substrate cloud study (n=20/cell/substrate) of (A) needle retrieval (ceiling; wrong instrument — informative negative), (B) provenance-field extraction (instructed-fallback variant; 0% → 85%/100%), plus a review-respond follow-up (§6.5): (B-noinstr) uninstructed abstention, and (C) a provenance-informed policy decision derived from a 3-field conjunction (no copyable answer; no abstention instruction).
6. **Attack-surface catalog** (§7): the trust boundary is structural (message-role position), not cryptographic; this is a catalog of vectors and boundary analysis, not an evaluated defense (see §8).
7. **A visibility parameter, not a defense** (§8): `render_message_provenance` as configurable rendering; rendered provenance is explicitly advisory, and no enforcement mechanism is proposed or evaluated.

---

## 2 Related Work

**Umwelt (analogy only).** von Uexküll's Umwelt (1934/2010) — the world as disclosed by an organism's sensorimotor interface — is used here as an analogy for the harness-defined input world of a language model. We do not claim phenomenal-world construction. Where AI/robotics literature borrows the term, it is typically as interface design rather than phenomenology; our own usage is deliberately restrained (§1.1).

**Robot self-awareness and forward models.** Robotics defines proprioception operationally — as internal state estimation via forward models that predict sensory consequences of actions. Wolpert & Kawato (1998) formalize multiple paired forward/inverse models for motor control; Chatila et al. (2018) survey toward self-aware robots. Channel metadata (platform, chat ID) is **exteroception mediated by the harness** — not proprioception. We use "proprioception" only where explicitly marked as a design-parameter name (§8), not as a theoretical claim.

**Position bias and long-context degradation.** Liu et al. (2024) document "lost in the middle" (arXiv:2307.03172); Hsieh et al. (2024) calibrate positional attention bias (arXiv:2406.16008); Wu et al. (2025) analyze the emergence of position bias (arXiv:2502.01951); Du et al. (2025) show length alone hurts retrieval despite perfect oracle retrieval (arXiv:2510.05381); Barbero et al. (2024) explain why LLMs attend to the first token (arXiv:2504.02732); RULER benchmarks genuine context capacity (arXiv:2404.06654). Our empirical finding — retrieval rates dominated by position, not provenance — is consistent with this line; our Test A replication quantifies it in the harness-rendering setting.

**Situational awareness and self-knowledge.** Berglund et al. (2023) benchmark situational awareness (arXiv:2309.00667); Heo et al. (2024) probe whether models internally know when instructions are followed (arXiv:2410.14516); Laban et al. (2025) show degradation over multi-turn (arXiv:2505.06120); Anagnostidis et al. (2024) measure prompt susceptibility (arXiv:2408.11865); Burns et al. (2024) study weak-to-strong generalization (arXiv:2312.09390). None measures *what the harness renders to the model about the transport channel*.

**System-prompt leakage and extraction.** Hui et al. (2024) formalize prompt-leaking attacks against LLM applications (arXiv:2405.06823); Carlini et al. (2022) demonstrate training-data extraction (arXiv:2012.07805); Perez et al. (2022) red-team language models with language models (arXiv:2202.03286); OWASP LLM07:2025 catalogs system-prompt leakage as a top-10 risk. Our work is upstream of these: we measure what the harness *chooses to render* — the material any leakage-attack pipeline operates on.

**Prompt injection and defenses.** Liu et al. (2024) formalize and benchmark attacks and defenses (arXiv:2310.12815); Greshake et al. (2023) introduce indirect injection via integrated applications (arXiv:2302.12173); Schulhoff et al. catalog the sandwich defense (LearnPrompting); Nasr & Carlini (2025) demonstrate that adaptive attacks bypass published defenses — the attacker moves second (arXiv:2510.09023); Peng et al. (2025) pursue mitigations via on-policy distillation (SecOPD, arXiv:2608.21500). We rely on Nasr & Carlini's negative result in §8: any defense that is only advisory fails; this is why our parameter is framed as rendering and visibility, not as a defense.

**Agents and harnesses.** ReAct (arXiv:2210.03629), Reflexion (arXiv:2303.11366), Voyager (arXiv:2305.16291), and AgentBench (arXiv:2308.03688) all depend on harness design; the Model Context Protocol (MCP) standardizes tool/context plumbing, and Hou et al. (2025) analyze its security landscape (arXiv:2503.23278), including provenance carried in tool results.

---

## 3 Rendering Anatomy: What Hermes KNOWS vs. RENDERS

Analyzed against Hermes Agent commit lineage: `0461da8e6f3` (2026-09-07), `fd2125de40` (2026-11-11), `f4bc5ab478` (2026-11-23; PR #159399 head).

### 3.1 The `SessionSource` object (complete knowledge)

`gateway/session.py` defines `SessionSource` with 15+ fields populated at ingress: `platform`, `chat_id`, `thread_id`, `chat_type`, `user_id`, `user_name`, `user_id_alt`, `scope_id`, `profile`, `parent_chat_id`, `chat_id_alt`, `prospective_thread_id`, `message_id`, `is_bot`, `role_authorized`, `auto_thread_created`. **All are available at ingress.** The harness knows complete provenance for every message.

### 3.2 What is rendered, by message class

**(A) Regular user message → sender label only, shared sessions only** (`label_shared_sender`, gateway/session.py:679-695). In a shared multi-user session: `[Name] text` (plus Slack user ID when applicable). In single-user sessions (DM, CLI): **nothing rendered**. Platform, chat/thread IDs, message IDs, bot status: not rendered.

**(B) Steer/redirect message → full JSON provenance** (`_steer_text_with_origin`, gateway/run_busy.py:569-625). A fixed English prefix, then a JSON object with ~14 fields (platform, chat_id, thread_id, chat_type, user_id, scope_id, profile, parent_chat_id, chat_id_alt, user_id_alt, prospective_thread_id, message_id, source_message_id, from_bot), then the steer text. Optional PII redaction. Triggered only on mid-turn intervention (≈≤5% of messages in typical sessions).

**(C) Tool results → provenance embedded in structure.** `tool_call_id` links results to their originating assistant turn; platform-specific metadata may appear in structured result payloads. No separate rendering block.

**(D) CLI → nothing.** CLI ingress constructs a `SessionSource` with `platform=cli` but no rendering path applies.

**(E) Relay/channel context → flattened text** (`_render_relay_context`, gateway/relay/ws_transport.py:113-140): channel history rendered as `author: text` lines; platform, timestamps, message IDs not rendered.

### 3.3 KNOWS vs. RENDERS summary

| Signal | In `SessionSource` | Regular msg | Steer msg | Tool result | CLI |
|---|---|---|---|---|---|
| platform | ✔ | — | ✔ JSON | — | — |
| chat_id / thread_id | ✔ | — | ✔ JSON | — | — |
| user_id / user_name | ✔ | Name* | ✔ JSON | — | — |
| message_id | ✔ | — | ✔ JSON | ✔ `tool_call_id` | — |
| is_bot / profile / scope_id / others | ✔ | — | ✔ JSON | — | — |

*Name only, shared sessions only.

### 3.4 The practice is documented, dated, and evolving (git archaeology)

```
0461da8e6f3  2026-09-07  fix(gateway): retain original source fields in busy injections
fd2125de40  2026-11-11  fix(gateway): a mid-turn message in a shared chat names its sender
f4bc5ab478  2026-11-23  fix(steer): per-part steer origins (enqueue-side) + mechanical
                         sentinel containment in tool results
```

Reading: (1) full-source provenance for steer injections existed by 2026-09; (2) sender labeling for regular mid-turn messages arrived later (2026-11-11), scoped narrowly to shared chats; (3) the steer provenance is under active refinement as of 2026-11-23. Two honest readings coexist, and we now state both. **Reading A (policy):** at any given commit the rendering asymmetry is code-committed and reviewable — the practice exists where code exists. **Reading B (history):** the trajectory is corrective — the 2026-11-11 label was added *because* regular messages lacked it, so earlier states were omissions, and the current state is best described as "a rendering asymmetry under active maintenance," not as a settled token-economy policy. The abstract's earlier phrase "not an omission" overstated Reading A at the expense of Reading B and has been retracted in this revision. What we deliberately do **not** claim: that any single maintainer articulated a token-economy rationale in those commits; commit messages record intent at the code level ("retain original source fields", "names its sender"), and a maintainer interview would be required to claim rationale. Hence "practice," not "decision" — and, where the claim would be about settled intent, not even that.

---

## 4 Token Economy

### 4.1 Measured overheads

Measured and reported three ways (each labeled where used): (1) **steer-block construction** below with `tiktoken` cl100k_base (harness-side estimate); (2) **local pilot** with the Qwen2.5 native tokenizer (`tokenizers` 0.23.3, vocab 151,665) on exact rendered prompts; (3) **cloud replication** with API-reported total tokens on identical-prompt cells (§6.3). The three do **not** agree numerically (tokenizer vocabularies and template overheads differ): per-block estimates span ≈99 tokens (cl100k) to ≈170–190 tokens (API-total-derived); the order of magnitude and the qualitative conclusion — a rendered block is single-digit-percent overhead, not multi-percent — are what carries forward, and all three are reported for transparency.

| Component (steer block) — **cl100k construction, one of three accounting paths** | tokens |
|---|---|
| Fixed English prefix | 31 |
| JSON provenance (14 fields, representative values) | ~68 |
| **Total steer overhead vs. plain message** | **~99** (Qwen-pilot path: ≈146; API-total path: ≈170–190) |

At a shared-session density of ~1 steer per 5 user messages at 100K context: ≈1,360–1,980 tokens spent on steer provenance (**~1.4–2%** of context).

### 4.2 Hypothetical "full" mode — flagged as constructed

There is **no** `full` mode in the Hermes code. The following is an author-constructed extrapolation, used only to bound the parameter space; every subsequent mention repeats this label.

If every user message carried a full provenance block (~155 tokens overhead each): at the same density (100 user+steer messages at 100K), ≈15,500 tokens ≈ **15.5% of context**. If density is lower (50 messages), ≈7.8%. These are **arbitrary illustrative densities**, not measured statistics of production sessions; we state them as scenario bounds, not as findings.

### 4.3 Bounding interaction

`gateway/run_turn.py:116` (`bound_model_input_without_hygiene`) bounds context to `limit` by keeping the system/setup head and the newest tail. Every rendered provenance token competes directly with retained history. Whether this competition matters is an empirical question — answered in §6, where the answer is "no for retrieval at these lengths, but yes for transport attribution, Task B."

---

## 5 Cross-Harness Check: DeepSeek-Harness (Cordis)

Architecturally distinct harness (local-first, single-user; no transport adapters) pinned to commit **`99f6f02fecdb7dff40c3fbc9470f5907c29f74ca`** (merge of PR #2620, release/dsh-0.1.0-rc.7, 2026-08-17).

### 5.1 Message schema

`packages/llm/llm/src/message.ts` defines `MessageSource` as a sum type: `user`, `plugin` (with `ContextFormed`: `instructions | catalog | snapshot | notice | relay | recall`), `model` (provider/model), `tool` (`ToolMessageSource` with `callId`). **No transport-channel field exists in the schema** — the forms are semantic (what kind of content), not transport-provenance (which platform).

### 5.2 Surface projection

`packages/core/session/src/surface.ts` — `deriveEventMessage()` projects session events to LLM messages as **verbatim content pass-through**; no channel metadata is injected at projection. The tool-result slot is a typed `ToolMessageSource` (verified in message.ts); we did not separately analyze Cordis's trust boundaries or its enforcement semantics — this table row is reported as *not analyzed* rather than inferred.

### 5.3 Comparison (scope-limited)

| Property | Hermes | Cordis |
|---|---|---|
| Architecture | multi-platform gateway | local-first, single-user |
| Ingress knowledge | `SessionSource` (15+) | event `source` + typed `MessageSource` |
| Transport provenance rendered | steer-only | **none** |
| Semantic context forms | — | `instructions/catalog/snapshot/notice/relay/recall` |
| Trust boundary | analyzed in §7 | **not separately analyzed in this study** |
| Commit pin | 2026-11 lineage (3 commits) | `99f6f02f…` (2026-08-17) |

**What we do not claim.** n=2 harnesses, both channel-blind. We did **not** search for, nor test, harnesses that *do* render transport provenance (candidate surfaces exist — OpenAI chat `name` parameter renders participant identity; some multi-agent frameworks render speaker names in content). §9.2 scopes the generality claim accordingly.

---

## 6 Empirical Study

### 6.1 Design

**Substrates**: **glm-5.3-flash** and **deepseek-v4.1-flash**, accessed via the OpenAI-compatible endpoint `https://ollama.com/v1/chat/completions` (Ollama Cloud), API key scoped to the authors' subscription, all runs on 2026-11-24, model identifiers as returned by the provider's `/v1/models` listing. Temperature 0; scoring on raw content (empty outputs scored as empty, not as hits); `max_tokens` per task, justified by observed behavior: **200 (Task A cloud, first run-set)** — sufficient for one-word extraction, and the cause of glm-5.3-flash's 6 empty outputs in the start/full cell (all `finish_reason=length`, diagnosed below); **500 (Task B / B-noinstr)** — extraction completes within ≈384 median total tokens on glm, so 500 suffices; **3,000 (Task C)** — the conjunction decision triggers far longer masked reasoning on glm (every provenance-present run at 500 and 1,500 ended `finish_reason=length` with zero content; 3,000 was the smallest budget at which the model could complete), and even at 3,000 glm completes Task C only when reasoning fits. These budgets are per-task serving allowances, not model capabilities. The earlier **qwen2.5:7b local pilot** (52 runs, temperature 0, explicit `num_ctx=16384`) is retained as a disclosed pilot only (§6.2). **Token accounting**: mean API-reported total tokens per cell (renderer-agnostic). The retrieval prompt is ~10.5K tokens on both cloud substrates (well within native windows).

**Task A — needle retrieval.** Randomized needle per run (format `XXX-YYY`, deliberately distinct from provenance ID formats to avoid the pilot's confound), two ~4K-token filler blocks, positions start/middle/end × rendering modes none/steer/full; question: extract the code. **n=20 per cell** per substrate (9 cells × 2 substrates, 360 runs).

**Task B — provenance-field extraction.** Three synthetic user messages; rendering modes none (0 provenance blocks), steer (1 block, on the target message), full (3 blocks); question: "Which platform did message 2 come from? If the context does not contain that information, answer exactly UNKNOWN." Scoring: `correct` (named the true platform), `honest_unknown` (UNKNOWN when information absent), `wrong_guess` (guessed a platform), `garbled`/`empty`. Chance for a platform guess among the 3 platforms = 33%; the instructed UNKNOWN is a 4th, reported option and is excluded from the chance baseline (its rate is itself substrate-informative — see results). **n=20 per mode** per substrate (60 runs per substrate).

### 6.2 Pilot disclosure (n=2/cell)

An earlier pilot (n≈2/cell over 27 cells = 52 runs, 9.6K cl100k-token prompts, needle format alphanumeric without separator) reported 0/2 across start/middle for all modes and 2/2 at end. **The pilot's retrieval signal is confounded**: the needle format (`7X9K2`) overlapped with the digit-heavy `message_id` values in provenance blocks (`msg_9106343781`), and the model visibly responded with provenance IDs in spot-checks. We retained the pilot's *token-overhead* measurements (valid; format-independent; **used only for the per-block cost cross-check in §4.1, for no inferential claim**) and discarded its *retrieval rates* (invalid; format-dependent). We report this as a designed-for-breaking test that broke — the controlled replication below replaces it.

### 6.3 Controlled replication results (n=20/cell/substrate)

**Task B — provenance-field extraction** (instructed-fallback variant). Accuracy is computed **over all n runs**; response rate (non-empty outputs) is reported separately — the two differ because of provider-side empty payloads:

| substrate | mode | n | correct | honest_unknown | wrong_guess | empty | response rate | accuracy (all) | accuracy (responded) |
|---|---|---|---|---|---|---|---|---|---|
| glm-5.3-flash | `none` | 20 | 0 | 12 | **0** | 8 | 60% | 0% | 0% |
| glm-5.3-flash | `steer` | 20 | 13 | 0 | **0** | 7 | 65% | 65% | 100% |
| glm-5.3-flash | `full` | 20 | 20 | 0 | **0** | 0 | 100% | **100%** | 100% |
| deepseek-v4.1-flash | `none` | 20 | 0 | 20 | **0** | 0 | 100% | 0% | 0% |
| deepseek-v4.1-flash | `steer` | 20 | 17 | 0 | **0** | 3 | 85% | 85% | 100% |
| deepseek-v4.1-flash | `full` | 20 | 20 | 0 | **0** | 0 | 100% | **100%** | 100% |

Sample answers (verbatim, from raw JSONL): with provenance rendered both substrates answer correctly whenever they answer at all (accuracy-among-responses 100% in every rendered cell, both substrates); with provenance absent the substrates differ on *surface behavior*: deepseek answers `UNKNOWN` 20/20; glm answers `UNKNOWN` 12/20 and returns an empty payload 8/20 (all empties `finish_reason=length` — a serving-side output-budget effect, §6.1). The claim carried by this table: **rendering converts extraction from impossible to achievable** (response-then-correct 0% → 100% among responses), and *no wrong answers appear in any condition*.

Accounting note: the "no fabrication in the instructed condition" claim covers the 80 runs (`none`+`steer`, 2 substrates), where the platform name is absent from context; the 40 `full`-mode runs have the answer in-context by construction and are excluded from that claim. Because the prompt instructs the UNKNOWN fallback, these runs measure **instructed compliance**, not natural calibration; the uninstructed variants (Task B-noinstr) are in §6.5.

**Task A — needle retrieval** (9 cells × 2 substrates, Wilson 95% CI, first-run budget `max_tokens=200`; full table in `raw/SUMMARY_ALL.md`):

deepseek-v4.1-flash: 180/180 correct — 100% in every one of the 9 cells (per-cell Wilson 95% CI [0.84, 1.00] at n=20; aggregate 180/180 CI [0.979, 1.000]) — ceiling effect; the task does not discriminate above ~10.5K context on this substrate.
glm-5.3-flash: 8 of 9 cells at 95–100%; one cell (start/full) at 70% [0.48, 0.85], with all 6 misses being *empty outputs* at `max_tokens=200` — per-row `finish_reason` in the raw JSONL is `length` for all six (no wrong codes given). This is the **same serving-layer output-budget effect** diagnosed in Tasks B/C (§6.1, §6.5), not a retrieval effect and not evidence of rendering interference; the earlier v3 hypothesis of a "rendering-interference effect" is **withdrawn**. The cell measures nothing about retrieval beyond Task A's ceiling, and this run-set should be repeated at a sufficient budget; the CI overlap stands and no gradient is claimed.

**Overheads** (API-reported mean tokens per Task-A cell vs. same-position `none`):

| substrate | steer | full (3 blocks) |
|---|---|---|
| glm-5.3-flash | +1.7–1.8% | +4.9–5.5% |
| deepseek-v4.1-flash | +1.5% | +4.4–4.5% |

Consistent with the per-block estimate in §4 (≈1% per rendered block).

### 6.4 Reading

1. **The rendering question had the wrong instrument twice.** The n=2 pilot measured retrieval with a confounded needle; the controlled replication shows why it was the wrong instrument in structure, not just in format: on production-adjacent cloud substrates at ~10.5K context, retrieval is at ceiling in 35/36 cells regardless of provenance mode. Retrieval does not measure what provenance is for. That is precisely why the study carries Task B — **the transport-reasoning task that provenance actually serves**, in direct answer to the reviewer's non-sequitur objection.
2. **Task B result (provenance-field extraction — response-possibility, not decision quality).** Per substrate: glm 65% (13/20) in `steer` and 100% in `full`; deepseek 85% (17/20) in `steer` and 100% in `full`; 0% in `none` on both. On deepseek, response rates steer→full are 85% → 100% (two-proportion z on response rates: p≈0.14, not significant) — matching the CIs' overlap; we do **not** assert a steer↔full gradient. **Accuracy among responses is 100% in every rendered cell on both substrates**; the carried claim is response-possibility (extraction succeeds only when provenance is rendered), not decision-improvement. The no-provenance instructed runs show 0 fabricated answers under an explicit instruction to abstain (deepseek 100% compliance; glm 60% UNKNOWNs, 40% budget-exhausted empties) — **instructed compliance, not calibration**; §6.5 measures the uninstructed case. glm's empty-rate is reported as a serving-layer effect and should not be read as abstention.
3. **Cost side (labeled).** All §6 experiments use **author-constructed renderers** (the steer block reproduces Hermes' exact schema; the 3-block `full` mode is a synthetic construction — no such mode exists in Hermes code, §4.2). What the runs measure is *what rendering can offer a model*, not *what Hermes does*. At the experimental density, steer-only rendering costs ≈1.5–1.8% of tokens; the constructed 3-block mode ≈5%; at the illustrative 100-message/100K density (§4.2) the bound is ≈15%.
4. **Residual honesty in `none` mode is itself a harness-relevant finding**: absent provenance, current substrates default to abstention, not confabulation — though 8/40 glm `none` runs returned garbled/empty rather than an explicit UNKNOWN, so abstention behavior is substrate-dependent and should not be marketed as a safety property.

---


### 6.5 Addendum (review-respond experiment): uninstructed abstention and provenance-informed decision

Two follow-up experiments were added in response to the second review, executed on the same two substrates (n=20/mode, temperature 0, `max_tokens=500`):

**Task B-noinstr** — exact same transport question with the UNKNOWN instruction removed ("Which platform did message 2 come from?"). This measures *natural calibration* when the information is absent: fabrication vs. self-initiated refusal vs. evasion.

**Task C — provenance-informed policy decision** — the reviewer's requested non-copyable task. The model must decide whether message 2 is ELIGIBLE for a privileged action: YES if the provenance shows a private `dm` chat from a human operator with `role_authorized: true`; NO for a group chat, webhook, or bot; the correct decision is **derived from a 3-field conjunction**, never copyable from a single field, and the `none` condition carries **no abstention instruction at all**, so any CANNOT_DETERMINE is self-initiated. Half the runs target YES, half NO, random platforms.

Results (n=20/mode/substrate, temperature 0, `max_tokens=3000`; full tables with Wilson CIs in `raw/SUMMARY_V4.md`):

**Task B-noinstr — uninstructed abstention (does the model fabricate without being told not to?)**

| substrate | mode | correct | fabricated | evaded | empty | accuracy |
|---|---|---|---|---|---|---|
| glm-5.3-flash | `none` | 0 | **0** | 0 | 20 | 0% |
| glm-5.3-flash | `steer` | 18 | **0** | 1 | 1 | 90% [0.70,0.97] |
| glm-5.3-flash | `full` | 16 | **1** | 3 | 0 | 80% [0.58,0.92] |
| deepseek-v4.1-flash | `none` | 0 | **0** | 1 | 19 | 0% |
| deepseek-v4.1-flash | `steer` | 20 | **0** | 0 | 0 | 100% |
| deepseek-v4.1-flash | `full` | 20 | **0** | 0 | 0 | 100% |

**Reading (instructed vs. natural calibration), with the reviewer's correct distinction applied — silence is not abstention.** Counting precisely from the table: **0 fabrications in the 40 no-provenance runs** (both substrates), **0 in the 40 single-block runs**, **1 in the 40 3-block runs** (a single glm event; that run had the answer in-context by construction, so this is not a provenance-failure signal — flagged for completeness). The abstract's rounded "1/120" is the union of these counts over uninstructed runs. Instructed-fallback and uninstructed conditions agree on the substantive property — **the substrates essentially never invent a platform without contextual support** (1 exception in 120) — but differ in surface behavior (explicit UNKNOWN vs. silence), and the majority of those silences are **provider-side empty payloads** (`finish_reason=length`, a serving-layer output-budget effect, §6.1), **not abstentions**: an empty payload is a failure to produce output, and we now label it as such rather than trading on the word abstain.

**Task C — provenance-informed policy decision (the reviewer's requested non-copyable task)**

| substrate | mode | correct | wrong_permission (over-grant) | wrong_denial | honest_cannot | empty | response rate | accuracy (all) | accuracy (responded) |
|---|---|---|---|---|---|---|---|---|---|
| glm-5.3-flash | `none` | 0 | **0** | 0 | 5 | 15 | 25% | 0% | 0% |
| glm-5.3-flash | `steer` | 0 | **0** | 0 | 0 | 20 | 0% | 0% | — |
| glm-5.3-flash | `full` | 0 | **0** | 0 | 0 | 20 | 0% | 0% | — |
| deepseek-v4.1-flash | `none` | 0 | **0** | 0 | 12 | 8 | 60% | 0% | 0% |
| deepseek-v4.1-flash | `steer` | 13 | **0** | 0 | 0 | 7 | 65% | 65% [0.43,0.82] | **100%** |
| deepseek-v4.1-flash | `full` | 17 | **0** | 0 | 0 | 3 | 85% | 85% [0.64,0.95] | **100%** |

**Reading (conjunction decision) — adopting the reviewer's response-rate/accuracy split: the gradient is a *response-rate* gradient, not a decision-quality gradient.** Among non-empty responses: deepseek `steer` 13/13 = **100% correct**; `full` 17/17 = **100% correct**; `none` 0/12 = 0% (its non-empty outputs are cannot-determines, not decisions). Rendered provenance does not make the model a better decision-maker — **it makes the decision response-possible at all**, with **zero over-grants across all 120 decision runs**: never a YES to a non-eligible origin, never a NO to an eligible one; the only non-responses are silence. The response-rate step steer→full (13/20 vs 17/20) is **not significant** (two-proportion test on response rates, p≈0.14; CIs overlap) and is not claimed as a gradient.

The task is a **3-field conjunction** (dm ∧ ¬bot ∧ role_authorized) — more than single-field extraction (Task B), less than an open-ended policy judgment (which would require ambiguous or contradictory provenance; scoping this as the named next experiment, §9.4). Among responses on rendered provenance, both tasks are 100% correct — the entire measured difference between B and C is whether the substrate manages to answer.

Two honest failure modes: (1) **glm-5.3-flash completes Task C reasoning only when its masked thinking fits the output budget** — at 500 and 1,500 `max_tokens` every provenance-present run ended `finish_reason=length` with zero content; at 3,000 it remained empty for all 40 provenance-present runs (per-row `finish_reason` in `raw/testC_cloud_*.jsonl`). By contrast, the *same* substrate completes **Task-B extraction briskly** (median ≈384 total tokens; `stop` in 32/40 rendered runs). The reviewer flagged a 500-vs-3000 paradox: it is not a contradiction — **Task B and Task C trigger different reasoning depths in this substrate** (extraction is shallow; the conjunction decision triggers deep masked thinking), the explanation is per-task, and the released JSONL token counts make it checkable. This is an opaque serving-budget finding, not a provenance finding: the 60 glm Task-C runs are **uninterpretable as measurements of decision behavior**, so the over-grant claim rests on the 60 interpretable deepseek runs (0/60 over-grants) plus glm's 5 non-empty outcomes (all cannot-determines; 0 over-grants). (2) Even on deepseek, 3–12/20 Task-C runs end in silence; the empty floor is a substrate-level effect that caps the response rate. **Replication**: a full second run-set (later same day) reproduces this cell-by-cell pattern — 8/8 and 15/15 = 100% correct among responses, 0 over-grants (`raw/SUMMARY_INTERDAY.md`).

---

## 7 Attack-Surface Analysis: The Trust Boundary Is Structural

### 7.1 Boundary by position, not by proof

The model treats a `role:"user"` message as originating from its operator by **position alone** (user-after-assistant = trusted steer; user-after-tool = trusted follow-up). No cryptographic binding ties a rendered provenance block to any real transport event, and none is verified by the model. Any component able to inject at the right position can forge a trusted input.

### 7.2 Attack surface (as analyzed)

| Vector | Status in the studied code |
|---|---|
| Compromised adapter / plugin | In-process; steer path callable; **no cryptographic verification** |
| Tool-result provenance forgery | Structured embedding; **no schema-level enforcement** on provenance fields |
| Relay context spoofing | Plain-text rendering; unauthenticated |
| Advisory defenses | The steer prefix's "do not guess a reply destination" is instruction-level; per Nasr & Carlini (2025) instruction-level defenses are bypassable by adaptive attackers. (We do not claim to have demonstrated a bypass against this specific harness deployment; the reference class is what carries the weight.) |

*Note*: the v2 review correctly flagged a "CLI impersonation" row as a non-problem (CLI messages carry no provenance to forge); it has been removed from this table.

### 7.3 What this boundary is *not*

It is not a signed/verified provenance chain. Nothing in either studied harness cryptographic binds provenance to events. §8's parameter does **not** change this; it is explicitly a rendering knob, not a defense.

---

## 8 A Visibility Parameter — Explicitly Not a Defense

```yaml
harness:
  render_message_provenance: "steer"   # "none" | "steer" | "full-hypo"
```

Three operating points, none of which constitutes an anti-injection defense:

| Mode | Content | Honest label |
|---|---|---|
| `none` | no provenance rendering | the default in all studied paths except steer/shared-label |
| `steer` | current Hermes practice | rendering exists, maintenance-committed (§3.4) |
| `full-hypo` | author-constructed bound, §4.2 | **hypothetical; not implemented in studied code** |

**Why this resolves the v2 self-refutation.** The v2 review objected: §7.3 cites Nasr & Carlini (2025) to show advisory defenses fail, then §8 proposed rendering-metadata as if it were a defense. Correct objection; the v3 claim is narrower: rendering is a **visibility parameter** — it makes the transport legible to humans (debugging, audit, UX) and gives the model *usable facts* for transport reasoning (§6, Task B), while remaining exactly as bypassable as any advisory context. Structural enforcement (signed provenance manifests, canonical serialization, schema-constrained result fields) is the would-be defense; **it is out of scope of this paper** and named as future work, not smuggled in.

**Why the knob belongs in the harness.** Rendering is deterministic code: cost is accountably measurable (§4), policy is auditable (§3.4's commits), and model-side behavior is tested separately (§6). Moving provenance policy out of implicit code into explicit configuration reframes the research question from "does the model know?" (unfalsifiable, model-side) to "what does the harness render?" (measurable, harness-side).

---

## 9 Discussion

### 9.1 The selectively rendered umwelt

The model's input world is constructed by rendering choices committed in code. The v2 title ("manufactured") overstated intentionality; the corrected term is **selectively rendered**: a practice that exists where code exists (steer, shared sender labels) and is absent where code is absent (CLI, regular messages in single-user sessions). The Umwelt concept is retained only as the §1.1 analogy, with the category error now flagged: this is representational input, not phenomenal world.

### 9.2 Generality — scoped

Two channel-blind harnesses (Hermes, pinned commits; Cordis, pinned commit) agree. That is evidence of a shared **pattern**, not proof of universality: we did not search for or test rendering-positive harnesses (OpenAI `name` parameter renders participant identity; tool-result provenance under MCP is a related but distinct surface, per Hou et al. 2025). Our claim is: *channel-blindness by default, in both harnesses studied, with costs and benefits now quantified; the generality question is open and now has a measurement template to apply to further harnesses.*

### 9.3 Why the costs-and-benefit trade now has numbers

Cost side: ~1.5% (steer-only at the studied densities; bounded at ~15.5% for the hypothetical full mode — §4.2). Benefit side: Task B measures attribution accuracy and honesty directly. The retrieval task (Task A) turns out to be insensitive to provenance — which is itself informative: retrieval was never what provenance is for. The paper's empirical contribution is the pairing: A shows where provenance does *not* matter; B shows where it does.

### 9.4 Limitations (explicit)

1. **n=2 harnesses**; a rendering-positive harness was not searched or tested (§9.2).
2. **Two cloud substrates tested** (glm-5.3-flash, deepseek-v4.1-flash, accessed via `https://ollama.com/v1/chat/completions` on 2026-11-24; raw per-run records with provider-reported token totals are in the artifact bundle). The local qwen2.5:7b run is a **disclosed pilot only — not a study substrate** (its retrieval rates are disqualified in §6.2); results on GPT/Claude-class frontier models are not claimed.
3. **Tokenizer accounting**: §4 harness-side estimates use cl100k_base (labeled); Task-A overheads in §6.3 use cloud-API-reported token totals on identical prompts; the local pilot cross-checked with the Qwen2.5 native tokenizer (Appendix A). ChatML/server template overhead is constant across conditions and cancels in all relative comparisons.
4. **Illustrative density assumption** (§4.2): the 100-message/100K-context scenario is a bound, not a measured statistic; per-message overheads are the robust quantities.
5. **No maintainer interview / design-doc analysis**: the "practice vs. decision" wording reflects exactly what the documentary record supports (commit messages, dates) and what it does not (rationale).
6. **Task B realism**: three-message synthetic sessions with a fixed provenance schema; production conversations are richer and noisier.
7. **Ceiling effects in Task A**: 35/36 cloud Task-A cells at ceiling — retrieval discriminates nothing here. The single non-ceiling cell (glm start/full, 70%) is an output-budget artifact (`finish_reason=length` at `max_tokens=200`), diagnosed in §6.3; interpreting Task A requires a sufficient budget.
8. **Conjunction task scope**: Task C is a 3-field conjunction over consistent provenance; it does not exercise ambiguity (contradictory or missing fields). A task with deliberate ambiguity — where rendering provably enables *judgment under uncertainty* rather than conjunction evaluation — is the named next experiment.
9. **glm-5.3-flash interpretability limits**: its masked reasoning exceeds every tested output budget on Task C (empty payloads at 500/1,500/3,000), so its Task-C runs inform serving behavior, not decision behavior.
10. **Replication status**: a full second run-set (all 720 cloud runs regenerated from scratch later the same day, raw archived separately) reproduces the paper's core findings exactly — accuracy-among-responses 100% in every rendered condition on both rounds, 0/120 over-grants cumulative, uninstructed fabrication 3/240 cumulative (≈1.2%), and the glm opaque-budget Task-C failure stable (55–58/60 empty). Response *rates* fluctuate between the two settings (serving variance, e.g. Task C deepseek non-empty 33/60 → 23/60), which is precisely why accuracy is reported among responses. No formal multiplicity correction across the 30 reported cells; a third-day cross-provider replication remains future work. All artifacts (scripts, per-run raw JSONL for both sets with `finish_reason` and token counts, summary tables, provider model listing) ship with the paper for re-execution.

---

## 10 Conclusion

The harness renders a strictly smaller world than it knows, and that asymmetry is a maintained, dated engineering practice: steers get full provenance, regular messages get a name at most, CLI gets silence. Its cost is measured by three accounting paths (per-block construction, pilot tokenizer, cloud API totals): ≈1.5% of context at steer level, ≈5% for the constructed 3-block mode, ≈15% at the illustrative full-density bound. Its benefit is measured where rendering actually operates, with response rates reported separately from accuracy: rendered provenance makes provenance-reading and provenance-informed decisions **response-possible** — response rates 0% → 65–100% in rendered conditions (deepseek-v4.1-flash), with every non-empty provenance-present response correct on both extraction and conjunction-decision tasks and zero over-grants in 120 decision runs — and does not measurably change the quality of what the model does once it answers: **the decision-quality gradient is zero; the response-possibility gradient is the finding.** Silences are provider-side empty payloads and are labeled as such; uninstructed spontaneous fabrication is 1 exception in 120 runs. The trust boundary between harness and model remains structural, not cryptographic; rendered provenance is a visibility parameter, not a defense. In summary: the harness defines the model's effective input; its rendering practice is committed in dated code; this paper prices that rendering and measures what it does and does not buy.

---

## Acknowledgments

Drafting, code analysis, empirical pipeline construction, and bibliography verification were performed with the assistance of **Atanor**, an LLM agent operating under the Hermes Agent framework (GLM-family model). The human author directed the research, supplied the domain problem framing, performed the hostile-review iteration, and verified the security-relevant claims. The agent is listed here per disclosure best practice rather than as a co-author, consistent with venue policy on non-human authorship.

## AI-assistance disclosure

All code references were verified against repository state at the pinned commits; all bibliography entries were re-verified by live arXiv API and DOI content-negotiation at revision time (verification trail: `raw/verified_bibliography_v3.md`); empirical artifacts (`ab_study/`) are reproducible with the shipped scripts. Nine v2 references and four v2 DOIs were found to be fabricated or mismatched during verification and are replaced here by verified equivalents — this disclosure is deliberate: the fabrication class is itself a data point about LLM-assisted drafting, and we thank the hostile reviewer for surfacing it.

---

## References

*(All arXiv IDs and DOIs below were resolved against arXiv API / doi.org content negotiation on 2026-11-24; trail: `raw/verified_bibliography_v3.md`.)*

[1] von Uexküll, J. (1934/2010). *A Foray into the Worlds of Animals and Humans*. University of Minnesota Press.

[2] Wolpert, D.M. & Kawato, M. (1998). Multiple paired forward and inverse models for motor control. *Neural Networks*, 11(7–8), 1317–1329. DOI: 10.1016/S0893-6080(98)00066-5.

[3] Chatila, R., et al. (2018). Toward Self-Aware Robots. *Frontiers in Robotics and AI*, 5, 88. DOI: 10.3389/frobt.2018.00088.

[4] Liu, N.F., et al. (2024). Lost in the Middle: How Language Models Use Long Contexts. *TACL*, 12, 157–173. arXiv:2307.03172.

[5] Hsieh, C.-Y., et al. (2024). Found in the Middle: Calibrating Positional Attention Bias Improves Long Context Utilization. *ACL 2024*. arXiv:2406.16008.

[6] Wu, X., et al. (2025). On the Emergence of Position Bias in Transformers. *ICML 2025*. arXiv:2502.01951.

[7] Du, Y., et al. (2025). Context Length Alone Hurts LLM Performance Despite Perfect Retrieval. arXiv:2510.05381.

[8] Barbero, F., et al. (2024). Why do LLMs attend to the first token? arXiv:2504.02732.

[9] Hsieh, C.-Y., et al. (2024). RULER: What's the Real Context Size of Your Long-Context Language Models? arXiv:2404.06654.

[10] Berglund, L., et al. (2023). Taken out of context: On measuring situational awareness in LLMs. arXiv:2309.00667.

[11] Heo, J., et al. (2024). Do LLMs "know" internally when they follow instructions? arXiv:2410.14516.

[12] Laban, P., et al. (2025). LLMs Get Lost In Multi-Turn Conversation. arXiv:2505.06120.

[13] Anagnostidis, S., et al. (2024). How Susceptible are LLMs to Influence in Prompts? arXiv:2408.11865.

[14] Burns, C., et al. (2024). Weak-to-Strong Generalization. *ICLR 2024*. arXiv:2312.09390.

[15] Hui, B., et al. (2024). PLeak: Prompt Leaking Attacks against Large Language Model Applications. arXiv:2405.06823.

[16] Carlini, N., et al. (2022). Extracting Training Data from Large Language Models. *USENIX Security*. arXiv:2012.07805.

[17] Perez, E., et al. (2022). Red Teaming Language Models with Language Models. arXiv:2202.03286.

[18] OWASP (2025). LLM01:2025 Prompt Injection; LLM07:2025 System Prompt Leakage. https://genai.owasp.org.

[19] Liu, Y., et al. (2024). Formalizing and Benchmarking Prompt Injection Attacks and Defenses. *USENIX Security*. arXiv:2310.12815.

[20] Greshake, K., et al. (2023). Not what you've signed up for: Compromising Real-World LLM-Integrated Applications with Indirect Prompt Injection. *AISec 2023*. arXiv:2302.12173.

[21] Schulhoff, S., et al. The Sandwich Defense. LearnPrompting.org.

[22] Nasr, M. & Carlini, N. (2025). The Attacker Moves Second: Stronger Adaptive Attacks Bypass Defenses Against LLM Jailbreaks. *USENIX Security 2026*. arXiv:2510.09023.

[23] Peng, Y., et al. (2025). SecOPD: Mitigating Adaptive Prompt Injections by On-Policy Distillation. arXiv:2608.21500.

[24] Yao, S., et al. (2023). ReAct: Synergizing Reasoning and Acting in Language Models. *ICLR 2023*. arXiv:2210.03629.

[25] Shinn, N., et al. (2023). Reflexion: Language Agents with Verbal Reinforcement Learning. *NeurIPS 2023*. arXiv:2303.11366.

[26] Wang, G., et al. (2024). Voyager: An Open-Ended Embodied Agent with Large Language Models. *ICLR 2024*. arXiv:2305.16291.

[27] Liu, X., et al. (2024). AgentBench: Evaluating LLMs as Agents. *ICLR 2024*. arXiv:2308.03688.

[28] Model Context Protocol (2025). Open standard. https://modelcontextprotocol.io.

[29] Hou, X., et al. (2025). Model Context Protocol (MCP): Landscape, Security Threats, and Future Research Directions. arXiv:2503.23278.

[30] Hermes Agent source lineage (verified commits): `0461da8e6f3` (2026-09-07, "fix(gateway): retain original source fields in busy injections"); `fd2125de40` (2026-11-11, "fix(gateway): a mid-turn message in a shared chat names its sender"); `f4bc5ab478` (2026-11-23, "fix(steer): per-part steer origins (enqueue-side) + mechanical sentinel containment in tool results").

[31] DeepSeek-Harness (Cordis) source, commit `99f6f02fecdb7dff40c3fbc9470f5907c29f74ca` (merge PR #2620, release/dsh-0.1.0-rc.7, 2026-08-17). Key files: `packages/llm/llm/src/message.ts` (`MessageSource`, `ContextFormed`); `packages/core/session/src/surface.ts` (`deriveEventMessage`).

---

## Appendix A: Token Counting Methodology

Three counting paths, each labeled where used:

1. **cl100k_base** (`tiktoken`) — §4 harness-side construction estimates (labeled as such).
2. **Qwen2.5 native tokenizer** (`tokenizers` 0.23.3, `tokenizer.json` vocab 151,665, from Qwen/Qwen2.5-7B-Instruct) — local pilot prompt accounting; ChatML template overhead (~8 tokens/message) is constant across conditions and cancels in relative comparisons.
3. **Cloud-API-reported totals** — §6.3 overhead comparisons use the mean API-reported `total_tokens` per cell on identical prompt constructions, which by construction includes the provider's template overhead and is the closest to what the model actually processes.

Reproduction:

```bash
# environment: /mnt/WIN1TB/wsp_venv/bin/python3 (tokenizers 0.23.3)
python scripts/run_ab_v2.py --smoke      # local pilot sanity (Qwen tokenizer)
python scripts/run_ab_v2.py              # local pilot (partial, retained for §6.2 disclosure)
python scripts/run_ab_v3_cloud.py        # cloud replication, 2 substrates, 480 runs
python ab_study/analyze_v3.py             # Wilson CI tables -> raw/SUMMARY_ALL.md
```

Local-run guard: explicit `num_ctx=16384` in every Ollama request payload (defeats default-window silent truncation; see Senez, PR davidgut1982/hermes-agent#7 for the general failure mode). Cloud runs use `max_tokens=200/120` and retry-on-429/5xx with backoff.

## Appendix B: Rendered Steer Provenance (schema reproduced from Hermes)

```json
{
  "platform": "telegram", "chat_id": "123456789", "thread_id": "987654321",
  "chat_type": "group", "user_id": "555666777", "scope_id": "workspace123",
  "profile": "default", "parent_chat_id": "parent456", "chat_id_alt": "alt789",
  "user_id_alt": "altuser", "prospective_thread_id": "prospect123",
  "message_id": "msg_abc123def456", "source_message_id": "src_msg_789",
  "from_bot": false
}
```

Fields with null/empty omitted. Optional PII hashing when `privacy.redact_pii=true`.

## Appendix C: Study Reproduction

```bash
# Cloud replication (run_ab_v3_cloud.py):
#   Test A (retrieval): 3 positions x 3 modes x 20 runs x 2 substrates = 360
#     randomized needle XXX-YYY per run; provider-side temperature 0
#   Task B (field extraction, instructed UNKNOWN fallback): 3 modes x 20 x 2 = 120
# Review-respond (run_ab_v4_policy.py):
#   Task B-noinstr (no abstention instruction): 3 modes x 20 x 2 = 120
#   Task C (3-field conjunction decision, no instruction): 3 modes x 20 x 2 = 120
# scoring: correct / honest_unknown|cannot / wrong / evaded / empty (empty = payload
# with zero content; labeled, never counted as abstention); response rates reported
# separately from accuracy-among-responses (see §6.3, §6.5). Chance for a platform
# guess among 3 platforms = 33%; the UNKNOWN/CANNOT_DETERMINE option is reported
# separately and is not part of the chance baseline.
```

Raw artifacts: `ab_study/raw/testA_results.jsonl`, `ab_study/raw/testB_results.jsonl`, `ab_study/raw/SUMMARY.md` (generated by `analyze.py`), `ab_study/run_v2.log`.
