# Guion De Demo - Plataforma De Agente IA Para Mantenimiento Industrial

## Objetivo De La Demo

Mostrar que la plataforma puede responder preguntas de mantenimiento, consultar datos operativos, recomendar prioridades, analizar fallas recurrentes y ejecutar un workflow serverless de mantenimiento.

## 1. Iniciar La Plataforma

```powershell
docker compose up -d --build
docker compose ps
```

Resultado esperado:

- Todos los servicios aparecen como `Up`.
- PostgreSQL aparece como `healthy`.

## 2. Abrir La Interfaz

Abrir:

```text
http://localhost:8501
```

Explicación:

El técnico puede usar esta interfaz de chat para hacer preguntas de mantenimiento en lenguaje natural.

## 3. Estado De Equipo

Preguntar:

```text
¿Cuál es el estado de PRESS-01?
```

Punto a explicar:

El agente identifica `PRESS-01`, llama la herramienta de información de equipo y devuelve estado actual, área y criticidad.

## 4. Priorización

Preguntar:

```text
¿Qué equipo debo priorizar hoy?
```

Punto a explicar:

El agente combina ranking de riesgo, órdenes críticas y datos de tiempo muerto para recomendar qué máquinas requieren atención primero.

## 5. Refacciones

Preguntar:

```text
¿Hay refacciones disponibles para CNC-01?
```

Punto a explicar:

El sistema consulta inventario de refacciones y devuelve partes disponibles, cantidades, almacén y condición de stock.

## 6. OEE Y Tiempo Muerto

Preguntar:

```text
¿Qué equipo genera más tiempo muerto?
```

Después preguntar:

```text
¿Qué máquina tiene el menor OEE?
```

Punto a explicar:

La plataforma soporta análisis de desempeño operativo, no solo consulta de tickets.

## 7. Mantenimiento Recomendado

Preguntar:

```text
Mantenimiento recomendado para PRESS-01
```

Punto a explicar:

El agente usa estado del equipo, riesgo, órdenes abiertas, historial y refacciones para generar una recomendación de mantenimiento.

## 8. Análisis De Patrón De Falla

Preguntar:

```text
¿La fuga de aceite ha ocurrido antes en PRESS-01?
```

Punto a explicar:

El sistema analiza órdenes históricas e identifica recurrencia, frecuencia, acción correctiva común y recomendación.

Punto clave:

Esta función demuestra análisis basado en historial de mantenimiento y reglas estadísticas.

## 9. Resumen Semanal

Preguntar:

```text
Genera un resumen semanal de mantenimiento.
```

Punto a explicar:

El sistema resume actividad reciente de mantenimiento, trabajo abierto, trabajo completado y prioridades críticas.

## 10. Prueba De Herramienta Serverless

Ejecutar:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:7071/api/get_equipment_info" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"equipment_id":"PRESS-01"}'
```

Punto a explicar:

Esto demuestra una herramienta expuesta mediante Azure Functions.

## 11. Prueba De Durable Workflow

Ejecutar:

```powershell
$start = Invoke-RestMethod `
  -Uri "http://localhost:7072/api/maintenance_workflow/start" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"equipment_id":"PRESS-01","priority":"critical","description":"Solicitud demo de workflow","recommended_action":"Inspeccionar prensa y validar historial de fuga de aceite","requested_by":"demo-user"}'

Start-Sleep -Seconds 5
Invoke-RestMethod -Uri $start.statusQueryGetUri | ConvertTo-Json -Depth 8
```

Resultado esperado:

```text
runtimeStatus: Completed
workflow_engine: Azure Durable Functions
work_order.status: success
notification.status: success
```

Punto a explicar:

El Durable Workflow coordina múltiples pasos: validación, consulta de equipo, verificación de refacciones, decisión, creación de orden y notificación.

## 12. Entrada De Reporte Técnico

En la interfaz Streamlit, bajar al formulario **Reporte De Mantenimiento Del Técnico**.

Enviar un reporte con:

```text
ID de Equipo: PRESS-01
Tipo de Falla: Fuga de aceite
Acción Tomada: Se reemplazó sello hidráulico y se limpió residuo de aceite
Estado del Equipo: running
Estado de Orden: completed
Prioridad: high
Refacción Usada: Hydraulic seal kit (min stock 2)
Cantidad Usada: 1
```

Punto a explicar:

El reporte se envía mediante API, no editando PostgreSQL directamente. El API crea o actualiza la orden, registra historial de mantenimiento, actualiza estado del equipo, ajusta inventario y escribe un log de auditoría.

Prueba directa por API:

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8001/submit_technician_report" `
  -Method POST `
  -ContentType "application/json" `
  -Body '{"equipment_id":"PRESS-01","reported_by":"tech-demo","failure_type":"Fuga de aceite","action_taken":"Se reemplazó sello hidráulico y se limpió residuo de aceite","status_equipment":"running","work_order_status":"completed","priority":"high","spare_part_used":"Hydraulic seal kit (min stock 2)","spare_part_quantity_used":1,"recurrence_risk":"high"}'
```

## 13. Cierre

Este proyecto demuestra un asistente IA de mantenimiento usando arquitectura de agentes. Combina interacción en lenguaje natural, herramientas backend, datos PostgreSQL, funciones serverless, workflows durables y una UI orientada a técnicos.
