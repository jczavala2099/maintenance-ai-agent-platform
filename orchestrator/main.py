from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
import re

app = FastAPI(title="Maintenance Agent Orchestrator")

OLLAMA_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
TOOLS_API_URL = os.getenv("TOOLS_API_URL", "http://localhost:8001")
LOGGING_API_URL = os.getenv("LOGGING_API_URL", "http://localhost:8002")
AZURE_FUNCTIONS_URL = os.getenv("AZURE_FUNCTIONS_URL", "http://localhost:7071/api")


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
        "all work orders", "show all work orders", "list all work orders",
        "work order history", "todas las ordenes", "todas las órdenes",
        "mostrar todas las ordenes", "mostrar todas las órdenes"
    ]
    return any(keyword in text for keyword in keywords)


def is_create_work_order_question(message: str):
    text = message.lower()
    keywords = [
        "create work order",
        "create a work order",
        "generate work order",
        "open work order",
        "raise work order",
        "create maintenance ticket",
        "create ticket",
        "crear orden",
        "crear orden de trabajo",
        "generar orden",
        "levantar orden",
        "crear ticket"
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
        "which machines need attention today",
        "what machines need attention today",
        "machines need attention today",
        "equipment need attention today",
        "need attention today",
        "need attention",
        "machines to check today",
        "equipment to check today",
        "machines needing attention",
        "equipment needing attention",
        "riesgo mas alto", "riesgo más alto",
        "maquina con mayor riesgo", "máquina con mayor riesgo",
        "equipo con mayor riesgo", "priorizar hoy",
        "prioridades de mantenimiento",
        "que equipo debo priorizar", "qué equipo debo priorizar",
        "maquinas que necesitan atencion",
        "máquinas que necesitan atención",
        "equipos que necesitan atencion",
        "equipos que necesitan atención"
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
        "downtime", "down time", "most downtime", "most down time", "machine with most down time", "machine with the most down time", "equipment with most down time", "equipment with the most down time", "generating the most downtime",
        "equipment is generating the most downtime",
        "machine is generating the most downtime",
        "tiempo muerto", "mayor downtime", "mayor tiempo muerto",
        "mas tiempo muerto", "más tiempo muerto"
    ]
    return any(keyword in text for keyword in keywords)


def is_oee_question(message: str):
    text = message.lower()
    keywords = [
        "oee", "overall equipment effectiveness",
        "eficiencia global", "efectividad global",
        "availability", "performance", "quality"
    ]
    return any(keyword in text for keyword in keywords)


def is_lowest_oee_question(message: str):
    text = message.lower()
    keywords = [
        "lowest oee", "lowest oee machine", "machine with lowest oee",
        "equipment with lowest oee", "worst oee",
        "lowest equipment effectiveness",
        "what is the machine with lowest oee",
        "which machine has the lowest oee",
        "which equipment has the lowest oee",
        "menor oee", "peor oee", "equipo con menor oee",
        "maquina con menor oee", "máquina con menor oee"
    ]
    return any(keyword in text for keyword in keywords)


def is_equipment_info_question(message: str):
    text = message.lower()
    keywords = [
        "status of", "what is the status",
        "show information for", "show info for",
        "equipment information", "equipment info",
        "show equipment", "get equipment",
        "equipment details", "get equipment details",
        "tell me about", "details for",
        "informacion del equipo", "información del equipo",
        "estado de", "detalles del equipo"
    ]
    return any(keyword in text for keyword in keywords)
def is_recommended_maintenance_question(message: str):
    text = message.lower()
    keywords = [
        "recommended maintenance", "recomended maintenance",
        "maintenance recommendation", "recommend maintenance",
        "recommended action", "what should i do",
        "what maintenance is recommended",
        "what do you recommend", "maintenance advice",
        "recommendation for", "recommended maintenance for",
        "recomendacion de mantenimiento", "recomendación de mantenimiento",
        "mantenimiento recomendado", "que mantenimiento recomiendas",
        "qué mantenimiento recomiendas"
    ]
    return any(keyword in text for keyword in keywords)

def is_common_failure_question(message: str):
    text = message.lower()
    keywords = [
        "most common failure",
        "common failure",
        "top failure",
        "top failures",
        "most frequent failure",
        "frequent failures",
        "failure types",
        "what failure is most common",
        "which is the most common failure",
        "falla mas comun",
        "falla más común",
        "fallas mas comunes",
        "fallas más comunes"
    ]
    return any(keyword in text for keyword in keywords)
def is_daily_maintenance_recommendation_question(message: str):
    text = message.lower()
    keywords = [
        "what maintenance should be done today",
        "what maintenance should i do today",
        "maintenance for today",
        "today maintenance",
        "today's maintenance",
        "daily maintenance recommendation",
        "daily maintenance priorities",
        "what should maintenance do today",
        "what should be done today",
        "mantenimiento de hoy",
        "mantenimiento para hoy",
        "que mantenimiento se debe hacer hoy",
        "qué mantenimiento se debe hacer hoy",
        "prioridades de mantenimiento hoy"
    ]
    return any(keyword in text for keyword in keywords)


