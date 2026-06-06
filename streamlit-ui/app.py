import streamlit as st
import requests
import os

ORCHESTRATOR_BASE_URL = os.getenv(
    "ORCHESTRATOR_URL",
    "http://localhost:8000"
)

ORCHESTRATOR_URL = f"{ORCHESTRATOR_BASE_URL}/chat"

TOOLS_API_BASE_URL = os.getenv(
    "TOOLS_API_URL",
    "http://localhost:8001"
)

st.set_page_config(
    page_title="Asistente IA de Mantenimiento",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ Asistente IA de Mantenimiento")
st.write(
    "Haz preguntas sobre órdenes de trabajo, riesgo, refacciones, tiempo muerto, OEE, "
    "historial de mantenimiento, órdenes críticas o resúmenes semanales."
)

question = st.text_input(
    "Pregunta",
    value="¿Qué máquina tiene el menor OEE?"
)

user_id = st.text_input(
    "ID de Usuario",
    value="supervisor_01"
)

if st.button("Preguntar"):
    payload = {
        "user_id": user_id,
        "message": question
    }

    try:
        response = requests.post(
            ORCHESTRATOR_URL,
            json=payload,
            timeout=10
        )

        data = response.json()

        if data.get("status") == "success":
            answer = data.get("answer", {})

            st.success(answer.get("summary", "Solicitud completada."))

            display_answer = data.get("display_answer")
            if display_answer:
                st.markdown(display_answer)

            # Weekly maintenance summary
            if "total_work_orders" in answer and "critical_open_work_orders" in answer:
                st.subheader("Resumen Semanal de Mantenimiento")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Total de Órdenes",
                    answer.get("total_work_orders", "N/A")
                )

                col2.metric(
                    "Órdenes Abiertas",
                    answer.get("open_work_orders", "N/A")
                )

                col3.metric(
                    "Órdenes Críticas Abiertas",
                    answer.get("critical_open_work_orders", "N/A")
                )

                col4.metric(
                    "Equipos Afectados",
                    answer.get("affected_equipment", "N/A")
                )

            # Single-equipment OEE response
            elif "oee" in answer:
                st.subheader("Análisis OEE")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "OEE",
                    f"{answer.get('oee', 'N/A')}%"
                )

                col2.metric(
                    "Disponibilidad",
                    f"{answer.get('availability', 'N/A')}%"
                )

                col3.metric(
                    "Rendimiento",
                    f"{answer.get('performance', 'N/A')}%"
                )

                col4.metric(
                    "Calidad",
                    f"{answer.get('quality', 'N/A')}%"
                )

                col5, col6, col7 = st.columns(3)

                col5.metric(
                    "Minutos Planeados",
                    answer.get("planned_minutes", "N/A")
                )

                col6.metric(
                    "Minutos de Tiempo Muerto",
                    answer.get("downtime_minutes", "N/A")
                )

                col7.metric(
                    "Minutos Operando",
                    answer.get("runtime_minutes", "N/A")
                )

            # Lowest OEE equipment ranking
            elif "lowest_oee_equipment" in answer:
                st.subheader("Equipos con Menor OEE")

                lowest_oee = answer.get("lowest_oee_equipment", [])

                if lowest_oee:
                    st.dataframe(
                        lowest_oee,
                        use_container_width=True
                    )

                    worst_equipment = lowest_oee[0]

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Equipos con Menor OEE",
                        worst_equipment.get("equipment_id", "N/A")
                    )

                    col2.metric(
                        "OEE",
                        f"{worst_equipment.get('oee', 'N/A')}%"
                    )

                    col3.metric(
                        "Disponibilidad",
                        f"{worst_equipment.get('availability', 'N/A')}%"
                    )

                    col4.metric(
                        "Minutos de Tiempo Muerto",
                        worst_equipment.get("downtime_minutes", "N/A")
                    )

                    if "oee_ranking" in answer:
                        st.subheader("Ranking Completo De OEE")
                        st.dataframe(
                            answer.get("oee_ranking", []),
                            use_container_width=True
                        )

                else:
                    st.info("No hay datos disponibles de ranking OEE.")

            # Downtime ranking
            elif "downtime_ranking" in answer:
                st.subheader("Ranking de Tiempo Muerto")

                downtime_ranking = answer.get("downtime_ranking", [])

                if downtime_ranking:
                    st.dataframe(
                        downtime_ranking,
                        use_container_width=True
                    )

                    top = downtime_ranking[0]

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Equipo con Mayor Tiempo Muerto",
                        top.get("equipment_id", "N/A")
                    )

                    col2.metric(
                        "Horas Estimadas de Tiempo Muerto",
                        top.get("estimated_downtime_hours", "N/A")
                    )

                    col3.metric(
                        "Total de Órdenes",
                        top.get("total_work_orders", "N/A")
                    )
                else:
                    st.info("No hay datos de tiempo muerto disponibles.")

            # Failure pattern analysis
            elif "failure_pattern_analysis" in answer:
                st.subheader("Análisis de Patrón de Falla")

                pattern = answer.get("failure_pattern_analysis", {})

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Tipo de Falla", pattern.get("failure_type", "N/A"))
                col2.metric("Ocurrencias", pattern.get("occurrences", "N/A"))
                col3.metric("Recurrencia", pattern.get("recurrence_level", "N/A"))
                col4.metric("Confianza", pattern.get("confidence", "N/A"))

                st.write(pattern.get("recommendation", "No hay recomendación disponible."))

                if pattern.get("failure_distribution"):
                    st.subheader("Distribución de Fallas")
                    st.dataframe(
                        pattern.get("failure_distribution", []),
                        use_container_width=True
                    )

                if pattern.get("action_distribution"):
                    st.subheader("Acciones Correctivas Usadas")
                    st.dataframe(
                        pattern.get("action_distribution", []),
                        use_container_width=True
                    )

                if pattern.get("recent_matching_orders"):
                    st.subheader("Órdenes Recientes Coincidentes")
                    st.dataframe(
                        pattern.get("recent_matching_orders", []),
                        use_container_width=True
                    )

                with st.expander("Detalles Técnicos"):
                    st.json(pattern)
            # Daily maintenance recommendations
            elif "recommended_focus" in answer:
                st.subheader("Foco Recomendado")

                recommended_focus = answer.get("recommended_focus", [])
                if recommended_focus:
                    st.dataframe(
                        recommended_focus,
                        use_container_width=True
                    )

                critical_orders = answer.get("critical_open_work_orders", [])
                if critical_orders:
                    st.subheader("Órdenes Críticas Abiertas")
                    st.dataframe(
                        critical_orders,
                        use_container_width=True
                    )

                downtime_equipment = answer.get("highest_downtime_equipment", [])
                if downtime_equipment:
                    st.subheader("Equipo con Mayor Tiempo Muerto")
                    st.dataframe(
                        downtime_equipment,
                        use_container_width=True
                    )

                with st.expander("Detalles Técnicos"):
                    st.json(answer)

            # Equipment-specific recommended maintenance
            elif "recommended_actions" in answer:
                st.subheader("Acciones Recomendadas")

                col1, col2, col3 = st.columns(3)
                col1.metric("Prioridad", answer.get("priority", "N/A"))
                col2.metric("Nivel de Riesgo", answer.get("risk_level", "N/A"))
                col3.metric("Score de Riesgo", answer.get("risk_score", "N/A"))

                for index, action in enumerate(answer.get("recommended_actions", []), start=1):
                    st.write(f"{index}. {action}")

                with st.expander("Detalles Técnicos"):
                    st.json(answer)

            # Common failure analysis
            elif "top_failure_types" in answer:
                st.subheader("Top Tipo de Fallas")

                most_common = answer.get("most_common_failure")
                if most_common:
                    col1, col2 = st.columns(2)
                    col1.metric("Falla Más Común", most_common.get("failure_type", "N/A"))
                    col2.metric("Ocurrencias", most_common.get("count", "N/A"))

                st.dataframe(
                    answer.get("top_failure_types", []),
                    use_container_width=True
                )

                with st.expander("Detalles Técnicos"):
                    st.json(answer)
            # All work orders for one equipment
            elif "all_work_orders" in answer:
                st.subheader("Todas las Órdenes")

                all_orders = answer.get("all_work_orders", [])

                if all_orders:
                    st.dataframe(
                        all_orders,
                        use_container_width=True
                    )

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "Total de Órdenes",
                        len(all_orders)
                    )

                    critical_count = len([
                        order for order in all_orders
                        if order.get("priority") == "critical"
                    ])

                    col2.metric(
                        "Órdenes Críticas",
                        critical_count
                    )
                else:
                    st.info("No se encontraron órdenes de trabajo.")

            # Highest risk equipment ranking
            elif "highest_risk_equipment" in answer:
                st.subheader("Equipos con Mayor Riesgo")

                highest_risk = answer.get("highest_risk_equipment", [])

                if highest_risk:
                    st.dataframe(
                        highest_risk,
                        use_container_width=True
                    )

                    top_equipment = highest_risk[0]

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Equipo de Mayor Prioridad",
                        top_equipment.get("equipment_id", "N/A")
                    )

                    col2.metric(
                        "Score de Riesgo",
                        top_equipment.get("risk_score", "N/A")
                    )

                    col3.metric(
                        "Score de Salud",
                        top_equipment.get("health_score", "N/A")
                    )

                    col4.metric(
                        "Nivel de Riesgo",
                        top_equipment.get("risk_level", "N/A")
                    )

                else:
                    st.info("No se encontraron equipos de alto riesgo.")

            # Critical work orders
            elif "critical_work_orders" in answer:
                critical_orders = answer.get("critical_work_orders", [])

                st.subheader("Órdenes Críticas")

                if critical_orders:
                    st.dataframe(
                        critical_orders,
                        use_container_width=True
                    )

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "Órdenes Críticas Abiertas",
                        len(critical_orders)
                    )

                    equipment_ids = {
                        order.get("equipment_id")
                        for order in critical_orders
                        if order.get("equipment_id")
                    }

                    col2.metric(
                        "Equipos Afectados",
                        len(equipment_ids)
                    )

                else:
                    st.info("No se encontraron órdenes críticas.")

            # Historial de mantenimiento
            elif "maintenance_history" in answer:
                st.subheader("Historial de Mantenimiento")

                history = answer.get("maintenance_history", {})

                if isinstance(history, dict):
                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Última Falla",
                        history.get("last_failure", "N/A")
                    )

                    col2.metric(
                        "Última Acción",
                        history.get("last_action", "N/A")
                    )

                    col3.metric(
                        "Días Desde Último Evento",
                        history.get("days_since_last_event", "N/A")
                    )

                    st.json(history)
                else:
                    st.dataframe(
                        history,
                        use_container_width=True
                    )

            # Standard risk / machine-specific response
            else:
                col1, col2, col3 = st.columns(3)

                col1.metric(
                    "Nivel de Riesgo",
                    answer.get("risk_level", "N/A")
                )

                col2.metric(
                    "Score de Riesgo",
                    answer.get("risk_score", "N/A")
                )

                col3.metric(
                    "Score de Salud",
                    answer.get("health_score", "N/A")
                )

                if "open_work_orders" in answer:
                    if isinstance(answer["open_work_orders"], list):
                        st.subheader("Órdenes Abiertas")
                        st.dataframe(
                            answer["open_work_orders"],
                            use_container_width=True
                        )
                    else:
                        st.metric(
                            "Órdenes Abiertas",
                            answer["open_work_orders"]
                        )

                other_fields = {
                    key: value
                    for key, value in answer.items()
                    if key not in [
                        "summary",
                        "risk_level",
                        "risk_score",
                        "health_score",
                        "open_work_orders",
                        "highest_risk_equipment",
                        "critical_work_orders",
                        "maintenance_history",
                        "all_work_orders",
                        "downtime_ranking",
                        "lowest_oee_equipment",
                        "oee_ranking",
                        "oee",
                        "availability",
                        "performance",
                        "quality",
                        "planned_minutes",
                        "downtime_minutes",
                        "runtime_minutes",
                        "total_work_orders",
                        "critical_open_work_orders",
                        "affected_equipment"
                    ]
                }

                if other_fields:
                    st.subheader("Detalles Adicionales")
                    st.json(other_fields)

        elif data.get("status") == "not_supported_yet":
            st.warning(data.get("message", "Solicitud no soportada todavía."))

            examples = data.get("examples", [])
            if examples:
                st.subheader("Supported Example Preguntas")
                for example in examples:
                    st.write(f"- {example}")

        else:
            st.error(data.get("message", "La solicitud falló."))
            st.json(data)

    except Exception as e:
        st.error(f"Error conectando con el orquestador: {e}")
