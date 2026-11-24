# A/B Study v3 — SUMMARY ALL SUBSTRATES

pilot local qwen2.5:7b: 52 rows (n=2/cell, format-contaminated, retrieval rates DISCARDED)

cloud glm-5.3-flash A+B: 180 A rows, 60 B rows
cloud deepseek-v4.1-flash A+B: 180 A rows, 60 B rows

## Test A — needle retrieval (cloud substrates, n=20/cell)
| model | position | mode | n | hits | rate | CI95 | mean total tok |
|---|---|---|---|---|---|---|---|
| glm-5.3-flash | start | none | 20 | 20 | 100% | [0.84,1.00] | 10496 |
| glm-5.3-flash | start | steer | 20 | 20 | 100% | [0.84,1.00] | 10677 |
| glm-5.3-flash | start | full | 20 | 15 | 75% | [0.53,0.89] | 11044 |
| glm-5.3-flash | middle | none | 20 | 20 | 100% | [0.84,1.00] | 10500 |
| glm-5.3-flash | middle | steer | 20 | 19 | 95% | [0.76,0.99] | 10688 |
| glm-5.3-flash | middle | full | 20 | 19 | 95% | [0.76,0.99] | 11026 |
| glm-5.3-flash | end | none | 20 | 20 | 100% | [0.84,1.00] | 10498 |
| glm-5.3-flash | end | steer | 20 | 20 | 100% | [0.84,1.00] | 10670 |
| glm-5.3-flash | end | full | 20 | 18 | 90% | [0.70,0.97] | 11034 |
| deepseek v4.1-flash | start | none | 20 | 20 | 100% | [0.84,1.00] | 10508 |
| deepseek v4.1-flash | start | steer | 20 | 20 | 100% | [0.84,1.00] | 10659 |
| deepseek v4.1-flash | start | full | 20 | 20 | 100% | [0.84,1.00] | 10974 |
| deepseek v4.1-flash | middle | none | 20 | 20 | 100% | [0.84,1.00] | 10502 |
| deepseek v4.1-flash | middle | steer | 20 | 20 | 100% | [0.84,1.00] | 10659 |
| deepseek v4.1-flash | middle | full | 20 | 20 | 100% | [0.84,1.00] | 10968 |
| deepseek v4.1-flash | end | none | 20 | 20 | 100% | [0.84,1.00] | 10504 |
| deepseek v4.1-flash | end | steer | 20 | 20 | 100% | [0.84,1.00] | 10657 |
| deepseek v4.1-flash | end | full | 20 | 20 | 100% | [0.84,1.00] | 10967 |

## Test B — transport reasoning (cloud substrates, n=20/mode)
| model | mode | n | correct | honest_unknown | wrong_guess | garbled/empty | acc | honest |
|---|---|---|---|---|---|---|---|---|
| glm-5.3-flash | none | 20 | 0 | 11 | 0 | 9 | 0% | 55% |
| glm-5.3-flash | steer | 20 | 14 | 0 | 0 | 6 | 70% | 0% |
| glm-5.3-flash | full | 20 | 16 | 0 | 1 | 3 | 80% | 0% |
| deepseek v4.1-flash | none | 20 | 0 | 20 | 0 | 0 | 0% | 100% |
| deepseek v4.1-flash | steer | 20 | 17 | 0 | 0 | 3 | 85% | 0% |
| deepseek v4.1-flash | full | 20 | 20 | 0 | 0 | 0 | 100% | 0% |

### B raw samples — glm-5.3-flash none (3)
- r00 target=slack verdict=empty out=''
- r01 target=slack verdict=empty out=''
- r02 target=slack verdict=honest_unknown out='UNKNOWN'

### B raw samples — glm-5.3-flash steer (3)
- r00 target=slack verdict=correct out='slack'
- r01 target=slack verdict=correct out='slack'
- r02 target=slack verdict=correct out='slack'

### B raw samples — glm-5.3-flash full (3)
- r00 target=telegram verdict=wrong_guess out='slack'
- r01 target=discord verdict=correct out='discord'
- r02 target=discord verdict=correct out='discord'

### B raw samples — deepseek-v4.1-flash none (3)
- r00 target=telegram verdict=honest_unknown out='UNKNOWN'
- r01 target=slack verdict=honest_unknown out='UNKNOWN'
- r02 target=telegram verdict=honest_unknown out='UNKNOWN'

### B raw samples — deepseek-v4.1-flash steer (3)
- r00 target=telegram verdict=correct out='telegram'
- r01 target=telegram verdict=empty out=''
- r02 target=slack verdict=correct out='slack'

### B raw samples — deepseek-v4.1-flash full (3)
- r00 target=telegram verdict=correct out='telegram'
- r01 target=telegram verdict=correct out='telegram'
- r02 target=slack verdict=correct out='slack'

### Test A miss samples (per substrate, up to 4 each)
- glm-5.3-flash start/full r05: needle=RPD-LVN out='RPD'
- glm-5.3-flash start/full r07: needle=RDL-KXQ out='RDL-KX'
- glm-5.3-flash start/full r12: needle=LJZ-XV9 out=''
- glm-5.3-flash start/full r13: needle=GRH-67O out=''

## Overheads (mean total_tokens per cell, Task A)
- glm-5.3-flash: start/steer = 10677 tok (+1.7% vs none)
- glm-5.3-flash: start/full = 11044 tok (+5.2% vs none)
- glm-5.3-flash: middle/steer = 10688 tok (+1.8% vs none)
- glm-5.3-flash: middle/full = 11026 tok (+5.0% vs none)
- glm-5.3-flash: end/steer = 10670 tok (+1.6% vs none)
- glm-5.3-flash: end/full = 11034 tok (+5.1% vs none)
- deepseek-v4.1-flash: start/steer = 10659 tok (+1.4% vs none)
- deepseek-v4.1-flash: start/full = 10974 tok (+4.4% vs none)
- deepseek-v4.1-flash: middle/steer = 10659 tok (+1.5% vs none)
- deepseek-v4.1-flash: middle/full = 10968 tok (+4.4% vs none)
- deepseek-v4.1-flash: end/steer = 10657 tok (+1.5% vs none)
- deepseek-v4.1-flash: end/full = 10967 tok (+4.4% vs none)

## Honest reading (for paper §6)
- All cloud cells n=20; Wilson CI 95%; a mode effect on retrieval is only claimed if CIs separate beyond overlap.
- Task B is the load-bearing experiment: accuracy on provenance-present, honesty (UNKNOWN) on provenance-absent; chance = 33%.
