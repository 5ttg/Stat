import requests
import os
import random
import string
import time
import sys

API = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
WEBHOOK = os.getenv("WEBHOOK_URL")

BATCH_SIZE = 700
COOLDOWN = 5          # base sleep
JITTER = 0.8

charset = string.ascii_lowercase + "_" + "."

print("[BOOT] Username checker starting", flush=True)
print("[BOOT] Webhook loaded:", bool(WEBHOOK), flush=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

def generate_name():
    length = random.choice([4])
    return "".join(random.choice(charset) for _ in range(length))

def generate_batch():
    names = set()
    while len(names) < BATCH_SIZE:
        names.add(generate_name())
    batch = list(names)
    print(f"[BATCH] Generated {len(batch)} usernames", flush=True)
    return batch

def send_webhook(name):
    if not WEBHOOK:
        return
    try:
        data = {
            "content": "@everyone",
            "allowed_mentions": {"parse": ["everyone"]},
            "embeds": [{
                "title": "Username Available",
                "description": f"**{name}** is available",
                "color": 5763719
            }]
        }
        r = session.post(WEBHOOK, json=data, timeout=6)
        print(f"[WEBHOOK] Alert for {name} — status={r.status_code}", flush=True)
    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}", flush=True)


def check(name):
    try:
        r = session.post(
            API,
            json={"username": name},
            timeout=12
        )

        if r.status_code == 200:
            data = r.json()
            if data.get("taken", True):
                print(f"[TAKEN] {name}", flush=True)
            else:
                print(f"[HIT] {name} AVAILABLE", flush=True)
                with open("hits.txt", "a", encoding="utf-8") as f:
                    f.write(name + "\n")
                send_webhook(name)

        elif r.status_code == 429:
            retry = r.headers.get("Retry-After", "unknown")
            print(f"[RATE LIMIT] 429 — Retry-After: {retry}", flush=True)
            print("[EXIT] Stopping this run → workflow will trigger a new one", flush=True)
            sys.exit(0)   # ← this is the key line

        else:
            print(f"[ERROR] {name} — status={r.status_code}", flush=True)

    except Exception as e:
        print(f"[REQUEST ERROR] {name} — {e}", flush=True)


def main():
    batch_count = 0

    while True:
        batch_count += 1
        print(f"\n===== Starting batch #{batch_count} =====", flush=True)

        batch = generate_batch()

        for i, name in enumerate(batch, 1):
            print(f"[CHECK {i:3d}/{BATCH_SIZE}] {name}", flush=True)
            check(name)
            time.sleep(random.uniform(COOLDOWN, COOLDOWN + JITTER))

        print(f"[BATCH DONE] {len(batch)} usernames checked", flush=True)
        # Optional: small pause between batches
        time.sleep(2)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("[INTERRUPT] Stopped by user", flush=True)
    except Exception as e:
        print(f"[FATAL] {e}", flush=True)
        sys.exit(1)