st.divider()
st.header("Reporte De Mantenimiento Del Técnico")
st.write(
    "Usa este formulario para registrar nueva información de mantenimiento en la base de datos "
    "a través de la API de herramientas."
)

with st.form("technician_report_form"):
    col1, col2, col3 = st.columns(3)

    report_equipment_id = col1.text_input(
        "ID de Equipo",
        value="PRESS-01"
    )

    reported_by = col2.text_input(
        "Reportado Por",
        value=user_id
    )

    report_priority = col3.selectbox(
        "Prioridad",
        ["low", "medium", "high", "critical"],
        index=2
    )

    failure_type = st.text_input(
        "Tipo de Falla",
        value="Fuga de aceite"
    )

    action_taken = st.text_area(
        "Acción Tomada",
        value="Se reemplazó sello hidráulico y se limpió residuo de aceite"
    )

    col4, col5, col6 = st.columns(3)

    equipment_status = col4.selectbox(
        "Estado Del Equipo",
        ["running", "maintenance", "down", "standby"],
        index=0
    )

    work_order_status = col5.selectbox(
        "Estado De Orden",
        ["created", "in_progress", "completed", "closed"],
        index=2
    )

    recurrence_risk = col6.selectbox(
        "Riesgo De Recurrencia",
        ["low", "medium", "high"],
        index=1
    )

    col7, col8 = st.columns(2)

    spare_part_used = col7.text_input(
        "Refacción Usada",
        value="Hydraulic seal kit (min stock 2)"
    )

    spare_part_quantity_used = col8.number_input(
        "Cantidad De Refacción Usada",
        min_value=0,
        max_value=100,
        value=0,
        step=1
    )

    submitted_report = st.form_submit_button("Enviar Reporte De Mantenimiento")

