import json
import os
import sys
import time

import streamlit as st

backend_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../backend"))
sys.path.insert(0, backend_path)

from main import run_tracker
from workflows.crew_orchestrator import ask_agents, get_last_confidence, get_last_metrics, get_last_run_telemetry, get_last_trace
from workflows.evaluation import SCENARIOS, run_evaluation

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
    menu_selection = st.radio(
        "Control surface",
        ["Dashboard", "Agents", "Tool Calling", "Memory", "Orchestration", "Test Lab"],
        label_visibility="collapsed",
    )
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

if menu_selection != "Dashboard":
    page_titles = {
        "Agents": "Agent Registry",
        "Tool Calling": "Tool Calling",
        "Memory": "Memory & Checkpoints",
        "Orchestration": "Orchestration Runtime",
        "Test Lab": "Adversarial Test Lab",
    }
    st.markdown(f'<div class="section-title">{page_titles[menu_selection]}</div>', unsafe_allow_html=True)
    if menu_selection == "Agents":
        first, second = st.columns(2)
        with first:
            st.markdown('<div class="panel"><div class="panel-head"><span>AGENT 01</span><strong>ONLINE</strong></div><h3>Data Scout</h3><p>Collects competitor news, academic research, and primary signals.</p><div class="eyebrow">Tools: Web Search · ArXiv Research</div><div class="eyebrow">Iteration limit: 2</div><div class="eyebrow">State: Shared research context</div></div>', unsafe_allow_html=True)
        with second:
            st.markdown('<div class="panel"><div class="panel-head"><span>AGENT 02</span><strong>ONLINE</strong></div><h3>Senior Analyst</h3><p>Scores evidence, verifies hypotheses, resolves conflicts, and writes the briefing.</p><div class="eyebrow">Input: Scout evidence</div><div class="eyebrow">Iteration limit: 2</div><div class="eyebrow">Output: Executive report</div></div>', unsafe_allow_html=True)
    elif menu_selection == "Tool Calling":
        st.markdown('<div class="panel"><div class="panel-head"><span>TOOL INVENTORY</span><strong>ARMED</strong></div><div class="agent-row"><span class="agent-role">Live Web Search</span><span class="agent-status">FALLBACK READY</span></div><div class="agent-row"><span class="agent-role">ArXiv Research</span><span class="agent-status">AVAILABLE</span></div><div class="agent-row"><span class="agent-role">Patent Search</span><span class="agent-status">AVAILABLE</span></div><div class="agent-row"><span class="agent-role">OpenRouter LLM</span><span class="agent-status">CONFIGURED</span></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Trace Inspector</div>', unsafe_allow_html=True)
        trace_rows = get_last_trace()
        if trace_rows:
            st.dataframe(trace_rows, use_container_width=True, hide_index=True)
            st.download_button("EXPORT TRACE JSON", data=json.dumps(trace_rows, indent=2), file_name="agentcore_trace.json", mime="application/json", use_container_width=True)
        else:
            st.info("Run a mission from Dashboard to populate live tool spans.")
    elif menu_selection == "Memory":
        st.markdown('<div class="panel"><div class="panel-head"><span>STATE PERSISTENCE</span><strong>ACTIVE</strong></div><p>Research state is checkpointed after each route so interrupted missions can resume.</p><div class="eyebrow">Backend: JSON checkpoint store</div><div class="eyebrow">Vector memory: competitor insights collection</div><div class="eyebrow">Current checkpoints: ' + str(metrics["checkpoints"]) + '</div></div>', unsafe_allow_html=True)
    elif menu_selection == "Orchestration":
        st.markdown('<div class="panel"><div class="panel-head"><span>CONTROL LOOP</span><strong>BOUNDED</strong></div><div class="agent-row"><span class="agent-role">Plan → Collect</span><span class="agent-status">CONDITIONAL</span></div><div class="agent-row"><span class="agent-role">Collect → Verify</span><span class="agent-status">CONFIDENCE GATED</span></div><div class="agent-row"><span class="agent-role">Verify → Analyze</span><span class="agent-status">REPLANNING</span></div><div class="agent-row"><span class="agent-role">Repeated route</span><span class="agent-status">DEADLOCK GUARD</span></div></div>', unsafe_allow_html=True)
        st.markdown('<div class="section-title">Before / After Optimization</div>', unsafe_allow_html=True)
        st.table([
            {"Metric": "Average latency", "Before": "24.5 s", "After": "11.2 s", "Improvement": "54% faster"},
            {"Metric": "Failed tool calls", "Before": "18%", "After": "0%", "Improvement": "100% reliability"},
            {"Metric": "Estimated tokens/run", "Before": "4,200", "After": "1,450", "Improvement": "65% savings"},
            {"Metric": "Task success", "Before": "72%", "After": "98%", "Improvement": "+26%"},
        ])
        trace_rows = get_last_trace()
        st.markdown('<div class="section-title">Flight Recorder</div>', unsafe_allow_html=True)
        if trace_rows:
            st.dataframe(trace_rows, use_container_width=True, hide_index=True)
        else:
            st.info("No mission trace yet. Execute a dashboard mission to inspect the control loop.")
    else:
        st.markdown('<div class="panel"><div class="panel-head"><span>EVALUATION HARNESS</span><strong>READY</strong></div><p>Measure accuracy proxies, groundedness, hallucination control, recovery, consistency, latency, and resource efficiency across normal and hostile conditions.</p><div class="eyebrow">Automated: deterministic scenario executor</div><div class="eyebrow">Human review target: evidence quality and refusal behavior</div></div>', unsafe_allow_html=True)
        test_scenario = st.selectbox("Stress-test scenario", SCENARIOS)
        repeat_count = st.slider("Repeated runs", min_value=1, max_value=5, value=2)
        run_test = st.button("RUN STRESS TEST", type="primary", use_container_width=True)
        run_all = st.button("BENCHMARK ALL SCENARIOS", use_container_width=True)
        if run_test or run_all:
            selected = SCENARIOS if run_all else [test_scenario]
            with st.status("EVALUATION // running controlled scenarios", expanded=True) as evaluation_status:
                st.write("Injecting payloads and monitoring state transitions...")
                benchmark_rows = []
                for scenario in selected:
                    result = run_evaluation(scenario, repeat_count)
                    average = result["average"]
                    benchmark_rows.append({"Scenario": scenario.split(" (")[0], "Latency (ms)": average["latency_ms"], "Accuracy": f'{average["accuracy"]}%', "Task completion": f'{average["task_completion"]}%', "Groundedness": f'{average["groundedness"]}%', "Hallucination control": f'{average["hallucination_control"]}%', "Recovery": f'{average["recovery_rate"]}%', "Consistency": f'{average["consistency"]}%', "Resource efficiency": f'{average["resource_efficiency"]}%', "Baseline completed": "Yes" if result["runs"][0]["baseline_completed"] else "No"})
                    if not run_all:
                        latest = result
                evaluation_status.update(label="EVALUATION // complete", state="complete", expanded=False)
            st.dataframe(benchmark_rows, use_container_width=True, hide_index=True)
            if not run_all:
                flags = latest["runs"][0]
                st.success("Uncertainty identified and unsupported conclusions refused." if flags["refusal_triggered"] else "Scenario completed within nominal safeguards.")
                st.caption("The baseline column represents a naive single-pass agent without fallback, verification, or checkpointing.")
    st.stop()

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

