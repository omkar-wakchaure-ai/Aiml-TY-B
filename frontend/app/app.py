import streamlit as st
import sys
import os

# Add backend directory to python path so it can find your agents and tasks
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.insert(0, backend_path)

# Import your backend execution function
from main import run_tracker

# Page Configuration
st.set_page_config(
    page_title="AI Research & Competitor Tracker",
    page_icon="🚀",
    layout="wide"
)

# App Header
st.title("🚀 AI-Powered Research & Competitor Tracker")
st.markdown("Deploy your autonomous **Data Scout** and **Senior Intelligence Analyst** agents to research any topic or competitor live on the web.")

# Sidebar Inputs for User Customization
st.sidebar.header("🎯 Target Configuration")
topic_input = st.sidebar.text_input("Research Topic", value="Solid State Battery")
competitor_input = st.sidebar.text_input("Competitor Name", value="Competitor X")

# Launch Button
if st.sidebar.button("🚀 Launch Agent Fleet", type="primary"):
    if not topic_input or not competitor_input:
        st.warning("Please enter both a topic and a competitor name.")
    else:
        with st.spinner(f"🤖 Agents are actively researching **{competitor_input}** in **{topic_input}**... Please wait..."):
            try:
                # Call your backend multi-agent workflow
                report = run_tracker(topic=topic_input, competitor=competitor_input)
                
                # Display Success and Final Report
                st.success("Intelligence gathering and analysis complete!")
                st.markdown("---")
                st.subheader("📊 Final Intelligence Report")
                st.markdown(report)
                
            except Exception as e:
                st.error(f"An error occurred while running the agents: {e}")
else:
    st.info("👈 Configure your topic and competitor in the sidebar, then click **Launch Agent Fleet** to begin!")