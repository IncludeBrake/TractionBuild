#!/usr/bin/env python3
"""
Enhanced Chat UI for ZeroToShip
Integrates with API and WebSocket events for real-time project updates
"""

import streamlit as st
import asyncio
import json
import websockets
import requests
from datetime import datetime
from typing import Dict, Any, Generator
import threading
import queue

# Configuration
API_BASE = "http://localhost:8000"
WS_BASE = "ws://localhost:8000"

class ProjectManager:
    def __init__(self):
        self.current_project_id = None
        self.event_queue = queue.Queue()
        self.is_streaming = False
    
    def create_project(self, name: str, description: str, hypothesis: str, target_avatars: list) -> str:
        """Create a new project via API."""
        project_data = {
            "name": name,
            "description": description,
            "hypothesis": hypothesis,
            "target_avatars": target_avatars,
            "workflow": "validation_and_launch"
        }
        
        try:
            response = requests.post(f"{API_BASE}/api/v1/projects", json=project_data)
            response.raise_for_status()
            result = response.json()
            return result["project_id"]
        except Exception as e:
            st.error(f"Failed to create project: {e}")
            return None
    
    def get_project_status(self, project_id: str) -> Dict[str, Any]:
        """Get project status via API."""
        try:
            response = requests.get(f"{API_BASE}/api/v1/projects/{project_id}/status")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to get project status: {e}")
            return None
    
    def get_project(self, project_id: str) -> Dict[str, Any]:
        """Get full project data via API."""
        try:
            response = requests.get(f"{API_BASE}/api/v1/projects/{project_id}")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            st.error(f"Failed to get project: {e}")
            return None

class WebSocketStreamer:
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.event_queue = queue.Queue()
        self.is_running = False
    
    async def stream_events(self):
        """Stream events from WebSocket."""
        uri = f"{WS_BASE}/ws/projects/{self.project_id}"
        try:
            async with websockets.connect(uri) as ws:
                self.is_running = True
                async for msg in ws:
                    event = json.loads(msg)
                    self.event_queue.put(event)
        except Exception as e:
            st.error(f"WebSocket error: {e}")
        finally:
            self.is_running = False
    
    def start_streaming(self):
        """Start WebSocket streaming in background thread."""
        def run_async():
            asyncio.run(self.stream_events())
        
        thread = threading.Thread(target=run_async, daemon=True)
        thread.start()
    
    def get_event(self, timeout=1):
        """Get next event from queue."""
        try:
            return self.event_queue.get(timeout=timeout)
        except queue.Empty:
            return None

def render_validation_result(artifact: Dict[str, Any]):
    """Render validation results."""
    st.subheader("🎯 Validation Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Go Recommendation", "✅ GO" if artifact.get("go_recommendation") else "❌ PIVOT")
        st.metric("Confidence", f"{artifact.get('confidence', 0) * 100:.1f}%")
    
    with col2:
        st.write("**MVP Features:**")
        for feature in artifact.get("mvp_features", []):
            st.write(f"• {feature}")
        
        st.write("**Risks:**")
        for risk in artifact.get("risks", []):
            st.write(f"• {risk}")

def render_advisory_result(artifact: Dict[str, Any]):
    """Render advisory results."""
    st.subheader("📋 Advisory Decision")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.metric("Approved", "✅ YES" if artifact.get("approved") else "❌ NO")
        st.write("**Rationale:**")
        st.write(artifact.get("rationale", "No rationale provided"))
    
    with col2:
        st.write("**Must-Haves:**")
        for item in artifact.get("must_haves", []):
            st.write(f"• {item}")
        
        st.write("**Cut Scope:**")
        for item in artifact.get("cut_scope", []):
            st.write(f"• {item}")
        
        st.write("**KPIs:**")
        for kpi, value in artifact.get("kpis", {}).items():
            st.write(f"• {kpi}: {value}")

