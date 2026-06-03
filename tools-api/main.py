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




class FailurePatternRequest(BaseModel):
    equipment_id: str
    failure_type: str | None = None
    years: int = 2

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
        history_records = (
            db.query(MaintenanceHistory)
            .filter(MaintenanceHistory.equipment_id == request.equipment_id)
            .order_by(MaintenanceHistory.days_since_last_event.asc())
            .all()
        )

        if not history_records:
            return {
                "status": "error",
                "error_code": "HISTORY_NOT_FOUND",
                "message": "No maintenance history found for this equipment."
            }

        latest = history_records[0]

        return {
            "status": "success",
            "equipment_id": request.equipment_id,
            "count": len(history_records),
            "coverage_years": 5,
            "last_failure": latest.last_failure,
            "last_action": latest.last_action,
            "days_since_last_event": latest.days_since_last_event,
            "recurrence_risk": latest.recurrence_risk,
            "history": [
                {
                    "last_failure": record.last_failure,
                    "last_action": record.last_action,
                    "days_since_last_event": record.days_since_last_event,
                    "recurrence_risk": record.recurrence_risk
                }
                for record in history_records
            ]
        }

    finally:
        db.close()

@app.post("/check_spare_parts")
def check_spare_parts(request: EquipmentRequest):
    db = SessionLocal()

    try:
        spare_parts = (
            db.query(SparePart)
            .filter(SparePart.equipment_id == request.equipment_id)
            .order_by(SparePart.quantity.asc())
            .all()
        )

        if not spare_parts:
            return {
                "status": "error",
                "error_code": "SPARE_PART_NOT_FOUND",
                "message": "No spare parts found for this equipment."
            }

        low_stock_parts = [part for part in spare_parts if part.quantity <= 2]
        available_parts = [part for part in spare_parts if part.available and part.quantity > 0]

        return {
            "status": "success",
            "equipment_id": request.equipment_id,
            "available": len(available_parts) > 0,
            "total_parts": len(spare_parts),
            "available_parts": len(available_parts),
            "low_stock_parts": len(low_stock_parts),
            "inventory": [
                {
                    "part_type": part.part_type,
                    "available": part.available,
                    "quantity": part.quantity,
                    "warehouse": part.warehouse,
                    "stock_status": "low_stock" if part.quantity <= 2 else "ok"
                }
                for part in spare_parts
            ]
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
@app.post("/get_all_work_orders")
def get_all_work_orders(request: EquipmentRequest):
    db = SessionLocal()

    try:
        work_orders = (
            db.query(WorkOrder)
            .filter(WorkOrder.equipment_id == request.equipment_id)
            .order_by(WorkOrder.created_at.desc())
            .all()
        )

        return {
            "status": "success",
            "equipment_id": request.equipment_id,
            "count": len(work_orders),
            "work_orders": [
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


@app.get("/get_downtime_ranking")
def get_downtime_ranking():
    db = SessionLocal()

    try:
        equipment_list = db.query(Equipment).all()
        ranking = []

        downtime_by_priority = {
            "critical": 8,
            "high": 5,
            "medium": 3,
            "low": 1
        }

        for equipment in equipment_list:
            work_orders = db.query(WorkOrder).filter(
                WorkOrder.equipment_id == equipment.equipment_id
            ).all()

            estimated_downtime_hours = sum(
                downtime_by_priority.get(wo.priority, 2)
                for wo in work_orders
            )

            ranking.append({
                "equipment_id": equipment.equipment_id,
                "equipment_name": equipment.name,
                "area": equipment.area,
                "estimated_downtime_hours": estimated_downtime_hours,
                "total_work_orders": len(work_orders)
            })

        ranking = sorted(
            ranking,
            key=lambda x: x["estimated_downtime_hours"],
            reverse=True
        )

        return {
            "status": "success",
            "count": len(ranking),
            "downtime_ranking": ranking
        }

    finally:
        db.close()


@app.post("/calculate_oee")
def calculate_oee(request: EquipmentRequest):
    db = SessionLocal()

    try:
        work_orders = db.query(WorkOrder).filter(
            WorkOrder.equipment_id == request.equipment_id
        ).all()

        planned_minutes = 480

        downtime_by_priority = {
            "critical": 60,
            "high": 40,
            "medium": 25,
            "low": 10
        }

        downtime_minutes = sum(
            downtime_by_priority.get(wo.priority, 20)
            for wo in work_orders
            if wo.status in ["created", "in_progress"]
        )

        runtime_minutes = max(planned_minutes - downtime_minutes, 1)

        availability = runtime_minutes / planned_minutes

        performance = max(0.70, 1 - (len(work_orders) * 0.01))

        quality = max(0.85, 1 - (len([
            wo for wo in work_orders if wo.priority == "critical"
        ]) * 0.02))

        oee = availability * performance * quality

        return {
            "status": "success",
            "equipment_id": request.equipment_id,
            "planned_minutes": planned_minutes,
            "downtime_minutes": downtime_minutes,
            "runtime_minutes": runtime_minutes,
            "availability": round(availability * 100, 2),
            "performance": round(performance * 100, 2),
            "quality": round(quality * 100, 2),
            "oee": round(oee * 100, 2)
        }

    finally:
        db.close()


@app.get("/weekly_maintenance_summary")
def weekly_maintenance_summary():
    db = SessionLocal()

    try:
        from datetime import datetime, timedelta

        week_start = datetime.utcnow() - timedelta(days=7)
        work_orders = db.query(WorkOrder).filter(
            WorkOrder.created_at >= week_start
        ).all()

        total_work_orders = len(work_orders)

        open_work_orders = len([
            wo for wo in work_orders
            if wo.status in ["created", "in_progress"]
        ])

        completed_work_orders = len([
            wo for wo in work_orders
            if wo.status in ["completed", "closed"]
        ])

        critical_work_orders = len([
            wo for wo in work_orders
            if wo.priority == "critical"
            and wo.status in ["created", "in_progress"]
        ])

        affected_equipment = len(set([
            wo.equipment_id for wo in work_orders
        ]))

        return {
            "status": "success",
            "summary": "Weekly maintenance summary generated successfully.",
            "period_days": 7,
            "total_work_orders": total_work_orders,
            "completed_work_orders": completed_work_orders,
            "open_work_orders": open_work_orders,
            "critical_open_work_orders": critical_work_orders,
            "affected_equipment": affected_equipment
        }

    finally:
        db.close()
@app.get("/get_oee_ranking")
def get_oee_ranking():
    db = SessionLocal()

    try:
        equipment_list = db.query(Equipment).all()
        oee_results = []

        for equipment in equipment_list:
            work_orders = db.query(WorkOrder).filter(
                WorkOrder.equipment_id == equipment.equipment_id
            ).all()

            planned_minutes = 480

            downtime_by_priority = {
                "critical": 60,
                "high": 40,
                "medium": 25,
                "low": 10
            }

            downtime_minutes = sum(
                downtime_by_priority.get(wo.priority, 20)
                for wo in work_orders
                if wo.status in ["created", "in_progress"]
            )

            runtime_minutes = max(planned_minutes - downtime_minutes, 1)

            availability = runtime_minutes / planned_minutes
            performance = max(0.70, 1 - (len(work_orders) * 0.01))

            critical_count = len([
                wo for wo in work_orders
                if wo.priority == "critical"
            ])

            quality = max(0.85, 1 - (critical_count * 0.02))

            oee = availability * performance * quality

            oee_results.append({
                "equipment_id": equipment.equipment_id,
                "equipment_name": equipment.name,
                "area": equipment.area,
                "planned_minutes": planned_minutes,
                "downtime_minutes": downtime_minutes,
                "runtime_minutes": runtime_minutes,
                "availability": round(availability * 100, 2),
                "performance": round(performance * 100, 2),
                "quality": round(quality * 100, 2),
                "oee": round(oee * 100, 2)
            })

        oee_results = sorted(
            oee_results,
            key=lambda x: x["oee"]
        )

        return {
            "status": "success",
            "count": len(oee_results),
            "lowest_oee_equipment": oee_results[:5],
            "oee_ranking": oee_results
        }

    finally:
        db.close()
@app.post("/analyze_failure_pattern")
def analyze_failure_pattern(request: FailurePatternRequest):
    db = SessionLocal()

    try:
        from datetime import datetime, timedelta

        start_date = datetime.utcnow() - timedelta(days=365 * request.years)

        query = db.query(WorkOrder).filter(
            WorkOrder.equipment_id == request.equipment_id,
            WorkOrder.created_at >= start_date
        )

        if request.failure_type:
            query = query.filter(
                WorkOrder.description.ilike(f"%{request.failure_type}%")
            )

        work_orders = query.order_by(WorkOrder.created_at.desc()).all()

        if not work_orders:
            return {
                "status": "error",
                "error_code": "NO_PATTERN_DATA",
                "message": "No matching work orders found for this failure pattern."
            }

        def extract_failure_type(description: str):
            marker = " detected on "
            if description and marker in description:
                return description.split(marker)[0].strip()
            return description or "Unknown failure"

        failure_counts = {}
        action_counts = {}
        dates = []
        critical_count = 0
        open_count = 0

        for order in work_orders:
            failure = extract_failure_type(order.description)
            failure_counts[failure] = failure_counts.get(failure, 0) + 1

            action = order.recommended_action or "Review equipment condition"
            action_counts[action] = action_counts.get(action, 0) + 1

            if order.created_at:
                dates.append(order.created_at)

            if order.priority == "critical":
                critical_count += 1

            if order.status in ["created", "in_progress"]:
                open_count += 1

        sorted_failures = sorted(
            failure_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )
        sorted_actions = sorted(
            action_counts.items(),
            key=lambda item: item[1],
            reverse=True
        )

        primary_failure, primary_count = sorted_failures[0]
        most_common_action = sorted_actions[0][0] if sorted_actions else "Perform preventive inspection"

        mtbf_days = None
        if len(dates) >= 2:
            dates_sorted = sorted(dates)
            intervals = [
                (dates_sorted[index] - dates_sorted[index - 1]).days
                for index in range(1, len(dates_sorted))
            ]
            mtbf_days = round(sum(intervals) / len(intervals), 1)

        if primary_count >= 10 or critical_count >= 3:
            recurrence_level = "high"
        elif primary_count >= 4:
            recurrence_level = "medium"
        else:
            recurrence_level = "low"

        confidence = min(0.95, round(0.45 + (primary_count * 0.04) + (critical_count * 0.03), 2))

        recommendation = (
            f"{primary_failure} has repeated {primary_count} times in the last {request.years} years. "
            f"Recommended action: {most_common_action}. "
            "Validate spare parts, inspect recurring components, and schedule preventive work before production impact increases."
        )

        return {
            "status": "success",
            "equipment_id": request.equipment_id,
            "failure_type": primary_failure,
            "requested_failure_type": request.failure_type,
            "analysis_window_years": request.years,
            "matching_work_orders": len(work_orders),
            "occurrences": primary_count,
            "critical_occurrences": critical_count,
            "open_work_orders": open_count,
            "average_days_between_failures": mtbf_days,
            "recurrence_level": recurrence_level,
            "most_common_action": most_common_action,
            "confidence": confidence,
            "recommendation": recommendation,
            "failure_distribution": [
                {"failure_type": failure, "count": count}
                for failure, count in sorted_failures[:10]
            ],
            "action_distribution": [
                {"recommended_action": action, "count": count}
                for action, count in sorted_actions[:10]
            ],
            "recent_matching_orders": [
                {
                    "work_order_id": order.work_order_id,
                    "equipment_id": order.equipment_id,
                    "failure_type": extract_failure_type(order.description),
                    "priority": order.priority,
                    "status_work_order": order.status,
                    "recommended_action": order.recommended_action,
                    "created_at": order.created_at.isoformat() if order.created_at else None
                }
                for order in work_orders[:10]
            ]
        }

    finally:
        db.close()