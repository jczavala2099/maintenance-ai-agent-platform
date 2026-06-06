from fastapi import FastAPI
from pydantic import BaseModel
from uuid import uuid4
from datetime import datetime

from db import Base, engine, SessionLocal
from models import Equipment, MaintenanceHistory, SparePart, WorkOrder, AuditLog

app = FastAPI(title="API de Herramientas de Mantenimiento")

Base.metadata.create_all(bind=engine)


def create_audit_log(db, request_id: str, event_type: str, detail: str):
    audit_log = AuditLog(
        request_id=request_id,
        event_type=event_type,
        detail=detail
    )
    db.add(audit_log)


def equipment_exists(db, equipment_id: str):
    return db.query(Equipment).filter(
        Equipment.equipment_id == equipment_id
    ).first()



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
        "Replace seals and inspect fittings": "Reemplazar sellos e inspeccionar conexiones",
        "Replaced hydraulic seal and cleaned oil residue": "Se reemplazó sello hidráulico y se limpió residuo de aceite",
        "Review equipment condition": "Revisar condición del equipo",
        "Perform preventive inspection": "Realizar inspección preventiva",
        "Inspect bearings, mounting base and alignment": "Inspeccionar rodamientos, base de montaje y alineación",
        "Inspect hydraulic pump, seals and pressure regulator": "Inspeccionar bomba hidráulica, sellos y regulador de presión",
        "Inspect press and validate oil leakage history": "Inspeccionar prensa y validar historial de fuga de aceite",
        "Demo workflow request": "Solicitud de workflow de demo",
        "Validate spare parts, inspect recurring components, and schedule preventive work before production impact increases.": "Validar refacciones, inspeccionar componentes recurrentes y programar trabajo preventivo antes de que aumente el impacto en producción.",
        "has repeated": "se ha repetido",
        "times in": "veces en",
        "the last": "los últimos",
        "years": "años"
    }

    translated = value
    for source, target in translations.items():
        translated = translated.replace(source, target)
        translated = translated.replace(source.lower(), target.lower())

    return translated

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


class EquipmentUpsertRequest(BaseModel):
    equipment_id: str
    name: str
    area: str
    criticality: str
    status_equipment: str
    submitted_by: str | None = None


class EquipmentStatusUpdateRequest(BaseModel):
    equipment_id: str
    status_equipment: str
    submitted_by: str | None = None


class SparePartUpsertRequest(BaseModel):
    equipment_id: str
    part_type: str
    available: bool
    quantity: int
    warehouse: str
    submitted_by: str | None = None


class InventoryAdjustmentRequest(BaseModel):
    equipment_id: str
    part_type: str
    quantity_delta: int
    warehouse: str | None = None
    submitted_by: str | None = None


class WorkOrderUpdateRequest(BaseModel):
    work_order_id: str
    priority: str | None = None
    description: str | None = None
    recommended_action: str | None = None
    assigned_team: str | None = None
    status_work_order: str | None = None
    submitted_by: str | None = None


class MaintenanceHistoryCreateRequest(BaseModel):
    equipment_id: str
    last_failure: str
    last_action: str
    days_since_last_event: int = 0
    recurrence_risk: str = "medium"
    submitted_by: str | None = None


class TechnicianMaintenanceReportRequest(BaseModel):
    equipment_id: str
    reported_by: str
    failure_type: str
    action_taken: str
    status_equipment: str | None = None
    work_order_id: str | None = None
    work_order_status: str = "completed"
    priority: str = "medium"
    spare_part_used: str | None = None
    spare_part_quantity_used: int = 0
    recurrence_risk: str = "medium"


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
                "message": "El equipment_id no existe."
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
                "message": "No se encontró historial de mantenimiento para este equipo."
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
                "message": "No se encontraron refacciones para este equipo."
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
            assigned_team="Mantenimiento Mecánico",
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
            "message": "Orden de trabajo creada correctamente y guardada en PostgreSQL."
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



