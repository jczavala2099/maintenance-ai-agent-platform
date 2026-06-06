import json
import os
import requests
import azure.functions as func
import azure.durable_functions as df

app = df.DFApp(http_auth_level=func.AuthLevel.ANONYMOUS)

TOOLS_API_URL = os.getenv("TOOLS_API_URL", "http://tools-api:8001")
AZURE_FUNCTIONS_URL = os.getenv(
    "AZURE_FUNCTIONS_URL",
    "http://azure-functions-tools/api"
)


def json_response(payload: dict, status_code: int = 200):
    return func.HttpResponse(
        json.dumps(payload),
        status_code=status_code,
        mimetype="application/json"
    )


@app.route(route="maintenance_workflow/start", methods=["POST"])
@app.durable_client_input(client_name="client")
async def start_maintenance_workflow(
    req: func.HttpRequest,
    client: df.DurableOrchestrationClient
) -> func.HttpResponse:
    try:
        payload = req.get_json()

        instance_id = await client.start_new(
            "maintenance_workflow_orchestrator",
            None,
            payload
        )

        return client.create_check_status_response(req, instance_id)

    except Exception as e:
        return json_response(
            {
                "status": "error",
                "message": str(e)
            },
            500
        )


@app.orchestration_trigger(context_name="context")
def maintenance_workflow_orchestrator(
    context: df.DurableOrchestrationContext
):
    payload = context.get_input()

    validation = yield context.call_activity(
        "validate_workflow_input",
        payload
    )

    if validation.get("status") != "success":
        return {
            "status": "error",
            "step": "validate_workflow_input",
            "detail": validation
        }

    equipment_id = validation["equipment_id"]

    equipment = yield context.call_activity(
        "get_equipment_info_activity",
        {
            "equipment_id": equipment_id
        }
    )

    spare_parts = yield context.call_activity(
        "check_spare_parts_activity",
        {
            "equipment_id": equipment_id
        }
    )

    decision = yield context.call_activity(
        "make_workflow_decision",
        {
            "equipment_id": equipment_id,
            "equipment": equipment,
            "spare_parts": spare_parts,
            "original_payload": payload
        }
    )

    work_order = None

    if decision.get("decision") == "create_work_order":
        work_order = yield context.call_activity(
            "create_work_order_activity",
            {
                "request_id": payload.get(
                    "request_id",
                    context.instance_id
                ),
                "equipment_id": equipment_id,
                "priority": payload.get("priority", "critical"),
                "description": payload.get(
                    "description",
                    "Solicitud de mantenimiento desde workflow durable"
                ),
                "recommended_action": payload.get(
                    "recommended_action",
                    "Inspeccionar equipo y realizar acción correctiva."
                ),
                "requested_by": payload.get(
                    "requested_by",
                    "durable_workflow"
                )
            }
        )

    notification = yield context.call_activity(
        "send_notification_activity",
        {
            "channel": payload.get(
                "channel",
                "maintenance_supervisor"
            ),
            "body": f"Workflow durable completado para {equipment_id}."
        }
    )

    return {
        "status": "success",
        "workflow_name": "maintenance_workflow",
        "workflow_engine": "Azure Durable Functions",
        "equipment_id": equipment_id,
        "equipment": equipment,
        "spare_parts": spare_parts,
        "decision": decision,
        "work_order": work_order,
        "notification": notification,
        "serverless_tools_used": [
            "get_equipment_info",
            "create_work_order",
            "send_notification"
        ]
    }


@app.activity_trigger(input_name="payload")
def validate_workflow_input(payload: dict):
    equipment_id = payload.get("equipment_id")

    if not equipment_id:
        return {
            "status": "error",
            "message": "equipment_id es requerido"
        }

    return {
        "status": "success",
        "equipment_id": equipment_id
    }


@app.activity_trigger(input_name="payload")
def get_equipment_info_activity(payload: dict):
    response = requests.post(
        f"{AZURE_FUNCTIONS_URL}/get_equipment_info",
        json={
            "equipment_id": payload["equipment_id"]
        },
        timeout=10
    )

    return response.json()


@app.activity_trigger(input_name="payload")
def check_spare_parts_activity(payload: dict):
    response = requests.post(
        f"{TOOLS_API_URL}/check_spare_parts",
        json={
            "equipment_id": payload["equipment_id"]
        },
        timeout=10
    )

    return response.json()


@app.activity_trigger(input_name="payload")
def make_workflow_decision(payload: dict):
    equipment = payload.get("equipment", {})
    spare_parts = payload.get("spare_parts", {})

    criticality = equipment.get("criticality", "unknown")
    parts_available = spare_parts.get("available")

    if criticality == "high" and parts_available is True:
        return {
            "status": "success",
            "decision": "create_work_order",
            "reason": "El equipo es de alta criticidad y hay refacciones disponibles."
        }

    if criticality == "high":
        return {
            "status": "success",
            "decision": "create_work_order",
            "reason": "El equipo es de alta criticidad. Se requiere orden de trabajo aunque la disponibilidad de refacciones sea incierta."
        }

    return {
        "status": "success",
        "decision": "notify_only",
        "reason": "El equipo no es de alta criticidad."
    }


@app.activity_trigger(input_name="payload")
def create_work_order_activity(payload: dict):
    response = requests.post(
        f"{AZURE_FUNCTIONS_URL}/create_work_order",
        json=payload,
        timeout=10
    )

    return response.json()


@app.activity_trigger(input_name="payload")
def send_notification_activity(payload: dict):
    response = requests.post(
        f"{AZURE_FUNCTIONS_URL}/send_notification",
        json=payload,
        timeout=10
    )

    return response.json()
