import streamlit as st
from streamlit_chat import message
import asyncio
# Adjust imports to your final project structure
from src.zerotoship.crews.advisory_board_crew import AdvisoryBoardCrew
from src.zerotoship.database.neo4j_lock_manager import Neo4jLockManager

st.set_page_config(page_title="ZeroToShip Advisory Board", layout="wide")
st.title("🚀 ZeroToShip Advisory Board")

# Initialize session state for chat history and lock manager
if 'messages' not in st.session_state:
    st.session_state.messages = [{"role": "assistant", "content": "Welcome! What's your big idea?"}]
if 'lock_manager' not in st.session_state:
    st.session_state.lock_manager = Neo4jLockManager()
if 'validated_mission' not in st.session_state:
    st.session_state.validated_mission = None

# Display chat messages
for msg in st.session_state.messages:
    message(msg["content"], is_user=msg["role"] == "user")

# User input
if prompt := st.chat_input("Enter your idea here..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    message(prompt, is_user=True)
    
    with st.spinner("The Advisory Board is deliberating..."):
        # Run the Advisory Board Crew
        crew = AdvisoryBoardCrew(project_data={"idea": prompt})
        result = asyncio.run(crew.run_async())
        validated_mission = result.get('advisoryboard', {}).get('output', "Error: Could not process idea.")
        st.session_state.validated_mission = validated_mission
        
        # Check for niche lock
        is_locked, conflicting_idea = asyncio.run(st.session_state.lock_manager.check_lock(validated_mission))
        
        if is_locked:
            response_text = f"🚨 This niche seems to be locked by a similar idea: '{conflicting_idea}'. Let's pivot slightly. How could we make this even more unique?"
        else:
            response_text = f"Okay, this is a strong direction! **Validated Mission:** {validated_mission}"
            
        st.session_state.messages.append({"role": "assistant", "content": response_text})
        st.rerun()

# Button to lock the niche
if st.session_state.validated_mission:
    st.write("---")
    st.write(f"**Final Validated Mission:** {st.session_state.validated_mission}")
    if st.button("✅ Lock This Niche & Proceed"):
        with st.spinner("Securing your niche in the knowledge graph..."):
            asyncio.run(st.session_state.lock_manager.create_lock(st.session_state.validated_mission, "default_user"))
            st.success("Niche Locked! You have 3 months of exclusivity. Now, let's build.")
            st.balloons()
            st.session_state.validated_mission = None # Clear after locking