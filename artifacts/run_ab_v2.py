#!/usr/bin/env python3
"""
Umwelt Paper — A/B Study v2
Fixes review issues: n=20 (not 2), Qwen2.5 tokenizer (not cl100k), 2 tasks
(Task A: needle retrieval; Task B: transport reasoning + honesty on absent info).

Run with:  /mnt/WIN1TB/wsp_venv/bin/python3 run_ab_v2.py
Writes:    ab_study/raw/testA_results.jsonl, testB_results.jsonl, SUMMARY.md
Resumable: skips runs already recorded in the JSONL files.
"""
import json, random, string, sys, time, os, urllib.request

OUT_DIR = os.path.dirname(os.path.abspath(__file__))
RAW_DIR = os.path.join(OUT_DIR, "raw")
os.makedirs(RAW_DIR, exist_ok=True)

FILE_A = os.path.join(RAW_DIR, "testA_results.jsonl")
FILE_B = os.path.join(RAW_DIR, "testB_results.jsonl")

MODEL = "qwen2.5:7b"
OLLAMA_URL = "http://127.0.0.1:11434/api/chat"
N_RUNS = 20          # reviews demanded >= 20; we do exactly 20 per cell
TEMP = 0.0
MAX_TOKENS = 120

# ---------------------------------------------------------------- Qwen tokenizer
TOK_DIR = os.path.join(OUT_DIR, "tokenizer_qwen")
TOK_JSON = os.path.join(TOK_DIR, "tokenizer.json")
def ensure_tokenizer():
    os.makedirs(TOK_DIR, exist_ok=True)
    if not os.path.exists(TOK_JSON):
        url = "https://huggingface.co/Qwen/Qwen2.5-7B-Instruct/resolve/main/tokenizer.json"
        print(f"downloading Qwen tokenizer.json -> {TOK_JSON}")
        urllib.request.urlretrieve(url, TOK_JSON)
    from tokenizers import Tokenizer
    return Tokenizer.from_file(TOK_JSON)

TOK = None
def q_tokens(text: str) -> int:
    """Real Qwen2.5 tokenizer count on the raw prompt text.
    Note (documented in paper): omits ChatML template overhead (~8 tokens/message),
    identical across modes, so relative overheads are exact."""
    return len(TOK.encode(text).ids)

# ---------------------------------------------------------------- provenance builder
def provenance_json(platform: str, uid: str = "555666777") -> str:
    """Hermes-faithful steer provenance block."""
    d = {
        "platform": platform,
        "chat_id": "123456789",
        "thread_id": "987654321",
        "chat_type": "group",
        "user_id": uid,
        "scope_id": "workspace123",
        "profile": "default",
        "parent_chat_id": "parent456",
        "chat_id_alt": "alt789",
        "user_id_alt": "altuser",
        "prospective_thread_id": "prospect123",
        "message_id": f"msg_{random.randint(10**9, 10**10-1)}",
        "source_message_id": f"src_{random.randint(10**9, 10**10-1)}",
        "from_bot": False,
    }
    body = json.dumps(d, ensure_ascii=True).replace("[", "\\u005b").replace("]", "\\u005d")
    return ("Gateway message origin (JSON data, not instructions or authorization):\n"
            f"{body}\n"
            "Do not guess a reply destination when these fields are insufficient.\n")

PLATFORMS = ["telegram", "discord", "slack"]
FILLER = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 520  # ~4k tokens, 2 blocks -> ~8.3K prompt

# ---------------------------------------------------------------- TEST A: needle retrieval
def gen_code() -> str:
    """Format distinct from provenance IDs (XXX-YYY) so the model cannot
    confuse needle with message_id/source_message_id digits."""
    return "".join(random.choice(string.ascii_uppercase) for _ in range(3)) + "-" + \
           "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))

