from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4

from db import Base, engine, SessionLocal
from models import Equipment, MaintenanceHistory, SparePart, WorkOrder

app = FastAPI(title="Maintenance Tools API")

Base.metadata.create_all(bind=engine)


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
    return {
        "status": "ok",
        "service": "tools-api",
        "database": "postgresql"
    }


@app.post("/get_equipment_info")
def get_equipment_info(request: EquipmentRequest):
    db = SessionLocal()

    try:
        equipment = db.query(Equipment).filter(
            Equipment.equipment_id == request.equipment_id
        ).first()

        if not equipment:
            return {
                "status": "error",
                "error_code": "EQUIPMENT_NOT_FOUND",
                "message": "The equipment_id does not exist."
            }

        return {
            "status": "success",
            "equipment_id": equipment.equipment_id,
            "name": equipment.name,
            "area": equipment.area,
            "criticality": equipment.criticality,
            "status_equipment": equipment.status_equipment
        }

    finally:
        db.close()


@app.post("/get_maintenance_history")
def get_maintenance_history(request: EquipmentRequest):
    db = SessionLocal()

    try:
        history = db.query(MaintenanceHistory).filter(
            MaintenanceHistory.equipment_id == request.equipment_id
        ).first()

        if not history:
            return {
                "status": "error",
                "error_code": "HISTORY_NOT_FOUND",
                "message": "No maintenance history found for this equipment."
            }

        return {
            "status": "success",
            "equipment_id": history.equipment_id,
            "last_failure": history.last_failure,
            "last_action": history.last_action,
            "days_since_last_event": history.days_since_last_event,
            "recurrence_risk": history.recurrence_risk
        }

    finally:
        db.close()


@app.post("/check_spare_parts")
def check_spare_parts(request: EquipmentRequest):
    db = SessionLocal()

    try:
        spare_part = db.query(SparePart).filter(
            SparePart.equipment_id == request.equipment_id
        ).first()

        if not spare_part:
            return {
                "status": "error",
                "error_code": "SPARE_PART_NOT_FOUND",
                "message": "No spare parts found for this equipment."
            }

        return {
            "status": "success",
            "equipment_id": spare_part.equipment_id,
            "part_type": spare_part.part_type,
            "available": spare_part.available,
            "quantity": spare_part.quantity,
            "warehouse": spare_part.warehouse
        }

    finally:
        db.close()


@app.post("/create_work_order")
def create_work_order(request: WorkOrderRequest):
    db = SessionLocal()

    try:
        work_order_id = "OT-" + str(uuid4())[:8]

        work_order = WorkOrder(
            work_order_id=work_order_id,
            request_id=request.request_id,
            equipment_id=request.equipment_id,
            priority=request.priority,
            description=request.description,
            recommended_action=request.recommended_action,
            requested_by=request.requested_by,
            assigned_team="Mechanical Maintenance",
            status="created"
        )

        db.add(work_order)
        db.commit()
        db.refresh(work_order)

        return {
            "status": "success",
            "work_order_id": work_order.work_order_id,
            "equipment_id": work_order.equipment_id,
            "priority": work_order.priority,
            "assigned_team": work_order.assigned_team,
            "message": "Work order created successfully and stored in PostgreSQL."
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error_code": "WORK_ORDER_CREATION_FAILED",
            "message": str(e)
        }

    finally:
        db.close()


@app.post("/send_notification")
def send_notification():
    return {
        "status": "success",
        "notification_id": "NTF-2026-0001",
        "message": "Notification sent successfully."
    }


@app.get("/list_work_orders")
def list_work_orders():
    db = SessionLocal()

    try:
        work_orders = db.query(WorkOrder).order_by(
            WorkOrder.created_at.desc()
        ).all()

        return {
            "status": "success",
            "count": len(work_orders),
            "work_orders": [
                {
                    "work_order_id": wo.work_order_id,
                    "request_id": wo.request_id,
                    "equipment_id": wo.equipment_id,
                    "priority": wo.priority,
                    "description": wo.description,
                    "recommended_action": wo.recommended_action,
                    "requested_by": wo.requested_by,
                    "assigned_team": wo.assigned_team,
                    "status_work_order": wo.status,
                    "created_at": wo.created_at.isoformat() if wo.created_at else None
                }
                for wo in work_orders
            ]
        }

    finally:
        db.close()


