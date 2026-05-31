from db import Base, engine, SessionLocal
from models import Equipment, MaintenanceHistory, SparePart, WorkOrder
from datetime import datetime, timedelta
from uuid import uuid4
import random

Base.metadata.create_all(bind=engine)

db = SessionLocal()

machines = [
    ("CNC-01", "CNC Milling Machine 01", "Machining", "high", "stopped"),
    ("CNC-02", "CNC Lathe Machine 02", "Machining", "high", "running"),
    ("PRESS-01", "Hydraulic Press 01", "Stamping", "high", "running"),
    ("CONV-01", "Main Conveyor 01", "Assembly", "medium", "running"),
    ("ROBOT-01", "Welding Robot 01", "Welding", "high", "running"),
    ("COMP-01", "Air Compressor 01", "Utilities", "high", "running"),
    ("PUMP-01", "Cooling Pump 01", "Cooling", "medium", "running"),
    ("FAN-01", "Extraction Fan 01", "Ventilation", "low", "running"),
    ("OVEN-01", "Industrial Oven 01", "Heat Treatment", "high", "running"),
    ("PACK-01", "Packaging Line 01", "Packaging", "medium", "running"),
]

failures = [
    "High vibration",
    "Overheating",
    "Oil leakage",
    "Low pressure",
    "Sensor failure",
    "Abnormal noise",
    "Motor overload",
    "Alignment issue",
    "Bearing wear",
    "Electrical fault",
]

actions = [
    "Bearing inspection",
    "Lubrication",
    "Sensor replacement",
    "Motor inspection",
    "Alignment correction",
    "Filter replacement",
    "Belt adjustment",
    "Cooling system inspection",
    "Electrical diagnosis",
    "Preventive maintenance",
]

parts = [
    "bearing",
    "sensor",
    "belt",
    "filter",
    "motor",
    "pump seal",
    "lubricant",
    "valve",
    "relay",
    "cooling hose",
]

try:
    # Clear old data
    db.query(WorkOrder).delete()
    db.query(SparePart).delete()
    db.query(MaintenanceHistory).delete()
    db.query(Equipment).delete()
    db.commit()

    # Insert equipment, history, and spare parts
    for machine in machines:
        equipment_id, name, area, criticality, status = machine

        db.add(Equipment(
            equipment_id=equipment_id,
            name=name,
            area=area,
            criticality=criticality,
            status_equipment=status
        ))

        db.add(MaintenanceHistory(
            equipment_id=equipment_id,
            last_failure=random.choice(failures),
            last_action=random.choice(actions),
            days_since_last_event=random.randint(5, 90),
            recurrence_risk=random.choice(["low", "medium", "high"])
        ))

        db.add(SparePart(
            equipment_id=equipment_id,
            part_type=random.choice(parts),
            available=random.choice([True, True, True, False]),
            quantity=random.randint(0, 12),
            warehouse=random.choice([
                "Main Maintenance Warehouse",
                "Secondary Warehouse",
                "External Supplier"
            ])
        ))

    db.commit()

    # Insert 1 year of historical work orders
    today = datetime.utcnow()
    start_date = today - timedelta(days=365)

    for i in range(120):
        equipment_id = random.choice([m[0] for m in machines])
        created_at = start_date + timedelta(days=random.randint(0, 365))

        priority = random.choice(["low", "medium", "high", "critical"])
        failure = random.choice(failures)
        action = random.choice(actions)

        db.add(WorkOrder(
            work_order_id="OT-" + str(uuid4())[:8],
            request_id=f"HIST-{2026}-{i+1:04d}",
            equipment_id=equipment_id,
            priority=priority,
            description=f"{failure} detected on {equipment_id}",
            recommended_action=action,
            requested_by=random.choice(["operator_01", "operator_02", "supervisor_01", "maintenance_planner"]),
            assigned_team=random.choice([
                "Mechanical Maintenance",
                "Electrical Maintenance",
                "Automation Team",
                "Utilities Maintenance"
            ]),
            status=random.choice(["created", "in_progress", "completed", "closed"]),
            created_at=created_at
        ))

    db.commit()

    print("Database seeded successfully with:")
    print("- 10 machines")
    print("- 10 maintenance history records")
    print("- 10 spare parts records")
    print("- 120 historical work orders over 1 year")

finally:
    db.close()