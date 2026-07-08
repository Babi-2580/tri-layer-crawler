import json
import os
from kafka import KafkaConsumer

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# FIXED: now shares the same EXPORT_DIR as the orchestrator/elastic_indexer
# instead of its own independent "exports" reference.
EXPORT_DIR = os.getenv("EXPORT_DIR", "exports")
LOG_FILE = os.path.join(EXPORT_DIR, "pipeline_faults.log")

os.makedirs(EXPORT_DIR, exist_ok=True)

consumer = KafkaConsumer(
    'error-data-queue',
    bootstrap_servers=[KAFKA_SERVER],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='error-handler-group',
    api_version=(3, 7, 0)
)

print("[FAULT_MONITOR] Error monitoring interface streaming...")

for message in consumer:
    error_packet = message.value
    target = error_packet.get('url', 'UNKNOWN')
    layer = error_packet.get('layer', 'UNKNOWN')
    error_msg = error_packet.get('error', 'No trace message provided.')

    log_entry = f"[CRITICAL FAULT] [{layer.upper()}] Target: {target} | Reason: {error_msg}\n"
    print(log_entry.strip())

    # Append the diagnostic stack trace to a persistent local text file
    with open(LOG_FILE, "a", encoding="utf-8") as f:
        f.write(log_entry)
