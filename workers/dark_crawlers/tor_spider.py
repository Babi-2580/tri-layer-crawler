import json
import os
import requests
from kafka import KafkaConsumer, KafkaProducer

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# NOTE: Default matches the Tor Browser bundled SOCKS proxy (port 9150).
# If you switch to running a standalone Tor service/daemon instead of Tor
# Browser, that typically listens on port 9050 -- update .env accordingly.
TOR_PROXY = os.getenv("TOR_PROXY_URL", "socks5h://127.0.0.1:9150")

PROXIES = {
    "http": TOR_PROXY,
    "https": TOR_PROXY,
}

# Listens for tasks from the Orchestrator
consumer = KafkaConsumer(
    'dark-web-tasks',
    bootstrap_servers=[KAFKA_SERVER],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='dark-worker-group',
    api_version=(3, 7, 0)
)

# Sends raw data back to the Pipeline
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_SERVER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(3, 7, 0)
)


def extract_onion_content(url: str) -> dict:
    """Routes the request through the local Tor SOCKS5 proxy to reach .onion targets."""
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Gecko/20100101 Firefox/128.0"
    }
    try:
        response = requests.get(url, proxies=PROXIES, headers=headers, timeout=60)
        response.raise_for_status()
        return {"content": response.text, "status_code": response.status_code}
    except Exception as e:
        return {"error": str(e)}


print(f"[DARK_NODE] Tor Engine Online. Routing through {TOR_PROXY}. Awaiting onion targets...")

for message in consumer:
    task = message.value
    target = task.get('url')

    print(f"\n[DARK_NODE] Establishing anonymous circuit for: {target}")
    result = extract_onion_content(target)

    if result.get("error"):
        task['error'] = result['error']
        producer.send('error-data-queue', value=task)
        print(f"[DARK_NODE] Circuit failed: {result['error']}")
    else:
        task['content'] = result.get('content', '')
        task['error'] = None
        producer.send('raw-data-queue', value=task)
        print("[DARK_NODE] Target acquired and dispatched to pipeline.")