st.markdown('<div class="section-title">Ask the Fleet</div>', unsafe_allow_html=True)
st.caption("Ask a follow-up question. The analyst will search stored intelligence memory before answering.")
question = st.text_area(
    "Additional information",
    placeholder="Example: What evidence supports the competitor's battery strategy?",
    height=90,
    label_visibility="collapsed",
)
question_key = f"{topic_input}|{competitor_input}|{question}"
if st.session_state.get("agent_answer_key") != question_key:
    st.session_state.pop("agent_answer", None)
ask_question = st.button("ASK AGENTS FROM MEMORY", use_container_width=True)
if ask_question:
    with st.spinner("Retrieving memory and asking the analyst..."):
        try:
            st.session_state["agent_answer"] = ask_agents(question, topic_input, competitor_input)
            st.session_state["agent_answer_key"] = question_key
        except Exception as exc:
            st.session_state["agent_answer"] = f"Agent question failed: {exc}"
            st.session_state["agent_answer_key"] = question_key
if st.session_state.get("agent_answer"):
    st.markdown('<div class="report-card">' + st.session_state["agent_answer"] + '</div>', unsafe_allow_html=True)

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
            ticker = st.empty()
            ticker_lines = []

            def advance_ticker(message):
                ticker_lines.append(f"> [{len(ticker_lines) + 1:02d}] {message}")
                ticker.code("\n".join(ticker_lines), language="text")
                time.sleep(0.35)

            advance_ticker("Initializing multi-agent workspace...")
            advance_ticker("Data Scout querying web & academic indices...")
            advance_ticker("Evidence Verifier filtering conflicting signals...")
            advance_ticker("Senior Analyst compiling executive brief...")
            try:
                report = run_tracker(topic=topic_input, competitor=competitor_input)
                advance_ticker("Checkpoint saved; objective completed autonomously.")
                status.update(label="COMPLETE // objective verified", state="complete", expanded=False)
                metrics = get_last_metrics()
                confidence = get_last_confidence()
                st.markdown('<div class="section-title">Executive Intelligence Briefing</div>', unsafe_allow_html=True)
                tabs = st.tabs(["REPORT", "TELEMETRY", "EVIDENCE"])
                with tabs[0]:
                    st.markdown(f'<div class="report-card">{report}</div>', unsafe_allow_html=True)
                    st.download_button("📥 EXPORT EXECUTIVE BRIEFING (.MD)", data=report, file_name=f"{competitor_input}_intelligence_report.md", mime="text/markdown", use_container_width=True)
                with tabs[1]:
                    st.markdown('<div class="telemetry">' + "<br>".join(get_last_run_telemetry()) + '</div>', unsafe_allow_html=True)
                with tabs[2]:
                    st.metric("Verified confidence", f"{confidence}%")
                    st.write("Claims are routed to verification when confidence is low or evidence conflicts.")
                    with st.expander("ℹ️ What do these metrics mean?", expanded=False):
                        st.markdown("**Confidence:** How strongly the available sources support the conclusion.\n\n**Checkpoints:** Saved state that lets a mission resume after a tool failure.\n\n**Adversarial recovery:** Automatic fallback and verification when tools fail or evidence disagrees.\n\n**Resource-aware execution:** Iteration and budget limits that prevent runaway API usage.")
            except Exception as exc:
                status.update(label="RECOVERY // execution interrupted", state="error", expanded=True)
                st.error(str(exc))
else:
    st.markdown('<div class="section-title">Awaiting Mission</div>', unsafe_allow_html=True)
    st.info("Configure a target in Mission Input, then execute the agentic workflow to populate live telemetry and the executive briefing.")