@app.post("/upsert_equipment")
def upsert_equipment(request: EquipmentUpsertRequest):
    db = SessionLocal()

    try:
        equipment = db.query(Equipment).filter(
            Equipment.equipment_id == request.equipment_id
        ).first()

        action = "updated"
        if not equipment:
            equipment = Equipment(
                equipment_id=request.equipment_id,
                name=request.name,
                area=request.area,
                criticality=request.criticality,
                status_equipment=request.status_equipment
            )
            db.add(equipment)
            action = "created"
        else:
            equipment.name = request.name
            equipment.area = request.area
            equipment.criticality = request.criticality
            equipment.status_equipment = request.status_equipment

        create_audit_log(
            db,
            request_id=f"EQUIPMENT-{request.equipment_id}",
            event_type="equipment_upsert",
            detail=f"Equipo {request.equipment_id} {action} por {request.submitted_by or 'system'}."
        )

        db.commit()
        db.refresh(equipment)

        return {
            "status": "success",
            "operation": action,
            "equipment": {
                "equipment_id": equipment.equipment_id,
                "name": equipment.name,
                "area": equipment.area,
                "criticality": equipment.criticality,
                "status_equipment": equipment.status_equipment
            }
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error_code": "EQUIPMENT_UPSERT_FAILED",
            "message": str(e)
        }

    finally:
        db.close()


@app.post("/update_equipment_status")
def update_equipment_status(request: EquipmentStatusUpdateRequest):
    db = SessionLocal()

    try:
        equipment = equipment_exists(db, request.equipment_id)

        if not equipment:
            return {
                "status": "error",
                "error_code": "EQUIPMENT_NOT_FOUND",
                "message": "El equipment_id no existe."
            }

        previous_status = equipment.status_equipment
        equipment.status_equipment = request.status_equipment

        create_audit_log(
            db,
            request_id=f"EQUIPMENT-{request.equipment_id}",
            event_type="equipment_status_update",
            detail=(
                f"Estado del equipo {request.equipment_id} cambiado de "
                f"{previous_status} to {request.status_equipment} by {request.submitted_by or 'system'}."
            )
        )

        db.commit()

        return {
            "status": "success",
            "equipment_id": equipment.equipment_id,
            "previous_status": previous_status,
            "status_equipment": equipment.status_equipment
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error_code": "EQUIPMENT_STATUS_UPDATE_FAILED",
            "message": str(e)
        }

    finally:
        db.close()


@app.post("/upsert_spare_part")
def upsert_spare_part(request: SparePartUpsertRequest):
    db = SessionLocal()

    try:
        equipment = equipment_exists(db, request.equipment_id)
        if not equipment:
            return {
                "status": "error",
                "error_code": "EQUIPMENT_NOT_FOUND",
                "message": "El equipment_id no existe."
            }

        spare_part = db.query(SparePart).filter(
            SparePart.equipment_id == request.equipment_id,
            SparePart.part_type == request.part_type
        ).first()

        action = "updated"
        if not spare_part:
            spare_part = SparePart(
                equipment_id=request.equipment_id,
                part_type=request.part_type,
                available=request.available,
                quantity=request.quantity,
                warehouse=request.warehouse
            )
            db.add(spare_part)
            action = "created"
        else:
            spare_part.available = request.available
            spare_part.quantity = request.quantity
            spare_part.warehouse = request.warehouse

        create_audit_log(
            db,
            request_id=f"SPARE-{request.equipment_id}",
            event_type="spare_part_upsert",
            detail=(
                f"Refacción {request.part_type} para {request.equipment_id} {action} "
                f"with quantity {request.quantity} by {request.submitted_by or 'system'}."
            )
        )

        db.commit()
        db.refresh(spare_part)

        return {
            "status": "success",
            "operation": action,
            "spare_part": {
                "equipment_id": spare_part.equipment_id,
                "part_type": spare_part.part_type,
                "available": spare_part.available,
                "quantity": spare_part.quantity,
                "warehouse": spare_part.warehouse,
                "stock_status": "low_stock" if spare_part.quantity <= 2 else "ok"
            }
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error_code": "SPARE_PART_UPSERT_FAILED",
            "message": str(e)
        }

    finally:
        db.close()


