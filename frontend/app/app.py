import streamlit as st
import sys
import os
import time

# Add backend directory to python path so it can find your agents and tasks
backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '../../backend'))
sys.path.insert(0, backend_path)

# Import your backend execution function
from main import run_tracker

# ==========================================
# PAGE CONFIGURATION
# ==========================================
st.set_page_config(
    page_title="AI Research & Competitor Tracker",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ==========================================
# CUSTOM CSS ANIMATIONS & STYLING
# ==========================================
st.markdown("""
    <style>
    /* Animated Gradient Title */
    .animated-title {
        background: linear-gradient(270deg, #FF4B4B, #FF8F00, #9C27B0, #3F51B5);
        background-size: 800% 800%;
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        animation: gradient-flow 6s ease infinite;
        font-size: 3.5rem;
        font-weight: 900;
        text-align: center;
        margin-bottom: 0px;
        padding-bottom: 0px;
    }
    
    @keyframes gradient-flow {
        0% { background-position: 0% 50%; }
        50% { background-position: 100% 50%; }
        100% { background-position: 0% 50%; }
    }

    /* Subtitle Styling */
    .subtitle {
        text-align: center;
        color: #A0AEC0;
        font-size: 1.2rem;
        margin-top: 10px;
        margin-bottom: 30px;
    }
    
    /* Custom Report Container */
    .report-container {
        background-color: #1E1E2E;
        padding: 30px;
        border-radius: 15px;
        border-left: 6px solid #FF4B4B;
        box-shadow: 0px 8px 16px rgba(0, 0, 0, 0.4);
        margin-top: 20px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# APP HEADER
# ==========================================
st.markdown('<div class="animated-title">🚀 AI Intelligence Fleet</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Deploy your autonomous Data Scout and Senior Intelligence Analyst agents.</div>', unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# SIDEBAR CONFIGURATION
# ==========================================
st.sidebar.image("https://cdn-icons-png.flaticon.com/512/8618/8618129.png", width=80)
st.sidebar.header("🎯 Target Configuration")
st.sidebar.markdown("Define your mission parameters below:")

topic_input = st.sidebar.text_input("📚 Research Topic", value="Solid State Battery")
competitor_input = st.sidebar.text_input("🏢 Competitor Name", value="Competitor X")

st.sidebar.markdown("---")

# ==========================================
# LAUNCH LOGIC
# ==========================================
if st.sidebar.button("🚀 Launch Agent Fleet", type="primary", use_container_width=True):
    if not topic_input or not competitor_input:
        st.sidebar.error("⚠️ Please enter both a topic and a competitor name.")
    else:
        # Using st.status for a cooler, animated multi-step loading UI
        with st.status("🛸 Booting up AI Agent Fleet...", expanded=True) as status:
            st.write("🔍 **Data Scout** is browsing the web for live data...")
            time.sleep(1) # Visual pause
            st.write("🧠 **Senior Intelligence Analyst** is synthesizing the findings...")
            
            try:
                # Call your backend multi-agent workflow
                report = run_tracker(topic=topic_input, competitor=competitor_input)
                
                # Update status to complete
                status.update(label="✅ Intelligence Gathering Complete!", state="complete", expanded=False)
                
                # Trigger celebration animation
                st.balloons()
                
                # Display Final Report inside a styled container
                st.markdown("### 📊 Executive Intelligence Briefing")
                
                # Render the markdown report
                st.markdown(f'<div class="report-container">{report}</div>', unsafe_allow_html=True)
                
            except Exception as e:
                status.update(label="❌ Mission Failed", state="error", expanded=True)
                st.error(f"An error occurred while running the agents: {e}")
else:
    # Empty state illustration
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.info("👈 Configure your mission parameters in the sidebar and click **Launch Agent Fleet** to begin data extraction!")