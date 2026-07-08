class IntelPipeline:
    """Catches data from Scrapy and shoots it directly into the Kafka Pipeline."""
    def __init__(self):
        self.producer = KafkaProducer(
            bootstrap_servers=[KAFKA_SERVER],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            api_version=(3, 7, 0)
        )