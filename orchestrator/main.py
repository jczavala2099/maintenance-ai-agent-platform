from fastapi import FastAPI
from pydantic import BaseModel
import requests
import os
import re
import unicodedata

app = FastAPI(title="Orquestador del Agente de Mantenimiento")

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


def translate_label(value: str | None):
    labels = {
        "critical": "crítico",
        "high": "alto",
        "medium": "medio",
        "low": "bajo",
        "created": "creada",
        "in_progress": "en progreso",
        "closed": "cerrada",
        "running": "operando",
        "maintenance": "mantenimiento",
        "down": "detenida",
        "standby": "en espera",
    }
    return labels.get(value, value)


def translate_maintenance_text(value: str | None):
    if value is None:
        return None

    translations = {
        "Oil Leakage": "Fuga de aceite",
        "Oil leakage": "Fuga de aceite",
        "Hydraulic Pressure Drop": "Caída de presión hidráulica",
        "Hydraulic pressure drop": "Caída de presión hidráulica",
        "High Vibration": "Vibración alta",
        "High vibration": "Vibración alta",
        "Overheating": "Sobrecalentamiento",
        "Sensor Failure": "Falla de sensor",
        "Sensor failure": "Falla de sensor",
        "Airflow Restriction": "Restricción de flujo de aire",
        "Airflow restriction": "Restricción de flujo de aire",
        "Temperature Deviation": "Desviación de temperatura",
        "Temperature deviation": "Desviación de temperatura",
        "Spindle Vibration": "Vibración de husillo",
        "Belt Slipping": "Deslizamiento de banda",
        "Belt slipping": "Deslizamiento de banda",
        "Die Alignment Issue": "Problema de alineación de troquel",
        "Die alignment issue": "Problema de alineación de troquel",
        "Wire Feed Issue": "Problema de alimentación de alambre",
        "Wire feed issue": "Problema de alimentación de alambre",
        "Electrical Fault": "Falla eléctrica",
        "Electrical fault": "Falla eléctrica",
        "Low Flow Rate": "Bajo caudal",
        "Low flow rate": "Bajo caudal",
        "Jam Detected": "Atasco detectado",
        "Jam detected": "Atasco detectado",
        "Tool Changer Fault": "Falla de cambiador de herramienta",
        "Tool changer fault": "Falla de cambiador de herramienta",
        "Conveyor Tracking Issue": "Problema de alineación de transportador",
        "Conveyor tracking issue": "Problema de alineación de transportador",
        "Low Air Pressure": "Baja presión de aire",
        "Low air pressure": "Baja presión de aire",
        "Replaced hydraulic seal and cleaned oil residue": "Se reemplazó sello hidráulico y se limpió residuo de aceite",
        "Demo workflow request": "Solicitud de workflow de demo",
        "Inspect press and validate oil leakage history": "Inspeccionar prensa y validar historial de fuga de aceite",
        "Inspect bearings, mounting base and alignment": "Inspeccionar rodamientos, base de montaje y alineación",
        "Inspect hydraulic pump, seals and pressure regulator": "Inspeccionar bomba hidráulica, sellos y regulador de presión",
        "Create a work order for": "Crear una orden de trabajo para",
        "because it is overheating": "porque se está sobrecalentando",
        "because it is sobrecalentamiento": "porque se está sobrecalentando",
        "Review reported issue and perform maintenance inspection": "Revisar el problema reportado y realizar inspección de mantenimiento",
        "detected on": "detectada en",
    }

    translated = value
    for source, target in translations.items():
        translated = translated.replace(source, target)
        translated = translated.replace(source.lower(), target.lower())
    return translated


