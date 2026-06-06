# Tool Schemas - Proyecto 3

## 1. Objetivo

Este documento describe el conjunto de tools usadas por el agente. Cada tool tiene contrato JSON de entrada y salida para que el orquestador pueda llamarla de forma controlada.

## 2. Convención General

Todas las tools devuelven una estructura base:

```json
{
  "status": "success",
  "data": {}
}
```

En caso de error:

```json
{
  "status": "error",
  "error_code": "ERROR_CODE",
  "message": "Descripción del error"
}
```

## 3. Tools Principales Del Agente

### 3.1 Obtener Información De Equipo

| Campo | Valor |
|---|---|
| Tool | `get_equipment_info` |
| Tipo | Tools API / Azure Function |
| Método | `POST` |
| Endpoint Tools API | `/get_equipment_info` |
| Endpoint Azure Function | `/api/get_equipment_info` |

Input:

```json
{
  "equipment_id": "PRESS-01"
}
```

Output:

```json
{
  "status": "success",
  "equipment_id": "PRESS-01",
  "name": "Hydraulic Press 01",
  "area": "Stamping",
  "criticality": "high",
  "status_equipment": "running"
}
```

Errores:

| Código | Significado |
|---|---|
| `EQUIPMENT_NOT_FOUND` | El equipo no existe |

### 3.2 Consultar Órdenes Abiertas

| Campo | Valor |
|---|---|
| Tool | `get_open_work_orders` |
| Método | `POST` |
| Endpoint | `/get_open_work_orders` |

Input:

```json
{
  "equipment_id": "ROBOT-01"
}
```

Output:

```json
{
  "status": "success",
  "equipment_id": "ROBOT-01",
  "count": 2,
  "open_work_orders": [
    {
      "work_order_id": "OT-065bf326",
      "priority": "critical",
      "description": "High vibration detected on ROBOT-01",
      "status_work_order": "in_progress"
    }
  ]
}
```

### 3.3 Crear Orden De Trabajo

| Campo | Valor |
|---|---|
| Tool | `create_work_order` |
| Tipo | Tools API / Azure Function |
| Método | `POST` |
| Endpoint Tools API | `/create_work_order` |
| Endpoint Azure Function | `/api/create_work_order` |

Input:

```json
{
  "request_id": "CHAT-AZFUNC-0001",
  "equipment_id": "PRESS-01",
  "priority": "high",
  "description": "PRESS-01 se está sobrecalentando",
  "recommended_action": "Revisar el problema reportado y realizar inspección de mantenimiento.",
  "requested_by": "demo-user"
}
```

Output:

```json
{
  "status": "success",
  "work_order_id": "OT-12345678",
  "equipment_id": "PRESS-01",
  "priority": "high"
}
```

Errores:

| Código | Significado |
|---|---|
| `EQUIPMENT_NOT_FOUND` | El equipo no existe |
| `VALIDATION_ERROR` | Faltan campos requeridos |

### 3.4 Consultar Refacciones

| Campo | Valor |
|---|---|
| Tool | `check_spare_parts` |
| Método | `POST` |
| Endpoint | `/check_spare_parts` |

Input:

```json
{
  "equipment_id": "CNC-01"
}
```

Output:

```json
{
  "status": "success",
  "equipment_id": "CNC-01",
  "available": true,
  "total_parts": 4,
  "available_parts": 4,
  "low_stock_parts": 1,
  "inventory": [
    {
      "part_type": "Spindle bearing",
      "available": true,
      "quantity": 3,
      "warehouse": "MRO-A",
      "stock_status": "ok"
    }
  ]
}
```

### 3.5 Predecir Riesgo De Falla

| Campo | Valor |
|---|---|
| Tool | `predict_failure_risk` |
| Método | `POST` |
| Endpoint | `/predict_failure_risk` |

Input:

```json
{
  "equipment_id": "PRESS-01"
}
```

Output:

```json
{
  "status": "success",
  "equipment_id": "PRESS-01",
  "criticality": "high",
  "risk_score": 96,
  "health_score": 4,
  "risk_level": "critical",
  "total_work_orders": 47,
  "critical_work_orders": 5,
  "open_work_orders": 2
}
```

### 3.6 Calcular OEE

| Campo | Valor |
|---|---|
| Tool | `calculate_oee` |
| Método | `POST` |
| Endpoint | `/calculate_oee` |