@app.post("/adjust_spare_part_inventory")
def adjust_spare_part_inventory(request: InventoryAdjustmentRequest):
    db = SessionLocal()

    try:
        spare_part = db.query(SparePart).filter(
            SparePart.equipment_id == request.equipment_id,
            SparePart.part_type == request.part_type
        ).first()

        if not spare_part:
            return {
                "status": "error",
                "error_code": "SPARE_PART_NOT_FOUND",
                "message": "La refacción no existe para este equipo."
            }

        previous_quantity = spare_part.quantity
        new_quantity = previous_quantity + request.quantity_delta

        if new_quantity < 0:
            return {
                "status": "error",
                "error_code": "NEGATIVE_INVENTORY_NOT_ALLOWED",
                "message": "El ajuste de inventario dejaría la cantidad en negativo."
            }

        spare_part.quantity = new_quantity
        spare_part.available = new_quantity > 0
        if request.warehouse:
            spare_part.warehouse = request.warehouse

        create_audit_log(
            db,
            request_id=f"SPARE-{request.equipment_id}",
            event_type="spare_part_inventory_adjustment",
            detail=(
                f"Refacción {request.part_type} para {request.equipment_id} cambió "
                f"from {previous_quantity} to {new_quantity} by {request.submitted_by or 'system'}."
            )
        )

        db.commit()

        return {
            "status": "success",
            "equipment_id": spare_part.equipment_id,
            "part_type": spare_part.part_type,
            "previous_quantity": previous_quantity,
            "quantity_delta": request.quantity_delta,
            "quantity": spare_part.quantity,
            "available": spare_part.available,
            "warehouse": spare_part.warehouse,
            "stock_status": "low_stock" if spare_part.quantity <= 2 else "ok"
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error_code": "INVENTORY_ADJUSTMENT_FAILED",
            "message": str(e)
        }

    finally:
        db.close()


@app.post("/update_work_order")
def update_work_order(request: WorkOrderUpdateRequest):
    db = SessionLocal()

    try:
        work_order = db.query(WorkOrder).filter(
            WorkOrder.work_order_id == request.work_order_id
        ).first()

        if not work_order:
            return {
                "status": "error",
                "error_code": "WORK_ORDER_NOT_FOUND",
                "message": "El work_order_id no existe."
            }

        changes = {}

        if request.priority is not None:
            changes["priority"] = [work_order.priority, request.priority]
            work_order.priority = request.priority
        if request.description is not None:
            changes["description"] = [work_order.description, request.description]
            work_order.description = request.description
        if request.recommended_action is not None:
            changes["recommended_action"] = [work_order.recommended_action, request.recommended_action]
            work_order.recommended_action = request.recommended_action
        if request.assigned_team is not None:
            changes["assigned_team"] = [work_order.assigned_team, request.assigned_team]
            work_order.assigned_team = request.assigned_team
        if request.status_work_order is not None:
            changes["status"] = [work_order.status, request.status_work_order]
            work_order.status = request.status_work_order

        create_audit_log(
            db,
            request_id=work_order.request_id,
            event_type="work_order_update",
            detail=(
                f"Work order {request.work_order_id} updated by {request.submitted_by or 'system'}. "
                f"Changes: {changes}"
            )
        )

        db.commit()
        db.refresh(work_order)

        return {
            "status": "success",
            "work_order": {
                "work_order_id": work_order.work_order_id,
                "equipment_id": work_order.equipment_id,
                "priority": work_order.priority,
                "description": work_order.description,
                "recommended_action": work_order.recommended_action,
                "assigned_team": work_order.assigned_team,
                "status_work_order": work_order.status,
                "created_at": work_order.created_at.isoformat() if work_order.created_at else None
            },
            "changes": changes
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error_code": "WORK_ORDER_UPDATE_FAILED",
            "message": str(e)
        }

    finally:
        db.close()