def main():
    st.set_page_config(
        page_title="ZeroToShip Chat",
        page_icon="🚀",
        layout="wide"
    )
    
    st.title("🚀 ZeroToShip AI Team")
    st.markdown("Chat with your AI team to validate and plan your next project.")
    
    # Initialize session state
    if "project_manager" not in st.session_state:
        st.session_state.project_manager = ProjectManager()
    if "streamer" not in st.session_state:
        st.session_state.streamer = None
    if "project_created" not in st.session_state:
        st.session_state.project_created = False
    if "events" not in st.session_state:
        st.session_state.events = []
    
    project_manager = st.session_state.project_manager
    
    # Sidebar for project creation
    with st.sidebar:
        st.header("📝 Create New Project")
        
        with st.form("project_form"):
            name = st.text_input("Project Name", value=f"Project-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
            description = st.text_area("Description", placeholder="Describe your project idea...")
            hypothesis = st.text_area("Hypothesis", placeholder="What problem are you solving?")
            target_avatars = st.multiselect(
                "Target Avatars",
                ["startup_entrepreneur", "sme", "investor_incubator", "corporate_innovation_lab"],
                default=["startup_entrepreneur"]
            )
            
            submitted = st.form_submit_button("🚀 Launch Project")
            
            if submitted and name and description and hypothesis:
                with st.spinner("Creating project..."):
                    project_id = project_manager.create_project(name, description, hypothesis, target_avatars)
                    
                    if project_id:
                        project_manager.current_project_id = project_id
                        st.session_state.project_created = True
                        st.session_state.streamer = WebSocketStreamer(project_id)
                        st.session_state.streamer.start_streaming()
                        st.session_state.events = []
                        st.success(f"Project created! ID: {project_id}")
                        st.rerun()
    
    # Main content area
    if st.session_state.project_created and project_manager.current_project_id:
        project_id = project_manager.current_project_id
        
        # Project info
        st.header(f"📊 Project: {project_id[:8]}...")
        
        # Status and progress
        status = project_manager.get_project_status(project_id)
        if status:
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Status", status.get("state", "Unknown"))
            with col2:
                st.metric("Progress", f"{status.get('progress', 0):.1f}%")
            with col3:
                st.metric("Current Step", status.get("current_step", "Unknown"))
        
        # Real-time events
        st.subheader("🔄 Real-time Updates")
        
        # Check for new events
        if st.session_state.streamer:
            event = st.session_state.streamer.get_event()
            if event:
                st.session_state.events.append(event)
                st.rerun()
        
        # Display events
        if st.session_state.events:
            for i, event in enumerate(st.session_state.events):
                with st.expander(f"Event {i+1}: {event.get('type', 'unknown')}", expanded=True):
                    if event.get("type") == "step_complete":
                        agent = event.get("agent")
                        artifact = event.get("artifact", {})
                        
                        if agent == "validator":
                            render_validation_result(artifact)
                        elif agent == "advisory":
                            render_advisory_result(artifact)
                        else:
                            st.json(artifact)
                    
                    elif event.get("type") == "status_update":
                        st.success(f"✅ Project {event.get('state', 'updated')}")
                    
                    elif event.get("type") == "error":
                        st.error(f"❌ Error: {event.get('error', 'Unknown error')}")
        
        # Final results
        if status and status.get("state") == "COMPLETED":
            st.subheader("🎉 Project Complete!")
            
            project_data = project_manager.get_project(project_id)
            if project_data and project_data.get("artifacts"):
                artifacts = project_data["artifacts"]
                
                if "validator" in artifacts:
                    render_validation_result(artifacts["validator"])
                
                if "advisory" in artifacts:
                    render_advisory_result(artifacts["advisory"])
                
                # Next steps
                st.subheader("🚀 Next Steps")
                st.write("1. **Review the validation and advisory results above**")
                st.write("2. **Decide: Go or Pivot based on the recommendations**")
                st.write("3. **If GO: Proceed to execution planning**")
                st.write("4. **If PIVOT: Refine your hypothesis and try again**")
                
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("✅ Proceed with GO", type="primary"):
                        st.info("Execution planning coming soon...")
                
                with col2:
                    if st.button("🔄 Start New Project"):
                        st.session_state.project_created = False
                        st.session_state.streamer = None
                        st.session_state.events = []
                        st.rerun()
    
    else:
        # Welcome screen
        st.markdown("""
        ## Welcome to ZeroToShip! 🚀
        
        **How it works:**
        1. **Create a project** using the form in the sidebar
        2. **Watch real-time updates** as our AI team validates your idea
        3. **Get actionable insights** from validation and advisory results
        4. **Make informed decisions** about whether to proceed or pivot
        
        **Your AI Team:**
        - 🎯 **Validator**: Analyzes market fit and validates your hypothesis
        - 📋 **Advisory Board**: Provides go/no-go decision with strategic recommendations
        
        Ready to launch your next project? Use the sidebar to get started!
        """)
        
        # Example project
        st.subheader("💡 Example Project")
        st.markdown("""
        **Name**: AI-Powered Task Manager for Solopreneurs
        
        **Description**: A smart task management tool that uses AI to prioritize, categorize, and schedule tasks for solo entrepreneurs.
        
        **Hypothesis**: Solopreneurs struggle with task prioritization and time management, and would pay for an AI tool that helps them focus on high-impact activities.
        
        **Target Avatars**: startup_entrepreneur, sme
        """)

if __name__ == "__main__":
    main()
