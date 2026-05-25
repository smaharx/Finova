import os
from datetime import date, datetime

import pandas as pd
import requests
import streamlit as st
from dotenv import load_dotenv

load_dotenv()

BACKEND_URL = os.getenv("BACKEND_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="SaaS Finance Tracker V2", layout="wide")

st.title("🛡️ Smart Finance Dashboard (V2.0)")
st.caption("Frontend client for the FastAPI backend")


def api_get(path: str, timeout: int = 15):
    return requests.get(f"{BACKEND_URL}{path}", timeout=timeout)


def api_post(path: str, payload: dict, timeout: int = 15):
    return requests.post(f"{BACKEND_URL}{path}", json=payload, timeout=timeout)


def api_put(path: str, payload: dict, timeout: int = 15):
    return requests.put(f"{BACKEND_URL}{path}", json=payload, timeout=timeout)


def api_delete(path: str, timeout: int = 15):
    return requests.delete(f"{BACKEND_URL}{path}", timeout=timeout)


@st.cache_data(ttl=5)
def fetch_health():
    try:
        response = api_get("/")
        if response.ok:
            return response.json(), None
        return None, f"Backend returned {response.status_code}"
    except requests.RequestException as e:
        return None, str(e)


@st.cache_data(ttl=5)
def fetch_transactions(limit: int = 100):
    try:
        response = api_get(f"/transactions?limit={limit}")
        if response.ok:
            return response.json().get("transactions", []), None
        return [], response.text
    except requests.RequestException as e:
        return [], str(e)


@st.cache_data(ttl=5)
def fetch_summary():
    try:
        response = api_get("/analytics/summary")
        if response.ok:
            return response.json(), None
        return None, response.text
    except requests.RequestException as e:
        return None, str(e)


@st.cache_data(ttl=5)
def fetch_corrections(limit: int = 25):
    try:
        response = api_get(f"/corrections?limit={limit}")
        if response.ok:
            return response.json().get("corrections", []), None
        return [], response.text
    except requests.RequestException as e:
        return [], str(e)


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


def update_transaction(transaction_id: int, payload: dict):
    try:
        response = api_put(f"/transactions/{transaction_id}", payload)
        if response.ok:
            return response.json(), None
        return None, response.text
    except requests.RequestException as e:
        return None, str(e)


def delete_transaction(transaction_id: int):
    try:
        response = api_delete(f"/transactions/{transaction_id}")
        if response.ok:
            return response.json(), None
        return None, response.text
    except requests.RequestException as e:
        return None, str(e)


def submit_correction(transaction_id: int, corrected_category: str, notes: str = ""):
    payload = {
        "corrected_category": corrected_category.strip(),
        "notes": notes.strip() if notes else None,
    }
    try:
        response = api_post(f"/transactions/{transaction_id}/correction", payload)
        if response.ok:
            return response.json(), None
        return None, response.text
    except requests.RequestException as e:
        return None, str(e)


def parse_date(date_value):
    if not date_value:
        return date.today()
    try:
        return datetime.strptime(str(date_value), "%Y-%m-%d").date()
    except ValueError:
        try:
            return datetime.fromisoformat(str(date_value)).date()
        except ValueError:
            return date.today()


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

summary, summary_error = fetch_summary()
transactions, tx_error = fetch_transactions(limit=200)
corrections, corr_error = fetch_corrections(limit=25)

df = pd.DataFrame(transactions) if transactions else pd.DataFrame()

search_text = ""
selected_category = "All"
only_anomalies = False
start_date = None
end_date = None

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
                st.cache_data.clear()
                st.rerun()

    st.divider()
    st.header("🔎 Filter Transactions")

    search_text = st.text_input("Search description", placeholder="Search by merchant or note")
    only_anomalies = st.checkbox("Show only anomalies", value=False)

    if not df.empty and "category" in df.columns:
        category_list = sorted([c for c in df["category"].dropna().astype(str).unique().tolist() if c.strip()])
        category_options = ["All"] + category_list
        selected_category = st.selectbox("Category", category_options, index=0)
    else:
        st.selectbox("Category", ["All"], index=0)

    if not df.empty and "date" in df.columns:
        temp_dates = pd.to_datetime(df["date"], errors="coerce").dropna().dt.date
        if not temp_dates.empty:
            min_date = temp_dates.min()
            max_date = temp_dates.max()
            date_range = st.date_input("Date range", value=(min_date, max_date), min_value=min_date, max_value=max_date)
            if isinstance(date_range, tuple) and len(date_range) == 2:
                start_date, end_date = date_range
            else:
                start_date = end_date = date_range


if not df.empty:
    if "date" in df.columns:
        df["date"] = pd.to_datetime(df["date"], errors="coerce").dt.date

    if search_text.strip():
        df = df[df["description"].astype(str).str.contains(search_text.strip(), case=False, na=False)]

    if selected_category != "All":
        df = df[df["category"].astype(str) == selected_category]

    if only_anomalies and "is_anomaly" in df.columns:
        df = df[df["is_anomaly"] == 1]

    if start_date and end_date and "date" in df.columns:
        df = df[(df["date"] >= start_date) & (df["date"] <= end_date)]

st.subheader("Live Dashboard")

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

if not df.empty:
    st.write(f"Filtered transactions: **{len(df)}**")
    st.write(f"Filtered total: **${df['amount'].sum():,.2f}**")

tab1, tab2, tab3, tab4 = st.tabs(["Transactions", "Category Breakdown", "Manage Transactions", "Teach AI"])

with tab1:
    st.subheader("Recent Transactions")
    if tx_error:
        st.error(f"Could not load transactions: {tx_error}")
    elif not df.empty:
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

with tab3:
    st.subheader("Edit or Delete a Transaction")

    if df.empty:
        st.info("No transactions available to edit or delete.")
    else:
        options = {
            f"ID {row['id']} | {row['date']} | {row['description']} | ${row['amount']:.2f} | {row['category']}": row
            for _, row in df.iterrows()
        }

        selected_label = st.selectbox("Select a transaction", list(options.keys()))
        selected = options[selected_label]

        current_id = int(selected["id"])
        current_date = parse_date(selected.get("date"))
        current_description = str(selected.get("description", ""))
        current_amount = float(selected.get("amount", 0.0))
        current_category = str(selected.get("category", ""))

        with st.form("edit_transaction_form"):
            edit_date = st.date_input("Date", value=current_date)
            edit_description = st.text_input("Description", value=current_description)
            edit_amount = st.number_input(
                "Amount",
                min_value=0.01,
                value=current_amount if current_amount > 0 else 0.01,
                step=0.01,
                format="%.2f",
            )
            edit_category = st.text_input("Category", value=current_category)
            save_changes = st.form_submit_button("Save Changes")

        if save_changes:
            payload = {
                "date": str(edit_date),
                "description": edit_description.strip(),
                "amount": edit_amount,
                "category": edit_category.strip(),
            }

            if not payload["description"]:
                st.error("Description cannot be empty.")
            elif not payload["category"]:
                st.error("Category cannot be empty.")
            else:
                result, error = update_transaction(current_id, payload)
                if error:
                    st.error(f"Update failed: {error}")
                else:
                    st.success("Transaction updated successfully.")
                    st.cache_data.clear()
                    st.rerun()

        st.write("### Delete Transaction")
        delete_confirm = st.checkbox("I want to delete this transaction")
        if delete_confirm:
            if st.button("Delete Now", type="primary"):
                result, error = delete_transaction(current_id)
                if error:
                    st.error(f"Delete failed: {error}")
                else:
                    st.success("Transaction deleted successfully.")
                    st.cache_data.clear()
                    st.rerun()

with tab4:
    st.subheader("Teach the AI")

    if df.empty:
        st.info("No transactions available to teach yet.")
    else:
        options = {
            f"ID {row['id']} | {row['date']} | {row['description']} | ${row['amount']:.2f} | {row['category']}": row
            for _, row in df.iterrows()
        }

        selected_label = st.selectbox("Select a transaction to correct", list(options.keys()), key="teach_ai_select")
        selected = options[selected_label]

        tx_id = int(selected["id"])
        current_predicted = str(selected.get("category", ""))

        st.info(f"Current AI guess: {current_predicted}")

        with st.form("teach_ai_form"):
            corrected_category = st.text_input("Correct Category", value=current_predicted)
            correction_notes = st.text_area("Notes (optional)", placeholder="Why is this correction needed?")
            save_correction = st.form_submit_button("Save Correction")

        if save_correction:
            if not corrected_category.strip():
                st.error("Corrected category cannot be empty.")
            else:
                result, error = submit_correction(tx_id, corrected_category, correction_notes)
                if error:
                    st.error(f"Could not save correction: {error}")
                else:
                    st.success("Correction saved. The model now has a better clue what it is doing.")
                    st.cache_data.clear()
                    st.rerun()

    st.write("### Recent Corrections")
    if corr_error:
        st.error(f"Could not load corrections: {corr_error}")
    elif corrections:
        corr_df = pd.DataFrame(corrections)
        display_cols = [
            "id",
            "transaction_id",
            "original_description",
            "predicted_category",
            "corrected_category",
            "notes",
            "created_at",
        ]
        existing_cols = [c for c in display_cols if c in corr_df.columns]
        st.dataframe(corr_df[existing_cols], use_container_width=True, hide_index=True)
    else:
        st.info("No corrections saved yet.")