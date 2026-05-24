import streamlit as st
import pandas as pd
import plotly.express as px
from frontend.api_client import client
from frontend import ui

st.set_page_config(page_title="Analytics - Invoice Insight", page_icon="📈", layout="wide")
ui.load_css()

st.title("📈 Performance Analytics")

if "token" not in st.session_state:
    st.warning("Please log in via the Auth page to view your analytics.")
    st.stop()

with st.spinner("Loading analytics data..."):
    response = client.get_metrics()
    if response.status_code == 200:
        metrics = response.json()
        
        # Top-level KPIs
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Invoices Processed", metrics["total"])
        col2.metric("Success Rate", f"{metrics['success_rate']:.1f}%")
        col3.metric("Avg Processing Time", f"{metrics['avg_processing_time_ms']/1000:.2f}s")
        
        st.divider()
        
        recent = metrics.get("recent_invoices", [])
        if recent:
            df = pd.DataFrame(recent)
            
            # Chart 1: Processing Time Trend
            st.subheader("Processing Time Trend (ms)")
            fig_time = px.line(df, x="created_at", y="processing_time_ms", markers=True, title="Processing Time Over Time")
            st.plotly_chart(fig_time, use_container_width=True)
            
            # Chart 2: Success vs Failure
            st.subheader("Success vs Failure")
            success_counts = df['success'].value_counts().reset_index()
            success_counts.columns = ['Status', 'Count']
            success_counts['Status'] = success_counts['Status'].map({True: 'Success', False: 'Failed'})
            
            fig_pie = px.pie(success_counts, values='Count', names='Status', title="Invoice Processing Success Rate", color='Status', color_discrete_map={'Success': 'green', 'Failed': 'red'})
            st.plotly_chart(fig_pie, use_container_width=True)
            
        else:
            st.info("Not enough data to display charts. Please upload some invoices.")
            
    else:
        st.error("Failed to load analytics.")
