#!/usr/bin/env python3
"""
tractionbuild Observability Dashboard
==================================

A real-time dashboard for monitoring tractionbuild performance, quality, and costs.
"""

import streamlit as st
import requests
import json
import time
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import pandas as pd
import numpy as np

# Configure Streamlit page
st.set_page_config(
    page_title="tractionbuild Dashboard",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API configuration
API_BASE_URL = "http://localhost:8000"

def get_api_data(endpoint):
    """Get data from the tractionbuild API."""
    try:
        response = requests.get(f"{API_BASE_URL}{endpoint}", timeout=5)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        st.error(f"Error fetching data from {endpoint}: {e}")
        return None

def create_metric_card(title, value, unit="", color="blue"):
    """Create a metric card."""
    st.metric(
        label=title,
        value=f"{value:.2f}{unit}",
        delta=None
    )

def create_gauge_chart(value, title, min_val=0, max_val=1):
    """Create a gauge chart."""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=value,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': title},
        delta={'reference': 0.8},
        gauge={
            'axis': {'range': [min_val, max_val]},
            'bar': {'color': "darkblue"},
            'steps': [
                {'range': [min_val, 0.6], 'color': "lightgray"},
                {'range': [0.6, 0.8], 'color': "yellow"},
                {'range': [0.8, max_val], 'color': "green"}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 0.9
            }
        }
    ))
    fig.update_layout(height=300)
    return fig

def main():
    """Main dashboard function."""
    
    # Header
    st.title("🚀 tractionbuild Observability Dashboard")
    st.markdown("Real-time monitoring of AI-powered product development")
    
    # Sidebar
    st.sidebar.title("Dashboard Controls")
    auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)
    refresh_interval = st.sidebar.slider("Refresh interval (seconds)", 5, 60, 30)
    
    if auto_refresh:
        time.sleep(1)  # Small delay for demo purposes
    
    # Get dashboard data
    overview_data = get_api_data("/dashboard/overview")
    
    if overview_data is None:
        st.error("Unable to connect to tractionbuild API. Please ensure the API server is running.")
        return
    
    # Main dashboard layout
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        health_score = overview_data.get("health_score", 0.0)
        create_metric_card("System Health", health_score, "", "green" if health_score > 0.8 else "orange" if health_score > 0.6 else "red")
    
    with col2:
        metrics = overview_data.get("metrics", {})
        quality_score = metrics.get("quality_score", 0.0)
        create_metric_card("Quality Score", quality_score, "", "green" if quality_score > 0.8 else "orange")
    
    with col3:
        error_rate = metrics.get("error_rate", 0.0)
        create_metric_card("Error Rate", error_rate, "%", "red" if error_rate > 0.1 else "green")
    
    with col4:
        time_to_value = metrics.get("time_to_value", 0.0)
        create_metric_card("Time to Value", time_to_value, " min", "green" if time_to_value < 120 else "orange")
    
    # Charts section
    st.subheader("📊 Performance Metrics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Quality gauge
        quality_score = metrics.get("quality_score", 0.0)
        st.plotly_chart(create_gauge_chart(quality_score, "Quality Score"), use_container_width=True)
    
    with col2:
        # Cost metrics
        cost_per_1k = metrics.get("cost_per_1k_tokens", 0.0)
        carbon_footprint = metrics.get("carbon_footprint", 0.0)
        
        cost_data = {
            "Metric": ["Cost per 1K Tokens", "Carbon Footprint"],
            "Value": [cost_per_1k, carbon_footprint],
            "Unit": ["$", "kg CO2"]
        }
        
        df_cost = pd.DataFrame(cost_data)
        fig_cost = px.bar(df_cost, x="Metric", y="Value", 
                         title="Cost & Sustainability Metrics",
                         color="Value",
                         color_continuous_scale="RdYlGn_r")
        st.plotly_chart(fig_cost, use_container_width=True)
    
    # Anomalies and Recommendations
    st.subheader("⚠️ Anomalies & Alerts")
    
    anomalies = overview_data.get("anomalies", [])
    recommendations = overview_data.get("recommendations", [])
    
    col1, col2 = st.columns(2)
    
    with col1:
        if anomalies:
            st.warning(f"Found {len(anomalies)} anomalies")
            for anomaly in anomalies:
                with st.expander(f"{anomaly.get('type', 'Unknown')} - {anomaly.get('severity', 'Unknown')}"):
                    st.write(f"**Description:** {anomaly.get('description', 'No description')}")
                    st.write(f"**Recommendation:** {anomaly.get('recommendation', 'No recommendation')}")
        else:
            st.success("No anomalies detected")
    
    with col2:
        if recommendations:
            st.info(f"Found {len(recommendations)} recommendations")
            for rec in recommendations:
                with st.expander(f"{rec.get('title', 'Unknown')} - {rec.get('priority', 'Unknown')}"):
                    st.write(f"**Description:** {rec.get('description', 'No description')}")
                    st.write("**Actions:**")
                    for action in rec.get('actions', []):
                        st.write(f"- {action}")
        else:
            st.success("No recommendations at this time")
    
    # Detailed metrics table
    st.subheader("📈 Detailed Metrics")
    
    if metrics:
        metrics_df = pd.DataFrame([
            {"Metric": "Quality Score", "Value": metrics.get("quality_score", 0.0), "Unit": ""},
            {"Metric": "Cost per 1K Tokens", "Value": metrics.get("cost_per_1k_tokens", 0.0), "Unit": "$"},
            {"Metric": "Drift Score", "Value": metrics.get("drift_score", 0.0), "Unit": ""},
            {"Metric": "Time to Value", "Value": metrics.get("time_to_value", 0.0), "Unit": "min"},
            {"Metric": "Error Rate", "Value": metrics.get("error_rate", 0.0), "Unit": "%"},
            {"Metric": "Carbon Footprint", "Value": metrics.get("carbon_footprint", 0.0), "Unit": "kg CO2"},
            {"Metric": "Compliance Score", "Value": metrics.get("compliance_score", 0.0), "Unit": ""}
        ])
        
        st.dataframe(metrics_df, use_container_width=True)
    
    # System status
    st.subheader("🔧 System Status")
    
    summary = overview_data.get("summary", {})
    system_status = summary.get("system_status", "unknown")
    
    if system_status == "healthy":
        st.success("🟢 System is healthy")
    elif system_status == "warning":
        st.warning("🟡 System has warnings")
    else:
        st.error("🔴 System has critical issues")
    
    # Footer
    st.markdown("---")
    st.markdown(f"*Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*")
    
    # Auto-refresh
    if auto_refresh:
        time.sleep(refresh_interval)
        st.experimental_rerun()

if __name__ == "__main__":
    main()
