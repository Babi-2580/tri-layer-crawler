import json
import os
from kafka import KafkaConsumer, KafkaProducer
from playwright.sync_api import sync_playwright

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Listens for tasks from the Orchestrator
consumer = KafkaConsumer(
    'deep-web-tasks',
    bootstrap_servers=[KAFKA_SERVER],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='deep-worker-group',
    api_version=(3, 7, 0)
)

# Sends raw data back to the Pipeline
producer = KafkaProducer(
    bootstrap_servers=[KAFKA_SERVER],
    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
    api_version=(3, 7, 0)
)

def extract_dynamic_content(url):
    """Spins up a headless browser to render JS and bypass basic WAFs."""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        # Using a standard user-agent to blend in with normal traffic
        context = browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36"
        )
        page = context.new_page()

        try:
            # wait_until="networkidle" ensures all background API calls finish loading
            page.goto(url, wait_until="networkidle", timeout=45000)

            data = {
                "title": page.title(),
                "content": page.locator("body").inner_text()
            }
            return data

        except Exception as e:
            return {"error": str(e)}
        finally:
            browser.close()

print("[DEEP_NODE] Playwright Engine Online. Awaiting dynamic targets...")

for message in consumer:
    task = message.value
    target = task.get('url')

    print(f"\n[DEEP_NODE] Executing stealth render for: {target}")
    result = extract_dynamic_content(target)

    # Attach original task metadata before sending to pipeline
    task['content'] = result.get('content', '')
    task['error'] = result.get('error', None)

    producer.send('raw-data-queue', value=task)
    print(f"[DEEP_NODE] Target acquired and dispatched to pipeline.")
