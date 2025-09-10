"""
Idea Submission and SMM Analysis Page for TractionBuild.
"""

import streamlit as st
import requests
import time
from typing import Dict, Any, Optional

# Configuration
API_BASE = "http://localhost:8000"

def submit_idea_to_api(idea_text: str) -> Optional[Dict[str, Any]]:
    """Submit idea to TractionBuild API for SMM analysis."""
    try:
        response = requests.post(
            f"{API_BASE}/ideas/ingest",
            json={"text": idea_text},
            timeout=60  # SMM analysis can take time
        )

        if response.status_code == 200:
            return response.json()
        else:
            st.error(f"API Error: {response.status_code} - {response.text}")
            return None

    except requests.exceptions.Timeout:
        st.error("Request timed out. The analysis might still be running.")
        return None
    except requests.exceptions.ConnectionError:
        st.error("Could not connect to TractionBuild API. Is the server running?")
        return None
    except Exception as e:
        st.error(f"Unexpected error: {str(e)}")
        return None

def get_smm_status(project_id: str) -> Optional[Dict[str, Any]]:
    """Get SMM analysis status for a project."""
    try:
        response = requests.get(f"{API_BASE}/ideas/status/{project_id}", timeout=10)

        if response.status_code == 200:
            return response.json()
        else:
            return None

    except Exception:
        return None

def display_market_analysis(analysis_data: Dict[str, Any]):
    """Display the market analysis results."""
    st.markdown("## 🎯 Market Analysis Results")

    # Summary
    if "summary" in analysis_data:
        st.success(analysis_data["summary"])

    # Performance metrics
    col1, col2, col3 = st.columns(3)

    with col1:
        if "stats" in analysis_data and "tokens_in" in analysis_data["stats"]:
            st.metric("Tokens Used", analysis_data["stats"]["tokens_in"])

    with col2:
        if "stats" in analysis_data and "duration_ms" in analysis_data["stats"]:
            duration_sec = analysis_data["stats"]["duration_ms"] / 1000
            st.metric("Analysis Time", ".1f")

    with col3:
        if "cache_hit" in analysis_data.get("stats", {}):
            cache_status = "✅ Cache Hit" if analysis_data["stats"]["cache_hit"] else "🔄 Fresh Analysis"
            st.metric("Cache Status", cache_status)

    # Placeholder for actual artifact display
    # In a full implementation, this would fetch artifacts via API
    st.markdown("### 📊 Analysis Artifacts")

    # Mock display of analysis sections
    tabs = st.tabs(["🎯 Avatars", "🏢 Competitors", "📢 Channels", "🎣 Hooks"])

    with tabs[0]:
        st.markdown("""
        **Identified Target Customer Segments:**
        - **Tech-Savvy Professional**: Needs workflow automation
        - **Small Business Owner**: Requires cost-effective solutions
        - **Enterprise Manager**: Seeks scalable enterprise solutions
        """)

    with tabs[1]:
        st.markdown("""
        **Competitive Landscape:**
        - **Legacy Solutions**: High cost, complex interfaces
        - **Simple Tools**: Limited features, good UX
        - **Market Gap**: Opportunity for comprehensive yet simple solution
        """)

    with tabs[2]:
        st.markdown("""
        **Recommended Channels:**
        - **LinkedIn**: Enterprise decision-makers
        - **Product Hunt**: Early adopters and enthusiasts
        - **Content Marketing**: Educational resources and guides
        """)

    with tabs[3]:
        st.markdown("""
        **Marketing Hooks:**
        - **Problem-Solution**: "Stop wasting 4 hours daily on repetitive tasks"
        - **Aspiration**: "Focus on what matters most while tools handle the rest"
        - **Social Proof**: "Join 10,000+ professionals who've transformed productivity"
        """)

def main():
    """Main Streamlit page for idea submission and SMM analysis."""
    st.title("🚀 Idea Submission & Market Analysis")
    st.markdown("""
    Submit your business idea and let our Synthetic Marketing Machine (SMM) generate
    comprehensive market analysis including customer avatars, competitors, marketing channels, and hooks.
    """)

    # Initialize session state
    if "project_id" not in st.session_state:
        st.session_state.project_id = None
    if "analysis_complete" not in st.session_state:
        st.session_state.analysis_complete = False
    if "analysis_data" not in st.session_state:
        st.session_state.analysis_data = None

    # Idea input section
    st.markdown("## 💡 Submit Your Idea")

    with st.form("idea_form"):
        idea_text = st.text_area(
            "Describe your business idea",
            placeholder="e.g., A task management app that uses AI to prioritize work and automate repetitive tasks...",
            height=100,
            help="Be specific about the problem you're solving and your target users"
        )

        submitted = st.form_submit_button("🚀 Analyze Idea", type="primary")

        if submitted:
            if not idea_text.strip():
                st.error("Please enter your idea before submitting.")
                return

            if len(idea_text.strip()) < 10:
                st.error("Please provide more detail (at least 10 characters).")
                return

            # Submit idea and start analysis
            with st.spinner("🤖 Running Synthetic Marketing Machine analysis..."):
                result = submit_idea_to_api(idea_text.strip())

                if result:
                    st.session_state.project_id = result["project_id"]
                    st.session_state.analysis_complete = True
                    st.session_state.analysis_data = result

                    st.success("✅ Idea submitted successfully!")
                    st.balloons()

                    # Display initial results
                    st.markdown(f"**Project ID:** `{result['project_id']}`")
                    st.markdown(f"**Status:** {result['message']}")

                    if result.get("cache_hit"):
                        st.info("🎯 This analysis was served from cache for faster results!")

                    # Show analysis results
                    display_market_analysis(result)

                else:
                    st.error("Failed to submit idea. Please try again.")

    # Status checking section (for ongoing analysis)
    if st.session_state.project_id and not st.session_state.analysis_complete:
        st.markdown("## 📊 Analysis Status")

        if st.button("🔄 Check Status"):
            with st.spinner("Checking analysis status..."):
                status = get_smm_status(st.session_state.project_id)

                if status:
                    if status["status"] == "completed":
                        st.session_state.analysis_complete = True
                        st.success("🎉 Analysis completed!")
                        display_market_analysis(status)
                    else:
                        st.info("⏳ Analysis still in progress...")
                        time.sleep(2)  # Brief pause before re-checking
                        st.rerun()
                else:
                    st.warning("Could not check status. Analysis might still be running.")

    # Results display section
    if st.session_state.analysis_complete and st.session_state.analysis_data:
        st.markdown("---")
        display_market_analysis(st.session_state.analysis_data)

    # Footer
    st.markdown("---")
    st.markdown("""
    **About Synthetic Marketing Machine (SMM):**
    - 🤖 AI-powered market analysis
    - 🎯 Customer avatar generation
    - 🏢 Competitive intelligence
    - 📢 Channel strategy optimization
    - 🎣 Marketing hook creation
    - ⚡ Semantic caching for performance
    - 🛡️ Anti-hallucination guardrails
    """)

if __name__ == "__main__":
    main()
