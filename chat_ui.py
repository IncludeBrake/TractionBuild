"""
Interactive Chat UI for ZeroToShip Advisory Board.
Provides a user-friendly interface for idea refinement.
"""

import streamlit as st
from streamlit_chat import message
import asyncio
import requests
import time
import json

# Page configuration
st.set_page_config(
    page_title="🚀 ZeroToShip Advisory Board",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        font-weight: bold;
        text-align: center;
        margin-bottom: 2rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .chat-container {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 20px;
        margin: 20px 0;
    }
    .stButton > button {
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 25px;
        padding: 10px 25px;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Header
st.markdown('<h1 class="main-header">🚀 ZeroToShip Advisory Board</h1>', unsafe_allow_html=True)

# Sidebar for configuration
with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API configuration
    api_url = st.text_input(
        "API URL",
        value="http://localhost:8000",
        help="URL of the ZeroToShip API"
    )
    
    # Workflow selection
    workflow_name = st.selectbox(
        "Workflow",
        ["advisory_board_workflow", "idea_validation_workflow", "full_pipeline_workflow"],
        help="Select the workflow to run"
    )
    
    # Polling interval
    poll_interval = st.slider(
        "Polling Interval (seconds)",
        min_value=1,
        max_value=10,
        value=2,
        help="How often to check task status"
    )
    
    st.divider()
    
    # Session management
    if st.button("🔄 Reset Session"):
        st.session_state.messages = [{"role": "assistant", "content": "Welcome! What's your big idea?"}]
        st.rerun()
    
    if st.button("📊 View Session Info"):
        st.json({
            "message_count": len(st.session_state.get("messages", [])),
            "api_url": api_url,
            "workflow": workflow_name
        })

# Initialize session state for chat history
if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! What's your big idea?"}]

# Main chat interface
st.markdown('<div class="chat-container">', unsafe_allow_html=True)

# Display chat messages
for i, msg in enumerate(st.session_state.messages):
    if msg["role"] == "user":
        message(msg["content"], is_user=True, key=f"user_{i}")
    else:
        message(msg["content"], is_user=False, key=f"assistant_{i}")

st.markdown('</div>', unsafe_allow_html=True)

# User input section
st.markdown("### 💡 Share Your Idea")
user_input = st.text_area(
    "Describe your idea in detail...",
    placeholder="e.g., I want to build an app that helps people...",
    height=100,
    help="Be as detailed as possible about your idea, target audience, and goals"
)

# Submit button
col1, col2, col3 = st.columns([1, 2, 1])
with col2:
    if st.button("🚀 Submit to Advisory Board", use_container_width=True):
        if user_input.strip():
            # Add user message to chat
            st.session_state.messages.append({"role": "user", "content": user_input})
            
            # Show processing status
            with st.spinner("🤔 The Advisory Board is deliberating..."):
                try:
                    # 1. Send the idea to the API to start the workflow
                    payload = {
                        "idea": user_input,
                        "workflow_name": workflow_name,
                        "user_context": {
                            "timestamp": time.time(),
                            "session_id": "chat_ui_session"
                        }
                    }
                    
                    response = requests.post(
                        f"{api_url}/run-workflow/",
                        json=payload,
                        timeout=30
                    )
                    
                    if response.status_code == 202:
                        task_info = response.json()
                        task_id = task_info['task_id']
                        
                        # Show task info
                        st.info(f"✅ Advisory session started. Task ID: {task_id}")
                        
                        # 2. Poll the task status endpoint until it's finished
                        status_url = f"{api_url}/task-status/{task_id}"
                        final_result = None
                        
                        # Create a progress bar
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                        
                        poll_count = 0
                        while True:
                            try:
                                status_response = requests.get(status_url, timeout=10)
                                if status_response.status_code == 200:
                                    status_data = status_response.json()
                                    poll_count += 1
                                    
                                    # Update progress
                                    progress = min(poll_count * 10, 90)  # Cap at 90% until complete
                                    progress_bar.progress(progress)
                                    
                                    if status_data['status'] == 'SUCCESS':
                                        final_result = status_data['result']
                                        progress_bar.progress(100)
                                        status_text.success("✅ Advisory Board session completed!")
                                        break
                                    elif status_data['status'] == 'FAILURE':
                                        st.error(f"❌ The advisory board session failed: {status_data.get('error', 'Unknown error')}")
                                        break
                                    elif status_data['status'] == 'PENDING':
                                        status_text.info("⏳ Advisory Board is analyzing your idea...")
                                    elif status_data['status'] == 'PROGRESS':
                                        status_text.info(f"🔄 {status_data.get('progress', 'Processing...')}")
                                    
                                else:
                                    st.error(f"Failed to get task status: {status_response.status_code}")
                                    break
                                    
                            except requests.exceptions.RequestException as e:
                                st.error(f"Network error while polling: {e}")
                                break
                                
                            time.sleep(poll_interval)
                        
                        # Process final result
                        if final_result:
                            try:
                                # Extract the advisory board output
                                advisory_output = final_result.get('advisoryboard', {})
                                mission_statement = advisory_output.get('mission_statement', 'Mission statement not available')
                                insights = advisory_output.get('insights', [])
                                recommendations = advisory_output.get('recommendations', [])
                                
                                # Format the response
                                formatted_response = f"""
**🎯 Your Refined Mission Statement:**
{mission_statement}

**💡 Key Insights:**
"""
                                for insight in insights:
                                    formatted_response += f"• {insight}\n"
                                
                                if recommendations:
                                    formatted_response += "\n**🚀 Recommendations:**\n"
                                    for rec in recommendations:
                                        formatted_response += f"• {rec}\n"
                                
                                # Add to chat
                                st.session_state.messages.append({"role": "assistant", "content": formatted_response})
                                st.rerun()
                                
                            except Exception as e:
                                st.error(f"Error processing result: {e}")
                                st.session_state.messages.append({
                                    "role": "assistant", 
                                    "content": "Sorry, there was an error processing the advisory board's response."
                                })
                                st.rerun()
                    else:
                        st.error(f"Failed to start advisory session: {response.status_code} - {response.text}")
                        st.session_state.messages.append({
                            "role": "assistant", 
                            "content": "Sorry, I couldn't start the advisory session. Please check your API configuration."
                        })
                        st.rerun()
                        
                except requests.exceptions.RequestException as e:
                    st.error(f"Network error: {e}")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "Sorry, I couldn't connect to the API. Please check your network connection and API URL."
                    })
                    st.rerun()
                except Exception as e:
                    st.error(f"Unexpected error: {e}")
                    st.session_state.messages.append({
                        "role": "assistant", 
                        "content": "Sorry, an unexpected error occurred. Please try again."
                    })
                    st.rerun()
        else:
            st.warning("Please enter your idea before submitting.")

# Footer
st.markdown("---")
st.markdown("""
<div style='text-align: center; color: #666;'>
    <p>🚀 ZeroToShip Advisory Board - Transform your ideas into validated missions</p>
    <p>Powered by AI agents and real-time market insights</p>
</div>
""", unsafe_allow_html=True)
