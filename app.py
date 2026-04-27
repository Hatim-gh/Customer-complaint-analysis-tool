import html
from pathlib import Path

import pandas as pd
import streamlit as st

from utils.analyzer import analyze_complaint
from utils.live_store import LIVE_DATA_COLUMNS, append_live_record, clear_live_data, load_live_data
from utils.vector_db import search_similar


st.set_page_config(
    page_title="Banking Complaint Command Center",
    page_icon="🏦",
    layout="wide",
    initial_sidebar_state="expanded",
)


REFERENCE_DATA_FILE = Path("data/complaints.csv")


def inject_styles() -> None:
    st.markdown(
        """
        <style>
            :root {
                --bg: #071019;
                --bg-deep: #030712;
                --panel: rgba(7, 16, 28, 0.78);
                --panel-strong: rgba(8, 19, 33, 0.94);
                --panel-border: rgba(148, 163, 184, 0.14);
                --panel-border-strong: rgba(125, 211, 252, 0.22);
                --text: #e8eef7;
                --muted: #8fa6bf;
                --accent: #7dd3fc;
                --accent-strong: #38bdf8;
                --accent-warm: #f59e0b;
                --danger: #fb7185;
                --success: #34d399;
                --shadow: 0 24px 70px rgba(2, 6, 23, 0.42);
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(56, 189, 248, 0.16), transparent 30%),
                    radial-gradient(circle at 85% 10%, rgba(245, 158, 11, 0.12), transparent 18%),
                    linear-gradient(180deg, #071019 0%, #030712 100%);
                color: var(--text);
                font-family: "Aptos", "Segoe UI", sans-serif;
                overflow-x: hidden;
            }

            [data-testid="stAppViewContainer"] {
                overflow-x: hidden;
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            [data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, rgba(6, 16, 28, 0.98), rgba(4, 10, 18, 0.98));
                border-right: 1px solid rgba(148, 163, 184, 0.1);
            }

            .block-container {
                padding-top: 1.5rem;
                padding-bottom: 3rem;
                max-width: 1320px;
            }

            [data-testid="stHorizontalBlock"] > div {
                min-width: 0;
            }

            h1, h2, h3 {
                color: #f8fafc;
                font-family: "Bahnschrift", "Aptos", sans-serif;
                letter-spacing: -0.03em;
            }

            p, label, .stCaption, .stMarkdown, .stText {
                color: var(--text);
            }

            .hero-shell {
                display: grid;
                grid-template-columns: minmax(0, 1.3fr) minmax(320px, 0.95fr);
                gap: 1.4rem;
                align-items: stretch;
                position: relative;
                overflow: hidden;
                padding: clamp(1.2rem, 2.5vw, 2rem);
                margin: 0 0 1.35rem 0;
                width: 100%;
                min-height: 0;
                border: 1px solid rgba(125, 211, 252, 0.14);
                border-radius: 30px;
                background:
                    radial-gradient(circle at 18% 15%, rgba(56, 189, 248, 0.13), transparent 24%),
                    radial-gradient(circle at 88% 20%, rgba(245, 158, 11, 0.11), transparent 16%),
                    linear-gradient(135deg, rgba(8, 19, 33, 0.98), rgba(4, 10, 19, 0.94));
                box-shadow: var(--shadow);
                isolation: isolate;
                animation: heroEntrance 0.8s ease-out both;
                box-sizing: border-box;
            }

            .hero-shell::before {
                content: "";
                position: absolute;
                inset: 0;
                background:
                    linear-gradient(120deg, rgba(125, 211, 252, 0.08), transparent 45%),
                    linear-gradient(180deg, transparent 60%, rgba(3, 7, 18, 0.35));
                pointer-events: none;
            }

            .hero-copy-group,
            .hero-visual {
                position: relative;
                z-index: 1;
                min-width: 0;
            }

            .eyebrow {
                margin: 0 0 0.6rem 0;
                color: var(--accent);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.18em;
                text-transform: uppercase;
            }

            .hero-title {
                margin: 0;
                font-size: clamp(2rem, 4.1vw, 3.7rem);
                line-height: 0.95;
                max-width: 11ch;
            }

            .hero-copy {
                max-width: 52ch;
                margin: 0.95rem 0 1.05rem 0;
                color: #cad8e8;
                font-size: clamp(0.98rem, 1.4vw, 1.05rem);
                line-height: 1.65;
            }

            .hero-stat-row {
                display: grid;
                grid-template-columns: repeat(3, minmax(0, 1fr));
                gap: 0.75rem;
                margin-top: 1rem;
            }

            .hero-stat {
                min-width: 0;
                padding: 0.9rem 0.95rem;
                border-radius: 18px;
                border: 1px solid rgba(148, 163, 184, 0.12);
                background: rgba(9, 17, 29, 0.5);
                backdrop-filter: blur(12px);
            }

            .hero-stat-value {
                display: block;
                margin-bottom: 0.18rem;
                color: #f8fafc;
                font-size: 1.15rem;
                font-weight: 700;
            }

            .hero-stat-label {
                color: #a9bdd3;
                font-size: 0.84rem;
                line-height: 1.45;
            }

            .hero-visual {
                display: grid;
                gap: 0.85rem;
                align-content: stretch;
                min-height: 100%;
            }

            .hero-side-panel,
            .hero-side-card {
                position: relative;
                padding: 1.05rem 1.1rem;
                border-radius: 24px;
                border: 1px solid rgba(148, 163, 184, 0.16);
                background:
                    linear-gradient(180deg, rgba(10, 21, 36, 0.9), rgba(4, 10, 18, 0.96));
                box-shadow: 0 18px 36px rgba(2, 6, 23, 0.24);
            }

            .hero-side-panel {
                display: grid;
                gap: 1rem;
                min-height: 100%;
            }

            .hero-side-label {
                color: #93a7bb;
                font-size: 0.76rem;
                text-transform: uppercase;
                letter-spacing: 0.16em;
            }

            .hero-side-title {
                margin-top: 0.4rem;
                color: #f8fafc;
                font-size: 1.2rem;
                font-weight: 700;
                line-height: 1.25;
            }

            .hero-side-copy {
                margin-top: 0.5rem;
                color: #c6d3e3;
                line-height: 1.6;
            }

            .hero-glance-grid {
                display: grid;
                grid-template-columns: repeat(2, minmax(0, 1fr));
                gap: 0.7rem;
            }

            .hero-glance-item {
                padding: 0.9rem;
                border-radius: 18px;
                border: 1px solid rgba(148, 163, 184, 0.12);
                background: rgba(6, 14, 24, 0.8);
            }

            .hero-glance-label {
                color: #90a7c0;
                font-size: 0.75rem;
                text-transform: uppercase;
                letter-spacing: 0.13em;
            }

            .hero-glance-value {
                margin-top: 0.4rem;
                color: #f8fafc;
                font-size: 1.18rem;
                font-weight: 700;
                line-height: 1.2;
                word-break: break-word;
            }

            .hero-side-card {
                background:
                    linear-gradient(180deg, rgba(8, 17, 29, 0.92), rgba(5, 11, 20, 0.98));
            }

            .section-kicker {
                margin: 1.6rem 0 0.35rem 0;
                color: var(--accent);
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.14em;
                text-transform: uppercase;
            }

            .section-title {
                margin: 0 0 0.4rem 0;
                font-size: clamp(1.45rem, 2.4vw, 2.15rem);
                font-weight: 700;
                color: #f8fafc;
            }

            .section-copy {
                max-width: 72ch;
                margin: 0 0 1.15rem 0;
                color: var(--muted);
                line-height: 1.6;
            }

            .metric-panel,
            .insight-panel {
                padding: 1.05rem 1.1rem;
                border-radius: 24px;
                border: 1px solid var(--panel-border);
                background:
                    linear-gradient(180deg, rgba(9, 19, 32, 0.78), rgba(5, 11, 20, 0.96));
                min-height: 150px;
                box-shadow: 0 18px 36px rgba(2, 6, 23, 0.18);
            }

            .metric-label,
            .insight-label {
                color: #9ab0c7;
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.13em;
            }

            .metric-value,
            .insight-value {
                margin-top: 0.8rem;
                color: #f8fafc;
                font-size: clamp(1.45rem, 2vw, 2.15rem);
                font-weight: 700;
                line-height: 1.05;
                word-break: break-word;
            }

            .metric-detail,
            .insight-detail {
                margin-top: 0.7rem;
                color: #c2d0e1;
                line-height: 1.5;
            }

            .info-strip {
                margin-top: 0.9rem;
                padding: 1rem 1.05rem;
                border-radius: 22px;
                border: 1px solid rgba(125, 211, 252, 0.16);
                background: rgba(7, 18, 31, 0.76);
                color: #dbeafe;
                line-height: 1.6;
            }

            .surface-note {
                padding: 1rem 1.05rem;
                border-radius: 22px;
                border: 1px solid rgba(148, 163, 184, 0.16);
                background: rgba(7, 18, 31, 0.72);
                color: #d7e5f7;
                line-height: 1.6;
            }

            .surface-note strong {
                color: #f8fafc;
            }

            .process-shell,
            .text-surface {
                padding: 1.05rem 1.1rem;
                border-radius: 24px;
                border: 1px solid var(--panel-border);
                background: linear-gradient(180deg, rgba(9, 19, 32, 0.78), rgba(5, 11, 20, 0.96));
                box-shadow: 0 18px 36px rgba(2, 6, 23, 0.18);
            }

            .process-shell + .surface-note,
            .text-surface + .text-surface {
                margin-top: 0.9rem;
            }

            .process-kicker,
            .text-surface-label {
                color: var(--accent);
                font-size: 0.78rem;
                font-weight: 700;
                text-transform: uppercase;
                letter-spacing: 0.14em;
            }

            .process-title,
            .text-surface-title {
                margin-top: 0.45rem;
                color: #f8fafc;
                font-size: 1.2rem;
                font-weight: 700;
                line-height: 1.25;
            }

            .text-surface-body {
                margin-top: 0.7rem;
                color: #c9d7e7;
                line-height: 1.7;
                white-space: normal;
            }

            .process-list {
                margin-top: 1rem;
                display: grid;
                gap: 0.85rem;
            }

            .process-step {
                display: grid;
                grid-template-columns: 40px minmax(0, 1fr);
                gap: 0.75rem;
                align-items: start;
            }

            .process-step-index {
                width: 40px;
                height: 40px;
                border-radius: 14px;
                border: 1px solid rgba(125, 211, 252, 0.18);
                background: rgba(12, 28, 46, 0.72);
                color: #f8fafc;
                display: grid;
                place-items: center;
                font-weight: 700;
            }

            .process-step-title {
                color: #f8fafc;
                font-size: 0.98rem;
                font-weight: 700;
            }

            .process-step-copy {
                margin-top: 0.2rem;
                color: #b9cade;
                font-size: 0.93rem;
                line-height: 1.55;
            }

            div[data-testid="stForm"] {
                border: 1px solid var(--panel-border-strong);
                border-radius: 28px;
                padding: 0.9rem 1rem 0.25rem;
                background:
                    linear-gradient(180deg, rgba(9, 19, 32, 0.8), rgba(5, 11, 20, 0.96));
                box-shadow: var(--shadow);
                transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
            }

            div[data-testid="stForm"]:hover,
            .metric-panel:hover,
            .process-shell:hover,
            .text-surface:hover,
            div[data-testid="stDataFrame"]:hover,
            div[data-testid="stVegaLiteChart"]:hover {
                transform: translateY(-2px);
                border-color: rgba(125, 211, 252, 0.22);
                box-shadow: 0 26px 52px rgba(2, 6, 23, 0.24);
            }

            .stTextArea textarea {
                min-height: 220px;
                border-radius: 22px;
                border: 1px solid rgba(148, 163, 184, 0.18);
                background: rgba(6, 14, 24, 0.94);
                color: #f8fafc;
                line-height: 1.65;
                padding: 1rem 1rem 1.05rem;
            }

            .stMultiSelect div[data-baseweb="select"],
            .stDateInput input,
            .stSelectbox div[data-baseweb="select"] {
                background: rgba(10, 18, 31, 0.86);
            }

            .stButton > button,
            .stFormSubmitButton > button {
                border: 0;
                border-radius: 999px;
                min-height: 50px;
                padding: 0.8rem 1.45rem;
                background: linear-gradient(135deg, #38bdf8, #2563eb);
                color: #eff6ff;
                font-weight: 700;
                letter-spacing: 0.01em;
                box-shadow: 0 18px 32px rgba(37, 99, 235, 0.26);
                transition: transform 180ms ease, box-shadow 180ms ease, filter 180ms ease;
            }

            .stButton > button:hover,
            .stFormSubmitButton > button:hover {
                filter: brightness(1.06);
                transform: translateY(-1px);
                box-shadow: 0 22px 36px rgba(37, 99, 235, 0.32);
            }

            div[data-testid="stDataFrame"],
            div[data-testid="stVegaLiteChart"] {
                border: 1px solid var(--panel-border);
                border-radius: 24px;
                padding: 0.45rem;
                background:
                    linear-gradient(180deg, rgba(9, 19, 32, 0.72), rgba(5, 11, 20, 0.94));
                box-shadow: 0 18px 36px rgba(2, 6, 23, 0.18);
                transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
            }

            [data-testid="stDataFrame"],
            [data-testid="stMetric"] {
                background: transparent;
            }

            [data-testid="stMetricValue"] {
                color: #f8fafc;
            }

            [data-testid="stSidebar"] [data-testid="stMetric"] {
                border: 1px solid rgba(148, 163, 184, 0.1);
                border-radius: 20px;
                padding: 0.65rem 0.75rem;
                background: rgba(8, 17, 30, 0.58);
            }

            .stTabs [data-baseweb="tab-list"] {
                gap: 0.5rem;
            }

            .stTabs [data-baseweb="tab"] {
                height: auto;
                padding: 0.7rem 1rem;
                border-radius: 999px;
                background: rgba(8, 17, 30, 0.78);
                color: #c9d6e5;
                border: 1px solid rgba(148, 163, 184, 0.12);
            }

            .stTabs [aria-selected="true"] {
                background: rgba(56, 189, 248, 0.14);
                color: #f8fafc;
                border-color: rgba(125, 211, 252, 0.26);
            }

            div[data-testid="stAlert"] {
                border-radius: 20px;
                border: 1px solid rgba(148, 163, 184, 0.14);
                background: rgba(7, 18, 31, 0.84);
            }

            @keyframes heroEntrance {
                from {
                    opacity: 0;
                    transform: translateY(18px);
                }
                to {
                    opacity: 1;
                    transform: translateY(0);
                }
            }

            @media (max-width: 980px) {
                .hero-shell {
                    grid-template-columns: 1fr;
                    padding: 1.3rem;
                    border-radius: 30px;
                }

                .hero-title {
                    max-width: 11ch;
                }

                .hero-stat-row,
                .hero-glance-grid {
                    grid-template-columns: 1fr;
                }
            }

            @media (max-width: 640px) {
                .block-container {
                    padding-top: 1rem;
                    padding-left: 0.85rem;
                    padding-right: 0.85rem;
                    padding-bottom: 2.25rem;
                }

                .hero-shell {
                    padding: 1.1rem;
                    margin-bottom: 1.25rem;
                    border-radius: 26px;
                }

                .hero-title {
                    font-size: 2.15rem;
                    line-height: 0.96;
                }

                .hero-copy {
                    font-size: 0.96rem;
                }

                .hero-stat-row {
                    grid-template-columns: 1fr;
                }

                .hero-side-panel,
                .hero-side-card {
                    border-radius: 20px;
                }

                .metric-panel,
                .insight-panel,
                .process-shell,
                .text-surface {
                    border-radius: 22px;
                }

                .stTextArea textarea {
                    min-height: 180px;
                }

                .stButton > button,
                .stFormSubmitButton > button {
                    width: 100%;
                }
            }
        </style>
        """,
        unsafe_allow_html=True,
    )
