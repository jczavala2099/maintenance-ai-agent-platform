import streamlit as st
import requests
import os

ORCHESTRATOR_BASE_URL = os.getenv(
    "ORCHESTRATOR_URL",
    "http://localhost:8000"
)

ORCHESTRATOR_URL = f"{ORCHESTRATOR_BASE_URL}/chat"

st.set_page_config(
    page_title="Maintenance AI Assistant",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ Maintenance AI Assistant")
st.write(
    "Ask questions about work orders, risk score, spare parts, downtime, OEE, "
    "maintenance history, critical work orders, or weekly summaries."
)

question = st.text_input(
    "Question",
    value="What machine has the lowest OEE?"
)

user_id = st.text_input(
    "User ID",
    value="supervisor_01"
)

if st.button("Ask"):
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

            st.success(answer.get("summary", "Request completed."))

            display_answer = data.get("display_answer")
            if display_answer:
                st.markdown(display_answer)

            # Weekly maintenance summary
            if "total_work_orders" in answer and "critical_open_work_orders" in answer:
                st.subheader("Weekly Maintenance Summary")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "Total Work Orders",
                    answer.get("total_work_orders", "N/A")
                )

                col2.metric(
                    "Open Work Orders",
                    answer.get("open_work_orders", "N/A")
                )

                col3.metric(
                    "Critical Open Orders",
                    answer.get("critical_open_work_orders", "N/A")
                )

                col4.metric(
                    "Affected Equipment",
                    answer.get("affected_equipment", "N/A")
                )

            # Single-equipment OEE response
            elif "oee" in answer:
                st.subheader("OEE Analysis")

                col1, col2, col3, col4 = st.columns(4)

                col1.metric(
                    "OEE",
                    f"{answer.get('oee', 'N/A')}%"
                )

                col2.metric(
                    "Availability",
                    f"{answer.get('availability', 'N/A')}%"
                )

                col3.metric(
                    "Performance",
                    f"{answer.get('performance', 'N/A')}%"
                )

                col4.metric(
                    "Quality",
                    f"{answer.get('quality', 'N/A')}%"
                )

                col5, col6, col7 = st.columns(3)

                col5.metric(
                    "Planned Minutes",
                    answer.get("planned_minutes", "N/A")
                )

                col6.metric(
                    "Downtime Minutes",
                    answer.get("downtime_minutes", "N/A")
                )

                col7.metric(
                    "Runtime Minutes",
                    answer.get("runtime_minutes", "N/A")
                )

            # Lowest OEE equipment ranking
            elif "lowest_oee_equipment" in answer:
                st.subheader("Lowest OEE Equipment")

                lowest_oee = answer.get("lowest_oee_equipment", [])

                if lowest_oee:
                    st.dataframe(
                        lowest_oee,
                        use_container_width=True
                    )

                    worst_equipment = lowest_oee[0]

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Lowest OEE Equipment",
                        worst_equipment.get("equipment_id", "N/A")
                    )

                    col2.metric(
                        "OEE",
                        f"{worst_equipment.get('oee', 'N/A')}%"
                    )

                    col3.metric(
                        "Availability",
                        f"{worst_equipment.get('availability', 'N/A')}%"
                    )

                    col4.metric(
                        "Downtime Minutes",
                        worst_equipment.get("downtime_minutes", "N/A")
                    )

                    if "oee_ranking" in answer:
                        st.subheader("Full OEE Ranking")
                        st.dataframe(
                            answer.get("oee_ranking", []),
                            use_container_width=True
                        )

                else:
                    st.info("No OEE ranking data available.")

            # Downtime ranking
            elif "downtime_ranking" in answer:
                st.subheader("Downtime Ranking")

                downtime_ranking = answer.get("downtime_ranking", [])

                if downtime_ranking:
                    st.dataframe(
                        downtime_ranking,
                        use_container_width=True
                    )

                    top = downtime_ranking[0]

                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Highest Downtime Equipment",
                        top.get("equipment_id", "N/A")
                    )

                    col2.metric(
                        "Estimated Downtime Hours",
                        top.get("estimated_downtime_hours", "N/A")
                    )

                    col3.metric(
                        "Total Work Orders",
                        top.get("total_work_orders", "N/A")
                    )
                else:
                    st.info("No downtime data available.")

            # Failure pattern analysis
            elif "failure_pattern_analysis" in answer:
                st.subheader("Failure Pattern Analysis")

                pattern = answer.get("failure_pattern_analysis", {})

                col1, col2, col3, col4 = st.columns(4)
                col1.metric("Failure Type", pattern.get("failure_type", "N/A"))
                col2.metric("Occurrences", pattern.get("occurrences", "N/A"))
                col3.metric("Recurrence", pattern.get("recurrence_level", "N/A"))
                col4.metric("Confidence", pattern.get("confidence", "N/A"))

                st.write(pattern.get("recommendation", "No recommendation available."))

                if pattern.get("failure_distribution"):
                    st.subheader("Failure Distribution")
                    st.dataframe(
                        pattern.get("failure_distribution", []),
                        use_container_width=True
                    )

                if pattern.get("action_distribution"):
                    st.subheader("Corrective Actions Used")
                    st.dataframe(
                        pattern.get("action_distribution", []),
                        use_container_width=True
                    )

                if pattern.get("recent_matching_orders"):
                    st.subheader("Recent Matching Work Orders")
                    st.dataframe(
                        pattern.get("recent_matching_orders", []),
                        use_container_width=True
                    )

                with st.expander("Technical Details"):
                    st.json(pattern)
            # Daily maintenance recommendations
            elif "recommended_focus" in answer:
                st.subheader("Recommended Focus")

                recommended_focus = answer.get("recommended_focus", [])
                if recommended_focus:
                    st.dataframe(
                        recommended_focus,
                        use_container_width=True
                    )

                critical_orders = answer.get("critical_open_work_orders", [])
                if critical_orders:
                    st.subheader("Critical Open Work Orders")
                    st.dataframe(
                        critical_orders,
                        use_container_width=True
                    )

                downtime_equipment = answer.get("highest_downtime_equipment", [])
                if downtime_equipment:
                    st.subheader("Highest Downtime Equipment")
                    st.dataframe(
                        downtime_equipment,
                        use_container_width=True
                    )

                with st.expander("Technical Details"):
                    st.json(answer)

            # Equipment-specific recommended maintenance
            elif "recommended_actions" in answer:
                st.subheader("Recommended Actions")

                col1, col2, col3 = st.columns(3)
                col1.metric("Priority", answer.get("priority", "N/A"))
                col2.metric("Risk Level", answer.get("risk_level", "N/A"))
                col3.metric("Risk Score", answer.get("risk_score", "N/A"))

                for index, action in enumerate(answer.get("recommended_actions", []), start=1):
                    st.write(f"{index}. {action}")

                with st.expander("Technical Details"):
                    st.json(answer)

            # Common failure analysis
            elif "top_failure_types" in answer:
                st.subheader("Top Failure Types")

                most_common = answer.get("most_common_failure")
                if most_common:
                    col1, col2 = st.columns(2)
                    col1.metric("Most Common Failure", most_common.get("failure_type", "N/A"))
                    col2.metric("Occurrences", most_common.get("count", "N/A"))

                st.dataframe(
                    answer.get("top_failure_types", []),
                    use_container_width=True
                )

                with st.expander("Technical Details"):
                    st.json(answer)
            # All work orders for one equipment
            elif "all_work_orders" in answer:
                st.subheader("All Work Orders")

                all_orders = answer.get("all_work_orders", [])

                if all_orders:
                    st.dataframe(
                        all_orders,
                        use_container_width=True
                    )

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "Total Work Orders",
                        len(all_orders)
                    )

                    critical_count = len([
                        order for order in all_orders
                        if order.get("priority") == "critical"
                    ])

                    col2.metric(
                        "Critical Work Orders",
                        critical_count
                    )
                else:
                    st.info("No work orders found.")

            # Highest risk equipment ranking
            elif "highest_risk_equipment" in answer:
                st.subheader("Highest Risk Equipment")

                highest_risk = answer.get("highest_risk_equipment", [])

                if highest_risk:
                    st.dataframe(
                        highest_risk,
                        use_container_width=True
                    )

                    top_equipment = highest_risk[0]

                    col1, col2, col3, col4 = st.columns(4)

                    col1.metric(
                        "Top Priority Equipment",
                        top_equipment.get("equipment_id", "N/A")
                    )

                    col2.metric(
                        "Risk Score",
                        top_equipment.get("risk_score", "N/A")
                    )

                    col3.metric(
                        "Health Score",
                        top_equipment.get("health_score", "N/A")
                    )

                    col4.metric(
                        "Risk Level",
                        top_equipment.get("risk_level", "N/A")
                    )

                else:
                    st.info("No high-risk equipment found.")

            # Critical work orders
            elif "critical_work_orders" in answer:
                critical_orders = answer.get("critical_work_orders", [])

                st.subheader("Critical Work Orders")

                if critical_orders:
                    st.dataframe(
                        critical_orders,
                        use_container_width=True
                    )

                    col1, col2 = st.columns(2)

                    col1.metric(
                        "Critical Open Work Orders",
                        len(critical_orders)
                    )

                    equipment_ids = {
                        order.get("equipment_id")
                        for order in critical_orders
                        if order.get("equipment_id")
                    }

                    col2.metric(
                        "Affected Equipment",
                        len(equipment_ids)
                    )

                else:
                    st.info("No critical work orders found.")

            # Maintenance history
            elif "maintenance_history" in answer:
                st.subheader("Maintenance History")

                history = answer.get("maintenance_history", {})

                if isinstance(history, dict):
                    col1, col2, col3 = st.columns(3)

                    col1.metric(
                        "Last Failure",
                        history.get("last_failure", "N/A")
                    )

                    col2.metric(
                        "Last Action",
                        history.get("last_action", "N/A")
                    )

                    col3.metric(
                        "Days Since Last Event",
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
                    "Risk Level",
                    answer.get("risk_level", "N/A")
                )

                col2.metric(
                    "Risk Score",
                    answer.get("risk_score", "N/A")
                )

                col3.metric(
                    "Health Score",
                    answer.get("health_score", "N/A")
                )

                if "open_work_orders" in answer:
                    if isinstance(answer["open_work_orders"], list):
                        st.subheader("Open Work Orders")
                        st.dataframe(
                            answer["open_work_orders"],
                            use_container_width=True
                        )
                    else:
                        st.metric(
                            "Open Work Orders",
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
                    st.subheader("Additional Details")
                    st.json(other_fields)

        elif data.get("status") == "not_supported_yet":
            st.warning(data.get("message", "Request not supported yet."))

            examples = data.get("examples", [])
            if examples:
                st.subheader("Supported Example Questions")
                for example in examples:
                    st.write(f"- {example}")

        else:
            st.error(data.get("message", "Request failed."))
            st.json(data)

    except Exception as e:
        st.error(f"Error connecting to Orchestrator: {e}")