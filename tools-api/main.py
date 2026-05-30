from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4

app = FastAPI(title="Maintenance Tools API")

class EquipmentRequest(BaseModel):
    equipment_id: str

class WorkOrderRequest(BaseModel):
    request_id: str
    equipment_id: str
    priority: str
    description: str
    recommended_action: str | None = None
    requested_by: str | None = None

@app.get("/")
def health_check():
    return {"status": "ok", "service": "tools-api"}

@app.post("/get_equipment_info")
def get_equipment_info(request: EquipmentRequest):
    equipment_data = {
        "CNC-01": {
            "name": "CNC Milling Machine 01",
            "area": "Machining",
            "criticality": "high",
            "status_equipment": "stopped"
        }
    }

    if request.equipment_id not in equipment_data:
        return {
            "status": "error",
            "error_code": "EQUIPMENT_NOT_FOUND",
            "message": "The equipment_id does not exist."
        }

    return {
        "status": "success",
        "equipment_id": request.equipment_id,
        **equipment_data[request.equipment_id]
    }

@app.post("/get_maintenance_history")
def get_maintenance_history(request: EquipmentRequest):
    return {
        "status": "success",
        "equipment_id": request.equipment_id,
        "last_failure": "High vibration",
        "last_action": "Bearing inspection",
        "days_since_last_event": 30,
        "recurrence_risk": "medium"
    }

@app.post("/check_spare_parts")
def check_spare_parts(request: EquipmentRequest):
    return {
        "status": "success",
        "equipment_id": request.equipment_id,
        "part_type": "bearing",
        "available": True,
        "quantity": 4,
        "warehouse": "Main Maintenance Warehouse"
    }

@app.post("/create_work_order")
def create_work_order(request: WorkOrderRequest):
    return {
        "status": "success",
        "work_order_id": "OT-" + str(uuid4())[:8],
        "equipment_id": request.equipment_id,
        "priority": request.priority,
        "assigned_team": "Mechanical Maintenance",
        "message": "Work order created successfully."
    }

@app.post("/send_notification")
def send_notification():
    return {
        "status": "success",
        "notification_id": "NTF-2026-0001",
        "message": "Notification sent successfully."
    }