@st.cache_data(show_spinner=False)
def load_data() -> pd.DataFrame:
    data = pd.read_csv(REFERENCE_DATA_FILE)
    data["Date"] = pd.to_datetime(data["Date"], errors="coerce")
    data["Month"] = data["Date"].dt.to_period("M").dt.to_timestamp()
    data["Year"] = data["Date"].dt.year
    return data


def render_metric_card(label: str, value: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="metric-panel">
            <div class="metric-label">{label}</div>
            <div class="metric-value">{value}</div>
            <div class="metric-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_insight_card(label: str, value: str, detail: str) -> None:
    st.markdown(
        f"""
        <div class="insight-panel">
            <div class="insight-label">{label}</div>
            <div class="insight-value">{value}</div>
            <div class="insight-detail">{detail}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_section_header(kicker: str, title: str, copy: str) -> None:
    st.markdown(
        f"""
        <div class="section-kicker">{html.escape(kicker)}</div>
        <div class="section-title">{html.escape(title)}</div>
        <div class="section-copy">{html.escape(copy)}</div>
        """,
        unsafe_allow_html=True,
    )


def render_text_surface(label: str, title: str, body: str) -> None:
    safe_body = html.escape(body).replace("\n", "<br>")
    st.markdown(
        f"""
        <div class="text-surface">
            <div class="text-surface-label">{html.escape(label)}</div>
            <div class="text-surface-title">{html.escape(title)}</div>
            <div class="text-surface-body">{safe_body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_process_surface() -> None:
    st.markdown(
        """
        <div class="process-shell">
            <div class="process-kicker">Live triage flow</div>
            <div class="process-title">What happens after a complaint is submitted</div>
            <div class="process-list">
                <div class="process-step">
                    <div class="process-step-index">1</div>
                    <div>
                        <div class="process-step-title">Sentiment model reads the customer tone</div>
                        <div class="process-step-copy">The Transformers pipeline estimates whether the case arrives as positive or negative language.</div>
                    </div>
                </div>
                <div class="process-step">
                    <div class="process-step-index">2</div>
                    <div>
                        <div class="process-step-title">Rules map the issue into a banking category</div>
                        <div class="process-step-copy">Keyword logic adds a complaint category and a short explanation that support teams can scan quickly.</div>
                    </div>
                </div>
                <div class="process-step">
                    <div class="process-step-index">3</div>
                    <div>
                        <div class="process-step-title">Embeddings pull related historical examples</div>
                        <div class="process-step-copy">Similarity search compares the new complaint with the static reference archive for context and precedent.</div>
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def build_trend_spec() -> dict:
    return {
        "height": 320,
        "mark": {
            "type": "line",
            "point": {"filled": True, "size": 84},
            "strokeWidth": 3,
            "interpolate": "monotone",
            "color": "#38bdf8",
        },
        "encoding": {
            "x": {
                "field": "RecordedAt",
                "type": "temporal",
                "title": None,
                "axis": {"labelAngle": -25, "format": "%d %b %H:%M"},
            },
            "y": {
                "field": "Complaints",
                "type": "quantitative",
                "title": "Analyses",
            },
            "tooltip": [
                {"field": "RecordedAt", "type": "temporal", "title": "Recorded at"},
                {"field": "Complaints", "type": "quantitative", "title": "Analyses"},
            ],
        },
        "config": {
            "background": None,
            "view": {"stroke": None},
            "axis": {
                "domain": False,
                "gridColor": "rgba(148,163,184,0.12)",
                "labelColor": "#9fb3c8",
                "tickColor": "rgba(148,163,184,0.12)",
                "titleColor": "#dbeafe",
            },
        },
    }


def build_donut_spec() -> dict:
    return {
        "height": 320,
        "mark": {"type": "arc", "innerRadius": 74, "outerRadius": 122},
        "encoding": {
            "theta": {"field": "Count", "type": "quantitative"},
            "color": {
                "field": "Sentiment",
                "type": "nominal",
                "scale": {
                    "domain": ["Negative", "Positive"],
                    "range": ["#fb7185", "#34d399"],
                },
                "legend": {"title": None, "labelColor": "#dbeafe"},
            },
            "tooltip": [
                {"field": "Sentiment", "type": "nominal"},
                {"field": "Count", "type": "quantitative"},
            ],
        },
        "config": {"background": None, "view": {"stroke": None}},
    }


def build_category_bar_spec() -> dict:
    return {
        "height": 320,
        "mark": {"type": "bar", "cornerRadiusEnd": 8, "color": "#38bdf8"},
        "encoding": {
            "x": {"field": "Count", "type": "quantitative", "title": "Cases"},
            "y": {
                "field": "Category",
                "type": "nominal",
                "sort": "-x",
                "title": None,
            },
            "tooltip": [
                {"field": "Category", "type": "nominal"},
                {"field": "Count", "type": "quantitative"},
            ],
        },
        "config": {
            "background": None,
            "view": {"stroke": None},
            "axis": {
                "domain": False,
                "gridColor": "rgba(148,163,184,0.12)",
                "labelColor": "#9fb3c8",
                "tickColor": "rgba(148,163,184,0.12)",
                "titleColor": "#dbeafe",
            },
        },
    }


def build_sentiment_by_category_spec(category_order: list[str]) -> dict:
    return {
        "height": 320,
        "mark": {"type": "bar", "cornerRadiusTopLeft": 6, "cornerRadiusTopRight": 6},
        "encoding": {
            "x": {
                "field": "Category",
                "type": "nominal",
                "sort": category_order,
                "title": None,
                "axis": {"labelAngle": -22},
            },
            "y": {"field": "Count", "type": "quantitative", "title": "Cases"},
            "color": {
                "field": "Sentiment",
                "type": "nominal",
                "scale": {
                    "domain": ["Negative", "Positive"],
                    "range": ["#fb7185", "#34d399"],
                },
                "legend": {"title": None, "labelColor": "#dbeafe"},
            },
            "tooltip": [
                {"field": "Category", "type": "nominal"},
                {"field": "Sentiment", "type": "nominal"},
                {"field": "Count", "type": "quantitative"},
            ],
        },
        "config": {
            "background": None,
            "view": {"stroke": None},
            "axis": {
                "domain": False,
                "gridColor": "rgba(148,163,184,0.12)",
                "labelColor": "#9fb3c8",
                "tickColor": "rgba(148,163,184,0.12)",
                "titleColor": "#dbeafe",
            },
        },
    }


inject_styles()
reference_data = load_data()
live_data = load_live_data()

if "analysis_result" not in st.session_state:
    st.session_state.analysis_result = None


st.sidebar.markdown("## Command Center")
st.sidebar.caption("Operational view of the live complaint pipeline and saved analyses.")
st.sidebar.metric("Reference Complaints", len(reference_data))
st.sidebar.metric("Saved Live Analyses", len(live_data))
st.sidebar.markdown(
    """
    <div class="surface-note">
        <strong>Control note</strong><br>
        The historical CSV powers similarity search. The charts and register below react only to live analyses saved into the database.
    </div>
    """,
    unsafe_allow_html=True,
)

if st.sidebar.button("Clear Live Dashboard"):
    clear_live_data()
    st.session_state.analysis_result = None
    st.rerun()

dashboard_df = live_data.copy()
if not dashboard_df.empty:
    dashboard_df["RecordedAt"] = pd.to_datetime(dashboard_df["RecordedAt"])
    dashboard_df["RecordedBucket"] = dashboard_df["RecordedAt"].dt.floor("min")
else:
    dashboard_df = pd.DataFrame(
        columns=[
            "Complaint",
            "Sentiment",
            "Category",
            "Summary",
            "Reason",
            "RecordedAt",
            "RecordedBucket",
        ]
    )

trend_counts = (
    dashboard_df.groupby("RecordedBucket")
    .size()
    .reset_index(name="Complaints")
    .rename(columns={"RecordedBucket": "RecordedAt"})
    .sort_values("RecordedAt")
    if not dashboard_df.empty
    else pd.DataFrame(columns=["RecordedAt", "Complaints"])
)
category_counts = (
    dashboard_df.groupby("Category")
    .size()
    .reset_index(name="Count")
    .sort_values("Count", ascending=False)
    if not dashboard_df.empty
    else pd.DataFrame(columns=["Category", "Count"])
)
sentiment_counts = (
    dashboard_df.groupby("Sentiment")
    .size()
    .reset_index(name="Count")
    .sort_values("Count", ascending=False)
    if not dashboard_df.empty
    else pd.DataFrame(columns=["Sentiment", "Count"])
)
sentiment_by_category = (
    dashboard_df.groupby(["Category", "Sentiment"])
    .size()
    .reset_index(name="Count")
    if not dashboard_df.empty
    else pd.DataFrame(columns=["Category", "Sentiment", "Count"])
)

total_cases = len(dashboard_df)
negative_cases = int(dashboard_df["Sentiment"].eq("Negative").sum()) if not dashboard_df.empty else 0
negative_rate = (negative_cases / total_cases * 100) if total_cases else 0
top_category = category_counts.iloc[0]["Category"] if not category_counts.empty else "No live data"
top_category_count = int(category_counts.iloc[0]["Count"]) if not category_counts.empty else 0
latest_record = dashboard_df["RecordedAt"].max() if not dashboard_df.empty else pd.NaT
avg_live_per_minute = trend_counts["Complaints"].mean() if not trend_counts.empty else 0
latest_record_label = latest_record.strftime("%d %b %Y %H:%M") if pd.notna(latest_record) else "No live analysis"
reference_window = (
    f"{reference_data['Date'].min().strftime('%d %b %Y')} to {reference_data['Date'].max().strftime('%d %b %Y')}"
)

st.markdown(
    f"""
    <div class="hero-shell">
        <div class="hero-copy-group">
            <div class="eyebrow">Banking Complaint Command Center</div>
            <h1 class="hero-title">Operational complaint triage built for live support teams.</h1>
            <p class="hero-copy">
                Run a new complaint through the AI pipeline, capture the result instantly, and
                monitor how live customer issues are shifting across tone, category, and activity.
            </p>
            <div class="hero-stat-row">
                <div class="hero-stat">
                    <span class="hero-stat-value">{total_cases}</span>
                    <span class="hero-stat-label">live analyses stored in the active dashboard</span>
                </div>
                <div class="hero-stat">
                    <span class="hero-stat-value">{negative_rate:.0f}%</span>
                    <span class="hero-stat-label">current negative share across live cases</span>
                </div>
                <div class="hero-stat">
                    <span class="hero-stat-value">{len(reference_data)}</span>
                    <span class="hero-stat-label">reference complaints ready for similarity search</span>
                </div>
            </div>
        </div>
        <div class="hero-visual">
            <div class="hero-side-panel">
                <div>
                    <div class="hero-side-label">Live workspace status</div>
                    <div class="hero-side-title">Track incoming complaint activity without losing the operational context.</div>
                    <div class="hero-side-copy">
                        Each analysis updates the live register, the activity trend, and the sentiment mix immediately.
                        The reference archive stays separate so the dashboard reflects only fresh submissions.
                    </div>
                </div>
                <div class="hero-glance-grid">
                    <div class="hero-glance-item">
                        <div class="hero-glance-label">Top category</div>
                        <div class="hero-glance-value">{top_category}</div>
                    </div>
                    <div class="hero-glance-item">
                        <div class="hero-glance-label">Latest run</div>
                        <div class="hero-glance-value">{latest_record_label}</div>
                    </div>
                    <div class="hero-glance-item">
                        <div class="hero-glance-label">Avg per minute</div>
                        <div class="hero-glance-value">{avg_live_per_minute:.1f}</div>
                    </div>
                    <div class="hero-glance-item">
                        <div class="hero-glance-label">Negative cases</div>
                        <div class="hero-glance-value">{negative_cases}</div>
                    </div>
                </div>
            </div>
            <div class="hero-side-card">
                <div class="hero-side-label">Reference knowledge base</div>
                <div class="hero-side-title">{len(reference_data)} archived complaints available</div>
                <div class="hero-side-copy">
                    Coverage window: {reference_window}<br><br>
                    Historical records stay available for similarity search and case comparison while the
                    live dashboard remains focused on new analyses only.
                </div>
            </div>
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

metric_cols = st.columns(4, gap="medium")
with metric_cols[0]:
    render_metric_card("Live Cases", str(total_cases), f"{avg_live_per_minute:.1f} average analyses per active minute")
with metric_cols[1]:
    render_metric_card("Negative Share", f"{negative_rate:.0f}%", f"{negative_cases} live complaints classified as negative")
with metric_cols[2]:
    render_metric_card("Top Live Category", top_category, f"{top_category_count} analyses in the leading category")
with metric_cols[3]:
    render_metric_card("Latest Analysis", latest_record_label, "Updates each time a new complaint is analyzed")

render_section_header(
    "AI Triage Workspace",
    "Analyze a new customer complaint",
    "Run the complaint through sentiment analysis, summarization, category reasoning, and similarity search. Every successful analysis is written into the live dashboard below.",
)

workspace_col, insight_col = st.columns([1.45, 0.9], gap="large")

with workspace_col:
    st.markdown(
        """
        <div class="surface-note">
            <strong>Input guidance</strong><br>
            Paste a real customer complaint with enough detail for the model to capture tone,
            summarize the issue, and match it against the reference archive.
        </div>
        """,
        unsafe_allow_html=True,
    )
    with st.form("complaint-analysis-form"):
        complaint_text = st.text_area(
            "Complaint text",
            placeholder="Example: Unauthorized debit card transaction is still not reversed and support has not responded for three days.",
        )
        submitted = st.form_submit_button("Run AI Triage")

    if submitted:
        if complaint_text.strip():
            with st.spinner("Analyzing complaint and retrieving similar cases..."):
                sentiment, category, summary, reason = analyze_complaint(complaint_text)
                similar_cases = search_similar(complaint_text, k=3).copy()
                recorded_at = pd.Timestamp.now()
                st.session_state.analysis_result = {
                    "complaint": complaint_text,
                    "sentiment": sentiment,
                    "category": category,
                    "summary": summary,
                    "reason": reason,
                    "recorded_at": recorded_at,
                    "similar_cases": similar_cases,
                }
                append_live_record(
                    {
                        "Complaint": complaint_text,
                        "Sentiment": sentiment,
                        "Category": category,
                        "Summary": summary,
                        "Reason": reason,
                        "RecordedAt": recorded_at.isoformat(),
                    }
                )
                st.rerun()
        else:
            st.warning("Please enter a complaint before running the analysis.")

with insight_col:
    render_process_surface()
    st.markdown(
        f"""
        <div class="info-strip">
            <strong>Pipeline note</strong><br>
            Similarity search uses {len(reference_data)} archived complaints collected from
            {reference_window}. Those reference records support lookup only and never alter the
            live dashboard counts.
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.analysis_result:
    result = st.session_state.analysis_result

    render_section_header(
        "Triage Output",
        "Latest complaint assessment",
        "This section shows the actual outputs generated by your models, rules, and similarity retrieval for the most recent live analysis.",
    )

    result_cols = st.columns(4, gap="medium")
    with result_cols[0]:
        render_metric_card("Sentiment", result["sentiment"], "Generated by the sentiment-analysis model")
    with result_cols[1]:
        render_metric_card("Category", result["category"], "Derived from category keyword logic")
    with result_cols[2]:
        render_metric_card(
            "Summary Status",
            "Ready" if result["summary"] != "Summary not available" else "Fallback",
            "Shows whether the summarization model returned a result",
        )
    with result_cols[3]:
        render_metric_card(
            "Similar Matches",
            str(len(result["similar_cases"])),
            "Retrieved from the complaint dataset for comparison",
        )

    result_tab, similar_tab = st.tabs(["Assessment", "Similar cases"])
    with result_tab:
        render_text_surface("Customer statement", "Original complaint", result["complaint"])
        summary_col, reason_col = st.columns([1.1, 0.9], gap="large")
        with summary_col:
            render_text_surface("AI summary", "Model-generated synopsis", result["summary"])
        with reason_col:
            render_text_surface("Category reason", "Why this issue was classified here", result["reason"])
    with similar_tab:
        similar_df = result["similar_cases"].copy()
        if "Date" in similar_df.columns:
            similar_df["Date"] = pd.to_datetime(similar_df["Date"], errors="coerce").dt.strftime("%d %b %Y")
        st.dataframe(
            similar_df[["Complaint", "Category", "Sentiment", "Date"]],
            use_container_width=True,
            hide_index=True,
        )

render_section_header(
    "Complaint Intelligence",
    "Live complaint analytics",
    "These charts refresh from complaints stored in the live database. Historical CSV data is used only for similarity search, not for the chart values.",
)

if dashboard_df.empty:
    st.info("Analyze at least one complaint to populate the live dashboard charts.")
else:
    chart_row_1 = st.columns([1.4, 1], gap="large")
    with chart_row_1[0]:
        st.markdown("#### Live analysis activity")
        st.caption("Counts how many complaints were analyzed over time in the live database.")
        st.vega_lite_chart(trend_counts, build_trend_spec(), use_container_width=True)
    with chart_row_1[1]:
        st.markdown("#### Live sentiment mix")
        st.caption("Distribution of model sentiment outputs in the live database.")
        st.vega_lite_chart(sentiment_counts, build_donut_spec(), use_container_width=True)

    chart_row_2 = st.columns(2, gap="large")
    with chart_row_2[0]:
        st.markdown("#### Live category distribution")
        st.caption("Predicted categories from live complaint analyses.")
        st.vega_lite_chart(category_counts, build_category_bar_spec(), use_container_width=True)
    with chart_row_2[1]:
        st.markdown("#### Live sentiment by category")
        st.caption("How live sentiment results are distributed across predicted categories.")
        st.vega_lite_chart(
            sentiment_by_category,
            build_sentiment_by_category_spec(category_counts["Category"].tolist()),
            use_container_width=True,
        )

render_section_header(
    "Case Register",
    "Live analysis register",
    "Each complaint analyzed in the workspace is saved to the live database and immediately reflected in the register and charts.",
)

if dashboard_df.empty:
    st.info("No live analyses yet. Submit a complaint above to start building the dashboard.")
else:
    table_df = dashboard_df.sort_values("RecordedAt", ascending=False).copy()
    table_df["RecordedAt"] = table_df["RecordedAt"].dt.strftime("%d %b %Y %H:%M")
    st.dataframe(
        table_df[["RecordedAt", "Complaint", "Category", "Sentiment"]],
        use_container_width=True,
        hide_index=True,
    )
