import json
import os
import multiprocessing
from kafka import KafkaConsumer

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")


def run_spider(target_url, extraction_query, export_format):
    """
    Runs in its OWN operating system process (not just a thread).
    This is required because Twisted's reactor (used by Scrapy) can only
    be started ONCE per process, ever. Running each crawl in a fresh
    subprocess sidesteps that limit entirely -- this fixes the
    'ReactorNotRestartable' crash that happened on every 2nd+ scan.
    """
    from scrapy.crawler import CrawlerProcess
    from spiders.public_spider import SurfaceSpider

    process = CrawlerProcess(settings={
        'USER_AGENT': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
        'LOG_LEVEL': 'INFO'
    })
    process.crawl(
        SurfaceSpider,
        start_urls=[target_url],
        extraction_query=extraction_query,
        export_format=export_format
    )
    process.start()


if __name__ == "__main__":
    consumer = KafkaConsumer(
        'surface-web-tasks',
        bootstrap_servers=[KAFKA_SERVER],
        value_deserializer=lambda m: json.loads(m.decode('utf-8')),
        group_id='surface-worker-group',
        api_version=(3, 7, 0)
    )

    print("[SURFACE_NODE] Scrapy Daemon Active. Awaiting public index targets...")

    for message in consumer:
        task = message.value
        target_url = task.get('url')
        print(f"\n[SURFACE_NODE] Spawning high-velocity crawler engine for: {target_url}")

        # Each crawl runs in its own subprocess -- waits here until that
        # one finishes before picking up the next Kafka message.
        p = multiprocessing.Process(
            target=run_spider,
            args=(target_url, task.get('extraction_query'), task.get('export_format'))
        )
        p.start()
        p.join()
