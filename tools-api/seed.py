from db import Base, engine, SessionLocal
from models import Equipment, MaintenanceHistory, SparePart, WorkOrder
from datetime import datetime, timedelta
from uuid import uuid4
import random

Base.metadata.create_all(bind=engine)

random.seed(2026)
db = SessionLocal()

machines = [
    ("CNC-01", "CNC Milling Machine 01", "Machining", "high", "stopped"),
    ("CNC-02", "CNC Lathe Machine 02", "Machining", "high", "running"),
    ("CNC-03", "CNC Router 03", "Machining", "medium", "running"),
    ("PRESS-01", "Hydraulic Press 01", "Stamping", "high", "running"),
    ("PRESS-02", "Mechanical Press 02", "Stamping", "high", "maintenance"),
    ("PRESS-03", "Frame Forming Press 03", "Stamping", "medium", "running"),
    ("CONV-01", "Main Conveyor 01", "Assembly", "medium", "running"),
    ("CONV-02", "Glass Transfer Conveyor 02", "Assembly", "medium", "running"),
    ("ROBOT-01", "Welding Robot 01", "Welding", "high", "running"),
    ("ROBOT-02", "Sealant Application Robot 02", "Assembly", "high", "running"),
    ("COMP-01", "Air Compressor 01", "Utilities", "high", "running"),
    ("COMP-02", "Backup Air Compressor 02", "Utilities", "medium", "standby"),
    ("PUMP-01", "Cooling Pump 01", "Cooling", "medium", "running"),
    ("PUMP-02", "Water Circulation Pump 02", "Cooling", "medium", "running"),
    ("FAN-01", "Extraction Fan 01", "Ventilation", "low", "running"),
    ("FAN-02", "Paint Booth Fan 02", "Ventilation", "medium", "running"),
    ("OVEN-01", "Industrial Oven 01", "Heat Treatment", "high", "running"),
    ("OVEN-02", "Paint Curing Oven 02", "Finishing", "high", "running"),
    ("PACK-01", "Packaging Line 01", "Packaging", "medium", "running"),
    ("PACK-02", "Final Inspection Packaging 02", "Packaging", "medium", "running"),
]

failure_by_area = {
    "Machining": ["Spindle vibration", "Tool changer fault", "Axis alignment issue", "Coolant pressure low"],
    "Stamping": ["Hydraulic pressure drop", "Die alignment issue", "Oil leakage", "Overheating"],
    "Assembly": ["Sensor failure", "Belt slipping", "Sealant flow variation", "Positioning error"],
    "Welding": ["Torch calibration drift", "Wire feed issue", "High vibration", "Electrical fault"],
    "Utilities": ["Low air pressure", "Motor overload", "Filter restriction", "Valve failure"],
    "Cooling": ["Pump seal leakage", "Low flow rate", "Cooling hose rupture", "Bearing wear"],
    "Ventilation": ["Fan imbalance", "Filter saturation", "Motor overheating", "Airflow restriction"],
    "Heat Treatment": ["Temperature deviation", "Burner ignition issue", "Thermocouple drift", "Door seal wear"],
    "Finishing": ["Temperature deviation", "Paint curing variation", "Airflow restriction", "Sensor failure"],
    "Packaging": ["Photoeye misalignment", "Jam detected", "Pneumatic actuator fault", "Conveyor tracking issue"],
}

