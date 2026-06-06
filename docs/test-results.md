# Resultados De Pruebas - Proyecto 3

## 1. Objetivo

Este documento resume las pruebas realizadas para validar que la plataforma cumple con el caso de uso, tool-calling, integración serverless, workflows, datos, UI y observabilidad.

## 2. Ambiente De Prueba

| Elemento | Valor |
|---|---|
| Sistema | Docker Compose local |
| Base de datos | PostgreSQL 16 |
| UI | Streamlit |
| Backend | FastAPI |
| Serverless | Azure Functions Python |
| Workflow | Durable Functions |
| Fecha de validación | 4 de junio de 2026 |

## 3. Servicios Esperados

| Servicio | Estado Esperado |
|---|---|
| `maintenance-streamlit-ui` | Up |
| `maintenance-agent-orchestrator` | Up |
| `maintenance-tools-api` | Up |
| `maintenance-logging-service` | Up |
| `maintenance-azure-functions-tools` | Up |
| `maintenance-durable-workflows` | Up |
| `maintenance-postgres-db` | Up / Healthy |
| `maintenance-azurite` | Up |

## 4. Dataset Validado

| Tabla | Registros |
|---|---:|
| `equipment` | 20 |
| `work_orders` | 693 |
| `maintenance_history` | 101 |
| `spare_parts` | 80 |

## 5. Pruebas Funcionales Del Chat

| # | Pregunta | Tool Principal | Resultado Esperado | Estado |
|---:|---|---|---|---|
| 1 | `¿Cuál es el estado de PRESS-01?` | `get_equipment_info` | Devuelve información del equipo | Aprobado |
| 2 | `¿Hay órdenes abiertas para ROBOT-01?` | `get_open_work_orders` | Devuelve órdenes abiertas | Aprobado |
| 3 | `Muestra todas las órdenes de PRESS-01` | `get_all_work_orders` | Lista órdenes históricas | Aprobado |
| 4 | `Crear orden de trabajo para PRESS-01 porque se está sobrecalentando` | `create_work_order` | Crea orden vía Azure Function | Aprobado |
| 5 | `¿Cuál es el riesgo de PRESS-01?` | `predict_failure_risk` | Devuelve score y nivel de riesgo | Aprobado |
| 6 | `¿Hay refacciones disponibles para CNC-01?` | `check_spare_parts` | Devuelve inventario | Aprobado |
| 7 | `¿Qué máquina tiene el mayor riesgo?` | `get_highest_risk_equipment` | Ranking de equipos por riesgo | Aprobado |
| 8 | `¿Qué equipo genera más tiempo muerto?` | `get_downtime_ranking` | Ranking de tiempo muerto | Aprobado |
| 9 | `¿Qué máquina tiene el menor OEE?` | `get_oee_ranking` | Ranking de menor OEE | Aprobado |
| 10 | `¿Cuál es el OEE de PRESS-01?` | `calculate_oee` | Métricas OEE | Aprobado |
| 11 | `Genera un resumen semanal de mantenimiento.` | `weekly_maintenance_summary` | Resumen semanal | Aprobado |
| 12 | `¿Qué historial de mantenimiento tiene ROBOT-01?` | `get_maintenance_history` | Historial del equipo | Aprobado |
| 13 | `Muestra todas las órdenes críticas.` | `get_critical_work_orders` | Órdenes críticas abiertas | Aprobado |
| 14 | `¿Cuál es la falla más común?` | `dashboard/top-failure-types` | Ranking de fallas | Aprobado |
| 15 | `¿La fuga de aceite ha ocurrido antes en PRESS-01?` | `analyze_failure_pattern` | Análisis de recurrencia | Aprobado |
| 16 | `Mantenimiento recomendado para PRESS-01` | combinación de tools | Recomendación por equipo | Aprobado |
| 17 | `¿Qué mantenimiento se debe hacer hoy?` | riesgo + críticas + downtime | Priorización diaria | Aprobado |

## 6. Prueba De Patrón De Falla

Pregunta:

```text
¿La fuga de aceite ha ocurrido antes en PRESS-01?
```

