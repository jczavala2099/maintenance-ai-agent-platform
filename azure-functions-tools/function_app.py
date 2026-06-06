import azure.functions as func
import requests
import json
import os

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)

TOOLS_API_URL = os.getenv("TOOLS_API_URL", "http://localhost:8001")


def json_response(payload: dict, status_code: int = 200):
    return func.HttpResponse(
        json.dumps(payload),
        status_code=status_code,
        mimetype="application/json"
    )


@app.route(route="get_equipment_info", methods=["POST"])
def get_equipment_info(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()
        equipment_id = body.get("equipment_id")

        if not equipment_id:
            return json_response(
                {
                    "status": "error",
                    "tool": "get_equipment_info",
                    "message": "equipment_id es requerido"
                },
                400
            )

        response = requests.post(
            f"{TOOLS_API_URL}/get_equipment_info",
            json={"equipment_id": equipment_id},
            timeout=10
        )

        return json_response(response.json(), response.status_code)

    except Exception as e:
        return json_response(
            {
                "status": "error",
                "tool": "get_equipment_info",
                "message": str(e)
            },
            500
        )


@app.route(route="create_work_order", methods=["POST"])
def create_work_order(req: func.HttpRequest) -> func.HttpResponse:
    try:
        body = req.get_json()

        required_fields = [
            "request_id",
            "equipment_id",
            "priority",
            "description",
            "recommended_action",
            "requested_by"
        ]

        missing_fields = [
            field for field in required_fields
            if field not in body or body.get(field) in [None, ""]
        ]

        if missing_fields:
            return json_response(
                {
                    "status": "error",
                    "tool": "create_work_order",
                    "message": "Faltan campos requeridos",
                    "missing_fields": missing_fields
                },
                400
            )

        response = requests.post(
            f"{TOOLS_API_URL}/create_work_order",
            json=body,
            timeout=10
        )

        return json_response(response.json(), response.status_code)

    except Exception as e:
        return json_response(
            {
                "status": "error",
                "tool": "create_work_order",
                "message": str(e)
            },
            500
        )


@app.route(route="send_notification", methods=["POST"])
def send_notification(req: func.HttpRequest) -> func.HttpResponse:
    try:
        try:
            body = req.get_json()
        except Exception:
            body = {}

        channel = body.get("channel", "maintenance_supervisor")
        message = body.get("body", "Notificación de mantenimiento activada.")

        response = requests.post(
            f"{TOOLS_API_URL}/send_notification",
            timeout=10
        )

        return json_response(
            {
                "status": "success",
                "tool": "send_notification",
                "channel": channel,
                "body": message,
                "notification_result": response.json()
            },
            200
        )

    except Exception as e:
        return json_response(
            {
                "status": "error",
                "tool": "send_notification",
                "message": str(e)
            },
            500
        )
