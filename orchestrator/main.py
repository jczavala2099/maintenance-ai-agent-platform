from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
import re

app = FastAPI(title="Maintenance Agent Orchestrator")

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
TOOLS_API_URL = os.getenv("TOOLS_API_URL", "http://localhost:8001")
LOGGING_API_URL = os.getenv("LOGGING_API_URL", "http://localhost:8002")


class UserRequest(BaseModel):
    user_id: str
    message: str


def send_log(request_id: str, event_type: str, detail: dict):
    try:
        requests.post(
            f"{LOGGING_API_URL}/log",
            json={
                "request_id": request_id,
                "event_type": event_type,
                "detail": detail
            },
            timeout=2
        )
    except Exception as e:
        print(f"Logging failed: {e}")


def detect_equipment_id(message: str):
    pattern = r"\b(CNC-\d{2}|PRESS-\d{2}|CONV-\d{2}|ROBOT-\d{2}|COMP-\d{2}|PUMP-\d{2}|FAN-\d{2}|OVEN-\d{2}|PACK-\d{2})\b"
    match = re.search(pattern, message.upper())

    if match:
        return match.group(1)

    return None


@app.get("/")
def health_check():
    return {
        "status": "ok",
        "service": "orchestrator"
    }


@app.post("/agent")
def agent(request: UserRequest):
    prompt = f"""
You are an industrial maintenance agent.

Analyze the maintenance incident and provide a short recommendation.

User message:
{request.message}
"""

    response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False
        },
        timeout=180
    )

    llm_response = response.json().get("response", "")

    return {
        "user_id": request.user_id,
        "message": request.message,
        "agent_response": llm_response
    }