@app.post("/record_maintenance_history")
def record_maintenance_history(request: MaintenanceHistoryCreateRequest):
    db = SessionLocal()

    try:
        equipment = equipment_exists(db, request.equipment_id)
        if not equipment:
            return {
                "status": "error",
                "error_code": "EQUIPMENT_NOT_FOUND",
                "message": "El equipment_id no existe."
            }

        history = MaintenanceHistory(
            equipment_id=request.equipment_id,
            last_failure=request.last_failure,
            last_action=request.last_action,
            days_since_last_event=request.days_since_last_event,
            recurrence_risk=request.recurrence_risk
        )
        db.add(history)

        create_audit_log(
            db,
            request_id=f"HISTORY-{request.equipment_id}",
            event_type="maintenance_history_recorded",
            detail=(
                f"Historial de mantenimiento registrado para {request.equipment_id} por "
                f"{request.submitted_by or 'system'}: {request.last_failure}."
            )
        )

        db.commit()
        db.refresh(history)

        return {
            "status": "success",
            "history": {
                "id": history.id,
                "equipment_id": history.equipment_id,
                "last_failure": history.last_failure,
                "last_action": history.last_action,
                "days_since_last_event": history.days_since_last_event,
                "recurrence_risk": history.recurrence_risk
            }
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error_code": "MAINTENANCE_HISTORY_CREATE_FAILED",
            "message": str(e)
        }

    finally:
        db.close()


@app.post("/submit_technician_report")
def submit_technician_report(request: TechnicianMaintenanceReportRequest):
    db = SessionLocal()

    try:
        equipment = equipment_exists(db, request.equipment_id)
        if not equipment:
            return {
                "status": "error",
                "error_code": "EQUIPMENT_NOT_FOUND",
                "message": "El equipment_id no existe."
            }

        work_order = None
        work_order_action = "none"

        if request.work_order_id:
            work_order = db.query(WorkOrder).filter(
                WorkOrder.work_order_id == request.work_order_id
            ).first()

            if not work_order:
                return {
                    "status": "error",
                    "error_code": "WORK_ORDER_NOT_FOUND",
                    "message": "El work_order_id no existe."
                }

            work_order.status = request.work_order_status
            work_order.recommended_action = request.action_taken
            work_order_action = "updated"
        else:
            work_order = WorkOrder(
                work_order_id="OT-" + str(uuid4())[:8],
                request_id="TECH-" + str(uuid4())[:8],
                equipment_id=request.equipment_id,
                priority=request.priority,
                description=f"{request.failure_type} detected on {request.equipment_id}",
                recommended_action=request.action_taken,
                requested_by=request.reported_by,
                assigned_team="Mantenimiento Mecánico",
                status=request.work_order_status,
                created_at=datetime.utcnow()
            )
            db.add(work_order)
            work_order_action = "created"

        history = MaintenanceHistory(
            equipment_id=request.equipment_id,
            last_failure=request.failure_type,
            last_action=request.action_taken,
            days_since_last_event=0,
            recurrence_risk=request.recurrence_risk
        )
        db.add(history)

        inventory_result = None
        if request.spare_part_used and request.spare_part_quantity_used > 0:
            spare_part = db.query(SparePart).filter(
                SparePart.equipment_id == request.equipment_id,
                SparePart.part_type == request.spare_part_used
            ).first()

            if spare_part:
                previous_quantity = spare_part.quantity
                spare_part.quantity = max(0, spare_part.quantity - request.spare_part_quantity_used)
                spare_part.available = spare_part.quantity > 0
                inventory_result = {
                    "part_type": spare_part.part_type,
                    "previous_quantity": previous_quantity,
                    "quantity_used": request.spare_part_quantity_used,
                    "quantity": spare_part.quantity,
                    "available": spare_part.available
                }
            else:
                inventory_result = {
                    "status": "warning",
                    "message": "La refacción fue reportada, pero no se encontró en inventario.",
                    "part_type": request.spare_part_used
                }

        previous_equipment_status = equipment.status_equipment
        if request.status_equipment:
            equipment.status_equipment = request.status_equipment

        create_audit_log(
            db,
            request_id=work_order.request_id,
            event_type="technician_report_submitted",
            detail=(
                f"Reporte técnico enviado por {request.reported_by} para {request.equipment_id}. "
                f"Falla: {request.failure_type}. Orden de trabajo {work_order_action}."
            )
        )

        db.commit()
        db.refresh(work_order)
        db.refresh(history)

        return {
            "status": "success",
            "message": "Reporte de mantenimiento del técnico guardado correctamente.",
            "equipment_id": request.equipment_id,
            "equipment_status": {
                "previous_status": previous_equipment_status,
                "current_status": equipment.status_equipment
            },
            "work_order_action": work_order_action,
            "work_order": {
                "work_order_id": work_order.work_order_id,
                "status_work_order": work_order.status,
                "priority": work_order.priority,
                "recommended_action": work_order.recommended_action
            },
            "maintenance_history": {
                "id": history.id,
                "last_failure": history.last_failure,
                "last_action": history.last_action,
                "recurrence_risk": history.recurrence_risk
            },
            "inventory_update": inventory_result
        }

    except Exception as e:
        db.rollback()
        return {
            "status": "error",
            "error_code": "TECHNICIAN_REPORT_FAILED",
            "message": str(e)
        }

    finally:
        db.close()
