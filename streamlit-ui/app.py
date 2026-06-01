import streamlit as st
import requests

ORCHESTRATOR_URL = "http://localhost:8000/chat"

st.set_page_config(
    page_title="Maintenance AI Assistant",
    page_icon="🛠️",
    layout="wide"
)

st.title("🛠️ Maintenance AI Assistant")
st.write(
    "Ask questions about machine work orders, risk score, spare parts, "
    "maintenance history, critical work orders, or daily priorities."
)

question = st.text_input(
    "Question",
    value="What equipment should I prioritize today?"
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

            if "highest_risk_equipment" in answer:
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

            elif "maintenance_history" in answer:
                st.subheader("Maintenance History")

                history = answer.get("maintenance_history", {})

                if isinstance(history, dict):
                    st.json(history)
                else:
                    st.dataframe(
                        history,
                        use_container_width=True
                    )

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
                        "maintenance_history"
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