def normalize_text(value: str | None):
    if not value:
        return ""

    value = unicodedata.normalize("NFKD", value)
    value = "".join(char for char in value if not unicodedata.combining(char))
    value = value.lower()
    value = re.sub(r"\b(CNC|PRESS|CONV|ROBOT|COMP|PUMP|FAN|OVEN|PACK)-\d{2}\b", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"[^a-z0-9\s]", " ", value)

    replacements = {
        "se esta sobrecalentando": "overheating",
        "sobrecalentando": "overheating",
        "sobrecalentamiento": "overheating",
        "calentando": "overheating",
        "fuga de aceite": "oil leakage",
        "tirando aceite": "oil leakage",
        "perdida de aceite": "oil leakage",
        "vibracion alta": "high vibration",
        "vibrando mucho": "high vibration",
        "baja presion hidraulica": "hydraulic pressure drop",
        "caida de presion hidraulica": "hydraulic pressure drop",
        "falla de sensor": "sensor failure",
    }
    for source, target in replacements.items():
        value = value.replace(source, target)

    stop_words = {
        "create", "crear", "generate", "generar", "open", "abrir",
        "work", "order", "orden", "trabajo", "ticket", "para",
        "for", "porque", "because", "due", "to", "por", "la", "el",
        "los", "las", "un", "una", "de", "del", "se", "esta", "está",
        "is", "it", "the", "a", "an"
    }
    tokens = [
        token for token in value.split()
        if token and token not in stop_words and len(token) > 1
    ]
    return " ".join(tokens)


def extract_reported_issue(message: str):
    text = message.strip()
    patterns = [
        r"\bporque\b(.+)$",
        r"\bbecause\b(.+)$",
        r"\bdue to\b(.+)$",
        r"\bpor\b(.+)$",
    ]

    for pattern in patterns:
        match = re.search(pattern, text, flags=re.IGNORECASE)
        if match:
            issue = match.group(1).strip()
            if issue:
                return issue

    equipment_id = detect_equipment_id(text)
    if equipment_id:
        text = re.sub(re.escape(equipment_id), "", text, flags=re.IGNORECASE)

    return text


def find_duplicate_open_work_order(open_orders: list[dict], reported_issue: str):
    normalized_issue = normalize_text(reported_issue)
    issue_tokens = set(normalized_issue.split())

    if not issue_tokens:
        return None

    for order in open_orders:
        normalized_description = normalize_text(order.get("description"))
        description_tokens = set(normalized_description.split())

        if not description_tokens:
            continue

        if normalized_issue in normalized_description or normalized_description in normalized_issue:
            return order

        overlap = issue_tokens.intersection(description_tokens)
        similarity = len(overlap) / max(len(issue_tokens), len(description_tokens))
        if similarity >= 0.6:
            return order

    return None


def is_open_work_orders_question(message: str):
    text = message.lower()
    keywords = [
        "open work orders", "open orders", "pending work orders",
        "active work orders", "ordenes abiertas", "órdenes abiertas",
        "ordenes pendientes", "órdenes pendientes"
    ]
    return any(keyword in text for keyword in keywords)


def is_all_machines_question(message: str):
    text = message.lower()
    keywords = [
        "show all machines",
        "list all machines",
        "all machines",
        "show all equipment",
        "list all equipment",
        "all equipment",
        "machines list",
        "equipment list",
        "mostrar todas las maquinas",
        "mostrar todas las máquinas",
        "muestra todas las maquinas",
        "muestra todas las máquinas",
        "listar todos los equipos",
        "lista de equipos",
        "todos los equipos",
        "todas las maquinas",
        "todas las máquinas",
    ]
    return any(keyword in text for keyword in keywords)