actions_by_failure = {
    "Spindle vibration": "Inspect spindle bearings and balance tooling",
    "Tool changer fault": "Calibrate tool changer and inspect actuator",
    "Axis alignment issue": "Perform axis alignment and backlash inspection",
    "Coolant pressure low": "Inspect coolant pump, filter and hose lines",
    "Hydraulic pressure drop": "Inspect hydraulic pump, seals and pressure regulator",
    "Die alignment issue": "Realign die set and verify press guides",
    "Oil leakage": "Replace seals and inspect fittings",
    "Overheating": "Inspect cooling circuit and motor load",
    "Sensor failure": "Replace sensor and validate signal wiring",
    "Belt slipping": "Adjust belt tension and inspect pulleys",
    "Sealant flow variation": "Clean nozzle and calibrate flow controller",
    "Positioning error": "Calibrate encoder and check mechanical stops",
    "Torch calibration drift": "Recalibrate welding torch and inspect fixture",
    "Wire feed issue": "Inspect wire feeder, liner and drive rolls",
    "High vibration": "Inspect bearings, mounting base and alignment",
    "Electrical fault": "Perform electrical diagnosis and inspect relays",
    "Low air pressure": "Inspect compressor, dryer and distribution leaks",
    "Motor overload": "Inspect motor current, bearings and load condition",
    "Filter restriction": "Replace filters and validate pressure drop",
    "Valve failure": "Inspect valve actuator and replace valve kit",
    "Pump seal leakage": "Replace pump seal and inspect shaft sleeve",
    "Low flow rate": "Inspect impeller, strainer and suction line",
    "Cooling hose rupture": "Replace hose and pressure test cooling circuit",
    "Bearing wear": "Replace bearing and inspect lubrication path",
    "Fan imbalance": "Balance fan wheel and inspect bearings",
    "Filter saturation": "Replace filter bank and clean ducts",
    "Motor overheating": "Inspect motor cooling, current draw and bearings",
    "Airflow restriction": "Clean ducting and inspect dampers",
    "Temperature deviation": "Calibrate temperature loop and inspect heater elements",
    "Burner ignition issue": "Inspect ignition module and gas train",
    "Thermocouple drift": "Replace thermocouple and verify calibration",
    "Door seal wear": "Replace door seal and inspect hinges",
    "Paint curing variation": "Validate oven profile and airflow balance",
    "Photoeye misalignment": "Realign photoeye and validate detection",
    "Jam detected": "Clear jam and inspect guides",
    "Pneumatic actuator fault": "Inspect actuator, solenoid and air supply",
    "Conveyor tracking issue": "Adjust tracking and inspect rollers",
}

parts_by_area = {
    "Machining": ["Spindle bearing", "Tool changer sensor", "Coolant filter", "Linear guide seal"],
    "Stamping": ["Hydraulic seal kit", "Pressure sensor", "Press guide bushing", "Oil filter"],
    "Assembly": ["Photoelectric sensor", "Conveyor belt", "Servo encoder", "Sealant nozzle"],
    "Welding": ["Welding torch tip", "Wire feeder roller", "Robot joint cable", "Fixture clamp"],
    "Utilities": ["Air filter", "Compressor belt", "Pressure regulator", "Solenoid valve"],
    "Cooling": ["Pump mechanical seal", "Cooling hose", "Impeller", "Flow sensor"],
    "Ventilation": ["Fan bearing", "Filter cartridge", "Motor starter", "V-belt"],
    "Heat Treatment": ["Thermocouple", "Burner igniter", "Door gasket", "Heater element"],
    "Finishing": ["Oven thermocouple", "Air filter", "Heater element", "Door gasket"],
    "Packaging": ["Photoeye sensor", "Pneumatic cylinder", "Conveyor roller", "Label printer ribbon"],
}

teams = [
    "Mechanical Maintenance",
    "Electrical Maintenance",
    "Automation Team",
    "Utilities Maintenance",
    "Facilities Maintenance",
]

requesters = [
    "operator_01",
    "operator_02",
    "operator_03",
    "supervisor_01",
    "supervisor_02",
    "maintenance_planner",
    "quality_engineer",
]

priority_weights = ["low", "medium", "high", "critical"]
status_weights = ["created", "in_progress", "completed", "closed"]