Input:

```json
{
  "equipment_id": "PRESS-01"
}
```

Output:

```json
{
  "status": "success",
  "equipment_id": "PRESS-01",
  "planned_minutes": 10080,
  "downtime_minutes": 420,
  "runtime_minutes": 9660,
  "availability": 95.83,
  "performance": 91.0,
  "quality": 94.0,
  "oee": 82.02
}
```

### 3.7 Ranking De Tiempo Muerto

| Campo | Valor |
|---|---|
| Tool | `get_downtime_ranking` |
| Método | `GET` |
| Endpoint | `/get_downtime_ranking` |

Output:

```json
{
  "status": "success",
  "downtime_ranking": [
    {
      "equipment_id": "PRESS-01",
      "equipment_name": "Hydraulic Press 01",
      "area": "Stamping",
      "estimated_downtime_hours": 251,
      "total_work_orders": 62
    }
  ]
}
```

### 3.8 Análisis De Patrón De Falla

| Campo | Valor |
|---|---|
| Tool | `analyze_failure_pattern` |
| Método | `POST` |
| Endpoint | `/analyze_failure_pattern` |

Input:

```json
{
  "equipment_id": "PRESS-01",
  "failure_type": "Oil Leakage",
  "years": 2
}
```

Output:

```json
{
  "status": "success",
  "equipment_id": "PRESS-01",
  "failure_type": "Fuga de aceite",
  "analysis_window_years": 2,
  "matching_work_orders": 15,
  "occurrences": 15,
  "critical_occurrences": 0,
  "open_work_orders": 1,
  "average_days_between_failures": 49.8,
  "recurrence_level": "high",
  "most_common_action": "Reemplazar sellos e inspeccionar conexiones",
  "confidence": 0.95,
  "recommendation": "Fuga de aceite se ha repetido 15 veces en los últimos 2 años..."
}
```

### 3.9 Registrar Reporte Técnico

| Campo | Valor |
|---|---|
| Tool | `submit_technician_report` |
| Método | `POST` |
| Endpoint | `/submit_technician_report` |

Input:

```json
{
  "equipment_id": "PRESS-01",
  "reported_by": "tech-01",
  "failure_type": "Fuga de aceite",
  "action_taken": "Se reemplazó sello hidráulico",
  "status_equipment": "running",
  "work_order_status": "closed",
  "priority": "high",
  "spare_part_used": "Hydraulic seal kit",
  "spare_part_quantity_used": 1,
  "recurrence_risk": "high"
}
```

Output:

```json
{
  "status": "success",
  "message": "Reporte técnico registrado correctamente.",
  "work_order": {
    "work_order_id": "OT-96bb25ed",
    "status_work_order": "closed"
  },
  "equipment_status": {
    "equipment_id": "PRESS-01",
    "current_status": "running"
  },
  "inventory_update": {
    "part_type": "Hydraulic seal kit",
    "new_quantity": 4
  }
}
```

## 4. Registro De Tools Para El LLM

Formato conceptual usado por el orquestador:

```json
[
  {
    "name": "get_equipment_info",
    "description": "Obtiene información operativa de un equipo industrial.",
    "input_schema": {
      "type": "object",
      "properties": {
        "equipment_id": {
          "type": "string",
          "description": "ID de equipo, por ejemplo PRESS-01"
        }
      },
      "required": ["equipment_id"]
    }
  },
  {
    "name": "create_work_order",
    "description": "Crea una orden de trabajo de mantenimiento.",
    "input_schema": {
      "type": "object",
      "properties": {
        "request_id": {"type": "string"},
        "equipment_id": {"type": "string"},
        "priority": {"type": "string"},
        "description": {"type": "string"},
        "recommended_action": {"type": "string"},
        "requested_by": {"type": "string"}
      },
      "required": ["request_id", "equipment_id", "priority", "description"]
    }
  }
]
```

## 5. Manejo De Errores

| Error | Manejo |
|---|---|
| Equipo no encontrado | Respuesta `status=error` con mensaje claro |
| Inventario insuficiente | No permite cantidad negativa |
| Falta ID de equipo | El orquestador solicita especificar equipo |
| Tool no disponible | El chat responde que la intención no está soportada |
| Datos históricos insuficientes | El análisis de patrón indica que no hay datos coincidentes |

