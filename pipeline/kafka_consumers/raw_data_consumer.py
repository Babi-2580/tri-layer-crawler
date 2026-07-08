import json
import os
from kafka import KafkaConsumer
from pipeline.parsers.llm_normalizer import process_with_llm
from pipeline.storage.elastic_indexer import save_and_export_data

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# Initialize the consumer to listen for raw worker data
consumer = KafkaConsumer(
    'raw-data-queue',
    bootstrap_servers=[KAFKA_SERVER],
    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
    group_id='pipeline-processors',
    auto_offset_reset='earliest',
    api_version=(3, 7, 0)
)

print("[SYSTEM] Intelligence Pipeline Active. Awaiting raw data blocks...")

for message in consumer:
    data_packet = message.value
    url = data_packet.get('url', 'UNKNOWN_TARGET')
    raw_content = data_packet.get('content', '')

    # These are the new parameters you added to the UI!
    extraction_query = data_packet.get('extraction_query', '')
    export_format = data_packet.get('export_format', 'json')

    print(f"\n[+] Incoming Data Block from {url}")

    try:
        # Step 1: Pass raw text and user instructions to the AI Parser
        normalized_data = process_with_llm(raw_content, extraction_query)

        # Step 2: Save to Database and generate the requested export file
        final_record = {
            "source_url": url,
            "layer": data_packet.get('layer'),
            "extracted_intelligence": normalized_data
        }

        save_and_export_data(final_record, export_format)
        print(f"[SUCCESS] Data successfully parsed and exported as .{export_format.upper()}")

    except Exception as e:
        print(f"[ERROR] Pipeline processing failed for {url}: {str(e)}")
