import azure.functions as func
import json

app = func.FunctionApp(http_auth_level=func.AuthLevel.ANONYMOUS)


@app.route(route="get_equipment_info", methods=["POST"])
def get_equipment_info(req: func.HttpRequest) -> func.HttpResponse:
    try:
        data = req.get_json()
        equipment_id = data.get("equipment_id")

        if not equipment_id:
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "error_code": "INVALID_INPUT",
                    "message": "equipment_id is required."
                }),
                status_code=400,
                mimetype="application/json"
            )

        equipment_data = {
            "CNC-01": {
                "name": "CNC Milling Machine 01",
                "area": "Machining",
                "criticality": "high",
                "status_equipment": "stopped"
            }
        }

        if equipment_id not in equipment_data:
            return func.HttpResponse(
                json.dumps({
                    "status": "error",
                    "error_code": "EQUIPMENT_NOT_FOUND",
                    "message": "The equipment_id does not exist."
                }),
                status_code=404,
                mimetype="application/json"
            )

        response = {
            "status": "success",
            "equipment_id": equipment_id,
            **equipment_data[equipment_id]
        }

        return func.HttpResponse(
            json.dumps(response),
            status_code=200,
            mimetype="application/json"
        )

    except Exception as e:
        return func.HttpResponse(
            json.dumps({
                "status": "error",
                "error_code": "INTERNAL_ERROR",
                "message": str(e)
            }),
            status_code=500,
            mimetype="application/json"
        )