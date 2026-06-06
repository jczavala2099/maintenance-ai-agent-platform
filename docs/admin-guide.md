# Guía De Administrador - Plataforma De Agente IA Para Mantenimiento Industrial

## 1. Objetivo De La Guía

Esta guía describe cómo instalar, ejecutar, validar y administrar localmente la plataforma de agente IA para mantenimiento industrial.

## 2. Requisitos

| Requisito | Uso |
|---|---|
| Docker Desktop | Ejecutar contenedores |
| Docker Compose | Levantar servicios |
| Git | Control de versiones |
| PowerShell | Comandos locales |
| Navegador web | Acceder a Streamlit |

## 3. Estructura Principal

```text
maintenance-agent-project/
  orchestrator/
  tools-api/
  logging-service/
  streamlit-ui/
  azure-functions-tools/
  durable-workflows/
  docs/
  tests/
  .github/workflows/
  docker-compose.yml
```

## 4. Servicios Del Sistema

| Servicio | Puerto | Responsabilidad |
|---|---:|---|
| Streamlit UI | 8501 | Interfaz de usuario |
| Orchestrator | 8000 | Chat, intención y tool-calling |
| Tools API | 8001 | Lógica de negocio y acceso a datos |
| Logging Service | 8002 | Registro de eventos |
| Azure Functions Tools | 7071 | Tools serverless |
| Durable Workflows | 7072 | Workflow multi-paso |
| PostgreSQL | 5432 | Base de datos |
| Azurite | 10000-10002 | Emulador de storage para Durable Functions |

## 5. Arranque Del Proyecto

Abrir PowerShell en la carpeta del proyecto:

```powershell
cd C:\Users\USERNAME\Documents\maintenance-agent-project
```

Levantar servicios:

```powershell
docker compose up -d --build
```

Verificar servicios:

```powershell
docker compose ps
```

## 6. URLs De Validación

| Componente | URL |
|---|---|
| Streamlit | `http://localhost:8501` |
| Orchestrator | `http://localhost:8000` |
| Tools API | `http://localhost:8001` |
| Logging Service | `http://localhost:8002` |
| Azure Functions | `http://localhost:7071/api` |
| Durable Workflows | `http://localhost:7072/api` |

## 7. Variables Y Configuración

El proyecto usa variables declaradas en `docker-compose.yml`.

Variables principales:

| Variable | Servicio | Uso |
|---|---|---|
| `DATABASE_URL` | Tools API | Conexión a PostgreSQL |
| `TOOLS_API_URL` | Orchestrator / Streamlit | URL de Tools API |
| `LOGGING_API_URL` | Orchestrator | URL del servicio de logs |
| `AZURE_FUNCTIONS_URL` | Orchestrator | URL de Azure Functions Tools |
| `OLLAMA_BASE_URL` | Orchestrator | URL del proveedor LLM local |

## 8. Base De Datos

Credenciales locales:

```text
Database: maintenance_db
User: maintenance_user
Password: maintenance_pass
Host: localhost
Port: 5432
```

Validar conteo de equipos:

```powershell
docker compose exec postgres-db psql -U maintenance_user -d maintenance_db -c "SELECT COUNT(*) FROM equipment;"
```

Tablas principales:

| Tabla | Descripción |
|---|---|
| `equipment` | Catálogo de equipos |
| `work_orders` | Órdenes de trabajo |
| `maintenance_history` | Historial de mantenimiento |
| `spare_parts` | Inventario de refacciones |
| `audit_logs` | Auditoría de acciones |

## 9. Entrada Controlada De Datos

Los usuarios no deben modificar datos mediante SQL directo. La escritura debe pasar por APIs para conservar validación, reglas de negocio y auditoría.

Endpoints administrativos:

| Endpoint | Uso |
|---|---|
| `POST /upsert_equipment` | Crear o actualizar equipo |
| `POST /update_equipment_status` | Cambiar estado operativo |
| `POST /upsert_spare_part` | Crear o actualizar refacción |
| `POST /adjust_spare_part_inventory` | Ajustar inventario |
| `POST /update_work_order` | Actualizar orden |
| `POST /record_maintenance_history` | Registrar historial |
| `POST /submit_technician_report` | Registrar reporte técnico completo |

## 10. Logs Y Auditoría

Consultar logs de contenedores:

```powershell
docker compose logs orchestrator
docker compose logs tools-api
docker compose logs logging-service
docker compose logs azure-functions-tools
docker compose logs durable-workflows
```

Consultar auditoría en base de datos:

```powershell
docker compose exec postgres-db psql -U maintenance_user -d maintenance_db -c "SELECT event_type, detail, created_at FROM audit_logs ORDER BY created_at DESC LIMIT 10;"
```

## 11. CI/CD

El pipeline se encuentra en:

```text
.github/workflows/cicd.yml
```

Actualmente valida:

- Instalación de dependencias.
- Compilación Python.
- Build de imágenes Docker principales.

Servicios cubiertos por build:

- Orchestrator.
- Tools API.
- Logging Service.

Para una entrega académica, este pipeline demuestra integración continua. El despliegue a cloud se documenta como patrón operativo, mientras la ejecución del proyecto se realiza localmente con Docker Compose.

## 12. Seguridad Operativa

Controles aplicados o documentados:

| Control | Estado |
|---|---|
| Contenedores separados por servicio | Implementado |
| Docker multi-stage | Implementado en servicios principales |
| Usuario non-root | Implementado en servicios FastAPI |
| Secrets externos | Documentado para producción |
| Auditoría de escrituras | Implementado en Tools API |
| Escaneo de vulnerabilidades | Ejecutable con Docker Scout o Trivy |

Comando recomendado para escaneo local:

```powershell
docker scout quickview
```

o:

```powershell
trivy image maintenance-agent-project-tools-api
```

## 13. Comandos De Mantenimiento

Reiniciar servicios:

```powershell
docker compose restart
```

Apagar servicios:

```powershell
docker compose down
```

Reconstruir:

```powershell
docker compose up -d --build
```

Ver estado:

```powershell
docker compose ps
```

## 14. Validación Rápida Del Chat

```powershell
Invoke-RestMethod `
  -Uri "http://localhost:8000/chat" `
  -Method POST `
  -ContentType "application/json; charset=utf-8" `
  -Body '{"user_id":"demo-user","message":"¿Cuál es el estado de PRESS-01?"}'
```

## 15. Recuperación De Problemas Frecuentes

| Problema | Causa Probable | Solución |
|---|---|---|
| Docker no conecta | Docker Desktop cerrado | Abrir Docker Desktop y esperar que inicie |
| Puerto ocupado | Servicio local usando el puerto | Cambiar puerto o detener servicio |
| Error de base de datos | PostgreSQL no está listo | Revisar healthcheck y logs |
| Streamlit no responde | Contenedor detenido | Revisar `docker compose ps` |
| Azure Functions falla | Azurite no disponible | Confirmar que Azurite está activo |