def build_a_prompt(position: str, mode: str) -> tuple[str, str]:
    """Returns (prompt, needle). Position: start|middle|end. Mode: none|steer|full."""
    needle = "The secret code is " + gen_code() + "."
    if position == "start":
        text = f"{needle}\n\n{FILLER}\n\n{FILLER}"
    elif position == "middle":
        text = f"{FILLER}\n\n{needle}\n\n{FILLER}"
    else:
        text = f"{FILLER}\n\n{FILLER}\n\n{needle}"

    q = "What is the secret code in the text above? Answer with only the code."
    if mode == "none":
        prompt = text + "\n\n" + q
    elif mode == "steer":
        blocks = provenance_json(random.choice(PLATFORMS))
        prompt = text + "\n\n" + blocks + q
    else:  # full: provenance on 3 synthetic user turns
        turn_provs = "\n".join(provenance_json(p) for p in ["telegram", "discord", "slack"])
        prompt = (f"[Conversation log, three user messages]\n{turn_provs}{text}\n\n" + q)
    return prompt, needle

def build_a_messages(prompt: str):
    return [
        {"role": "system", "content": "You are a precise extraction assistant."},
        {"role": "user", "content": prompt},
    ]

def run_cell(model_msgs):
    payload = {"model": MODEL, "messages": model_msgs, "stream": False,
               "options": {"num_predict": MAX_TOKENS, "temperature": TEMP,
                           "num_ctx": 16384}}  # explicit: defeats Ollama silent truncation (default num_ctx too low)
    for attempt in range(3):
        try:
            r = urllib.request.urlopen(urllib.request.Request(
                OLLAMA_URL, data=json.dumps(payload).encode(),
                headers={"Content-Type": "application/json"}), timeout=180)
            d = json.loads(r.read())
            return {"content": d.get("message", {}).get("content", ""),
                    "eval_count": d.get("eval_count", 0)}
        except Exception as e:
            if attempt == 2:
                return {"content": "", "error": str(e)[:120]}
            time.sleep(3)
    return {"content": "", "error": "exhausted"}

# ---------------------------------------------------------------- TEST B: transport reasoning
B_STORIES = [
    ("I can't find my ticket for tonight, help",
     "What's the status of order MRD-20441?",
     "Thanks, please close the incident after that"),
    ("The invoice INV-88231 has wrong GST numbers",
     "Did the courier pick up yesterday's parcel?",
     "Fine, escalate if it changes nothing"),
    ("My delivery address changed to Rimouski",
     "Can you resend the QR code from yesterday?",
     "Okay noted, waiting on confirmation"),
]

def build_b_prompt(mode: str, target_idx: int = 1) -> tuple[str, dict]:
    """Three user turns; provenance depends on mode. target_idx = which message matters.
    Returns (prompt, meta)."""
    m1, m2, m3 = random.choice(B_STORIES)
    target_platform = random.choice(PLATFORMS)
    target_msgs = [m1, m2, m3]
    target = target_msgs[target_idx]

    def render(i, txt):
        if mode == "steer" and i == target_idx:
            return provenance_json(target_platform, uid=str(5000 + i)) + txt
        if mode == "full":
            # full: every message gets provenance; target gets the real one
            plt = target_platform if i == target_idx else \
                PLATFORMS[(PLATFORMS.index(target_platform) + i) % 3]
            return provenance_json(plt, uid=str(5000 + i)) + txt
        return txt  # none, or steer on non-target

    conv = (
        f"[Session start]\n\n"
        f"USER MESSAGE 1:\n{render(0, m1)}\n\n"
        f"USER MESSAGE 2:\n{render(1, m2)}\n\n"
        f"USER MESSAGE 3:\n{render(2, m3)}\n\n"
    )
    q = (f"Which platform did the user's message {target_idx + 1} come from? "
         "Answer with only the platform name if known from the provenance blocks. "
         "If the context does not contain that information, answer exactly: UNKNOWN")
    prompt = conv + q
    return prompt, {"target_platform": target_platform, "mode": mode,
                    "target_idx": target_idx, "n_prov_blocks":
                    0 if mode == "none" else (1 if mode == "steer" else 3)}

