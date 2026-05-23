import streamlit as st
import requests
import pandas as pd
from datetime import date

st.set_page_config(page_title="SaaS Finance Tracker V2", layout="wide")

BACKEND_URL = "http://127.0.0.1:8000"

st.title("🛡️ Smart Finance Dashboard (V2.0)")
st.caption("Frontend client for the FastAPI backend")

def api_get(path: str, timeout: int = 5):
    return requests.get(f"{BACKEND_URL}{path}", timeout=timeout)

def api_post(path: str, payload: dict, timeout: int = 5):
    return requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=timeout)

def fetch_health():
    try:
        response = api_get("/")
        if response.ok:
            return response.json(), None
        return None, f"Backend returned {response.status_code}"
    except requests.RequestException as e:
        return None, str(e)

def fetch_transactions(limit: int = 50):
    try:
        response = api_get(f"/transactions?limit={limit}")
        if response.ok:
            return response.json().get("transactions", [])
        return [], f"Backend returned {response.status_code}"
    except requests.RequestException as e:
        return [], str(e)

def fetch_summary():
    try:
        response = api_get("/analytics/summary")
        if response.ok:
            return response.json(), None
        return None, f"Backend returned {response.status_code}"
    except requests.RequestException as e:
        return None, str(e)

def submit_transaction(txn_date: str, description: str, amount: float):
    payload = {
        "date": txn_date,
        "description": description.strip(),
        "amount": amount,
    }
    try:
        response = api_post("/transactions", payload)
        if response.ok:
            return response.json(), None
        return None, response.text
    except requests.RequestException as e:
        return None, str(e)

health, health_error = fetch_health()

if health:
    st.success(f"✅ Backend Online: {health.get('message', 'Connected')}")
    if health.get("ai_model_loaded"):
        st.info("AI model is loaded.")
    else:
        st.warning("AI model is not loaded yet.")
else:
    st.error(f"❌ Backend Offline: {health_error}")
    st.stop()

with st.sidebar:
    st.header("➕ Add Transaction")

    with st.form("add_transaction_form", clear_on_submit=True):
        txn_date = st.date_input("Date", value=date.today())
        description = st.text_input("Description", placeholder="Netflix, Petrol, Groceries")
        amount = st.number_input("Amount", min_value=0.01, step=0.01, format="%.2f")
        submitted = st.form_submit_button("Save Transaction")

    if submitted:
        if not description.strip():
            st.error("Description cannot be empty.")
        else:
            result, error = submit_transaction(str(txn_date), description, amount)
            if error:
                st.error(f"Failed to save transaction: {error}")
            else:
                saved = result.get("data", {})
                st.success(f"Saved as: {saved.get('category', 'Unknown')}")
                if saved.get("is_anomaly"):
                    st.warning("⚠️ This transaction was flagged as unusual.")
                st.rerun()

st.subheader("Live Dashboard")

summary, summary_error = fetch_summary()
transactions, tx_error = fetch_transactions(limit=100)

col1, col2, col3 = st.columns(3)

if summary:
    overall = summary.get("overall", {})
    breakdown = summary.get("categorical_breakdown", [])

    col1.metric("Total Spent", f"${overall.get('total_spent', 0):,.2f}")
    col2.metric("Transactions", f"{overall.get('transaction_count', 0)}")
    top_category = breakdown[0]["category"] if breakdown else "N/A"
    col3.metric("Top Category", top_category)
else:
    col1.metric("Total Spent", "—")
    col2.metric("Transactions", "—")
    col3.metric("Top Category", "—")
    st.warning(f"Could not load summary: {summary_error}")

tab1, tab2 = st.tabs(["Transactions", "Category Breakdown"])

with tab1:
    st.subheader("Recent Transactions")
    if tx_error:
        st.error(f"Could not load transactions: {tx_error}")
    elif transactions:
        df = pd.DataFrame(transactions)
        display_cols = ["id", "date", "description", "category", "amount", "is_anomaly"]
        existing_cols = [c for c in display_cols if c in df.columns]
        st.dataframe(df[existing_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No transactions found yet.")

with tab2:
    st.subheader("Category Summary")
    if summary and summary.get("categorical_breakdown"):
        breakdown_df = pd.DataFrame(summary["categorical_breakdown"])
        st.dataframe(breakdown_df, use_container_width=True, hide_index=True)
    else:
        st.info("No category data yet.")