@app.post("/send_notification")
def send_notification():
    return {
        "status": "success",
        "notification_id": "NTF-2026-0001",
        "message": "Notificación enviada correctamente."
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
                    "failure_type": translate_maintenance_text(failure),
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
                "message": "Equipo no encontrado."
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
            "summary": "Resumen semanal de mantenimiento generado correctamente.",
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
                "message": "No se encontraron órdenes de trabajo coincidentes para este patrón de falla."
            }

        def extract_failure_type(description: str):
            marker = " detected on "
            if description and marker in description:
                return description.split(marker)[0].strip()
            return description or "Falla desconocida"

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
            f"Acción recomendada: {most_common_action}. "
            "Validate spare parts, inspect recurring components, and schedule preventive work before production impact increases."
        )

        return {
            "status": "success",
            "equipment_id": request.equipment_id,
            "failure_type": translate_maintenance_text(primary_failure),
            "requested_failure_type": request.failure_type,
            "analysis_window_years": request.years,
            "matching_work_orders": len(work_orders),
            "occurrences": primary_count,
            "critical_occurrences": critical_count,
            "open_work_orders": open_count,
            "average_days_between_failures": mtbf_days,
            "recurrence_level": recurrence_level,
            "most_common_action": translate_maintenance_text(most_common_action),
            "confidence": confidence,
            "recommendation": translate_maintenance_text(recommendation),
            "failure_distribution": [
                {"failure_type": translate_maintenance_text(failure), "count": count}
                for failure, count in sorted_failures[:10]
            ],
            "action_distribution": [
                {"recommended_action": translate_maintenance_text(action), "count": count}
                for action, count in sorted_actions[:10]
            ],
            "recent_matching_orders": [
                {
                    "work_order_id": order.work_order_id,
                    "equipment_id": order.equipment_id,
                    "failure_type": translate_maintenance_text(extract_failure_type(order.description)),
                    "priority": order.priority,
                    "status_work_order": order.status,
                    "recommended_action": translate_maintenance_text(order.recommended_action),
                    "created_at": order.created_at.isoformat() if order.created_at else None
                }
                for order in work_orders[:10]
            ]
        }

    finally:
        db.close()






