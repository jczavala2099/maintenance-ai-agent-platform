from sqlalchemy import Column, Integer, String, Boolean, DateTime, Text
from datetime import datetime
from db import Base


class Equipment(Base):
    __tablename__ = "equipment"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String, unique=True, index=True, nullable=False)
    name = Column(String, nullable=False)
    area = Column(String, nullable=False)
    criticality = Column(String, nullable=False)
    status_equipment = Column(String, nullable=False)


class MaintenanceHistory(Base):
    __tablename__ = "maintenance_history"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String, index=True, nullable=False)
    last_failure = Column(String, nullable=False)
    last_action = Column(String, nullable=False)
    days_since_last_event = Column(Integer, nullable=False)
    recurrence_risk = Column(String, nullable=False)


class SparePart(Base):
    __tablename__ = "spare_parts"

    id = Column(Integer, primary_key=True, index=True)
    equipment_id = Column(String, index=True, nullable=False)
    part_type = Column(String, nullable=False)
    available = Column(Boolean, nullable=False)
    quantity = Column(Integer, nullable=False)
    warehouse = Column(String, nullable=False)


class WorkOrder(Base):
    __tablename__ = "work_orders"

    id = Column(Integer, primary_key=True, index=True)
    work_order_id = Column(String, unique=True, index=True, nullable=False)
    request_id = Column(String, index=True, nullable=False)
    equipment_id = Column(String, index=True, nullable=False)
    priority = Column(String, nullable=False)
    description = Column(Text, nullable=False)
    recommended_action = Column(Text, nullable=True)
    requested_by = Column(String, nullable=True)
    assigned_team = Column(String, nullable=False)
    status = Column(String, nullable=False, default="created")
    created_at = Column(DateTime, default=datetime.utcnow)


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(Integer, primary_key=True, index=True)
    request_id = Column(String, index=True, nullable=False)
    event_type = Column(String, nullable=False)
    detail = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)