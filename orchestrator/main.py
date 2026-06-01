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


def is_open_work_orders_question(message: str):
    text = message.lower()
    keywords = [
        "open work orders", "open orders", "pending work orders",
        "active work orders", "ordenes abiertas", "órdenes abiertas",
        "ordenes pendientes", "órdenes pendientes"
    ]
    return any(keyword in text for keyword in keywords)


def is_all_work_orders_question(message: str):
    text = message.lower()
    keywords = [
        "all work orders",
        "show all work orders",
        "list all work orders",
        "work order history",
        "todas las ordenes",
        "todas las órdenes",
        "mostrar todas las ordenes",
        "mostrar todas las órdenes"
    ]
    return any(keyword in text for keyword in keywords)


def is_risk_question(message: str):
    text = message.lower()
    keywords = [
        "risk", "risk score", "health score", "failure risk",
        "riesgo", "score", "salud"
    ]
    return any(keyword in text for keyword in keywords)


def is_spare_parts_question(message: str):
    text = message.lower()
    keywords = [
        "spare parts", "parts available", "part available", "inventory",
        "refacciones", "repuestos", "partes disponibles"
    ]
    return any(keyword in text for keyword in keywords)


def is_highest_risk_question(message: str):
    text = message.lower()
    keywords = [
        "highest risk", "most risky", "highest risk machine",
        "highest risk equipment", "which machine has the highest risk",
        "what machine has the highest risk", "critical machines",
        "machines at risk", "highest risk asset",
        "what equipment should i prioritize today",
        "what machines should i prioritize today",
        "which equipment should i prioritize today",
        "what should i prioritize today",
        "maintenance priorities", "daily priorities", "prioritize today",
        "riesgo mas alto", "riesgo más alto",
        "maquina con mayor riesgo", "máquina con mayor riesgo",
        "equipo con mayor riesgo", "priorizar hoy",
        "prioridades de mantenimiento",
        "que equipo debo priorizar", "qué equipo debo priorizar"
    ]
    return any(keyword in text for keyword in keywords)


def is_maintenance_history_question(message: str):
    text = message.lower()
    keywords = [
        "maintenance history", "history", "past failures",
        "repair history", "failure history", "historial",
        "historial de mantenimiento", "historial de fallas"
    ]
    return any(keyword in text for keyword in keywords)


def is_critical_work_orders_question(message: str):
    text = message.lower()
    keywords = [
        "critical work orders", "critical orders",
        "show all critical work orders",
        "open critical work orders",
        "critical maintenance orders",
        "ordenes criticas", "órdenes críticas",
        "ordenes críticas abiertas", "órdenes críticas abiertas"
    ]
    return any(keyword in text for keyword in keywords)


def is_downtime_question(message: str):
    text = message.lower()
    keywords = [
        "downtime",
        "most downtime",
        "generating the most downtime",
        "equipment is generating the most downtime",
        "machine is generating the most downtime",
        "tiempo muerto",
        "mayor downtime",
        "mayor tiempo muerto",
        "mas tiempo muerto",
        "más tiempo muerto"
    ]
    return any(keyword in text for keyword in keywords)


def is_oee_question(message: str):
    text = message.lower()
    keywords = [
        "oee",
        "overall equipment effectiveness",
        "eficiencia global",
        "efectividad global",
        "availability",
        "performance",
        "quality"
    ]
    return any(keyword in text for keyword in keywords)


