import json
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import Optional
from kafka import KafkaProducer

app = FastAPI(title="Tri-Layer Intelligence Orchestrator", version="1.0.0")

# Enable CORS so your React Hacker UI can communicate with this API safely
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

KAFKA_SERVER = os.getenv("KAFKA_BOOTSTRAP_SERVERS", "localhost:9092")

# FIXED: was hardcoded to "/app/exports" (a Docker-only path that doesn't
# exist on native Windows). Now reads the same EXPORT_DIR the pipeline
# writes to, so the download button can actually find the files.
EXPORT_DIR = os.getenv("EXPORT_DIR", "exports")

try:
    producer = KafkaProducer(
        bootstrap_servers=[KAFKA_SERVER],
        value_serializer=lambda v: json.dumps(v).encode('utf-8'),
        api_version=(3, 7, 0)
    )
except Exception as e:
    print(f"[WARNING] Kafka Broker offline. Running in isolation mode. Error: {e}")
    producer = None


class ScanRequest(BaseModel):
    url: str
    layer: str
    export_format: str
    extraction_query: Optional[str] = None


@app.post("/api/v1/scan")
async def start_scan(request: ScanRequest):
    valid_layers = ["surface", "deep", "dark"]
    if request.layer not in valid_layers:
        raise HTTPException(status_code=400, detail="Invalid routing layer specified.")

    payload = {
        "url": request.url,
        "layer": request.layer,
        "export_format": request.export_format,
        "extraction_query": request.extraction_query
    }

    topic = f"{request.layer}-web-tasks"

    if producer:
        try:
            producer.send(topic, value=payload)
            producer.flush()
            return {"status": "SUCCESS", "message": f"Directive queued on channel: {topic}"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"Kafka dispatch failure: {str(e)}")
    else:
        print(f"[DIAGNOSTIC MOCK] Route target: {topic} | Payload: {payload}")
        return {"status": "MOCK_SUCCESS", "message": "Kafka offline. Diagnostic logged to console."}


@app.get("/api/v1/exports")
async def list_exports():
    """Scans the shared volume and returns a list of all crawled files."""
    if not os.path.exists(EXPORT_DIR):
        return {"files": []}
    try:
        files = [f for f in os.listdir(EXPORT_DIR) if os.path.isfile(os.path.join(EXPORT_DIR, f))]
        return {"files": sorted(files, reverse=True)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/exports/download/{filename}")
async def download_export(filename: str):
    """Streams the requested intelligence file directly to the user's browser."""
    filepath = os.path.join(EXPORT_DIR, filename)

    # Path traversal protection guardrail
    if not os.path.abspath(filepath).startswith(os.path.abspath(EXPORT_DIR)):
        raise HTTPException(status_code=403, detail="Access Denied.")

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Requested intelligence node payload not found.")

    return FileResponse(path=filepath, filename=filename, media_type='application/octet-stream')


@app.get("/api/v1/health")
async def health_check():
    return {"status": "ONLINE", "broker_connection": "ACTIVE" if producer else "OFFLINE"}
