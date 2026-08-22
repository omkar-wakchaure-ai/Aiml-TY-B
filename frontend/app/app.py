import os
import sys
import time

import streamlit as st

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
sys.path.insert(0, backend_path)

from main import run_tracker
from workflows.crew_orchestrator import get_last_confidence, get_last_metrics, get_last_run_telemetry

st.set_page_config(page_title="AgentCore | Research Control", page_icon="AG", layout="wide", initial_sidebar_state="expanded")

st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;500;600&family=Space+Grotesk:wght@500;600;700&display=swap');
    :root { --ink:#f4f7ef; --muted:#69706a; --lime:#c6ff00; --line:#202520; --panel:#0e110f; --black:#050605; }
    .stApp { background: var(--black); color: var(--ink); }
    [data-testid="stHeader"] { background: transparent; }
    [data-testid="stSidebar"] { background:#080a08; border-right:1px solid var(--line); }
    [data-testid="stSidebar"] > div:first-child { padding-top:1rem; }
    .block-container { max-width:1500px; padding:1.3rem 3.5rem 3rem; }
    h1,h2,h3,p,button,label { font-family:'Space Grotesk',sans-serif; }
    .mono, .eyebrow, .metric-label, .nav-item, .telemetry { font-family:'IBM Plex Mono',monospace; }
    .topline { display:flex; justify-content:space-between; align-items:flex-start; border-bottom:1px solid var(--line); padding-bottom:1.1rem; animation:rise .5s ease both; }
    .brand-mark { display:inline-block; background:var(--lime); color:#050605; padding:3px 10px; font:600 9px 'IBM Plex Mono'; letter-spacing:.08em; }
    .hero-title { margin:.5rem 0 0; color:var(--ink); font-size:2.25rem; letter-spacing:-.04em; }
    .hero-sub { color:var(--muted); font:400 11px 'IBM Plex Mono'; letter-spacing:.04em; }
    .system-state { color:var(--lime); font:500 10px 'IBM Plex Mono'; text-align:right; }
    .system-state span { color:#f6b700; margin-left:18px; }
    .rail-brand { color:var(--ink); font:600 14px 'IBM Plex Mono'; letter-spacing:.14em; margin:1rem 0 2rem; }
    .rail-brand b { color:#050605; background:var(--lime); padding:5px; margin-right:8px; }
    .rail-section { color:#3f4840; font:500 9px 'IBM Plex Mono'; letter-spacing:.15em; margin:1.5rem 0 .6rem; }
    .nav-item { color:#727a72; padding:.55rem .2rem; font-size:11px; border-left:2px solid transparent; }
    .nav-item.active { color:var(--lime); border-left-color:var(--lime); padding-left:.7rem; background:rgba(198,255,0,.05); }
    .mission-box { border:1px solid var(--line); padding:1rem; margin-top:1rem; background:#0b0d0b; }
    .eyebrow, .metric-label { color:#566057; font-size:9px; letter-spacing:.12em; text-transform:uppercase; }
    .section-title { font:600 15px 'Space Grotesk'; margin:1.7rem 0 .7rem; }
    [data-testid="stMetric"] { background:var(--panel); border:1px solid var(--line); border-radius:0; padding:1rem; animation:rise .5s ease both; }
    [data-testid="stMetricValue"] { color:var(--ink); font-family:'IBM Plex Mono'; font-size:1.8rem; }
    [data-testid="stMetricLabel"] { color:#566057; font-family:'IBM Plex Mono'; font-size:9px; text-transform:uppercase; letter-spacing:.1em; }
    .panel { background:var(--panel); border:1px solid var(--line); padding:1rem 1.2rem; min-height:175px; }
    .panel-head { display:flex; justify-content:space-between; border-bottom:1px solid var(--line); padding-bottom:.7rem; margin-bottom:.8rem; font:500 10px 'IBM Plex Mono'; color:#798279; }
    .panel-head strong { color:var(--lime); font-weight:500; }
    .agent-row { display:flex; justify-content:space-between; align-items:center; padding:.65rem 0; border-bottom:1px solid #161b16; font:500 11px 'IBM Plex Mono'; }
    .agent-role { color:var(--ink); } .agent-status { color:var(--lime); font-size:9px; }
    .dot { display:inline-block; width:6px; height:6px; border-radius:50%; background:var(--lime); margin-right:8px; animation:pulse 1.8s infinite; }
    .report-card { background:#0d110e; border:1px solid #293329; border-left:3px solid var(--lime); padding:1.3rem 1.5rem; animation:rise .5s ease both; }
    .telemetry { background:#050705; border:1px solid var(--line); color:#9aaa9a; font-size:10px; line-height:1.8; padding:1rem; min-height:180px; }
    .telemetry::first-line { color:var(--lime); }
    .stButton > button { border-radius:0; font-family:'IBM Plex Mono'; font-size:10px; letter-spacing:.04em; }
    .stButton > button[kind="primary"] { background:var(--lime); color:#050605; border:0; }
    .stDownloadButton > button { border-radius:0; font-family:'IBM Plex Mono'; font-size:10px; }
    @keyframes rise { from {opacity:0; transform:translateY(9px)} to {opacity:1; transform:translateY(0)} }
    @keyframes pulse { 0%,100% { box-shadow:0 0 0 0 rgba(198,255,0,.25) } 50% { box-shadow:0 0 0 5px rgba(198,255,0,0) } }
    </style>
    """,
    unsafe_allow_html=True,
)

with st.sidebar:
    st.markdown('<div class="rail-brand"><b>AG</b> AGENTCORE</div>', unsafe_allow_html=True)
    st.markdown('<div class="rail-section">CONTROL SURFACE</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item active">01 &nbsp; Dashboard</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">02 &nbsp; Agents</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">03 &nbsp; Tool Calling</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">04 &nbsp; Memory</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">05 &nbsp; Orchestration</div>', unsafe_allow_html=True)
    st.markdown('<div class="nav-item">06 &nbsp; Test Lab</div>', unsafe_allow_html=True)
    st.markdown('<div class="rail-section">MISSION INPUT</div>', unsafe_allow_html=True)
    topic_input = st.text_input("Research domain", value="Electric Vehicles", label_visibility="collapsed", placeholder="Research domain")
    competitor_input = st.text_input("Target entity", value="Tesla", label_visibility="collapsed", placeholder="Target entity")
    st.markdown('<div class="rail-section">SAFETY</div>', unsafe_allow_html=True)
    abort_mission = st.toggle("Abort mission", value=False, help="Blocks a new run until switched off.")
    st.caption("Iteration cap: 2 per agent\nBudget guard: active\nCheckpointing: active")

metrics = get_last_metrics()
confidence = get_last_confidence()

st.markdown(
    '<div class="topline"><div><span class="brand-mark">AGENT FRAMEWORK</span><h1 class="hero-title">Autonomous Agent Framework</h1><div class="hero-sub">Dynamic Planning  ·  Multi-Agent Orchestration  ·  Adversarial Recovery</div></div><div class="system-state">● SYSTEM ACTIVE<br><span>● ADVERSARIAL TEST READY</span></div></div>',
    unsafe_allow_html=True,
)

st.markdown('<div class="section-title">Execution Overview</div>', unsafe_allow_html=True)
metric_cols = st.columns(4)
metric_cols[0].metric("Active agents", metrics["agents"], "+2")
metric_cols[1].metric("Tools called", metrics["tools"], f"{metrics['recoveries']} recovered")
metric_cols[2].metric("Checkpoints", metrics["checkpoints"], "saved")
metric_cols[3].metric("Confidence", f"{confidence}%", "uncertainty-aware")

left, right = st.columns([1.25, 1])
with left:
    st.markdown('<div class="section-title">Orchestration Graph</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="panel-head"><span>LIVE AGENT TOPOLOGY</span><strong>PARALLEL READY</strong></div><div class="agent-row"><span class="agent-role"><i class="dot"></i>Data Scout</span><span class="agent-status">TOOLS: WEB · ARXIV</span></div><div class="agent-row"><span class="agent-role"><i class="dot"></i>Evidence Verifier</span><span class="agent-status">ROUTE: CONDITIONAL</span></div><div class="agent-row"><span class="agent-role"><i class="dot"></i>Senior Analyst</span><span class="agent-status">STATE: SHARED</span></div><div class="agent-row"><span class="agent-role"><i class="dot"></i>Recovery Controller</span><span class="agent-status">FALLBACK: ARMED</span></div></div>', unsafe_allow_html=True)
with right:
    st.markdown('<div class="section-title">Framework Contract</div>', unsafe_allow_html=True)
    st.markdown('<div class="panel"><div class="panel-head"><span>TASK 5 COVERAGE</span><strong>7 / 7 ACTIVE</strong></div><div class="eyebrow">Planning</div><div class="eyebrow">Routing · Parallel execution · Shared state</div><div class="eyebrow">Checkpointing · Replanning · Memory reasoning</div><div class="eyebrow">Failure recovery · Conflict resolution</div></div>', unsafe_allow_html=True)

st.markdown('<div class="section-title">Mission Control</div>', unsafe_allow_html=True)
launch_col, status_col = st.columns([1, 2.3])
with launch_col:
    launch = st.button("EXECUTE AGENTIC WORKFLOW", type="primary", use_container_width=True, disabled=abort_mission)
with status_col:
    if abort_mission:
        st.warning("Mission abort is armed. Disable the safety switch to execute.")
    else:
        st.caption("Bounded execution · adaptive decomposition · checkpointed state")

if launch:
    if not topic_input.strip() or not competitor_input.strip():
        st.error("Mission parameters are required.")
    else:
        with st.status("PLANNING // dispatching agent fleet", expanded=True) as status:
            st.write("PLAN // decomposing objective into parallel evidence branches")
            st.write("ROUTE // conditional tool selection and fallback controls armed")
            try:
                report = run_tracker(topic=topic_input, competitor=competitor_input)
                status.update(label="COMPLETE // objective verified", state="complete", expanded=False)
                metrics = get_last_metrics()
                confidence = get_last_confidence()
                st.markdown('<div class="section-title">Executive Intelligence Briefing</div>', unsafe_allow_html=True)
                tabs = st.tabs(["REPORT", "TELEMETRY", "EVIDENCE"])
                with tabs[0]:
                    st.markdown(f'<div class="report-card">{report}</div>', unsafe_allow_html=True)
                    st.download_button("DOWNLOAD REPORT · MARKDOWN", data=report, file_name=f"{competitor_input}_intelligence_report.md", mime="text/markdown", use_container_width=True)
                with tabs[1]:
                    st.markdown('<div class="telemetry">' + "<br>".join(get_last_run_telemetry()) + '</div>', unsafe_allow_html=True)
                with tabs[2]:
                    st.metric("Verified confidence", f"{confidence}%")
                    st.write("Claims are routed to verification when confidence is low or evidence conflicts.")
            except Exception as exc:
                status.update(label="RECOVERY // execution interrupted", state="error", expanded=True)
                st.error(str(exc))
else:
    st.markdown('<div class="section-title">Awaiting Mission</div>', unsafe_allow_html=True)
    st.info("Configure a target in Mission Input, then execute the agentic workflow to populate live telemetry and the executive briefing.")
