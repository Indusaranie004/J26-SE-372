"""
Component A — Precedent Validity Knowledge Graph
Pipeline Dashboard & Analytics
Run: streamlit run dashboard.py
"""

import streamlit as st
import os
import sys
import json
import subprocess
import threading
import queue
import time
from datetime import datetime
from dotenv import load_dotenv

# Load .env from component-a directory
from pathlib import Path
env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path)

# ── Page config ───────────────────────────────────────────────────
st.set_page_config(
    page_title="Component A — KG Dashboard",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Force light theme override
st.markdown("""
<style>
    [data-testid="stAppViewContainer"] { background: #f8f9fc !important; }
    [data-testid="stSidebar"] { background: #ffffff !important; border-right: 1px solid #e2e6ef; }
    [data-testid="stSidebar"] * { color: #111827 !important; }
    [data-testid="stHeader"] { background: #f8f9fc !important; }
    .stRadio label, .stRadio div { color: #374151 !important; }
    .stTextInput input { background: #ffffff !important; color: #111827 !important; border: 1px solid #d1d5db !important; }
    .stSelectbox select, .stNumberInput input { background: #ffffff !important; color: #111827 !important; }
    h1, h2, h3, p, label, div { color: #111827; }
    .stButton button[kind="primary"] { background: #4f46e5 !important; color: white !important; }
</style>
""", unsafe_allow_html=True)

# ── Styles ────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400;500&display=swap');

    html, body, [class*="css"] {
        font-family: 'Inter', sans-serif;
    }
    .main { background: #f8f9fc; }
    .stApp { background: #f8f9fc; }

    .metric-card {
        background: #ffffff;
        border: 1px solid #e2e6ef;
        border-radius: 8px;
        padding: 20px 24px;
        margin-bottom: 12px;
    }
    .metric-value {
        font-size: 2.2rem;
        font-weight: 600;
        color: #111827;
        line-height: 1;
        margin-bottom: 4px;
        font-family: 'JetBrains Mono', monospace;
    }
    .metric-label {
        font-size: 0.78rem;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.08em;
    }
    .metric-delta {
        font-size: 0.85rem;
        color: #059669;
        margin-top: 6px;
    }

    .log-container {
        background: #f1f3f8;
        border: 1px solid #e2e6ef;
        border-radius: 8px;
        padding: 16px;
        height: 420px;
        overflow-y: auto;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.82rem;
    }
    .log-line { margin: 2px 0; line-height: 1.6; }
    .log-info  { color: #374151; }
    .log-ok    { color: #059669; }
    .log-warn  { color: #d97706; }
    .log-error { color: #dc2626; }
    .log-head  { color: #4f46e5; font-weight: 500; }

    .edge-badge {
        display: inline-block;
        padding: 3px 10px;
        border-radius: 4px;
        font-size: 0.78rem;
        font-weight: 500;
        margin: 2px;
    }
    .badge-followed    { background: #d1fae5; color: #065f46; }
    .badge-overruled   { background: #fee2e2; color: #991b1b; }
    .badge-distinguished { background: #dbeafe; color: #1e40af; }
    .badge-doubted     { background: #fef3c7; color: #92400e; }

    .section-header {
        font-size: 0.72rem;
        text-transform: uppercase;
        letter-spacing: 0.1em;
        color: #374151;
        margin: 24px 0 12px 0;
        padding-bottom: 8px;
        border-bottom: 1px solid #e8ecf3;
    }
    .status-dot {
        display: inline-block;
        width: 8px; height: 8px;
        border-radius: 50%;
        margin-right: 6px;
    }
    .dot-green  { background: #10b981; }
    .dot-yellow { background: #f59e0b; }
    .dot-red    { background: #ef4444; }
    .dot-grey   { background: #9ca3af; }
</style>
""", unsafe_allow_html=True)


# ── Data helpers ──────────────────────────────────────────────────
@st.cache_resource
def get_mongo():
    from pymongo import MongoClient
    uri = os.getenv("MONGODB_URI")
    if not uri:
        return None
    try:
        client = MongoClient(uri, serverSelectionTimeoutMS=3000)
        client.server_info()
        return client["lk_legal"]
    except Exception:
        return None

@st.cache_resource
def get_neo4j():
    from neo4j import GraphDatabase
    uri  = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    pw   = os.getenv("NEO4J_PASSWORD")
    if not all([uri, user, pw]):
        return None
    try:
        driver = GraphDatabase.driver(uri, auth=(user, pw))
        driver.verify_connectivity()
        return driver
    except Exception:
        return None

def mongo_stats():
    db = get_mongo()
    if db is None:
        return None
    cases = db["cases"].count_documents({})
    stubs = db["stubs"].count_documents({}) if "stubs" in db.list_collection_names() else 0
    # year distribution
    pipeline = [{"$group": {"_id": {"$substr": ["$date", 0, 4]}, "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}}]
    years = {r["_id"]: r["count"] for r in db["cases"].aggregate(pipeline) if r["_id"]}
    return {"cases": cases, "stubs": stubs, "years": years}

def neo4j_stats():
    driver = get_neo4j()
    if driver is None:
        return None
    with driver.session() as s:
        nodes = s.run("""
            MATCH (n) RETURN labels(n)[0] AS label, count(*) AS cnt
        """).data()
        edges = s.run("""
            MATCH ()-[r]->() RETURN type(r) AS rel, count(*) AS cnt
        """).data()
        treatments = s.run("""
            MATCH ()-[t:TREATED_BY]->()
            RETURN t.treatment_type AS tp, count(*) AS cnt
        """).data()
        validity = s.run("""
            MATCH (c:Case)
            WHERE c.validity_status IS NOT NULL
            RETURN c.validity_status AS status, count(*) AS cnt
        """).data()
    return {
        "nodes": {r["label"]: r["cnt"] for r in nodes},
        "edges": {r["rel"]: r["cnt"] for r in edges},
        "treatments": {r["tp"]: r["cnt"] for r in treatments},
        "validity": {r["status"]: r["cnt"] for r in validity}
    }


# ── Sidebar nav ───────────────────────────────────────────────────
with st.sidebar:
    st.markdown("### ⚖️ Component A")
    st.markdown("**Precedent Validity KG**")
    st.markdown("---")
    page = st.radio(
        "Navigation",
        ["📊 Analytics", "🚀 Pipeline Runner", "🔍 Case Explorer"],
        label_visibility="collapsed"
    )
    st.markdown("---")

    # Connection status
    db = get_mongo()
    driver = get_neo4j()
    mongo_ok = db is not None
    neo4j_ok = driver is not None

    st.markdown("**Connections**")
    dot_m = "dot-green" if mongo_ok else "dot-red"
    dot_n = "dot-green" if neo4j_ok else "dot-red"
    st.markdown(f'<span class="status-dot {dot_m}"></span> MongoDB {"✓" if mongo_ok else "✗"}', unsafe_allow_html=True)
    st.markdown(f'<span class="status-dot {dot_n}"></span> Neo4j {"✓" if neo4j_ok else "✗"}', unsafe_allow_html=True)

    st.markdown("---")
    st.caption("J26-SE-372 · SLIIT · 2026")


# ══════════════════════════════════════════════════════════════════
# PAGE 1 — ANALYTICS
# ══════════════════════════════════════════════════════════════════
if page == "📊 Analytics":
    st.markdown("## Knowledge Graph Analytics")
    st.markdown('<div class="section-header">Document Store — MongoDB</div>', unsafe_allow_html=True)

    ms = mongo_stats()
    ns = neo4j_stats()

    if ms:
        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{ms['cases']:,}</div>
                <div class="metric-label">SC Judgments</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{ms['stubs']:,}</div>
                <div class="metric-label">Stub Cases</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            total_docs = ms['cases'] + ms['stubs']
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_docs:,}</div>
                <div class="metric-label">Total Cases</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            years = ms.get("years", {})
            year_range = f"{min(years)} – {max(years)}" if years else "N/A"
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{year_range}</div>
                <div class="metric-label">Year Range</div>
            </div>""", unsafe_allow_html=True)

        # Year distribution chart
        if years:
            st.markdown('<div class="section-header">Documents by Year</div>', unsafe_allow_html=True)
            import pandas as pd
            df_years = pd.DataFrame(
                [(y, c) for y, c in sorted(years.items()) if y and y.isdigit()],
                columns=["Year", "Documents"]
            )
            st.bar_chart(df_years.set_index("Year"), color="#818cf8")
    else:
        st.warning("MongoDB not connected — check MONGODB_URI in .env")

    # Neo4j stats
    st.markdown('<div class="section-header">Knowledge Graph — Neo4j</div>', unsafe_allow_html=True)

    if ns:
        c1, c2, c3, c4 = st.columns(4)
        nodes = ns["nodes"]
        edges = ns["edges"]

        with c1:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{nodes.get('Case', 0):,}</div>
                <div class="metric-label">Case Nodes</div>
            </div>""", unsafe_allow_html=True)
        with c2:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{nodes.get('Judge', 0):,}</div>
                <div class="metric-label">Judge Nodes</div>
            </div>""", unsafe_allow_html=True)
        with c3:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{nodes.get('Act', 0):,}</div>
                <div class="metric-label">Act Nodes</div>
            </div>""", unsafe_allow_html=True)
        with c4:
            total_edges = sum(edges.values())
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-value">{total_edges:,}</div>
                <div class="metric-label">Total Edges</div>
            </div>""", unsafe_allow_html=True)

        # Edge breakdown
        c1, c2 = st.columns(2)
        with c1:
            st.markdown('<div class="section-header">Edge Types</div>', unsafe_allow_html=True)
            for rel, cnt in sorted(edges.items(), key=lambda x: -x[1]):
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #e8ecf3;">
                    <span style="color:#374151;font-size:0.85rem;">{rel}</span>
                    <span style="color:#111827;font-family:'JetBrains Mono',monospace;font-size:0.85rem;">{cnt:,}</span>
                </div>""", unsafe_allow_html=True)

        with c2:
            st.markdown('<div class="section-header">Treatment Types</div>', unsafe_allow_html=True)
            treatment_colors = {
                "followed":      ("badge-followed",     "Followed"),
                "overruled":     ("badge-overruled",    "Overruled"),
                "distinguished": ("badge-distinguished","Distinguished"),
                "doubted":       ("badge-doubted",      "Doubted"),
            }
            treatments = ns.get("treatments", {})
            for tp, cnt in sorted(treatments.items(), key=lambda x: -x[1]):
                badge_cls, label = treatment_colors.get(tp, ("", tp))
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;align-items:center;padding:8px 0;border-bottom:1px solid #e8ecf3;">
                    <span class="edge-badge {badge_cls}">{label}</span>
                    <span style="color:#111827;font-family:'JetBrains Mono',monospace;font-size:0.85rem;">{cnt:,}</span>
                </div>""", unsafe_allow_html=True)

            # Validity status
            st.markdown('<div class="section-header" style="margin-top:20px;">Validity Status</div>', unsafe_allow_html=True)
            validity = ns.get("validity", {})
            status_colors = {
                "good_law": "#34d399",
                "no_longer_good_law": "#f87171",
                "partially_invalidated": "#fbbf24"
            }
            for status, cnt in sorted(validity.items(), key=lambda x: -x[1]):
                color = status_colors.get(status, "#9ca3af")
                label = status.replace("_", " ").title()
                st.markdown(f"""
                <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid #e8ecf3;">
                    <span style="color:{color};font-size:0.85rem;">● {label}</span>
                    <span style="color:#111827;font-family:'JetBrains Mono',monospace;font-size:0.85rem;">{cnt:,}</span>
                </div>""", unsafe_allow_html=True)
    else:
        st.warning("Neo4j not connected — check NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD in .env")

    # Study 1 results
    st.markdown('<div class="section-header">Study 1 — InLegalBERT Results</div>', unsafe_allow_html=True)
    c1, c2 = st.columns(2)
    with c1:
        results = [
            ("Overall Weighted F1", "73.6%", "vs 60% rule-based baseline"),
            ("Followed F1",         "76.4%", "+11% over rule-based"),
            ("Distinguished F1",    "85.7%", "+85.7% — was 0% rule-based"),
            ("Doubted F1",          "100%",  "+100% — was 0% rule-based"),
            ("Overruled F1",        "0%",    "Insufficient training examples"),
            ("Overall Accuracy",    "61%",   "On held-out test set (n=52)"),
        ]
        for label, value, note in results:
            color = "#34d399" if "%" in value and value != "0%" else "#f87171" if value == "0%" else "#e8eaf0"
            st.markdown(f"""
            <div style="display:flex;justify-content:space-between;align-items:center;padding:10px 0;border-bottom:1px solid #e8ecf3;">
                <div>
                    <div style="color:#374151;font-size:0.85rem;">{label}</div>
                    <div style="color:#374151;font-size:0.75rem;">{note}</div>
                </div>
                <span style="color:{color};font-family:'JetBrains Mono',monospace;font-size:1.1rem;font-weight:600;">{value}</span>
            </div>""", unsafe_allow_html=True)
    with c2:
        st.markdown("""
        <div class="metric-card" style="height:100%;">
            <div style="color:#4f46e5;font-size:0.78rem;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:16px;">Annotation Summary</div>
            <div style="color:#111827;font-size:0.85rem;line-height:1.8;">
                <div>270 manually annotated sentences</div>
                <div>1,904 SC judgments searched</div>
                <div>Base model: law-ai/InLegalBERT</div>
                <div>Oversampling: target_count=60</div>
                <div>Train: 218 · Test: 52</div>
                <div style="margin-top:12px;color:#374151;">
                    Full Study 1 with CA corpus<br>annotation planned for PP2
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════════
# PAGE 2 — PIPELINE RUNNER
# ══════════════════════════════════════════════════════════════════
elif page == "🚀 Pipeline Runner":
    st.markdown("## Pipeline Runner")

    c1, c2 = st.columns([2, 1])
    with c1:
        corpus_path = st.text_input(
            "Corpus path",
            value=r"D:\Projects\Y4S1 Project\RP\lk_supreme_court_judgements\data\lk_supreme_court_judgements",
            placeholder="Absolute path to corpus folder"
        )
        col_a, col_b, col_c = st.columns(3)
        with col_a:
            court = st.selectbox("Court", ["SC", "CA", "DC"])
        with col_b:
            limit = st.number_input("Limit (0 = all)", min_value=0, value=0, step=50)
        with col_c:
            st.markdown("<div style='height:28px'></div>", unsafe_allow_html=True)
            run_btn = st.button("▶ Run Pipeline", type="primary", use_container_width=True)

    with c2:
        st.markdown("""
        <div class="metric-card">
            <div class="metric-label">Pipeline info</div>
            <div style="color:#374151;font-size:0.82rem;line-height:1.8;margin-top:8px;">
                • Scans corpus for new documents<br>
                • Skips already-processed doc_ids<br>
                • Uploads to MongoDB<br>
                • Populates Neo4j KG<br>
                • Idempotent — safe to re-run
            </div>
        </div>
        """, unsafe_allow_html=True)

    st.markdown('<div class="section-header">Pipeline Log</div>', unsafe_allow_html=True)
    log_placeholder = st.empty()
    stats_placeholder = st.empty()

    if "log_lines" not in st.session_state:
        st.session_state.log_lines = []
    if "pipeline_running" not in st.session_state:
        st.session_state.pipeline_running = False
    if "pipeline_stats" not in st.session_state:
        st.session_state.pipeline_stats = {}

    def render_log(lines):
        html = '<div class="log-container">'
        for line in lines[-200:]:
            cls = "log-info"
            if any(k in line for k in ["Pipeline started", "Pipeline complete", "Constraints"]):
                cls = "log-head"
            elif any(k in line for k in ["New documents:", "Treatment edges:", "Skipped:"]):
                cls = "log-ok"
            elif "Error" in line or "error" in line:
                cls = "log-error"
            elif "Warning" in line or "No text" in line:
                cls = "log-warn"
            ts = datetime.now().strftime("%H:%M:%S")
            html += f'<div class="log-line {cls}">[{ts}] {line}</div>'
        html += '</div>'
        return html

    # Show existing log
    log_placeholder.markdown(render_log(st.session_state.log_lines), unsafe_allow_html=True)

    if run_btn and not st.session_state.pipeline_running:
        if not corpus_path or not os.path.exists(corpus_path):
            st.error("Corpus path does not exist.")
        else:
            st.session_state.log_lines = []
            st.session_state.pipeline_running = True
            st.session_state.pipeline_stats = {}

            # Build command
            pipeline_path = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "pipeline.py"
            )
            cmd = [sys.executable, pipeline_path,
                   "--corpus", corpus_path,
                   "--court", court]
            if limit > 0:
                cmd += ["--limit", str(limit)]

            st.session_state.log_lines.append(f"Starting pipeline...")
            st.session_state.log_lines.append(f"Command: {' '.join(cmd)}")
            log_placeholder.markdown(render_log(st.session_state.log_lines), unsafe_allow_html=True)

            try:
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.STDOUT,
                    text=True,
                    bufsize=1,
                    cwd=os.path.dirname(pipeline_path)
                )

                stats = {
                    "new": 0, "skipped": 0,
                    "no_text": 0, "edges": 0, "errors": 0
                }

                for line in process.stdout:
                    line = line.rstrip()
                    if not line:
                        continue
                    st.session_state.log_lines.append(line)

                    # Parse stats from output
                    if "New documents:" in line:
                        try: stats["new"] = int(line.split(":")[-1].strip())
                        except: pass
                    elif "Skipped:" in line:
                        try: stats["skipped"] = int(line.split(":")[-1].strip())
                        except: pass
                    elif "No text:" in line:
                        try: stats["no_text"] = int(line.split(":")[-1].strip())
                        except: pass
                    elif "Treatment edges:" in line:
                        try: stats["edges"] = int(line.split(":")[-1].strip())
                        except: pass
                    elif "Errors:" in line:
                        try: stats["errors"] = int(line.split(":")[-1].strip())
                        except: pass

                    log_placeholder.markdown(
                        render_log(st.session_state.log_lines),
                        unsafe_allow_html=True
                    )

                    # Live stats update
                    stats_placeholder.markdown(f"""
                    <div style="display:flex;gap:12px;flex-wrap:wrap;margin-top:8px;">
                        <div class="metric-card" style="flex:1;min-width:120px;padding:12px 16px;">
                            <div class="metric-value" style="font-size:1.5rem;color:#059669">{stats['new']}</div>
                            <div class="metric-label">New docs</div>
                        </div>
                        <div class="metric-card" style="flex:1;min-width:120px;padding:12px 16px;">
                            <div class="metric-value" style="font-size:1.5rem;">{stats['skipped']}</div>
                            <div class="metric-label">Skipped</div>
                        </div>
                        <div class="metric-card" style="flex:1;min-width:120px;padding:12px 16px;">
                            <div class="metric-value" style="font-size:1.5rem;color:#4f46e5">{stats['edges']}</div>
                            <div class="metric-label">KG edges added</div>
                        </div>
                        <div class="metric-card" style="flex:1;min-width:120px;padding:12px 16px;">
                            <div class="metric-value" style="font-size:1.5rem;color:#d97706">{stats['no_text']}</div>
                            <div class="metric-label">No text</div>
                        </div>
                        <div class="metric-card" style="flex:1;min-width:120px;padding:12px 16px;">
                            <div class="metric-value" style="font-size:1.5rem;color:#dc2626">{stats['errors']}</div>
                            <div class="metric-label">Errors</div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)

                process.wait()
                st.session_state.pipeline_stats = stats
                st.session_state.pipeline_running = False
                st.session_state.log_lines.append("── Pipeline finished ──")
                log_placeholder.markdown(
                    render_log(st.session_state.log_lines),
                    unsafe_allow_html=True
                )
                st.success(f"Done — {stats['new']} new documents, {stats['edges']} treatment edges added.")
                # Clear cache so analytics refresh
                get_mongo.clear()
                get_neo4j.clear()

            except Exception as e:
                st.session_state.pipeline_running = False
                st.error(f"Pipeline error: {e}")


# ══════════════════════════════════════════════════════════════════
# PAGE 3 — CASE EXPLORER
# ══════════════════════════════════════════════════════════════════
elif page == "🔍 Case Explorer":
    st.markdown("## Case Explorer")

    db = get_mongo()
    driver = get_neo4j()

    query = st.text_input(
        "Search by case name, case number or doc_id",
        placeholder="e.g. Silva v Attorney General, SC/FR/527/2011, 2016-07-22-SC-FR-527-2011"
    )

    if query and db is not None:
        # Search MongoDB
        results = list(db["cases"].find(
            {"$or": [
                {"doc_id": {"$regex": query, "$options": "i"}},
                {"case_num": {"$regex": query, "$options": "i"}},
                {"case_name": {"$regex": query, "$options": "i"}},
            ]},
            {"doc_id": 1, "case_num": 1, "case_name": 1,
             "date": 1, "court": 1, "validity_status": 1,
             "appeal_chain_parsed": 1, "legislation_parsed": 1}
        ).limit(10))

        if not results:
            st.info("No cases found.")
        else:
            st.markdown(f"**{len(results)} result(s)**")
            for rec in results:
                with st.expander(f"{rec.get('case_num', rec['doc_id'])} — {rec.get('date', '')}"):
                    c1, c2 = st.columns(2)
                    with c1:
                        st.markdown(f"**Doc ID:** `{rec['doc_id']}`")
                        st.markdown(f"**Court:** {rec.get('court', 'N/A')}")
                        st.markdown(f"**Date:** {rec.get('date', 'N/A')}")
                        vs = rec.get("validity_status", "good_law")
                        color = {"good_law": "green", "no_longer_good_law": "red",
                                 "partially_invalidated": "orange"}.get(vs, "grey")
                        st.markdown(f"**Validity:** :{color}[{vs.replace('_', ' ').title()}]")

                    with c2:
                        if driver is not None:
                            doc_id = rec["doc_id"]
                            with driver.session() as s:
                                cits = s.run("""
                                    MATCH (a:Case {doc_id:$id})-[t:TREATED_BY]->(b:Case)
                                    RETURN t.treatment_type AS tp,
                                           b.case_name AS cited,
                                           t.effective_date AS date
                                    LIMIT 10
                                """, id=doc_id).data()

                            if cits:
                                st.markdown("**Citations from this case:**")
                                for c in cits:
                                    tp = c.get("tp", "")
                                    badge_map = {
                                        "followed": "badge-followed",
                                        "overruled": "badge-overruled",
                                        "distinguished": "badge-distinguished",
                                        "doubted": "badge-doubted"
                                    }
                                    badge = badge_map.get(tp, "")
                                    st.markdown(
                                        f'<span class="edge-badge {badge}">{tp}</span> '
                                        f'<span style="color:#374151;font-size:0.82rem;">{c.get("cited","Unknown")}</span>',
                                        unsafe_allow_html=True
                                    )
                            else:
                                st.caption("No citation edges found in KG.")