import React, { useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Bell,
  BookOpen,
  BriefcaseBusiness,
  CalendarClock,
  Check,
  ChevronRight,
  CircleAlert,
  FileText,
  Filter,
  Gauge,
  Globe2,
  Lightbulb,
  Newspaper,
  Radar,
  Search,
  ShieldCheck,
  Sparkles,
  TrendingUp,
} from "lucide-react";
import "./styles.css";

const insights = [
  {
    id: 1,
    type: "Research",
    title: "Foundation model papers are shifting toward smaller domain agents",
    source: "arXiv, ACL Anthology",
    time: "12 min ago",
    impact: "High",
    score: 94,
    summary:
      "Recent papers show rising attention on compact agentic systems for chemistry, finance, and legal workflows.",
    tags: ["LLM", "Agents", "Domain AI"],
  },
  {
    id: 2,
    type: "Patent",
    title: "Competitor filed a semantic search patent for invention scouting",
    source: "USPTO Monitor",
    time: "48 min ago",
    impact: "Critical",
    score: 98,
    summary:
      "The filing describes vector-based prior-art matching and automated novelty scoring across patent families.",
    tags: ["Patent", "Search", "IP Risk"],
  },
  {
    id: 3,
    type: "Competitor",
    title: "Rival hiring pattern indicates expansion into healthcare AI",
    source: "Career pages, LinkedIn signals",
    time: "1 hr ago",
    impact: "Medium",
    score: 76,
    summary:
      "Five new roles mention clinical validation, medical data governance, and FDA-aligned model evaluation.",
    tags: ["Hiring", "Healthcare", "Strategy"],
  },
  {
    id: 4,
    type: "News",
    title: "Industry funding rebounds for applied robotics intelligence",
    source: "Tech news cluster",
    time: "2 hrs ago",
    impact: "Medium",
    score: 71,
    summary:
      "Investors are favoring robotics startups with proprietary datasets and measurable deployment traction.",
    tags: ["Funding", "Robotics", "Market"],
  },
];

const sources = [
  { name: "Scientific Publications", value: 1284, icon: BookOpen, status: "Live" },
  { name: "Patent Databases", value: 426, icon: FileText, status: "Live" },
  { name: "Competitor Signals", value: 238, icon: BriefcaseBusiness, status: "Live" },
  { name: "News and Social", value: 912, icon: Newspaper, status: "Live" },
];

const competitorMoves = [
  { company: "NovaMind Labs", signal: "Filed 3 patents", risk: "High", area: "Semantic search" },
  { company: "Helio Robotics", signal: "Raised Series B", risk: "Medium", area: "Autonomous inspection" },
  { company: "SynapseGrid", signal: "Opened EU roles", risk: "Medium", area: "Privacy-first agents" },
  { company: "CortexForge", signal: "Released benchmark", risk: "Low", area: "Synthetic evaluation" },
];

const trendData = [
  { label: "AI agents", value: 86 },
  { label: "Edge AI", value: 62 },
  { label: "Robotics", value: 58 },
  { label: "Bio-AI", value: 52 },
  { label: "IP search", value: 48 },
];

const filters = ["All", "Research", "Patent", "Competitor", "News"];

