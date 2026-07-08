FROM python:3.11-slim
# Install the native Tor routing proxy daemon directly into the Linux container
RUN apt-get update && apt-get install -y tor xz-utils && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
# Boot the native Tor network daemon in the background before spinning up your Python script
CMD tor & python tor_spider.py