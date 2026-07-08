import json
import os
import scrapy
from kafka import KafkaProducer

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


class IntelPipeline:
    """Catches data from Scrapy and shoots it directly into the Kafka Pipeline."""
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=[KAFKA_SERVER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            api_version=(3, 7, 0)
        )

    def process_item(self, item, spider):
        self.producer.send('raw-data-queue', value=dict(item))
        return item


class SurfaceSpider(scrapy.Spider):
    name = "surface_spider"

    # In a real run, the orchestrator passes these dynamically
    start_urls = ["https://en.wikipedia.org/wiki/Open-source_intelligence"]

    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'DOWNLOAD_DELAY': 1.5,  # Be polite to avoid IP bans
        'ITEM_PIPELINES': {'spiders.public_spider.IntelPipeline': 100}
    }

    def parse(self, response):
        print(f"[SURFACE_NODE] Indexing: {response.url}")

        yield {
            "url": response.url,
            "layer": "surface",
            "export_format": "json",
            "extraction_query": "Extract the main intelligence concepts discussed.",
            "content": " ".join(response.css('p::text').getall())
        }