try:
    db.query(WorkOrder).delete()
    db.query(SparePart).delete()
    db.query(MaintenanceHistory).delete()
    db.query(Equipment).delete()
    db.commit()

    for equipment_id, name, area, criticality, status in machines:
        db.add(Equipment(
            equipment_id=equipment_id,
            name=name,
            area=area,
            criticality=criticality,
            status_equipment=status
        ))

        area_failures = failure_by_area.get(area, ["Preventive inspection"])

        # Five years of maintenance history per machine. The model stores days since event,
        # so we keep one representative record per year instead of adding schema complexity.
        for year_offset in range(5):
            failure = random.choice(area_failures)
            db.add(MaintenanceHistory(
                equipment_id=equipment_id,
                last_failure=failure,
                last_action=actions_by_failure.get(failure, "Preventive maintenance"),
                days_since_last_event=random.randint(year_offset * 365 + 5, year_offset * 365 + 330),
                recurrence_risk=random.choices(
                    ["low", "medium", "high"],
                    weights=[25, 45, 30],
                    k=1
                )[0]
            ))

        # Spare parts inventory: four parts per machine, including low-stock cases.
        for part_type in parts_by_area.get(area, ["General maintenance kit"]):
            minimum_stock = random.randint(2, 6)
            quantity = random.choices(
                [0, 1, minimum_stock, minimum_stock + 3, minimum_stock + 8],
                weights=[8, 12, 30, 35, 15],
                k=1
            )[0]
            db.add(SparePart(
                equipment_id=equipment_id,
                part_type=f"{part_type} (min stock {minimum_stock})",
                available=quantity > 0,
                quantity=quantity,
                warehouse=random.choice([
                    "Main Maintenance Warehouse",
                    "Line-side Cabinet",
                    "Secondary Warehouse",
                    "External Supplier"
                ])
            ))

    db.commit()

    today = datetime.utcnow()
    start_date = today - timedelta(days=365 * 5)
    machine_ids = [m[0] for m in machines]
    area_lookup = {m[0]: m[2] for m in machines}

    # Five years of historical work orders for KPI, OEE, downtime and risk analysis.
    for i in range(650):
        equipment_id = random.choice(machine_ids)
        area = area_lookup[equipment_id]
        failure = random.choice(failure_by_area.get(area, ["Preventive inspection"]))
        created_at = start_date + timedelta(days=random.randint(0, 365 * 5))

        age_days = (today - created_at).days
        if age_days > 120:
            status = random.choices(["completed", "closed"], weights=[65, 35], k=1)[0]
        elif age_days > 30:
            status = random.choices(["completed", "closed", "in_progress"], weights=[55, 35, 10], k=1)[0]
        else:
            status = random.choices(status_weights, weights=[25, 30, 30, 15], k=1)[0]

        db.add(WorkOrder(
            work_order_id="OT-" + str(uuid4())[:8],
            request_id=f"HIST-{created_at.year}-{i + 1:04d}",
            equipment_id=equipment_id,
            priority=random.choices(priority_weights, weights=[20, 35, 30, 15], k=1)[0],
            description=f"{failure} detected on {equipment_id}",
            recommended_action=actions_by_failure.get(failure, "Perform preventive maintenance"),
            requested_by=random.choice(requesters),
            assigned_team=random.choice(teams),
            status=status,
            created_at=created_at
        ))

    active_cases = [
        ("PRESS-01", "Hydraulic pressure drop", "critical", "created", 1),
        ("ROBOT-01", "High vibration", "critical", "in_progress", 2),
        ("CNC-01", "Spindle vibration", "high", "created", 3),
        ("OVEN-01", "Temperature deviation", "high", "in_progress", 4),
        ("COMP-01", "Low air pressure", "high", "created", 5),
        ("PUMP-02", "Low flow rate", "medium", "in_progress", 6),
        ("CONV-02", "Belt slipping", "medium", "created", 8),
        ("PACK-01", "Jam detected", "medium", "created", 10),
        ("FAN-02", "Airflow restriction", "high", "in_progress", 12),
        ("PRESS-02", "Oil leakage", "critical", "created", 14),
    ]

    for index, (equipment_id, failure, priority, status, age_days) in enumerate(active_cases, start=1):
        db.add(WorkOrder(
            work_order_id="OT-" + str(uuid4())[:8],
            request_id=f"ACTIVE-2026-{index:04d}",
            equipment_id=equipment_id,
            priority=priority,
            description=f"{failure} detected on {equipment_id}",
            recommended_action=actions_by_failure.get(failure, "Perform preventive maintenance"),
            requested_by=random.choice(requesters),
            assigned_team=random.choice(teams),
            status=status,
            created_at=today - timedelta(days=age_days)
        ))

    db.commit()

    print("Database seeded successfully with:")
    print("- 20 machines")
    print("- 100 maintenance history records across 5 years")
    print("- 80 spare parts inventory records")
    print("- 650 historical work orders across 5 years")
    print("- 10 active recent work orders for demo scenarios")

finally:
    db.close()