def is_all_work_orders_question(message: str):
    text = message.lower()
    keywords = [
        "all work orders", "show all work orders", "list all work orders",
        "work order history", "todas las ordenes", "todas las órdenes",
        "mostrar todas las ordenes", "mostrar todas las órdenes",
        "muestra todas las ordenes", "muestra todas las órdenes"
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
        "mayor riesgo",
        "que maquina tiene el mayor riesgo",
        "qué máquina tiene el mayor riesgo",
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
        "muestra informacion", "muestra información",
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


def is_failure_pattern_question(message: str):
    text = message.lower()
    keywords = [
        "has this failure happened before",
        "happened before",
        "failure pattern",
        "recurring failure",
        "repeated failure",
        "how many times",
        "how often",
        "has oil leakage happened before",
        "analyze failure",
        "failure recurrence",
        "similar work orders",
        "patron de falla",
        "patrón de falla",
        "falla recurrente",
        "cuantas veces",
        "cuántas veces",
        "ha ocurrido antes",
        "ocurrido antes",
        "se ha presentado",
        "ha pasado antes"
    ]
    return any(keyword in text for keyword in keywords)


def extract_failure_type(message: str):
    text = message.lower()
    spanish_failures = {
        "fuga de aceite": "Oil Leakage",
        "caida de presion hidraulica": "Hydraulic Pressure Drop",
        "caída de presión hidráulica": "Hydraulic Pressure Drop",
        "vibracion alta": "High Vibration",
        "vibración alta": "High Vibration",
        "sobrecalentamiento": "Overheating",
        "falla de sensor": "Sensor Failure",
        "desviacion de temperatura": "Temperature Deviation",
        "desviación de temperatura": "Temperature Deviation"
    }

    for failure, translated_failure in spanish_failures.items():
        if failure in text:
            return translated_failure

    known_failures = [
        "oil leakage", "hydraulic pressure drop", "high vibration",
        "overheating", "sensor failure", "airflow restriction",
        "spindle vibration", "belt slipping", "temperature deviation",
        "low air pressure", "die alignment issue", "wire feed issue",
        "electrical fault", "low flow rate", "jam detected"
    ]

    for failure in known_failures:
        if failure in text:
            return failure.title()

    patterns = [
        r"(?:failure|falla)\s+(?:in|on|for|de)\s+([a-zA-Z\s]+?)\s+(?:on|in|for)\s+",
        r"(?:has|have)\s+([a-zA-Z\s]+?)\s+happened",
        r"analyze\s+([a-zA-Z\s]+?)\s+(?:on|for)\s+"
    ]

    for pattern in patterns:
        match = re.search(pattern, text)
        if match:
            candidate = match.group(1).strip()
            if candidate:
                return candidate.title()

    return None
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
        "what is the recommended maintenance for today",
        "what is the recommended maintance for today",
        "recommended maintenance for today",
        "recommended maintance for today",
        "recommend maintenance for today",
        "what maintenance should i do today",
        "maintenance for today", "maintance for today",
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
        "resumen semanal de mantenimiento",
        "genera un resumen semanal",
        "generar resumen semanal"
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
Eres un agente de mantenimiento industrial.

Analiza el incidente de mantenimiento y entrega una recomendación breve en español.

Mensaje del usuario:
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
            "message": "No se detectó ID de equipo. Especifica un equipo, por ejemplo CNC-01, PRESS-01 o ROBOT-01."
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
            "body": f"Orden de mantenimiento creada para {equipment_id}."
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
            "message": "No se detectó ID de equipo. Especifica un equipo, por ejemplo CNC-01, PRESS-01 o ROBOT-01."
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
            "message": "Entrada validada correctamente.",
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
            "reason": "El equipo es crítico y hay refacciones disponibles."
        }
    else:
        decision = {
            "decision": "escalate_to_supervisor",
            "reason": "Las refacciones no están disponibles o no pudieron confirmarse."
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
            "body": f"Workflow crítico ejecutado para {equipment_id}."
        },
        timeout=10
    ).json()

    add_step("azure_function_send_notification", "success", notification)

    final_response = {
        "summary": "Workflow crítico de mantenimiento completado usando herramientas serverless de Azure Functions.",
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
            "message": "No se detectó ID de equipo. Especifica un equipo, por ejemplo CNC-01, PRESS-01 o ROBOT-01."
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
Eres un asesor experto de mantenimiento industrial.

Analiza estos datos reales de mantenimiento y responde en español con:
1. Nivel de riesgo de falla
2. Causa raíz más probable
3. Acción de mantenimiento recomendada
4. Recomendación de refacciones
5. Prioridad operativa
6. Explicación breve para un supervisor de mantenimiento

Problema reportado por el usuario:
{request.message}

Equipo detectado:
{equipment_id}

Datos del equipo:
{equipment}

Historial de mantenimiento:
{history}

Refacciones:
{spare_parts}

Órdenes recientes:
{work_orders}

Predicción de riesgo de mantenimiento:
{risk_prediction}
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
        "advisor_type": "Asesor IA de Mantenimiento",
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
    if is_all_machines_question(request.message):
        equipment_response = requests.get(
            f"{TOOLS_API_URL}/dashboard/work-orders-by-equipment",
            timeout=5
        ).json()

        equipment_list = equipment_response.get("data", [])
        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": f"Se encontraron {len(equipment_list)} equipos registrados.",
                "equipment_list": equipment_list
            }
        }

    if is_highest_risk_question(request.message):
        highest_risk = requests.get(
            f"{TOOLS_API_URL}/get_highest_risk_equipment",
            timeout=5
        ).json()

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": "Ranking de equipos con mayor riesgo generado correctamente.",
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
                "summary": "Ranking de equipos con menor OEE generado correctamente.",
                "lowest_oee_equipment": oee_ranking.get("lowest_oee_equipment", []),
                "oee_ranking": oee_ranking.get("oee_ranking", [])
            }
        }

    if is_downtime_question(request.message):
        downtime = requests.get(
            f"{TOOLS_API_URL}/get_downtime_ranking",
            timeout=5
        ).json()

        downtime_ranking = downtime.get("downtime_ranking", [])
        display_lines = ["### Ranking De Tiempo Muerto", ""]
        if downtime_ranking:
            top = downtime_ranking[0]
            display_lines.append(
                f"Equipo con mayor tiempo muerto: **{top.get('equipment_id')} - {top.get('equipment_name')}** "
                f"con **{top.get('estimated_downtime_hours')} horas estimadas**."
            )
            display_lines.append("")
            display_lines.append("Principales equipos por tiempo muerto:")
            for index, item in enumerate(downtime_ranking[:5], start=1):
                display_lines.append(
                    f"{index}. **{item.get('equipment_id')}** - {item.get('estimated_downtime_hours')} horas "
                    f"({item.get('area')}, {item.get('total_work_orders')} órdenes)"
                )
        else:
            display_lines.append("No hay datos de tiempo muerto disponibles.")

        return {
            "status": "success",
            "question": request.message,
            "display_answer": "\n".join(display_lines),
            "answer": {
                "summary": "Ranking de tiempo muerto generado correctamente.",
                "downtime_ranking": downtime_ranking
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
        critical_items = critical_orders.get("critical_work_orders", [])
        detected_equipment_id = detect_equipment_id(request.message)

        if detected_equipment_id:
            critical_items = [
                item for item in critical_items
                if item.get("equipment_id") == detected_equipment_id
            ]
            summary = (
                f"Se encontraron {len(critical_items)} órdenes críticas abiertas "
                f"para {detected_equipment_id}."
            )
        else:
            summary = f"Se encontraron {len(critical_items)} órdenes críticas abiertas."

        return {
            "status": "success",
            "question": request.message,
            "answer": {
                "summary": summary,
                "equipment_id": detected_equipment_id,
                "count": len(critical_items),
                "critical_work_orders": critical_items
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
                "reason": f"Nivel de riesgo {translate_label(item.get('risk_level'))} con score {item.get('risk_score')}.",
                "recommended_action": "Inspeccionar condición del equipo, revisar órdenes abiertas y validar refacciones antes de iniciar el trabajo."
            })

        display_lines = [
            "### Recomendación Diaria De Mantenimiento",
            "",
            "Enfocar primero el trabajo de mantenimiento de hoy en los equipos de mayor riesgo.",
            ""
        ]
        for index, item in enumerate(recommendations, start=1):
            display_lines.append(f"**Prioridad {index}: {item.get('equipment_id')}**")
            display_lines.append(f"- Prioridad: {translate_label(item.get('priority'))}")
            display_lines.append(f"- Razón: {item.get('reason')}")
            display_lines.append(f"- Acción: {item.get('recommended_action')}")
            display_lines.append("")

        if critical_items:
            display_lines.append("Órdenes críticas abiertas:")
            for item in critical_items[:3]:
                display_lines.append(
                    f"- **{item.get('equipment_id')}**: {translate_maintenance_text(item.get('description'))} "
                    f"({translate_label(item.get('status_work_order'))})"
                )
            display_lines.append("")

        if downtime_items:
            display_lines.append("Equipo con mayor tiempo muerto:")
            for index, item in enumerate(downtime_items, start=1):
                display_lines.append(
                    f"{index}. **{item.get('equipment_id')}** - {item.get('estimated_downtime_hours')} horas"
                )

        return {
            "status": "success",
            "question": request.message,
            "display_answer": "\n".join(display_lines),
            "answer": {
                "summary": "Recomendaciones diarias de mantenimiento generadas desde ranking de riesgo, órdenes críticas y datos de tiempo muerto.",
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

        display_lines = ["### Falla Más Común", ""]
        if most_common:
            display_lines.append(
                f"La falla más común es **{most_common.get('failure_type')}** "
                f"con **{most_common.get('count')} ocurrencias**."
            )
            display_lines.append("")
            display_lines.append("Principales tipos de falla:")
            for index, item in enumerate(failure_data[:10], start=1):
                display_lines.append(f"{index}. **{item.get('failure_type')}** - {item.get('count')} ocurrencias")
        else:
            display_lines.append("No hay datos de fallas disponibles.")

        return {
            "status": "success",
            "question": request.message,
            "display_answer": "\n".join(display_lines),
            "answer": {
                "summary": "Tipos de falla más comunes generados correctamente.",
                "most_common_failure": most_common,
                "top_failure_types": failure_data,
                "data_source": "dashboard/top-failure-types"
            }
        }
    equipment_id = detect_equipment_id(request.message)

    if not equipment_id:
        return {
            "status": "error",
            "message": "No se detectó ID de equipo. Especifica un equipo, por ejemplo CNC-01, PRESS-01 o ROBOT-01."
        }

    if is_failure_pattern_question(request.message):
        failure_type = extract_failure_type(request.message)
        pattern = requests.post(
            f"{TOOLS_API_URL}/analyze_failure_pattern",
            json={
                "equipment_id": equipment_id,
                "failure_type": failure_type,
                "years": 2
            },
            timeout=5
        ).json()

        if pattern.get("status") != "success":
            return {
                "status": "error",
                "question": request.message,
                "message": pattern.get("message", "No hay datos disponibles para este patrón de falla.")
            }

        recurrence_labels = {
            "critical": "crítico",
            "high": "alto",
            "medium": "medio",
            "low": "bajo"
        }
        recurrence_level = recurrence_labels.get(
            pattern.get("recurrence_level"),
            pattern.get("recurrence_level")
        )

        display_lines = [
            f"### Análisis De Patrón De Falla Para {equipment_id}",
            "",
            f"Tipo de falla: **{pattern.get('failure_type')}**",
            f"Ocurrencias en los últimos {pattern.get('analysis_window_years')} años: **{pattern.get('occurrences')}**",
            f"Nivel de recurrencia: **{recurrence_level}**",
            f"Días promedio entre fallas: **{pattern.get('average_days_between_failures') or 'N/A'}**",
            "",
            f"Acción correctiva más común: **{pattern.get('most_common_action')}**",
            "",
            f"Recomendación: {pattern.get('recommendation')}",
            "",
            f"Confianza: **{pattern.get('confidence')}**"
        ]

        return {
            "status": "success",
            "question": request.message,
            "display_answer": "\n".join(display_lines),
            "answer": {
                "summary": f"Análisis de patrón de falla generado para {equipment_id}.",
                "failure_pattern_analysis": pattern
            }
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
                "summary": f"Información de equipo obtenida para {equipment_id}.",
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
            translate_maintenance_text(latest_action) or "Realizar inspección preventiva de mantenimiento",
            "Revisar órdenes abiertas antes de iniciar la intervención",
            "Validar disponibilidad de refacciones antes de programar paro"
        ]

        if latest_failure:
            actions.insert(0, f"Inspeccionar el modo de falla recurrente: {translate_maintenance_text(latest_failure)}")
        if low_stock_parts > 0:
            actions.append("Reordenar refacciones con bajo inventario antes de cerrar el plan de mantenimiento")

        display_lines = [
            f"### Mantenimiento Recomendado Para {equipment_id}",
            "",
            f"Prioridad: **{translate_label(priority)}**",
            f"Riesgo: **{translate_label(risk_level)}** con score **{risk_score}**",
            f"Último patrón de falla: **{translate_maintenance_text(latest_failure) or 'N/A'}**",
            "",
            "Acciones recomendadas:"
        ]
        for index, action in enumerate(actions, start=1):
            display_lines.append(f"{index}. {action}")
        display_lines.extend([
            "",
            f"Órdenes abiertas: **{open_order_count}**",
            f"Refacciones disponibles: **{'Sí' if spare_parts.get('available') else 'No'}**",
            f"Refacciones con bajo inventario: **{low_stock_parts}**"
        ])

        return {
            "status": "success",
            "question": request.message,
            "display_answer": "\n".join(display_lines),
            "answer": {
                "summary": f"Mantenimiento recomendado generado para {equipment_id}.",
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
        reported_issue = extract_reported_issue(request.message)
        open_orders_response = requests.post(
            f"{TOOLS_API_URL}/get_open_work_orders",
            json={"equipment_id": equipment_id},
            timeout=5
        ).json()
        open_orders = open_orders_response.get("open_work_orders", [])
        duplicate_order = find_duplicate_open_work_order(open_orders, reported_issue)

        if duplicate_order:
            display_lines = [
                f"### Orden Ya Abierta Para {equipment_id}",
                "",
                f"La orden **{duplicate_order.get('work_order_id')}** ya está abierta para esta situación.",
                f"Estado: **{translate_label(duplicate_order.get('status_work_order'))}**",
                f"Prioridad: **{translate_label(duplicate_order.get('priority'))}**",
                f"Reporte existente: {translate_maintenance_text(duplicate_order.get('description'))}",
                "",
                "No se creó una orden duplicada."
            ]

            return {
                "status": "success",
                "question": request.message,
                "display_answer": "\n".join(display_lines),
                "answer": {
                    "summary": (
                        f"La orden {duplicate_order.get('work_order_id')} ya está abierta "
                        f"para esta situación en {equipment_id}."
                    ),
                    "duplicate_detected": True,
                    "equipment_id": equipment_id,
                    "reported_issue": reported_issue,
                    "existing_work_order": duplicate_order,
                    "work_order_created": False
                }
            }

        payload = {
            "request_id": "CHAT-AZFUNC-0001",
            "equipment_id": equipment_id,
            "priority": "high",
            "description": request.message,
            "recommended_action": "Revisar el problema reportado y realizar inspección de mantenimiento.",
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
            "display_answer": (
                f"### Orden De Trabajo Creada Para {equipment_id}\n\n"
                f"Se creó la orden **{work_order.get('work_order_id')}** para el reporte: "
                f"{translate_maintenance_text(reported_issue)}."
            ),
            "answer": {
                "summary": f"Orden de trabajo serverless creada para {equipment_id}.",
                "serverless_tool": "azure_function_create_work_order",
                "equipment_id": equipment_id,
                "reported_issue": reported_issue,
                "duplicate_detected": False,
                "work_order_created": True,
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
                "summary": f"{equipment_id} tiene {all_orders.get('count')} órdenes de trabajo en total.",
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
                "summary": f"El OEE de {equipment_id} es {oee.get('oee')}%.",
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
                "summary": f"{equipment_id} tiene {len(orders)} órdenes abiertas.",
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
                "summary": f"El nivel de riesgo de {equipment_id} es {risk.get('risk_level')}.",
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
                "summary": f"Historial de mantenimiento obtenido para {equipment_id}.",
                "equipment_id": equipment_id,
                "maintenance_history": history
            }
        }

    return {
        "status": "not_supported_yet",
        "message": "Este endpoint de chat actualmente soporta información de equipos, mantenimiento recomendado, recomendaciones diarias, análisis de falla común, análisis de patrones de falla, órdenes abiertas, todas las órdenes, creación serverless de órdenes, riesgo, refacciones, equipos con mayor riesgo, equipos con menor OEE, ranking de tiempo muerto, OEE, resumen semanal, historial de mantenimiento y órdenes críticas.",
        "examples": [
            "¿Cuál es el estado de PRESS-01?",
            "Muestra información de ROBOT-01",
            "Mantenimiento recomendado para PRESS-01",
            "¿Qué mantenimiento se debe hacer hoy?",
            "¿Cuál es la falla más común?",
            "¿La fuga de aceite ha ocurrido antes en PRESS-01?",
            "¿Hay órdenes abiertas para ROBOT-01?",
            "Muestra todas las órdenes de PRESS-01",
            "Crear orden de trabajo para PRESS-01 porque se está sobrecalentando",
            "¿Cuál es el riesgo de PRESS-01?",
            "¿Hay refacciones disponibles para CNC-01?",
            "¿Qué máquina tiene el mayor riesgo?",
            "¿Qué equipo debo priorizar hoy?",
            "¿Qué equipo genera más tiempo muerto?",
            "¿Qué máquina tiene el menor OEE?",
            "¿Cuál es el OEE de PRESS-01?",
            "Genera un resumen semanal de mantenimiento.",
            "¿Qué historial de mantenimiento tiene ROBOT-01?",
            "Muestra todas las órdenes críticas."
        ]
    }