Resultado validado:

| Métrica | Resultado |
|---|---:|
| Tipo de falla | Fuga de aceite |
| Ventana de análisis | 2 años |
| Ocurrencias | 15 |
| Días promedio entre fallas | 49.8 |
| Nivel de recurrencia | Alto |
| Confianza | 0.95 |

Conclusión:

El sistema identifica recurrencia histórica y genera una recomendación basada en conteos, frecuencia y acción correctiva común.

## 7. Pruebas De Escritura En Base De Datos

| Endpoint | Escenario | Resultado | Estado |
|---|---|---|---|
| `/upsert_equipment` | Crear o actualizar equipo | Registro persistido | Aprobado |
| `/update_equipment_status` | Cambiar estado | Estado actualizado | Aprobado |
| `/upsert_spare_part` | Crear refacción | Inventario creado/actualizado | Aprobado |
| `/adjust_spare_part_inventory` | Descontar refacción | Cantidad ajustada | Aprobado |
| `/update_work_order` | Cerrar orden | Orden actualizada | Aprobado |
| `/record_maintenance_history` | Registrar historial | Evento almacenado | Aprobado |
| `/submit_technician_report` | Reporte técnico completo | Orden, historial, estado, inventario y auditoría actualizados | Aprobado |

## 8. Pruebas De Serverless Tools

| Azure Function | Entrada | Resultado Esperado | Estado |
|---|---|---|---|
| `get_equipment_info` | `equipment_id` | Información de equipo | Aprobado |
| `create_work_order` | Payload de orden | Orden creada | Aprobado |
| `send_notification` | Canal y mensaje | Confirmación de envío | Aprobado |

## 9. Prueba De Durable Workflow

Flujo validado:

```text
Input -> get_equipment_info -> check_spare_parts -> decision -> create_work_order/send_notification -> output
```

Resultado esperado:

- Workflow iniciado.
- Equipo consultado.
- Refacciones verificadas.
- Decisión tomada.
- Orden creada cuando aplica.
- Notificación enviada.
- Resultado final devuelto.

Estado: Aprobado.

## 10. Pruebas De UI

| Prueba | Resultado | Estado |
|---|---|---|
| Carga `http://localhost:8501` | HTTP 200 | Aprobado |
| Pregunta desde chat | Respuesta visible | Aprobado |
| Render de tablas | DataFrames visibles | Aprobado |
| Render de `display_answer` | Markdown visible | Aprobado |
| Formulario técnico | Envío correcto | Aprobado |

## 11. Pruebas De CI/CD

Pipeline:

```text
.github/workflows/cicd.yml
```

Validaciones:

| Paso | Resultado Esperado |
|---|---|
| Checkout | Repositorio disponible |
| Setup Python 3.11 | Runtime listo |
| Instalar dependencias | Dependencias instaladas |
| Compilar Python | Sin errores de sintaxis |
| Build Docker Orchestrator | Imagen construida |
| Build Docker Tools API | Imagen construida |
| Build Docker Logging | Imagen construida |

Estado: Implementado para integración continua local/académica.

## 12. Observabilidad Validada

| Elemento | Validación |
|---|---|
| Logs de contenedores | Disponibles con `docker compose logs` |
| Logging Service | Recibe eventos del orquestador |
| Audit Logs | Se registran escrituras en base de datos |
| Trazabilidad | Request, tool-call y respuesta pueden inspeccionarse |

## 13. Riesgos Detectados Y Mitigación

| Riesgo | Mitigación |
|---|---|
| Docker Desktop cerrado | Verificar Docker antes de demo |
| Pregunta sin ID de equipo | Mensaje claro solicitando ID válido |
| Datos históricos insuficientes | Respuesta de error controlada |
| Inventario negativo | Validación impide cantidad negativa |
| Dependencia de puertos locales | Puertos documentados en guía admin |

## 14. Conclusión De Pruebas

Las pruebas validan que el agente puede recibir preguntas en lenguaje natural, ejecutar tools, consultar y actualizar datos, interactuar con funciones serverless, ejecutar workflows y presentar resultados en una interfaz web.

