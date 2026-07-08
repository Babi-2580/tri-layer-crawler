import json
import csv
import os
from elasticsearch import Elasticsearch

# FIXED: your native Elasticsearch install has security enabled (HTTPS +
# login), unlike the old docker-compose setup which had
# xpack.security.enabled=false. Without credentials, every write here was
# failing silently (caught below) and nothing was actually being indexed.
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "https://localhost:9200")
ELASTIC_USERNAME = os.getenv("ELASTIC_USERNAME", "elastic")
ELASTIC_PASSWORD = os.getenv("ELASTIC_PASSWORD", "")

es = Elasticsearch(
    ELASTICSEARCH_URL,
    basic_auth=(ELASTIC_USERNAME, ELASTIC_PASSWORD),
    verify_certs=False,  # local self-signed cert, fine for localhost dev
)

# FIXED: now reads the same EXPORT_DIR used by the orchestrator's download
# endpoint, instead of an independent hardcoded "exports" that could drift.
EXPORT_DIR = os.getenv("EXPORT_DIR", "exports")
os.makedirs(EXPORT_DIR, exist_ok=True)


def save_and_export_data(record: dict, format_type: str):
    """Indexes data to Elasticsearch and generates physical export files."""

    # 1. Indexing into Elasticsearch
    try:
        es.index(index="intel-database", document=record)
        print("  -> [DATABASE] Record injected into Elasticsearch index 'intel-database'")
    except Exception as e:
        print(f"  -> [WARNING] Database unreachable. Skipping DB injection. ({e})")

    # 2. File Export Generation
    safe_filename = record['source_url'].replace("https://", "").replace("http://", "").replace("/", "_")[:30]
    filepath = os.path.join(EXPORT_DIR, f"{safe_filename}.{format_type}")

    if format_type == "json":
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(record, f, indent=4)

    elif format_type == "csv":
        # Check if file exists so we can write headers if it's new
        file_exists = os.path.isfile(filepath)
        with open(filepath, 'a', newline='', encoding='utf-8') as f:
            writer = csv.DictWriter(f, fieldnames=["source_url", "layer", "extracted_intelligence"])
            if not file_exists:
                writer.writeheader()
            writer.writerow(record)

    elif format_type == "txt":
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(f"TARGET: {record['source_url']}\n")
            f.write(f"LAYER: {record['layer']}\n")
            f.write(f"{'-'*40}\n")
            f.write(f"{record['extracted_intelligence']}\n")

    print(f"  -> [EXPORT] File generated at: {filepath}")