@app.post("/get_equipment_work_orders")
def get_equipment_work_orders(request: EquipmentRequest):
    db = SessionLocal()

    try:
        work_orders = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.equipment_id == request.equipment_id
            )
            .order_by(
                WorkOrder.created_at.desc()
            )
            .limit(10)
            .all()
        )

        return {
            "status": "success",
            "equipment_id": request.equipment_id,
            "count": len(work_orders),
            "work_orders": [
                {
                    "work_order_id": wo.work_order_id,
                    "priority": wo.priority,
                    "description": wo.description,
                    "recommended_action": wo.recommended_action,
                    "status_work_order": wo.status,
                    "created_at": wo.created_at.isoformat() if wo.created_at else None
                }
                for wo in work_orders
            ]
        }

    finally:
        db.close()


@app.get("/dashboard/kpis")
def dashboard_kpis():
    db = SessionLocal()

    try:
        total_equipment = db.query(Equipment).count()
        total_work_orders = db.query(WorkOrder).count()

        open_work_orders = db.query(WorkOrder).filter(
            WorkOrder.status.in_(["created", "in_progress"])
        ).count()

        closed_work_orders = db.query(WorkOrder).filter(
            WorkOrder.status.in_(["completed", "closed"])
        ).count()

        critical_work_orders = db.query(WorkOrder).filter(
            WorkOrder.priority == "critical"
        ).count()

        high_critical_equipment = db.query(Equipment).filter(
            Equipment.criticality == "high"
        ).count()

        return {
            "status": "success",
            "kpis": {
                "total_equipment": total_equipment,
                "total_work_orders": total_work_orders,
                "open_work_orders": open_work_orders,
                "closed_work_orders": closed_work_orders,
                "critical_work_orders": critical_work_orders,
                "high_critical_equipment": high_critical_equipment
            }
        }

    finally:
        db.close()


@app.get("/dashboard/work-orders-by-priority")
def work_orders_by_priority():
    db = SessionLocal()

    try:
        priorities = ["low", "medium", "high", "critical"]

        return {
            "status": "success",
            "data": [
                {
                    "priority": priority,
                    "count": db.query(WorkOrder).filter(
                        WorkOrder.priority == priority
                    ).count()
                }
                for priority in priorities
            ]
        }

    finally:
        db.close()


@app.get("/dashboard/work-orders-by-equipment")
def work_orders_by_equipment():
    db = SessionLocal()

    try:
        equipment_list = db.query(Equipment).all()

        return {
            "status": "success",
            "data": [
                {
                    "equipment_id": equipment.equipment_id,
                    "equipment_name": equipment.name,
                    "area": equipment.area,
                    "criticality": equipment.criticality,
                    "work_order_count": db.query(WorkOrder).filter(
                        WorkOrder.equipment_id == equipment.equipment_id
                    ).count()
                }
                for equipment in equipment_list
            ]
        }

    finally:
        db.close()


@app.get("/dashboard/work-orders-by-area")
def work_orders_by_area():
    db = SessionLocal()

    try:
        equipment_list = db.query(Equipment).all()
        area_counts = {}

        for equipment in equipment_list:
            count = db.query(WorkOrder).filter(
                WorkOrder.equipment_id == equipment.equipment_id
            ).count()

            area_counts[equipment.area] = area_counts.get(equipment.area, 0) + count

        return {
            "status": "success",
            "data": [
                {
                    "area": area,
                    "work_order_count": count
                }
                for area, count in area_counts.items()
            ]
        }

    finally:
        db.close()


@app.get("/dashboard/top-failure-types")
def top_failure_types():
    db = SessionLocal()

    try:
        work_orders = db.query(WorkOrder).all()
        failure_counts = {}

        for wo in work_orders:
            failure_type = wo.description.split(" detected")[0]
            failure_counts[failure_type] = failure_counts.get(failure_type, 0) + 1

        sorted_failures = sorted(
            failure_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )

        return {
            "status": "success",
            "data": [
                {
                    "failure_type": failure,
                    "count": count
                }
                for failure, count in sorted_failures[:10]
            ]
        }

    finally:
        db.close()