if submitted_report:
    report_payload = {
        "equipment_id": report_equipment_id,
        "reported_by": reported_by,
        "failure_type": failure_type,
        "action_taken": action_taken,
        "status_equipment": equipment_status,
        "work_order_status": work_order_status,
        "priority": report_priority,
        "spare_part_used": spare_part_used or None,
        "spare_part_quantity_used": spare_part_quantity_used,
        "recurrence_risk": recurrence_risk
    }

    try:
        report_response = requests.post(
            f"{TOOLS_API_BASE_URL}/submit_technician_report",
            json=report_payload,
            timeout=10
        )

        report_data = report_response.json()

        if report_data.get("status") == "success":
            st.success(report_data.get("message", "Reporte enviado."))

            col1, col2, col3 = st.columns(3)
            col1.metric(
                "Orden De Trabajo",
                report_data.get("work_order", {}).get("work_order_id", "N/A")
            )
            col2.metric(
                "Estado De Orden",
                report_data.get("work_order", {}).get("status_work_order", "N/A")
            )
            col3.metric(
                "Estado Del Equipo",
                report_data.get("equipment_status", {}).get("current_status", "N/A")
            )

            if report_data.get("inventory_update"):
                st.subheader("Actualización De Inventario")
                st.json(report_data.get("inventory_update"))

            with st.expander("Detalles Del Reporte Guardado"):
                st.json(report_data)
        else:
            st.error(report_data.get("message", "Falló el envío del reporte."))
            st.json(report_data)

    except Exception as e:
        st.error(f"Error enviando reporte de mantenimiento: {e}")


