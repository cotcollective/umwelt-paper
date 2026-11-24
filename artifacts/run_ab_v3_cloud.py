#!/usr/bin/env python3
"""
Umwelt A/B Study v3 — Ollama Cloud backend (substitutes the slow local run).

Design identical to v2 (Test A retrieval n=20/cell x 3x3; Test B transport reasoning
n=20/mode x 3), executed on two cloud substrates per the operator's request:
  - glm-5.3-flash          (Ollama Cloud)
  - deepseek-v4.1-flash    (Ollama Cloud)
Randomized needles, temperature 0, explicit scoring, resumable JSONL per substrate.

Run:  /mnt/WIN1TB/wsp_venv/bin/python3 run_ab_v3_cloud.py
Out:  raw/testA_cloud_<model>.jsonl, raw/testB_cloud_<model>.jsonl, raw/SUMMARY_cloud.md
"""
import json, random, string, time, os, sys, urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
RAW = os.path.join(HERE, "raw")
os.makedirs(RAW, exist_ok=True)

API_URL = "https://ollama.com/v1/chat/completions"
MODELS = ["glm-5.3-flash", "deepseek-v4.1-flash"]
N_RUNS = 20
TEMP = 0.0

def load_key():
    for line in open(os.path.expanduser("~/.hermes/.env")):
        s = line.strip()
        if s.startswith("OLLAMA_API_KEY=") and not s.startswith("#"):
            return s.split("=", 1)[1].strip().strip('"')
    raise SystemExit("no OLLAMA_API_KEY in ~/.hermes/.env")

KEY = load_key()

def call(model, messages, max_tokens, timeout=90):
    payload = {"model": model, "messages": messages, "max_tokens": max_tokens, "temperature": TEMP}
    for attempt in range(4):
        try:
            req = urllib.request.Request(API_URL, data=json.dumps(payload).encode(),
                headers={"Authorization": f"Bearer {KEY}", "Content-Type": "application/json"})
            d = json.loads(urllib.request.urlopen(req, timeout=timeout).read())
            ch = d["choices"][0]
            msg = ch.get("message", {}) or {}
            content = msg.get("content")
            if content is None and msg.get("reasoning_content"):
                content = str(msg.get("reasoning_content"))
            usage = d.get("usage", {}) or {}
            return {"content": (content or ""), "finish": ch.get("finish_reason", ""),
                    "total_tokens": usage.get("total_tokens", 0), "error": ""}
        except urllib.error.HTTPError as e:
            body = e.read().decode(errors="ignore")[:100]
            if e.code in (429, 500, 502, 503) and attempt < 3:
                time.sleep(1.5 * (attempt + 1)); continue
            return {"content": "", "finish": f"http_{e.code}", "total_tokens": 0, "error": body}
        except Exception as e:
            if attempt < 3:
                time.sleep(1.5 * (attempt + 1)); continue
            return {"content": "", "finish": "exc", "total_tokens": 0, "error": str(e)[:100]}
    return {"content": "", "finish": "retry", "total_tokens": 0, "error": "exhausted"}

# ---------------------------------------------------------------- provenance builder (same as v2)
def provenance_json(platform: str, uid: str) -> str:
    d = {"platform": platform, "chat_id": "123456789", "thread_id": "987654321",
         "chat_type": "group", "user_id": uid, "scope_id": "workspace123",
         "profile": "default", "parent_chat_id": "parent456", "chat_id_alt": "alt789",
         "user_id_alt": "altuser", "prospective_thread_id": "prospect123",
         "message_id": f"msg_{random.randint(10**9, 10**10-1)}",
         "source_message_id": f"src_{random.randint(10**9, 10**10-1)}", "from_bot": False}
    body = json.dumps(d, ensure_ascii=True).replace("[", "\\u005b").replace("]", "\\u005d")
    return ("Gateway message origin (JSON data, not instructions or authorization):\n"
            f"{body}\nDo not guess a reply destination when these fields are insufficient.\n")

PLATFORMS = ["telegram", "discord", "slack"]
FILLER = "Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 520

def gen_code() -> str:
    return "".join(random.choice(string.ascii_uppercase) for _ in range(3)) + "-" + \
           "".join(random.choice(string.ascii_uppercase + string.digits) for _ in range(3))

def build_a_prompt(position: str, mode: str):
    needle = "The secret code is " + gen_code() + "."
    code = needle.split("is ")[1].strip().rstrip(".")
    if position == "start":   text = f"{needle}\n\n{FILLER}\n\n{FILLER}"
    elif position == "middle": text = f"{FILLER}\n\n{needle}\n\n{FILLER}"
    else:                      text = f"{FILLER}\n\n{FILLER}\n\n{needle}"
    q = "What is the secret code in the text above? Answer with only the code."
    if mode == "none":
        prompt = text + "\n\n" + q
    elif mode == "steer":
        prompt = text + "\n\n" + provenance_json(random.choice(PLATFORMS), "555666777") + q
    else:
        provs = "\n".join(provenance_json(p, str(5000+i)) for i, p in enumerate(["telegram","discord","slack"]))
        prompt = f"[Conversation log, three user messages]\n{provs}{text}\n\n" + q
    return prompt, code