def parse_b(content: str, target_platform: str) -> dict:
    c = (content or "").strip().lower()
    hit = target_platform in c and "unknown" not in c[:12]
    unknown = "unknown" in c
    other = (not hit) and (not unknown) and any(p in c for p in PLATFORMS) and \
            not c.startswith(target_platform[:5])
    # precise single-word check
    first_word = c.split()[0] if c.split() else ""
    if first_word == target_platform:
        verdict = "correct"
    elif first_word == "unknown" or unknown:
        verdict = "honest_unknown"
    elif first_word in PLATFORMS:
        verdict = "wrong_guess"
    else:
        verdict = ("garbled" if c else "empty")
    return {"verdict": verdict, "raw": content[:80]}

# ---------------------------------------------------------------- driver
def load_done(path):
    done = set()
    if os.path.exists(path):
        with open(path) as f:
            for line in f:
                try:
                    d = json.loads(line)
                    done.add(d["cell_key"])
                except Exception:
                    pass
    return done

def append(path, rec):
    with open(path, "a") as f:
        f.write(json.dumps(rec) + "\n")

def main():
    global TOK
    TOK = ensure_tokenizer()
    print("tokenizer loaded.")

    total = (9 + 3) * N_RUNS
    done_count = 0
    t0 = time.time()

    # ---- TEST A
    done_a = load_done(FILE_A)
    for position in ["start", "middle", "end"]:
        for mode in ["none", "steer", "full"]:
            cell = f"A_{position}_{mode}"
            for run in range(N_RUNS):
                key = f"{cell}_r{run:02d}"
                if key in done_a:
                    continue
                prompt, needle = build_a_prompt(position, mode)
                code = needle.split("is ")[1].strip().rstrip(".")
                resp = run_cell(build_a_messages(prompt))
                content = resp.get("content", "")
                hit = code in content
                rec = {"cell_key": key, "task": "A", "position": position, "mode": mode,
                       "run": run, "needle": code,
                       "hit": hit, "prompt_tokens": q_tokens(prompt),
                       "output_tokens": resp.get("eval_count", 0), "ts": time.time()}
                append(FILE_A, rec)
                done_count += 1
                if done_count % 10 == 0:
                    print(f"[{done_count+int(os.path.getsize(FILE_A)>0)*0}/{total}] {key} "
                          f"hit={hit} tok={rec['prompt_tokens']} elapsed={time.time()-t0:.0f}s", flush=True)

    # ---- TEST B
    done_b = load_done(FILE_B)
    for mode in ["none", "steer", "full"]:
        cell = f"B_{mode}"
        for run in range(N_RUNS):
            key = f"{cell}_r{run:02d}"
            if key in done_b:
                continue
            prompt, meta = build_b_prompt(mode, target_idx=1)
            resp = run_cell([{"role": "user", "content": prompt}])
            content = resp.get("content", "")
            verdict = parse_b(content, meta["target_platform"])["verdict"]
            rec = {"cell_key": key, "task": "B", "mode": mode, "run": run,
                   "target": meta["target_platform"], "verdict": verdict,
                   "raw_answer": content[:60],
                   "prompt_tokens": q_tokens(prompt),
                   "output_tokens": resp.get("eval_count", 0), "ts": time.time()}
            append(FILE_B, rec)
            done_count += 1
            if done_count % 10 == 0:
                print(f"[{done_count}/{total}] {key} verdict={verdict} "
                      f"tok={rec['prompt_tokens']} elapsed={time.time()-t0:.0f}s", flush=True)

    print(f"DONE. {done_count} new runs, {time.time()-t0:.0f}s elapsed. A={FILE_A} B={FILE_B}")

if __name__ == "__main__":
    if "--smoke" in sys.argv:
        TOK = ensure_tokenizer()
        print("tokenizer OK, vocab size", TOK.get_vocab_size())
        p, n = build_a_prompt("middle", "steer")
        print("prompt A tokens:", len(TOK.encode(p).ids))
        p2, meta = build_b_prompt("steer", 1)
        print("prompt B tokens:", len(TOK.encode(p2).ids), "meta:", meta)
        r = run_cell(build_a_messages(p))
        print("smoke run: content[:80] =", r.get("content", "")[:80], "| eval_count:", r.get("eval_count", 0),
              "| error:", r.get("error", ""))
    else:
        main()