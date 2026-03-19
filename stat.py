import requests
import os
import random
import string
import time
import sys

API = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
WEBHOOK = os.getenv("WEBHOOK_URL")

BATCH_SIZE = 700
COOLDOWN = 5

charset = string.ascii_lowercase + string.digits + "_" + "."

print("[BOOT] Username checker starting", flush=True)
print("[BOOT] Webhook loaded:", bool(WEBHOOK), flush=True)

session = requests.Session()
session.headers.update({
    "User-Agent": "Mozilla/5.0"
})

def generate_name():
    length = random.choice([3, 4])
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
        print("[WEBHOOK] Not configured", flush=True)
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

        r = session.post(WEBHOOK, json=data, timeout=5)

        print(f"[WEBHOOK] Sent alert for {name} status={r.status_code}", flush=True)

    except Exception as e:
        print("[WEBHOOK ERROR]", e, flush=True)


def check(name):

    try:
        r = session.post(
            API,
            json={"username": name},
            timeout=10
        )

        if r.status_code == 200:

            data = r.json()

            if data["taken"]:
                print(f"[TAKEN] {name}", flush=True)
            else:
                print(f"[HIT] {name} AVAILABLE", flush=True)

                with open("hits.txt", "a") as f:
                    f.write(name + "\n")

                send_webhook(name)

        elif r.status_code == 429:

            retry = r.headers.get("Retry-After", "unknown")

            print("[RATE LIMIT] hit — retry after:", retry, flush=True)
            print("[EXIT] Ending run so workflow restarts", flush=True)

            sys.exit(0)

        else:
            print(f"[ERROR] {name} status={r.status_code}", flush=True)

    except Exception as e:
        print(f"[REQUEST ERROR] {name} {e}", flush=True)


def main():

    batch = generate_batch()

    for i, name in enumerate(batch, 1):

        print(f"[CHECK {i}/{BATCH_SIZE}] {name}", flush=True)

        check(name)

        time.sleep(random.uniform(COOLDOWN, COOLDOWN + 0.8))

    print("[DONE] Finished batch of 700 usernames", flush=True)


if __name__ == "__main__":
    main()