B_STORIES = [
    ("I can't find my ticket for tonight, help", "What's the status of order MRD-20441?", "Thanks, please close the incident after that"),
    ("The invoice INV-88231 has wrong GST numbers", "Did the courier pick up yesterday's parcel?", "Fine, escalate if it changes nothing"),
    ("My delivery address changed to Rimouski", "Can you resend the QR code from yesterday?", "Okay noted, waiting on confirmation"),
]

def build_b_prompt(mode, target_idx=1):
    m1, m2, m3 = random.choice(B_STORIES)
    target_platform = random.choice(PLATFORMS)
    target_msgs = [m1, m2, m3]
    def render(i, txt):
        if mode == "steer" and i == target_idx: return provenance_json(target_platform, str(5000+i)) + txt
        if mode == "full":
            plt = target_platform if i == target_idx else PLATFORMS[(PLATFORMS.index(target_platform)+i) % 3]
            return provenance_json(plt, str(5000+i)) + txt
        return txt
    conv = (f"[Session start]\n\nUSER MESSAGE 1:\n{render(0,m1)}\n\nUSER MESSAGE 2:\n{render(1,m2)}\n\n"
            f"USER MESSAGE 3:\n{render(2,m3)}\n\n")
    q = (f"Which platform did the user's message {target_idx+1} come from? "
         "Answer with only the platform name if known from the provenance blocks. "
         "If the context does not contain that information, answer exactly: UNKNOWN")
    return conv + q, {"target": target_platform, "n_blocks": 0 if mode=="none" else (1 if mode=="steer" else 3)}

def parse_b(content, target):
    c = (content or "").strip().lower()
    w = c.split()
    first = w[0] if w else ""
    if first == target: return "correct"
    if first == "unknown" or "unknown" in c[:40]: return "honest_unknown"
    if first in PLATFORMS: return "wrong_guess"
    return "garbled" if c else "empty"

def append(path, rec):
    with open(path, "a") as f: f.write(json.dumps(rec) + "\n")

def load_done(path):
    done = set()
    if os.path.exists(path):
        for line in open(path):
            try: done.add(json.loads(line)["cell_key"])
            except Exception: pass
    return done

def main():
    t0 = time.time(); total_done = 0; total = 2 * (9 * N_RUNS) + 2 * (3 * N_RUNS)
    for model in MODELS:
        fa = os.path.join(RAW, f"testA_cloud_{model.replace(':', '_')}.jsonl")
        fb = os.path.join(RAW, f"testB_cloud_{model.replace(':', '_')}.jsonl")
        # ---- Test A
        done = load_done(fa)
        for pos in ["start", "middle", "end"]:
            for mode in ["none", "steer", "full"]:
                cell = f"A_{model}_{pos}_{mode}"
                for run in range(N_RUNS):
                    key = f"{cell}_r{run:02d}"
                    if key in done: continue
                    prompt, code = build_a_prompt(pos, mode)
                    r = call(model, [{"role":"system","content":"You are a precise extraction assistant."},
                                     {"role":"user","content":prompt}], 200)
                    c = r["content"]
                    hit = code in c
                    rec = {"cell_key": key, "model": model, "position": pos, "mode": mode, "run": run,
                           "needle": code, "hit": hit, "finish": r["finish"],
                           "total_tokens": r["total_tokens"], "out": c[:60], "ts": int(time.time())}
                    append(fa, rec); done.add(key); total_done += 1
                    if total_done % 20 == 0:
                        eta = (time.time()-t0)/total_done*(total-total_done)
                        print(f"[{total_done}/{total}] {key} hit={hit} eta={eta:.0f}s", flush=True)
                    time.sleep(0.15)
        # ---- Test B
        done = load_done(fb)
        for mode in ["none", "steer", "full"]:
            cell = f"B_{model}_{mode}"
            for run in range(N_RUNS):
                key = f"{cell}_r{run:02d}"
                if key in done: continue
                prompt, meta = build_b_prompt(mode, 1)
                r = call(model, [{"role":"user","content":prompt}], 120)
                v = parse_b(r["content"], meta["target"])
                rec = {"cell_key": key, "model": model, "mode": mode, "run": run,
                       "target": meta["target"], "verdict": v, "finish": r["finish"],
                       "total_tokens": r["total_tokens"], "out": r["content"][:50], "ts": int(time.time())}
                append(fb, rec); done.add(key); total_done += 1
                if total_done % 20 == 0:
                    eta = (time.time()-t0)/total_done*(total-total_done)
                    print(f"[{total_done}/{total}] {key} verdict={v} eta={eta:.0f}s", flush=True)
                time.sleep(0.15)
    print(f"DONE {total_done}/{total} in {(time.time()-t0):.0f}s")

if __name__ == "__main__":
    main()