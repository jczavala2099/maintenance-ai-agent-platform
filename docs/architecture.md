# Arquitectura - Proyecto 3

## 1. Visión General

La solución implementa una arquitectura de agente IA para mantenimiento industrial usando patrón agentic, tool-calling, funciones serverless, workflows durables, servicios contenerizados y base de datos estructurada.

## 2. Diagrama Lógico Principal

```mermaid
flowchart TD
    U["Usuario: técnico o supervisor"] --> UI["Streamlit UI"]
    UI --> ORCH["Orchestrator FastAPI"]
    ORCH --> INTENT["Detección de intención y extracción de entidades"]
    INTENT --> TOOLS["Tools API"]
    INTENT --> AZF["Azure Functions Tools"]
    INTENT --> DWF["Durable Functions Workflow"]
    INTENT --> LLM["LLM Provider / Ollama Llama 3"]
    TOOLS --> DB[("PostgreSQL")]
    AZF --> TOOLS
    DWF --> AZF
    DWF --> TOOLS
    DWF --> AZURITE[("Azurite Storage Emulator")]
    ORCH --> LOGS["Logging Service"]
    TOOLS --> AUDIT[("Audit Logs")]
    AUDIT --> DB
```

## 3. Flujo ReAct + Tool-Calling

El patrón principal es ReAct: el agente interpreta la intención, decide qué acción ejecutar, llama una tool, observa el resultado y genera una respuesta.

```mermaid
sequenceDiagram
    participant U as Usuario
    participant UI as Streamlit
    participant A as Orquestador
    participant T as Tool
    participant DB as PostgreSQL

    U->>UI: Pregunta en lenguaje natural
    UI->>A: POST /chat
    A->>A: Detecta intención
    A->>A: Extrae equipment_id / failure_type
    A->>T: Llama tool requerida
    T->>DB: Consulta o actualiza datos
    DB-->>T: Resultado
    T-->>A: JSON de observación
    A->>A: Construye respuesta final
    A-->>UI: answer + display_answer
    UI-->>U: Respuesta legible
```

## 4. Mecanismo De Decisión Del Agente

El orquestador evalúa la pregunta contra intenciones soportadas:

| Intención | Tool |
|---|---|
| Estado de equipo | `get_equipment_info` |
| Órdenes abiertas | `get_open_work_orders` |
| Todas las órdenes | `get_all_work_orders` |
| Crear orden | `create_work_order` vía Azure Function |
| Riesgo | `predict_failure_risk` |
| Refacciones | `check_spare_parts` |
| OEE | `calculate_oee` |
| Tiempo muerto | `get_downtime_ranking` |
| Falla común | `dashboard/top-failure-types` |
| Patrón de falla | `analyze_failure_pattern` |
| Mantenimiento diario | combinación de riesgo, órdenes críticas y tiempo muerto |

## 5. Arquitectura Serverless

Las Azure Functions implementan tools independientes:

```mermaid
flowchart LR
    ORCH["Orchestrator"] --> F1["get_equipment_info"]
    ORCH --> F2["create_work_order"]
    ORCH --> F3["send_notification"]
    F1 --> API["Tools API"]
    F2 --> API
    F3 --> LOG["Notification Result"]
    API --> DB[("PostgreSQL")]
```

## 6. Workflow Durable

El workflow multi-paso modela un proceso crítico de mantenimiento:

```mermaid
flowchart TD
    A["Inicio workflow"] --> B["Validar input"]
    B --> C["Consultar información del equipo"]
    C --> D["Consultar refacciones"]
    D --> E{"¿Hay refacciones disponibles?"}
    E -->|Sí| F["Crear orden de trabajo"]
    E -->|No| G["Escalar a supervisor"]
    F --> H["Enviar notificación"]
    G --> H
    H --> I["Registrar resultado"]
    I --> J["Finalizar workflow"]
```

## 7. Contenerización

Servicios contenerizados:

| Servicio | Imagen | Seguridad |
|---|---|---|
| Orchestrator | Python FastAPI | Multi-stage, non-root |
| Tools API | Python FastAPI | Multi-stage, non-root |
| Logging Service | Python FastAPI | Multi-stage, non-root |
| Streamlit UI | Python Streamlit | Imagen liviana |
| Azure Functions Tools | Azure Functions Python | Runtime oficial |
| Durable Workflows | Azure Functions Python | Runtime oficial |
| PostgreSQL | Postgres 16 | Imagen oficial |
| Azurite | Microsoft Azurite | Imagen oficial |

## 8. Observabilidad

```mermaid
flowchart TD
    ORCH["Orchestrator"] --> LOG["Logging Service"]
    TOOLS["Tools API"] --> AUDIT["AuditLog Model"]
    AUDIT --> DB[("PostgreSQL audit_logs")]
    LOG --> OUT["Logs de contenedor"]
```

Se observan:

- Requests al agente.
- Tool-calls.
- Eventos de workflow.
- Escrituras operativas.
- Auditoría de reportes técnicos.

## 9. Infraestructura Y Puertos

| Componente | Puerto |
|---|---:|
| Streamlit UI | 8501 |
| Orchestrator | 8000 |
| Tools API | 8001 |
| Logging Service | 8002 |
| Azure Functions Tools | 7071 |
| Durable Workflows | 7072 |
| PostgreSQL | 5432 |
| Azurite Blob | 10000 |
| Azurite Queue | 10001 |
| Azurite Table | 10002 |

## 10. Trade-Offs De Arquitectura

| Decisión | Ventaja | Trade-off |
|---|---|---|
| Orquestador central | Control claro de intenciones | Menos flexible que tool-calling nativo completo |
| Tools API separada | Reutilizable por chat, functions y UI | Requiere mantener contratos JSON |
| Serverless wrappers | Demuestra cloud-native tools | En local depende de runtime Azure Functions |
| Durable workflow | Modela proceso empresarial multi-paso | Más componentes que una API simple |
| PostgreSQL | Datos estructurados y consultables | Requiere administración de credenciales |
| Streamlit | Demo rápida y funcional | No reemplaza una app empresarial completa |