@app.post("/maintenance-case")
def maintenance_case(request: UserRequest):
    request_id = "REQ-2026-0001"
    equipment_id = detect_equipment_id(request.message)

    if not equipment_id:
        return {
            "status": "error",
            "request_id": request_id,
            "message": "Equipment ID not detected. Please specify equipment, for example CNC-01, PRESS-01, ROBOT-01."
        }

    send_log(
        request_id,
        "request_received",
        {
            "user_id": request.user_id,
            "message": request.message,
            "equipment_id": equipment_id
        }
    )

    equipment = requests.post(
        f"{TOOLS_API_URL}/get_equipment_info",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    history = requests.post(
        f"{TOOLS_API_URL}/get_maintenance_history",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    spare_parts = requests.post(
        f"{TOOLS_API_URL}/check_spare_parts",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    work_order = requests.post(
        f"{TOOLS_API_URL}/create_work_order",
        json={
            "request_id": request_id,
            "equipment_id": equipment_id,
            "priority": "high",
            "description": request.message,
            "recommended_action": "Inspect bearings, shaft alignment and mounting base",
            "requested_by": request.user_id
        },
        timeout=5
    ).json()

    notification = requests.post(
        f"{TOOLS_API_URL}/send_notification",
        timeout=5
    ).json()

    final_response = (
        "A high priority maintenance work order was created "
        "and the supervisor was notified."
    )

    send_log(
        request_id,
        "final_response_generated",
        {
            "equipment_id": equipment_id,
            "final_response": final_response,
            "work_order_id": work_order.get("work_order_id")
        }
    )

    return {
        "agent_flow": "User -> Orchestrator -> Tool(s) -> Logging -> Response",
        "request_id": request_id,
        "user_id": request.user_id,
        "detected_equipment_id": equipment_id,
        "original_message": request.message,
        "equipment": equipment,
        "history": history,
        "spare_parts": spare_parts,
        "work_order": work_order,
        "notification": notification,
        "final_response": final_response
    }


@app.post("/critical-maintenance-workflow")
def critical_maintenance_workflow(request: UserRequest):
    request_id = "WF-2026-0001"
    equipment_id = detect_equipment_id(request.message)

    if not equipment_id:
        return {
            "status": "error",
            "workflow_id": request_id,
            "message": "Equipment ID not detected. Please specify equipment, for example CNC-01, PRESS-01, ROBOT-01."
        }

    workflow_steps = []

    def add_step(step_name, status, detail):
        step = {
            "step": step_name,
            "status": status,
            "detail": detail
        }
        workflow_steps.append(step)

        send_log(
            request_id,
            "workflow_step",
            step
        )

    send_log(
        request_id,
        "workflow_started",
        {
            "user_id": request.user_id,
            "message": request.message,
            "equipment_id": equipment_id,
            "workflow_name": "critical_maintenance_workflow"
        }
    )

    if not request.message:
        add_step(
            "validate_input",
            "failed",
            {
                "error_code": "INVALID_INPUT",
                "message": "User message is required."
            }
        )

        return {
            "status": "error",
            "workflow_id": request_id,
            "failed_step": "validate_input",
            "message": "User message is required.",
            "steps": workflow_steps
        }

    add_step(
        "validate_input",
        "success",
        {
            "message": "Input validated successfully.",
            "equipment_id": equipment_id
        }
    )

    try:
        equipment = requests.post(
            f"{TOOLS_API_URL}/get_equipment_info",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        if equipment.get("status") == "error":
            add_step("get_equipment_info", "failed", equipment)

            return {
                "status": "error",
                "workflow_id": request_id,
                "failed_step": "get_equipment_info",
                "message": "Equipment could not be validated.",
                "steps": workflow_steps
            }

        add_step("get_equipment_info", "success", equipment)

    except Exception as e:
        add_step(
            "get_equipment_info",
            "failed",
            {
                "error_code": "TOOL_TIMEOUT_OR_UNAVAILABLE",
                "message": str(e)
            }
        )

        return {
            "status": "error",
            "workflow_id": request_id,
            "failed_step": "get_equipment_info",
            "message": "Equipment tool failed.",
            "steps": workflow_steps
        }

    try:
        history = requests.post(
            f"{TOOLS_API_URL}/get_maintenance_history",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        add_step("get_maintenance_history", "success", history)

    except Exception as e:
        history = {
            "status": "warning",
            "message": "Maintenance history unavailable.",
            "error": str(e)
        }

        add_step("get_maintenance_history", "warning", history)

    try:
        spare_parts = requests.post(
            f"{TOOLS_API_URL}/check_spare_parts",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        add_step("check_spare_parts", "success", spare_parts)

    except Exception as e:
        spare_parts = {
            "status": "warning",
            "available": False,
            "message": "Spare parts check unavailable.",
            "error": str(e)
        }

        add_step("check_spare_parts", "warning", spare_parts)

    if spare_parts.get("available") is True:
        decision = {
            "decision": "create_work_order",
            "reason": "Equipment is critical and spare parts are available."
        }
    else:
        decision = {
            "decision": "escalate_to_supervisor",
            "reason": "Spare parts are not available or could not be confirmed."
        }

    add_step("decision", "success", decision)

    if decision["decision"] == "create_work_order":
        try:
            work_order = requests.post(
                f"{TOOLS_API_URL}/create_work_order",
                json={
                    "request_id": request_id,
                    "equipment_id": equipment_id,
                    "priority": "critical",
                    "description": request.message,
                    "recommended_action": "Inspect bearings, shaft alignment and mounting base.",
                    "requested_by": request.user_id
                },
                timeout=5
            ).json()

            add_step("create_work_order", "success", work_order)

        except Exception as e:
            add_step(
                "create_work_order",
                "failed",
                {
                    "error_code": "WORK_ORDER_CREATION_FAILED",
                    "message": str(e)
                }
            )

            return {
                "status": "error",
                "workflow_id": request_id,
                "failed_step": "create_work_order",
                "message": "Could not create work order.",
                "steps": workflow_steps
            }

    else:
        work_order = None

        add_step(
            "escalate_to_supervisor",
            "success",
            {
                "message": "Incident escalated because spare parts are not confirmed."
            }
        )

    try:
        notification = requests.post(
            f"{TOOLS_API_URL}/send_notification",
            timeout=5
        ).json()

        add_step("send_notification", "success", notification)

    except Exception as e:
        notification = {
            "status": "warning",
            "message": "Notification failed but workflow completed.",
            "error": str(e)
        }

        add_step("send_notification", "warning", notification)

    final_response = {
        "summary": "Critical maintenance workflow completed.",
        "equipment_id": equipment_id,
        "priority": "critical",
        "decision": decision["decision"],
        "work_order_id": work_order.get("work_order_id") if work_order else None,
        "notification_status": notification.get("status")
    }

    send_log(
        request_id,
        "workflow_completed",
        final_response
    )

    return {
        "status": "success",
        "workflow_id": request_id,
        "workflow_name": "critical_maintenance_workflow",
        "detected_equipment_id": equipment_id,
        "final_response": final_response,
        "steps": workflow_steps
    }


@app.post("/ai-maintenance-advisor")
def ai_maintenance_advisor(request: UserRequest):
    request_id = "AI-2026-0001"
    equipment_id = detect_equipment_id(request.message)

    if not equipment_id:
        return {
            "status": "error",
            "request_id": request_id,
            "message": "Equipment ID not detected. Please specify equipment, for example CNC-01, PRESS-01, ROBOT-01."
        }

    equipment = requests.post(
        f"{TOOLS_API_URL}/get_equipment_info",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    history = requests.post(
        f"{TOOLS_API_URL}/get_maintenance_history",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    spare_parts = requests.post(
        f"{TOOLS_API_URL}/check_spare_parts",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    work_orders = requests.post(
        f"{TOOLS_API_URL}/get_equipment_work_orders",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    risk_prediction = requests.post(
        f"{TOOLS_API_URL}/predict_failure_risk",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    send_log(
        request_id,
        "ai_advisor_context_loaded",
        {
            "equipment_id": equipment_id,
            "work_orders_count": work_orders.get("count"),
            "risk_level": risk_prediction.get("risk_level"),
            "risk_score": risk_prediction.get("risk_score"),
            "health_score": risk_prediction.get("health_score")
        }
    )

    prompt = f"""
You are an expert industrial maintenance advisor.

Analyze this real maintenance data and provide:
1. Failure risk level
2. Most likely root cause
3. Recommended maintenance action
4. Spare parts recommendation
5. Operational priority
6. Short explanation for a maintenance supervisor

User reported issue:
{request.message}

Detected equipment:
{equipment_id}

Equipment data:
{equipment}

Maintenance history:
{history}

Spare parts:
{spare_parts}

Recent work orders:
{work_orders}

Predictive maintenance risk score:
{risk_prediction}

Respond in clear professional English.
"""

    llm_response = requests.post(
        f"{OLLAMA_URL}/api/generate",
        json={
            "model": "llama3",
            "prompt": prompt,
            "stream": False,
            "options": {
                "num_predict": 220,
                "temperature": 0.2
            }
        },
        timeout=180
    ).json()

    recommendation = llm_response.get("response", "")

    send_log(
        request_id,
        "ai_advisor_recommendation_generated",
        {
            "equipment_id": equipment_id,
            "recommendation": recommendation
        }
    )

    return {
        "status": "success",
        "advisor_type": "AI Maintenance Advisor",
        "equipment_id": equipment_id,
        "user_message": request.message,
        "data_sources": {
            "equipment": equipment,
            "history": history,
            "spare_parts": spare_parts,
            "recent_work_orders": work_orders,
            "risk_prediction": risk_prediction
        },
        "ai_recommendation": recommendation
    }