import pandas as pd
import streamlit as st
from pathlib import Path

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
                --bg: #06111f;
                --bg-soft: rgba(13, 24, 43, 0.82);
                --panel: rgba(10, 23, 39, 0.76);
                --panel-border: rgba(148, 163, 184, 0.18);
                --text: #e2e8f0;
                --muted: #8aa0bc;
                --accent: #38bdf8;
                --accent-strong: #0ea5e9;
                --warning: #f97316;
                --danger: #fb7185;
                --success: #34d399;
            }

            .stApp {
                background:
                    radial-gradient(circle at top left, rgba(14, 165, 233, 0.14), transparent 28%),
                    radial-gradient(circle at top right, rgba(251, 113, 133, 0.12), transparent 24%),
                    linear-gradient(180deg, #08111e 0%, #040a13 100%);
                color: var(--text);
                font-family: "Aptos", "Segoe UI", sans-serif;
            }

            [data-testid="stHeader"] {
                background: transparent;
            }

            [data-testid="stSidebar"] {
                background:
                    linear-gradient(180deg, rgba(7, 18, 32, 0.98), rgba(5, 13, 24, 0.98));
                border-right: 1px solid rgba(148, 163, 184, 0.12);
            }

            .block-container {
                padding-top: 2.1rem;
                padding-bottom: 2.5rem;
                max-width: 1380px;
            }

            h1, h2, h3 {
                color: #f8fafc;
                font-family: "Bahnschrift", "Aptos", sans-serif;
                letter-spacing: -0.02em;
            }

            p, label, .stCaption, .stMarkdown, .stText {
                color: var(--text);
            }

            .hero-panel {
                display: grid;
                grid-template-columns: minmax(0, 1.8fr) minmax(280px, 0.9fr);
                gap: 1.2rem;
                padding: 1.5rem;
                margin-bottom: 1.1rem;
                border: 1px solid rgba(56, 189, 248, 0.15);
                border-radius: 28px;
                background:
                    linear-gradient(135deg, rgba(8, 22, 39, 0.96), rgba(6, 17, 31, 0.82)),
                    linear-gradient(135deg, rgba(56, 189, 248, 0.08), rgba(251, 113, 133, 0.04));
                box-shadow: 0 24px 60px rgba(2, 8, 23, 0.45);
            }

            .eyebrow {
                margin: 0 0 0.6rem 0;
                color: #7dd3fc;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.16em;
            }

            .hero-title {
                margin: 0;
                font-size: clamp(2rem, 3.8vw, 3.4rem);
                line-height: 0.98;
                max-width: 12ch;
            }

            .hero-copy {
                max-width: 58ch;
                margin: 0.9rem 0 1.1rem 0;
                color: #bfd3ea;
                font-size: 1rem;
                line-height: 1.65;
            }

            .pill-row {
                display: flex;
                flex-wrap: wrap;
                gap: 0.6rem;
            }

            .hero-pill {
                padding: 0.48rem 0.82rem;
                border-radius: 999px;
                border: 1px solid rgba(148, 163, 184, 0.18);
                background: rgba(15, 23, 42, 0.55);
                color: #dbeafe;
                font-size: 0.88rem;
            }

            .hero-aside {
                padding: 1.2rem;
                border-radius: 22px;
                border: 1px solid rgba(148, 163, 184, 0.16);
                background: linear-gradient(180deg, rgba(15, 23, 42, 0.72), rgba(9, 17, 30, 0.92));
                align-self: stretch;
            }

            .hero-aside-label {
                color: #94a3b8;
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.14em;
            }

            .hero-aside-value {
                margin-top: 0.6rem;
                font-size: 2rem;
                font-weight: 700;
                color: #f8fafc;
            }

            .hero-aside-copy {
                margin-top: 0.65rem;
                color: #bfd3ea;
                line-height: 1.6;
            }

            .section-kicker {
                margin: 1.4rem 0 0.25rem 0;
                color: #7dd3fc;
                font-size: 0.78rem;
                font-weight: 700;
                letter-spacing: 0.12em;
                text-transform: uppercase;
            }

            .section-title {
                margin: 0 0 0.35rem 0;
                font-size: 1.55rem;
                font-weight: 700;
                color: #f8fafc;
            }

            .section-copy {
                margin: 0 0 1rem 0;
                color: var(--muted);
                line-height: 1.6;
            }

            .metric-panel,
            .insight-panel {
                padding: 1rem 1.05rem;
                border-radius: 22px;
                border: 1px solid var(--panel-border);
                background:
                    linear-gradient(180deg, rgba(14, 25, 43, 0.72), rgba(7, 14, 24, 0.96));
                min-height: 144px;
            }

            .metric-label,
            .insight-label {
                color: #94a3b8;
                font-size: 0.82rem;
                text-transform: uppercase;
                letter-spacing: 0.12em;
            }

            .metric-value,
            .insight-value {
                margin-top: 0.8rem;
                color: #f8fafc;
                font-size: 2rem;
                font-weight: 700;
                line-height: 1;
            }

            .metric-detail,
            .insight-detail {
                margin-top: 0.7rem;
                color: #bfd3ea;
                line-height: 1.5;
            }

            .info-strip {
                margin-top: 0.8rem;
                padding: 0.85rem 1rem;
                border-radius: 18px;
                border: 1px solid rgba(56, 189, 248, 0.16);
                background: rgba(8, 21, 36, 0.72);
                color: #dbeafe;
                line-height: 1.6;
            }

            .surface-note {
                padding: 0.95rem 1rem;
                border-radius: 18px;
                border: 1px solid rgba(148, 163, 184, 0.16);
                background: rgba(8, 18, 31, 0.74);
                color: #d7e5f7;
                line-height: 1.6;
            }

            .stTextArea textarea {
                min-height: 180px;
                border-radius: 20px;
                border: 1px solid rgba(148, 163, 184, 0.22);
                background: rgba(10, 18, 31, 0.92);
                color: #f8fafc;
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
                padding: 0.72rem 1.35rem;
                background: linear-gradient(135deg, #0ea5e9, #2563eb);
                color: #eff6ff;
                font-weight: 700;
                box-shadow: 0 16px 30px rgba(14, 165, 233, 0.24);
            }

            .stButton > button:hover,
            .stFormSubmitButton > button:hover {
                background: linear-gradient(135deg, #38bdf8, #2563eb);
            }

            [data-testid="stDataFrame"],
            [data-testid="stMetric"] {
                background: transparent;
            }

            [data-testid="stMetricValue"] {
                color: #f8fafc;
            }

            @media (max-width: 980px) {
                .hero-panel {
                    grid-template-columns: 1fr;
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


st.sidebar.markdown("## Live Dashboard")
st.sidebar.caption("These charts update from complaints stored in the live database.")
st.sidebar.metric("Reference Complaints", len(reference_data))
st.sidebar.metric("Saved Live Analyses", len(live_data))

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
    <div class="hero-panel">
        <div>
            <div class="eyebrow">BANKING CX INTELLIGENCE</div>
            <h1 class="hero-title">Live complaint analysis dashboard powered by your pretrained models.</h1>
            <p class="hero-copy">
                Analyze a complaint, generate model outputs in real time, and watch the dashboard
                update from live database activity instead of fixed historical chart data.
            </p>
            <div class="pill-row">
                <div class="hero-pill">{total_cases} live analyses stored</div>
                <div class="hero-pill">{negative_rate:.0f}% live negative share</div>
                <div class="hero-pill">{len(reference_data)} reference complaints loaded for similarity search</div>
            </div>
        </div>
        <div class="hero-aside">
            <div class="hero-aside-label">Reference Knowledge Base</div>
            <div class="hero-aside-value">{len(reference_data)}</div>
            <div class="hero-aside-copy">
                complaint records from {reference_window} are kept only for similarity search,
                demo support, and reference lookup. The live dashboard below is database-backed.
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

st.markdown('<div class="section-kicker">AI Triage Workspace</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Analyze a new customer complaint</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-copy">Run the complaint through sentiment analysis, category reasoning, structured summarization, and similarity search. Each analysis is added to the live dashboard below.</div>',
    unsafe_allow_html=True,
)

workspace_col, insight_col = st.columns([1.45, 0.9], gap="large")

with workspace_col:
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
    render_insight_card("Sentiment Model", "Lightweight NLP", "Uses a deployment-safe sentiment classifier with fallback rules")
    render_insight_card("Category Logic", "Rules", "Maps banking keywords into complaint categories with explanations")
    render_insight_card("Similarity Search", "Token Match", "Retrieves related complaints from the static reference dataset")

    st.markdown(
        """
        <div class="info-strip">
            <strong>Pipeline note</strong><br>
            Sentiment is computed with a lightweight classifier and fallback rules, category is inferred
            from complaint terms, and similar cases are retrieved using token overlap against the reference dataset.
        </div>
        """,
        unsafe_allow_html=True,
    )

if st.session_state.analysis_result:
    result = st.session_state.analysis_result

    st.markdown('<div class="section-kicker">Triage Output</div>', unsafe_allow_html=True)
    st.markdown('<div class="section-title">Latest complaint assessment</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="section-copy">This section presents the actual outputs your project generates from lightweight NLP, rules, and dataset retrieval.</div>',
        unsafe_allow_html=True,
    )

    result_cols = st.columns(4, gap="medium")
    with result_cols[0]:
        render_metric_card("Sentiment", result["sentiment"], "Generated by the lightweight sentiment classifier")
    with result_cols[1]:
        render_metric_card("Category", result["category"], "Derived from category keyword logic")
    with result_cols[2]:
        render_metric_card(
            "Summary Type",
            "Triage",
            "Uses a structured complaint summary for consistent case review",
        )
    with result_cols[3]:
        render_metric_card(
            "Similar Matches",
            str(len(result["similar_cases"])),
            "Retrieved from the complaint dataset for comparison",
        )

    summary_col, reason_col = st.columns([1.15, 0.85], gap="large")
    with summary_col:
        st.markdown("#### AI Summary")
        st.info(result["summary"])
    with reason_col:
        st.markdown("#### Category Reason")
        st.info(result["reason"])

    st.markdown(
        '<div class="section-title" style="font-size:1.2rem; margin-top:1.1rem;">Similar historical complaints</div>',
        unsafe_allow_html=True,
    )
    similar_df = result["similar_cases"].copy()
    if "Date" in similar_df.columns:
        similar_df["Date"] = pd.to_datetime(similar_df["Date"], errors="coerce").dt.strftime("%d %b %Y")
    st.dataframe(
        similar_df[["Complaint", "Category", "Sentiment", "Date"]],
        use_container_width=True,
        hide_index=True,
    )

st.markdown('<div class="section-kicker">Complaint Intelligence</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Live complaint analytics</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-copy">These charts update in real time from complaints stored in the live database. They do not use the historical CSV for chart values.</div>',
    unsafe_allow_html=True,
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

st.markdown('<div class="section-kicker">Case Register</div>', unsafe_allow_html=True)
st.markdown('<div class="section-title">Live analysis register</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="section-copy">Each new complaint analyzed is saved to the live database and immediately reflected in the live charts.</div>',
    unsafe_allow_html=True,
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