def is_weekly_summary_question(message: str):
    text = message.lower()
    keywords = [
        "weekly maintenance summary",
        "generate a weekly maintenance summary",
        "weekly summary",
        "maintenance summary",
        "resumen semanal",
        "resumen de mantenimiento",
        "resumen semanal de mantenimiento"
    ]
    return any(keyword in text for keyword in keywords)


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
            "stream": False,
            "options": {
                "num_predict": 220,
                "temperature": 0.2
            }
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

    add_step(
        "validate_input",
        "success",
        {
            "message": "Input validated successfully.",
            "equipment_id": equipment_id
        }
    )

    equipment = requests.post(
        f"{TOOLS_API_URL}/get_equipment_info",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    add_step("get_equipment_info", "success", equipment)

    history = requests.post(
        f"{TOOLS_API_URL}/get_maintenance_history",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    add_step("get_maintenance_history", "success", history)

    spare_parts = requests.post(
        f"{TOOLS_API_URL}/check_spare_parts",
        json={"equipment_id": equipment_id},
        timeout=5
    ).json()

    add_step("check_spare_parts", "success", spare_parts)

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
    else:
        work_order = None

    notification = requests.post(
        f"{TOOLS_API_URL}/send_notification",
        timeout=5
    ).json()

    add_step("send_notification", "success", notification)

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


@app.post("/chat")
def chat(request: UserRequest):
    request_id = "CHAT-2026-0001"

    if is_highest_risk_question(request.message):
        highest_risk = requests.get(
            f"{TOOLS_API_URL}/get_highest_risk_equipment",
            timeout=5
        ).json()

        equipment_list = highest_risk.get("highest_risk_equipment", [])

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": "Highest risk equipment ranking generated successfully.",
                "highest_risk_equipment": equipment_list
            }
        }

    if is_downtime_question(request.message):
        downtime = requests.get(
            f"{TOOLS_API_URL}/get_downtime_ranking",
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": "Downtime ranking generated successfully.",
                "downtime_ranking": downtime.get("downtime_ranking", [])
            }
        }

    if is_weekly_summary_question(request.message):
        summary = requests.get(
            f"{TOOLS_API_URL}/weekly_maintenance_summary",
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": summary.get("summary"),
                "total_work_orders": summary.get("total_work_orders"),
                "open_work_orders": summary.get("open_work_orders"),
                "critical_open_work_orders": summary.get("critical_open_work_orders"),
                "affected_equipment": summary.get("affected_equipment")
            }
        }

    if is_critical_work_orders_question(request.message):
        critical_orders = requests.get(
            f"{TOOLS_API_URL}/get_critical_work_orders",
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"{critical_orders.get('count')} open critical work orders found.",
                "critical_work_orders": critical_orders.get("critical_work_orders", [])
            }
        }

    equipment_id = detect_equipment_id(request.message)

    if not equipment_id:
        return {
            "status": "error",
            "message": "Equipment ID not detected. Please specify equipment, for example CNC-01, PRESS-01, ROBOT-01."
        }

    if is_all_work_orders_question(request.message):
        all_orders = requests.post(
            f"{TOOLS_API_URL}/get_all_work_orders",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"{equipment_id} has {all_orders.get('count')} total work orders.",
                "equipment_id": equipment_id,
                "all_work_orders": all_orders.get("work_orders", [])
            }
        }

    if is_oee_question(request.message):
        oee = requests.post(
            f"{TOOLS_API_URL}/calculate_oee",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"{equipment_id} OEE is {oee.get('oee')}%.",
                "equipment_id": equipment_id,
                "planned_minutes": oee.get("planned_minutes"),
                "downtime_minutes": oee.get("downtime_minutes"),
                "runtime_minutes": oee.get("runtime_minutes"),
                "availability": oee.get("availability"),
                "performance": oee.get("performance"),
                "quality": oee.get("quality"),
                "oee": oee.get("oee")
            }
        }

    if is_open_work_orders_question(request.message):
        open_orders = requests.post(
            f"{TOOLS_API_URL}/get_open_work_orders",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        risk = requests.post(
            f"{TOOLS_API_URL}/predict_failure_risk",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        orders = open_orders.get("open_work_orders", [])

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"{equipment_id} has {len(orders)} open work orders.",
                "equipment_id": equipment_id,
                "risk_level": risk.get("risk_level"),
                "risk_score": risk.get("risk_score"),
                "health_score": risk.get("health_score"),
                "open_work_orders": [
                    {
                        "work_order_id": wo.get("work_order_id"),
                        "status": wo.get("status_work_order"),
                        "priority": wo.get("priority"),
                        "description": wo.get("description")
                    }
                    for wo in orders
                ]
            }
        }

    if is_risk_question(request.message):
        risk = requests.post(
            f"{TOOLS_API_URL}/predict_failure_risk",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"{equipment_id} risk level is {risk.get('risk_level')}.",
                "equipment_id": equipment_id,
                "risk_score": risk.get("risk_score"),
                "health_score": risk.get("health_score"),
                "risk_level": risk.get("risk_level"),
                "total_work_orders": risk.get("total_work_orders"),
                "critical_work_orders": risk.get("critical_work_orders"),
                "open_work_orders": risk.get("open_work_orders")
            }
        }

    if is_spare_parts_question(request.message):
        spare_parts = requests.post(
            f"{TOOLS_API_URL}/check_spare_parts",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": spare_parts
        }

    if is_maintenance_history_question(request.message):
        history = requests.post(
            f"{TOOLS_API_URL}/get_maintenance_history",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"Maintenance history retrieved for {equipment_id}.",
                "equipment_id": equipment_id,
                "maintenance_history": history
            }
        }

    return {
        "status": "not_supported_yet",
        "message": "This chat endpoint currently supports open work orders, all work orders, risk score, spare parts, highest risk equipment, downtime ranking, OEE, weekly summary, maintenance history, and critical work orders questions.",
        "examples": [
            "Are there open work orders for ROBOT-01?",
            "Show all work orders for PRESS-01",
            "What is the risk score for PRESS-01?",
            "Are spare parts available for CNC-01?",
            "Which machine has the highest risk?",
            "What equipment should I prioritize today?",
            "Which equipment is generating the most downtime?",
            "What is the OEE of PRESS-01?",
            "Generate a weekly maintenance summary.",
            "What maintenance history does ROBOT-01 have?",
            "Show all critical work orders."
        ]
    }