function App() {
  const [activeFilter, setActiveFilter] = useState("All");
  const [query, setQuery] = useState("");

  const filteredInsights = useMemo(() => {
    const text = query.trim().toLowerCase();
    return insights.filter((item) => {
      const matchesFilter = activeFilter === "All" || item.type === activeFilter;
      const matchesSearch =
        !text ||
        [item.title, item.summary, item.source, item.type, ...item.tags]
          .join(" ")
          .toLowerCase()
          .includes(text);
      return matchesFilter && matchesSearch;
    });
  }, [activeFilter, query]);

  return (
    <main className="app-shell">
      <aside className="sidebar" aria-label="Main navigation">
        <div className="brand">
          <span className="brand-mark">
            <Radar size={22} aria-hidden="true" />
          </span>
          <div>
            <strong>IntelWatch AI</strong>
            <span>Autonomous intelligence agent</span>
          </div>
        </div>

        <nav className="nav-stack">
          <a href="#overview" className="nav-item active">
            <Gauge size={18} aria-hidden="true" />
            Overview
          </a>
          <a href="#sources" className="nav-item">
            <Globe2 size={18} aria-hidden="true" />
            Sources
          </a>
          <a href="#insights" className="nav-item">
            <Sparkles size={18} aria-hidden="true" />
            Insights
          </a>
          <a href="#alerts" className="nav-item">
            <Bell size={18} aria-hidden="true" />
            Alerts
          </a>
        </nav>

        <div className="agent-card">
          <span className="pulse-dot" />
          <p>Agent status</p>
          <strong>Tracking 2,860 signals</strong>
          <small>Next digest in 18 minutes</small>
        </div>
      </aside>

      <section className="workspace">
        <header className="topbar">
          <div>
            <p className="eyebrow">Real-time research and competitor monitoring</p>
            <h1>Actionable intelligence before the market moves</h1>
          </div>
          <button className="icon-button" aria-label="Open notifications">
            <Bell size={20} aria-hidden="true" />
            <span className="notification-dot" />
          </button>
        </header>

        <section id="overview" className="metrics-grid" aria-label="Overview metrics">
          <MetricCard label="New Signals" value="2,860" change="+18%" tone="good" />
          <MetricCard label="High Priority Alerts" value="24" change="+7" tone="risk" />
          <MetricCard label="Sources Connected" value="42" change="100%" tone="good" />
          <MetricCard label="Avg. Response Time" value="4.2m" change="-31%" tone="good" />
        </section>

        <section className="content-grid">
          <div className="panel wide" id="insights">
            <div className="panel-header">
              <div>
                <p className="eyebrow">AI-ranked updates</p>
                <h2>Insight Feed</h2>
              </div>
              <div className="search-box">
                <Search size={18} aria-hidden="true" />
                <input
                  value={query}
                  onChange={(event) => setQuery(event.target.value)}
                  placeholder="Search signals"
                  aria-label="Search insights"
                />
              </div>
            </div>

            <div className="filter-row" aria-label="Insight filters">
              <Filter size={17} aria-hidden="true" />
              {filters.map((filter) => (
                <button
                  key={filter}
                  className={filter === activeFilter ? "chip active" : "chip"}
                  onClick={() => setActiveFilter(filter)}
                  type="button"
                >
                  {filter}
                </button>
              ))}
            </div>

            <div className="insight-list">
              {filteredInsights.map((item) => (
                <article className="insight-item" key={item.id}>
                  <div className={`type-badge ${item.type.toLowerCase()}`}>{item.type}</div>
                  <div className="insight-body">
                    <div className="insight-title-row">
                      <h3>{item.title}</h3>
                      <span className={`impact ${item.impact.toLowerCase()}`}>{item.impact}</span>
                    </div>
                    <p>{item.summary}</p>
                    <div className="meta-row">
                      <span>{item.source}</span>
                      <span>{item.time}</span>
                      <span>Confidence {item.score}%</span>
                    </div>
                    <div className="tag-row">
                      {item.tags.map((tag) => (
                        <span key={tag}>{tag}</span>
                      ))}
                    </div>
                  </div>
                  <button className="arrow-button" aria-label={`Open ${item.title}`}>
                    <ChevronRight size={20} aria-hidden="true" />
                  </button>
                </article>
              ))}
            </div>
          </div>

          <div className="panel" id="sources">
            <div className="panel-header compact">
              <div>
                <p className="eyebrow">Connected monitors</p>
                <h2>Source Coverage</h2>
              </div>
            </div>
            <div className="source-stack">
              {sources.map((source) => {
                const Icon = source.icon;
                return (
                  <div className="source-item" key={source.name}>
                    <span className="source-icon">
                      <Icon size={19} aria-hidden="true" />
                    </span>
                    <div>
                      <strong>{source.name}</strong>
                      <small>{source.value.toLocaleString()} items scanned today</small>
                    </div>
                    <span className="live-pill">{source.status}</span>
                  </div>
                );
              })}
            </div>
          </div>

          <div className="panel">
            <div className="panel-header compact">
              <div>
                <p className="eyebrow">Emerging topics</p>
                <h2>Trend Velocity</h2>
              </div>
            </div>
            <div className="trend-stack">
              {trendData.map((trend) => (
                <div className="trend-row" key={trend.label}>
                  <div>
                    <strong>{trend.label}</strong>
                    <span>{trend.value}% momentum</span>
                  </div>
                  <div className="bar-track" aria-hidden="true">
                    <span style={{ width: `${trend.value}%` }} />
                  </div>
                </div>
              ))}
            </div>
          </div>

          <div className="panel wide">
            <div className="panel-header compact">
              <div>
                <p className="eyebrow">Strategic watchlist</p>
                <h2>Competitor Activity</h2>
              </div>
              <button className="text-button" type="button">
                Export brief
              </button>
            </div>
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Organization</th>
                    <th>Signal</th>
                    <th>Focus Area</th>
                    <th>Risk</th>
                  </tr>
                </thead>
                <tbody>
                  {competitorMoves.map((move) => (
                    <tr key={move.company}>
                      <td>{move.company}</td>
                      <td>{move.signal}</td>
                      <td>{move.area}</td>
                      <td>
                        <span className={`risk ${move.risk.toLowerCase()}`}>{move.risk}</span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>

          <div className="panel action-panel" id="alerts">
            <div className="panel-header compact">
              <div>
                <p className="eyebrow">Recommended action</p>
                <h2>Today&apos;s Brief</h2>
              </div>
              <Lightbulb size={22} aria-hidden="true" />
            </div>
            <div className="brief-list">
              <BriefPoint icon={CircleAlert} text="Review semantic patent filing for overlap with current roadmap." />
              <BriefPoint icon={TrendingUp} text="Prioritize a market scan on healthcare-focused agent platforms." />
              <BriefPoint icon={ShieldCheck} text="Prepare leadership digest with confidence-ranked evidence links." />
              <BriefPoint icon={CalendarClock} text="Schedule weekly scout summary for R&D and strategy teams." />
            </div>
          </div>
        </section>
      </section>
    </main>
  );
}

function MetricCard({ label, value, change, tone }) {
  return (
    <article className="metric-card">
      <span className={tone === "risk" ? "metric-icon risk-tone" : "metric-icon"}>
        {tone === "risk" ? <CircleAlert size={18} aria-hidden="true" /> : <Check size={18} aria-hidden="true" />}
      </span>
      <p>{label}</p>
      <div>
        <strong>{value}</strong>
        <span className={tone === "risk" ? "delta risk-tone" : "delta"}>{change}</span>
      </div>
    </article>
  );
}

function BriefPoint({ icon: Icon, text }) {
  return (
    <div className="brief-point">
      <span>
        <Icon size={18} aria-hidden="true" />
      </span>
      <p>{text}</p>
    </div>
  );
}

createRoot(document.getElementById("root")).render(<App />);
