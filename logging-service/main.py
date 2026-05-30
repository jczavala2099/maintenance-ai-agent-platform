from fastapi import FastAPI
from pydantic import BaseModel
from datetime import datetime
import json
import os

app = FastAPI(title="Logging Service")

LOG_FILE = "/tmp/agent_logs.jsonl"


class LogEvent(BaseModel):
    request_id: str
    event_type: str
    detail: dict


@app.get("/")
def health_check():
    return {"status": "ok", "service": "logging-service"}


@app.post("/log")
def log_event(event: LogEvent):
    log_record = {
        "timestamp": datetime.utcnow().isoformat(),
        "request_id": event.request_id,
        "event_type": event.event_type,
        "detail": event.detail
    }

    with open(LOG_FILE, "a", encoding="utf-8") as file:
        file.write(json.dumps(log_record, ensure_ascii=False) + "\n")

    return {
        "status": "success",
        "message": "Log stored",
        "log_file": LOG_FILE
    }