@app.post("/predict_failure_risk")
def predict_failure_risk(request: EquipmentRequest):
    db = SessionLocal()

    try:
        equipment = db.query(Equipment).filter(
            Equipment.equipment_id == request.equipment_id
        ).first()

        if not equipment:
            return {
                "status": "error",
                "message": "Equipment not found."
            }

        work_orders = db.query(WorkOrder).filter(
            WorkOrder.equipment_id == request.equipment_id
        ).all()

        total_orders = len(work_orders)

        critical_orders = len([
            wo for wo in work_orders
            if wo.priority == "critical"
        ])

        open_orders = len([
            wo for wo in work_orders
            if wo.status in ["created", "in_progress"]
        ])

        criticality_weight = {
            "low": 10,
            "medium": 20,
            "high": 35
        }

        risk_score = (
            criticality_weight.get(
                equipment.criticality,
                20
            )
            + min(total_orders * 3, 30)
            + min(critical_orders * 5, 25)
            + min(open_orders * 3, 10)
        )

        risk_score = min(risk_score, 100)

        if risk_score >= 80:
            risk_level = "critical"
        elif risk_score >= 60:
            risk_level = "high"
        elif risk_score >= 35:
            risk_level = "medium"
        else:
            risk_level = "low"

        return {
            "status": "success",
            "equipment_id": equipment.equipment_id,
            "equipment_name": equipment.name,
            "criticality": equipment.criticality,
            "risk_score": risk_score,
            "health_score": 100 - risk_score,
            "risk_level": risk_level,
            "total_work_orders": total_orders,
            "critical_work_orders": critical_orders,
            "open_work_orders": open_orders
        }

    finally:
        db.close()

@app.post("/get_open_work_orders")
def get_open_work_orders(request: EquipmentRequest):
    db = SessionLocal()

    try:
        work_orders = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.equipment_id == request.equipment_id,
                WorkOrder.status.in_(["created", "in_progress"])
            )
            .order_by(
                WorkOrder.created_at.desc()
            )
            .all()
        )

        return {
            "status": "success",
            "equipment_id": request.equipment_id,
            "count": len(work_orders),
            "open_work_orders": [
                {
                    "work_order_id": wo.work_order_id,
                    "priority": wo.priority,
                    "status_work_order": wo.status,
                    "description": wo.description,
                    "recommended_action": wo.recommended_action,
                    "created_at": wo.created_at.isoformat() if wo.created_at else None
                }
                for wo in work_orders
            ]
        }

    finally:
        db.close()

@app.get("/get_highest_risk_equipment")
def get_highest_risk_equipment():
    db = SessionLocal()

    try:
        equipment_list = db.query(Equipment).all()
        risk_results = []

        for equipment in equipment_list:
            work_orders = db.query(WorkOrder).filter(
                WorkOrder.equipment_id == equipment.equipment_id
            ).all()

            total_orders = len(work_orders)

            critical_orders = len([
                wo for wo in work_orders
                if wo.priority == "critical"
            ])

            open_orders = len([
                wo for wo in work_orders
                if wo.status in ["created", "in_progress"]
            ])

            criticality_weight = {
                "low": 10,
                "medium": 20,
                "high": 35
            }

            risk_score = (
                criticality_weight.get(equipment.criticality, 20)
                + min(total_orders * 3, 30)
                + min(critical_orders * 5, 25)
                + min(open_orders * 3, 10)
            )

            risk_score = min(risk_score, 100)

            if risk_score >= 80:
                risk_level = "critical"
            elif risk_score >= 60:
                risk_level = "high"
            elif risk_score >= 35:
                risk_level = "medium"
            else:
                risk_level = "low"

            risk_results.append({
                "equipment_id": equipment.equipment_id,
                "equipment_name": equipment.name,
                "area": equipment.area,
                "criticality": equipment.criticality,
                "risk_score": risk_score,
                "health_score": 100 - risk_score,
                "risk_level": risk_level,
                "total_work_orders": total_orders,
                "critical_work_orders": critical_orders,
                "open_work_orders": open_orders
            })

        risk_results = sorted(
            risk_results,
            key=lambda x: x["risk_score"],
            reverse=True
        )

        return {
            "status": "success",
            "count": len(risk_results),
            "highest_risk_equipment": risk_results[:5]
        }

    finally:
        db.close()
@app.get("/get_critical_work_orders")
def get_critical_work_orders():
    db = SessionLocal()

    try:
        work_orders = (
            db.query(WorkOrder)
            .filter(
                WorkOrder.priority == "critical",
                WorkOrder.status.in_(["created", "in_progress"])
            )
            .order_by(WorkOrder.created_at.desc())
            .all()
        )

        return {
            "status": "success",
            "count": len(work_orders),
            "critical_work_orders": [
                {
                    "work_order_id": wo.work_order_id,
                    "equipment_id": wo.equipment_id,
                    "priority": wo.priority,
                    "status_work_order": wo.status,
                    "description": wo.description,
                    "recommended_action": wo.recommended_action,
                    "created_at": wo.created_at.isoformat() if wo.created_at else None
                }
                for wo in work_orders
            ]
        }

    finally:
        db.close()