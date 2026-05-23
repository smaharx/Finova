import streamlit as st
import requests

st.set_page_config(page_title="SaaS Finance Tracker V2", layout="wide")

st.title("🛡️ Smart Finance Dashboard (V2.0)")
st.write("Connected to FastAPI Cloud Engine")

# Define the Backend URL (Update this if your port is different)
BACKEND_URL = "http://127.0.0.1:8000"

# Test the Connection
try:
    response = requests.get(f"{BACKEND_URL}/")
    if response.status_code == 200:
        st.success(f"✅ Backend Online: {response.json()['message']}")
except:
    st.error("❌ Backend Offline. Please start your Uvicorn server.")   