def is_weekly_summary_question(message: str):
    text = message.lower()
    keywords = [
        "weekly maintenance summary",
        "generate a weekly maintenance summary",
        "weekly summary", "maintenance summary",
        "resumen semanal", "resumen de mantenimiento",
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
        f"{AZURE_FUNCTIONS_URL}/create_work_order",
        json={
            "request_id": request_id,
            "equipment_id": equipment_id,
            "priority": "high",
            "description": request.message,
            "recommended_action": "Inspect bearings, shaft alignment and mounting base",
            "requested_by": request.user_id
        },
        timeout=10
    ).json()

    notification = requests.post(
        f"{AZURE_FUNCTIONS_URL}/send_notification",
        json={
            "channel": "maintenance_supervisor",
            "body": f"Maintenance work order created for {equipment_id}."
        },
        timeout=10
    ).json()

    final_response = (
        "A high priority maintenance work order was created using an Azure Function "
        "and the supervisor was notified using a serverless tool."
    )

    return {
        "agent_flow": "User -> Orchestrator -> Azure Function Tool(s) -> Tools API -> PostgreSQL -> Response",
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

    add_step(
        "validate_input",
        "success",
        {
            "message": "Input validated successfully.",
            "equipment_id": equipment_id
        }
    )

    equipment = requests.post(
        f"{AZURE_FUNCTIONS_URL}/get_equipment_info",
        json={"equipment_id": equipment_id},
        timeout=10
    ).json()

    add_step("azure_function_get_equipment_info", "success", equipment)

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
            f"{AZURE_FUNCTIONS_URL}/create_work_order",
            json={
                "request_id": request_id,
                "equipment_id": equipment_id,
                "priority": "critical",
                "description": request.message,
                "recommended_action": "Inspect bearings, shaft alignment and mounting base.",
                "requested_by": request.user_id
            },
            timeout=10
        ).json()

        add_step("azure_function_create_work_order", "success", work_order)
    else:
        work_order = None

    notification = requests.post(
        f"{AZURE_FUNCTIONS_URL}/send_notification",
        json={
            "channel": "maintenance_supervisor",
            "body": f"Critical workflow executed for {equipment_id}."
        },
        timeout=10
    ).json()

    add_step("azure_function_send_notification", "success", notification)

    final_response = {
        "summary": "Critical maintenance workflow completed using Azure Functions serverless tools.",
        "equipment_id": equipment_id,
        "priority": "critical",
        "decision": decision["decision"],
        "work_order_id": work_order.get("work_order_id") if work_order else None,
        "notification_status": notification.get("status"),
        "serverless_tools_used": [
            "get_equipment_info",
            "create_work_order",
            "send_notification"
        ]
    }

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
        f"{AZURE_FUNCTIONS_URL}/get_equipment_info",
        json={"equipment_id": equipment_id},
        timeout=10
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
        "serverless_tool_used": "azure_function_get_equipment_info",
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
    if is_highest_risk_question(request.message):
        highest_risk = requests.get(
            f"{TOOLS_API_URL}/get_highest_risk_equipment",
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": "Highest risk equipment ranking generated successfully.",
                "highest_risk_equipment": highest_risk.get("highest_risk_equipment", [])
            }
        }

    if is_lowest_oee_question(request.message):
        oee_ranking = requests.get(
            f"{TOOLS_API_URL}/get_oee_ranking",
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": "Lowest OEE equipment ranking generated successfully.",
                "lowest_oee_equipment": oee_ranking.get("lowest_oee_equipment", []),
                "oee_ranking": oee_ranking.get("oee_ranking", [])
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

    if is_daily_maintenance_recommendation_question(request.message):
        highest_risk = requests.get(
            f"{TOOLS_API_URL}/get_highest_risk_equipment",
            timeout=5
        ).json()

        critical_orders = requests.get(
            f"{TOOLS_API_URL}/get_critical_work_orders",
            timeout=5
        ).json()

        downtime = requests.get(
            f"{TOOLS_API_URL}/get_downtime_ranking",
            timeout=5
        ).json()

        risk_items = highest_risk.get("highest_risk_equipment", [])[:3]
        critical_items = critical_orders.get("critical_work_orders", [])[:5]
        downtime_items = downtime.get("downtime_ranking", [])[:3]

        recommendations = []
        for item in risk_items:
            recommendations.append({
                "equipment_id": item.get("equipment_id"),
                "priority": "critical" if item.get("risk_level") == "critical" else "high",
                "reason": f"Risk level {item.get('risk_level')} with score {item.get('risk_score')}.",
                "recommended_action": "Inspect equipment condition, review open work orders, and validate spare parts before starting work."
            })

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": "Daily maintenance recommendations generated from risk ranking, critical work orders, and downtime data.",
                "recommended_focus": recommendations,
                "critical_open_work_orders": critical_items,
                "highest_downtime_equipment": downtime_items,
                "data_sources": [
                    "get_highest_risk_equipment",
                    "get_critical_work_orders",
                    "get_downtime_ranking"
                ]
            }
        }
    if is_common_failure_question(request.message):
        failures = requests.get(
            f"{TOOLS_API_URL}/dashboard/top-failure-types",
            timeout=5
        ).json()

        failure_data = failures.get("data", [])
        most_common = failure_data[0] if failure_data else None

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": "Most common failure types generated successfully.",
                "most_common_failure": most_common,
                "top_failure_types": failure_data,
                "data_source": "dashboard/top-failure-types"
            }
        }
    equipment_id = detect_equipment_id(request.message)

    if not equipment_id:
        return {
            "status": "error",
            "message": "Equipment ID not detected. Please specify equipment, for example CNC-01, PRESS-01, ROBOT-01."
        }

    if is_equipment_info_question(request.message):
        equipment = requests.post(
            f"{TOOLS_API_URL}/get_equipment_info",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"Equipment information retrieved for {equipment_id}.",
                "equipment_id": equipment_id,
                "equipment": equipment
            }
        }

    if is_recommended_maintenance_question(request.message):
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

        latest_failure = history.get("last_failure")
        latest_action = history.get("last_action")
        recurrence_risk = history.get("recurrence_risk")
        risk_level = risk.get("risk_level")
        risk_score = risk.get("risk_score")
        criticality = equipment.get("criticality")
        low_stock_parts = spare_parts.get("low_stock_parts", 0)
        open_order_count = open_orders.get("count", 0)

        priority = "medium"
        if risk_level in ["critical", "high"] or criticality == "high":
            priority = "high"
        if risk_level == "critical" or open_order_count > 0:
            priority = "critical"

        actions = [
            latest_action or "Perform a preventive maintenance inspection",
            "Review open work orders before starting the intervention",
            "Validate spare parts availability before scheduling downtime"
        ]

        if latest_failure:
            actions.insert(0, f"Inspect the recurring failure mode: {latest_failure}")
        if low_stock_parts > 0:
            actions.append("Reorder low-stock spare parts before closing the maintenance plan")

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"Recommended maintenance generated for {equipment_id}.",
                "equipment_id": equipment_id,
                "priority": priority,
                "risk_level": risk_level,
                "risk_score": risk_score,
                "recurrence_risk": recurrence_risk,
                "latest_failure": latest_failure,
                "recommended_actions": actions,
                "open_work_orders": open_order_count,
                "spare_parts_available": spare_parts.get("available"),
                "low_stock_parts": low_stock_parts,
                "data_sources": [
                    "get_equipment_info",
                    "get_maintenance_history",
                    "check_spare_parts",
                    "get_open_work_orders",
                    "predict_failure_risk"
                ]
            }
        }
    if is_create_work_order_question(request.message):
        payload = {
            "request_id": "CHAT-AZFUNC-0001",
            "equipment_id": equipment_id,
            "priority": "high",
            "description": request.message,
            "recommended_action": "Review reported issue and perform maintenance inspection.",
            "requested_by": request.user_id
        }

        work_order = requests.post(
            f"{AZURE_FUNCTIONS_URL}/create_work_order",
            json=payload,
            timeout=10
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"Serverless work order created for {equipment_id}.",
                "serverless_tool": "azure_function_create_work_order",
                "equipment_id": equipment_id,
                "work_order": work_order
            }
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
        "message": "This chat endpoint currently supports equipment information, recommended maintenance, daily maintenance recommendations, common failure analysis, open work orders, all work orders, serverless work order creation, risk score, spare parts, highest risk equipment, lowest OEE equipment, downtime ranking, OEE, weekly summary, maintenance history, and critical work orders questions.",
        "examples": [
            "What is the status of PRESS-01?",
            "Show information for ROBOT-01",
            "Recommended maintenance for PRESS-01",
            "What maintenance should be done today?",
            "Which is the most common failure?",
            "Are there open work orders for ROBOT-01?",
            "Show all work orders for PRESS-01",
            "Create a work order for PRESS-01 because it is overheating",
            "What is the risk score for PRESS-01?",
            "Are spare parts available for CNC-01?",
            "Which machine has the highest risk?",
            "What equipment should I prioritize today?",
            "Which equipment is generating the most downtime?",
            "What machine has the lowest OEE?",
            "What is the OEE of PRESS-01?",
            "Generate a weekly maintenance summary.",
            "What maintenance history does ROBOT-01 have?",
            "Show all critical work orders."
        ]
    }
