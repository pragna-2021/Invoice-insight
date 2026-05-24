import streamlit as st
import pandas as pd
from frontend.api_client import client
from frontend import ui

st.set_page_config(page_title="Dashboard - Invoice Insight", page_icon="📊", layout="wide")
ui.load_css()

st.title("📊 Dashboard")

if "token" not in st.session_state:
    st.warning("Please log in via the Auth page to view your dashboard.")
    st.stop()

st.header("Upload New Invoice")
uploaded_file = st.file_uploader("Choose an image (JPG/PNG) or PDF", type=["png", "jpg", "jpeg", "pdf"])

if uploaded_file is not None:
    if st.button("Process Invoice", type="primary"):
        with st.spinner("Processing your invoice using AI (OCR & Translation)..."):
            response = client.upload_invoice(uploaded_file)
            if response.status_code == 200:
                st.success("Invoice processed successfully!")
                data = response.json()
                st.json(data["data"])
            else:
                st.error(f"Error processing invoice: {response.text}")

st.divider()

st.header("Recent Invoices")
with st.spinner("Loading recent invoices..."):
    metrics_response = client.get_metrics()
    if metrics_response.status_code == 200:
        metrics = metrics_response.json()
        recent = metrics.get("recent_invoices", [])
        
        if not recent:
            st.info("No invoices found. Upload your first invoice above!")
        else:
            df = pd.DataFrame(recent)
            st.dataframe(
                df[["filename", "status", "success", "total_amount", "processing_time_ms", "created_at"]],
                use_container_width=True
            )
    else:
        st.error("Failed to load invoices. Is the backend running?")
