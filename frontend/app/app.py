import streamlit as st
import time

# 1. Page Configuration
st.set_page_config(
    page_title="Autonomous Competitor Tracker",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Initialize Session State to remember if the agents have run
if 'agents_run' not in st.session_state:
    st.session_state.agents_run = False
if 'target_topic' not in st.session_state:
    st.session_state.target_topic = ""
if 'competitor_name' not in st.session_state:
    st.session_state.competitor_name = ""

# 2. Inject Custom Cyber & AI Styled CSS
st.markdown("""
<style>
    .stApp { background-color: #0d1117; color: #c9d1d9; }
    
    .main-header {
        background: linear-gradient(135deg, #1f6feb 0%, #8957e5 50%, #da3633 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.6rem; font-weight: 800;
        margin-bottom: 0px;
    }

    .pulse-dot {
        display: inline-block; width: 10px; height: 10px;
        border-radius: 50%; background: #238636;
        animation: pulse 1.6s infinite; margin-right: 8px;
    }
    @keyframes pulse {
        0% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(35, 134, 54, 0.7); }
        70% { transform: scale(1); box-shadow: 0 0 0 10px rgba(35, 134, 54, 0); }
        100% { transform: scale(0.95); box-shadow: 0 0 0 0 rgba(35, 134, 54, 0); }
    }

    .agent-badge {
        display: inline-block; padding: 6px 12px; border-radius: 20px;
        font-size: 0.85rem; font-weight: 600;
        background: rgba(88, 166, 255, 0.15); color: #58a6ff;
        border: 1px solid rgba(88, 166, 255, 0.3); margin-right: 10px;
    }
    
    /* CSS for the Insight Cards */
    .insight-card {
        background: #161b22;
        border: 1px solid #30363d;
        border-left: 4px solid #8957e5;
        border-radius: 8px;
        padding: 16px;
        margin-bottom: 16px;
    }
    .insight-title {
        color: #fff;
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 8px;
    }
    .insight-meta {
        font-size: 0.8rem;
        color: #8b949e;
        margin-bottom: 8px;
    }

    div.stButton > button:first-child {
        background: linear-gradient(90deg, #238636 0%, #2ea043 100%);
        color: white; border: none; font-weight: 700;
    }
</style>
""", unsafe_allow_html=True)

# 3. Header Section
st.markdown('<div class="main-header">🤖 Autonomous Research & Competitor Tracker</div>', unsafe_allow_html=True)
st.markdown('<div><span class="pulse-dot"></span><span style="color: #8b949e; font-size: 0.95rem;">System Active • Real-time Agentic Engine Online</span></div><br>', unsafe_allow_html=True)

# 4. Main Tabs Navigation
tab1, tab2, tab3 = st.tabs(["📊 Live Insights", "🚀 Run Workflow", "⚙️ Configurations"])

with tab2:
    st.markdown("### ⚡ Trigger Autonomous Tracking Pipeline")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            topic = st.text_input("🎯 Target Topic", value="Solid State Battery")
        with col2:
            competitor = st.text_input("🏢 Competitor Name", value="Competitor X")
            
        col3, col4 = st.columns(2)
        with col3:
            search_depth = st.selectbox("🔍 Search Depth", ["Standard (Fast)", "Deep Agentic Scan"])
        with col4:
            st.write("<br>", unsafe_allow_html=True)
            run_btn = st.button("🚀 Launch Agent Fleet", use_container_width=True)

    if run_btn:
        st.write("---")
        st.markdown('''
            <span class="agent-badge">🕵️ Scout: ACTIVE</span>
            <span class="agent-badge">🧠 Analyst: WAITING</span>
        ''', unsafe_allow_html=True)
        
        with st.status("🛸 Agents deploying across networks...", expanded=True) as status:
            time.sleep(1)
            st.write(f"🕵️ **Scout:** Searching ArXiv API for {topic}...")
            time.sleep(1)
            st.write(f"🌐 **Scout:** Crawling patents for {competitor}...")
            time.sleep(1)
            st.write("🧠 **Analyst:** Running semantic comparison...")
            time.sleep(1)
            status.update(label="✅ Agent Workflow Completed Successfully!", state="complete", expanded=False)

        st.success("Analysis Complete! Check the 'Live Insights' tab for results.")
        
        # Save state so Tab 1 knows to show data
        st.session_state.agents_run = True
        st.session_state.target_topic = topic
        st.session_state.competitor_name = competitor

with tab1:
    st.markdown("### 📊 Real-Time Insight Feed")
    
    # If the user hasn't clicked run yet, show the empty message
    if not st.session_state.agents_run:
        st.info("No recent executions in this session. Run the workflow tab to populate live data.")
    
    # If the agents HAVE run, show the data!
    else:
        st.markdown(f"Displaying freshest insights for **{st.session_state.competitor_name}** in the field of **{st.session_state.target_topic}**.")
        
        # Insight Card 1 (Dummy Data)
        st.markdown(f'''
        <div class="insight-card" style="border-left-color: #da3633;">
            <div class="insight-title">🚨 High-Impact Patent Filed</div>
            <div class="insight-meta">Source: USPTO API | Impact Score: 9/10 | Time: 2 mins ago</div>
            <div>{st.session_state.competitor_name} recently filed patent #US202612345 relating to {st.session_state.target_topic} thermal management. This indicates a shift away from traditional liquid cooling architectures.</div>
        </div>
        ''', unsafe_allow_html=True)

        # Insight Card 2 (Dummy Data)
        st.markdown(f'''
        <div class="insight-card" style="border-left-color: #1f6feb;">
            <div class="insight-title">📄 ArXiv Publication Trend Detected</div>
            <div class="insight-meta">Source: Semantic Scholar | Impact Score: 6/10 | Time: 1 hour ago</div>
            <div>Scout Agent detected 4 new papers published today by researchers formerly employed by {st.session_state.competitor_name}, all focusing on material degradation in {st.session_state.target_topic} environments.</div>
        </div>
        ''', unsafe_allow_html=True)

with tab3:
    st.markdown("### ⚙️ System Settings")
    st.text_input("Slack / Teams Webhook URL", type="password")
    st.slider("Minimum Alert Impact Score (1-10)", 1, 10, 7)
    if st.button("Save Configurations"):
        st.toast("Settings saved successfully!")