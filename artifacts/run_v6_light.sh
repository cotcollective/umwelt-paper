#!/bin/bash
# E1+E3 light protocol — 3 local substrates sequential (E1 x4 + E3 x2 = 6 cells x N runs each)
# Pre-registered in PRE_REGISTRATION_v6.md (commit b6e469a); light scope per hostile-review round 6.
set -u
PY=/mnt/WIN1TB/wsp_venv/bin/python3
DIR="$(cd "$(dirname "$0")" && pwd)"
N="${V6_N:-60}"
cd "$DIR"
for SUB in "local/qwen2.5:7b" "local/llama3.1:8b" "local/mistral:7b"; do
  SAFE=$(echo "$SUB" | sed 's/local\//local_/; s/:/_/g')
  echo "=== $(date -u +%FT%TZ) starting $SUB ($SAFE) ==="
  $PY run_ab_v6_factorial.py "$SUB" "E1/user/auth_early,E1/user/ref_early,E1/tool/auth_early,E1/tool/ref_early,E3/u_user,E3/t_tool" "$N" > "run_v6_${SAFE}.log" 2>&1
  echo "=== $(date -u +%FT%TZ) finished $SUB ==="
done
echo "ALL SUBSTRATES DONE $(date -u +%FT%TZ)"
