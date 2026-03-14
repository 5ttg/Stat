import requests
import threading
import itertools
import time
import os
import random
import string

API = "https://discord.com/api/v9/unique-username/username-attempt-unauthed"
WEBHOOK = os.getenv("WEBHOOK_URL")

THREADS = 5
COOLDOWN = 1.5
MAX_RETRIES = 5
BATCH_SIZE = 700

charset = string.ascii_lowercase + string.digits + "_"

print("[BOOT] Username checker starting", flush=True)

# load proxies
try:
    with open("proxies.txt", "r") as f:
        proxies = [p.strip() for p in f if p.strip()]
    print(f"[BOOT] Loaded {len(proxies)} proxies", flush=True)
except:
    proxies = []
    print("[BOOT] No proxies loaded", flush=True)

proxy_cycle = itertools.cycle(proxies) if proxies else None

use_proxies = False
current_proxy = None

request_lock = threading.Lock()
cooldown_lock = threading.Lock()


def generate_name():
    length = random.choice([3, 4, 5])
    return "".join(random.choice(charset) for _ in range(length))


def generate_batch():
    names = set()

    while len(names) < BATCH_SIZE:
        names.add(generate_name())

    print(f"[BATCH] Generated {len(names)} usernames", flush=True)
    return list(names)


def send_webhook(name):
    if not WEBHOOK:
        print("[WEBHOOK] not configured", flush=True)
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

        r = requests.post(WEBHOOK, json=data, timeout=5)
        print(f"[WEBHOOK] sent for {name} status={r.status_code}", flush=True)

    except Exception as e:
        print(f"[WEBHOOK ERROR] {e}", flush=True)


def get_proxy():
    global current_proxy

    if not use_proxies or not proxy_cycle:
        return None

    current_proxy = next(proxy_cycle)

    print(f"[PROXY] {current_proxy}", flush=True)

    return {
        "http": f"http://{current_proxy}",
        "https": f"http://{current_proxy}"
    }


def wait_global():
    with cooldown_lock:
        time.sleep(COOLDOWN)


def check(name):
    global use_proxies

    retries = 0

    while retries < MAX_RETRIES:

        wait_global()
        proxy = get_proxy()

        print(f"[CHECK] {name} try={retries+1}", flush=True)

        try:
            r = requests.post(
                API,
                json={"username": name},
                proxies=proxy,
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

                return

            elif r.status_code == 429:

                with request_lock:
                    if not use_proxies:
                        print("[RATE LIMIT] switching to proxies", flush=True)
                        use_proxies = True
                    else:
                        print("[RATE LIMIT] rotating proxy", flush=True)

                retries += 1
                time.sleep(1)

            else:
                print(f"[ERROR] {name} status={r.status_code}", flush=True)
                return

        except Exception as e:
            print(f"[REQUEST ERROR] {name} error={e}", flush=True)
            retries += 1
            time.sleep(1)

    print(f"[FAIL] {name}", flush=True)


def worker(names):
    for name in names:
        check(name)


while True:

    batch = generate_batch()

    print("[BATCH] Starting checks", flush=True)

    chunks = [batch[i::THREADS] for i in range(THREADS)]

    threads = []

    for i in range(THREADS):
        t = threading.Thread(target=worker, args=(chunks[i],))
        t.start()
        threads.append(t)

    for t in threads:
        t.join()

    print("[BATCH] Completed 700 usernames\n", flush=True)
