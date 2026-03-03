import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import sqlite3
import logging
import json
from datetime import datetime

# ── Local imports ──────────────────────────────────────────────────────────────
from database import get_historical_sentiment, initialize_db
from stock_data import StockDataFetcher
from advanced_analysis import AdvancedSentimentAnalyzer, TradingSignalGenerator
from config import FEEDS_TO_PROCESS

# ── App-level setup ────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Stock Insight Agent",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded",
)
logging.basicConfig(level=logging.INFO, format="%(levelname)s:%(name)s: %(message)s")

# ── Cached expensive objects ───────────────────────────────────────────────────
@st.cache_resource
def get_stock_fetcher():
    return StockDataFetcher()

@st.cache_resource
def get_analyzers():
    return AdvancedSentimentAnalyzer(), TradingSignalGenerator()

# ── Session State ──────────────────────────────────────────────────────────────
for key, default in {
    "active_company": None,   # dict: {name, ticker, fig}
    "last_refresh": datetime.now().strftime("%H:%M:%S"),
}.items():
    if key not in st.session_state:
        st.session_state[key] = default

# ══════════════════════════════════════════════════════════════════════════════
# THEME / CSS
# ══════════════════════════════════════════════════════════════════════════════
CUSTOM_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

/* ── Global reset ── */
html, body, [class*="css"] {
    font-family: 'Inter', sans-serif !important;
}

/* ── Page background ── */
.stApp {
    background: linear-gradient(135deg, #0a0e1a 0%, #0d1528 50%, #0a0e1a 100%);
    color: #e2e8f0;
}

/* ── Animated gradient header ── */
.dash-header {
    background: linear-gradient(270deg, #6366f1, #8b5cf6, #06b6d4, #10b981, #6366f1);
    background-size: 400% 400%;
    animation: gradientShift 8s ease infinite;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.5px;
    margin-bottom: 0;
}
@keyframes gradientShift {
    0%   { background-position: 0%   50%; }
    50%  { background-position: 100% 50%; }
    100% { background-position: 0%   50%; }
}

.dash-subtitle {
    color: #64748b;
    font-size: 0.85rem;
    margin-top: 2px;
    letter-spacing: 0.5px;
}

/* ── KPI cards ── */
.kpi-card {
    background: rgba(255,255,255,0.04);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 18px 20px;
    position: relative;
    overflow: hidden;
    transition: transform 0.2s ease, box-shadow 0.2s ease;
}
.kpi-card:hover {
    transform: translateY(-2px);
    box-shadow: 0 8px 32px rgba(99,102,241,0.18);
}
.kpi-card::before {
    content: '';
    position: absolute;
    top: 0; left: 0;
    width: 100%; height: 3px;
}
.kpi-card.kpi-total::before  { background: linear-gradient(90deg, #6366f1, #8b5cf6); }
.kpi-card.kpi-pos::before    { background: linear-gradient(90deg, #10b981, #34d399); }
.kpi-card.kpi-neg::before    { background: linear-gradient(90deg, #ef4444, #f87171); }
.kpi-card.kpi-impact::before { background: linear-gradient(90deg, #f59e0b, #fbbf24); }

.kpi-label {
    font-size: 0.72rem;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #64748b;
    font-weight: 600;
}
.kpi-value {
    font-size: 2rem;
    font-weight: 700;
    line-height: 1.1;
    margin-top: 4px;
}
.kpi-total .kpi-value  { color: #a5b4fc; }
.kpi-pos   .kpi-value  { color: #34d399; }
.kpi-neg   .kpi-value  { color: #f87171; }
.kpi-impact .kpi-value { color: #fbbf24; }
.kpi-delta {
    font-size: 0.75rem;
    color: #475569;
    margin-top: 2px;
}

/* ── Section headers ── */
.section-header {
    font-size: 1rem;
    font-weight: 600;
    color: #94a3b8;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin: 16px 0 10px;
    padding-bottom: 6px;
    border-bottom: 1px solid rgba(255,255,255,0.06);
}

/* ── Insight cards ── */
.insight-card {
    background: rgba(15, 23, 42, 0.7);
    border: 1px solid rgba(255,255,255,0.07);
    border-radius: 14px;
    padding: 18px 20px;
    margin-bottom: 14px;
    position: relative;
    transition: border-color 0.2s;
}
.insight-card:hover { border-color: rgba(99,102,241,0.4); }

.insight-card.pos { border-left: 4px solid #10b981; }
.insight-card.neg { border-left: 4px solid #ef4444; }
.insight-card.neu { border-left: 4px solid #64748b; }

.insight-title {
    font-size: 0.95rem;
    font-weight: 600;
    color: #e2e8f0;
    line-height: 1.4;
    margin-bottom: 8px;
}
.insight-meta {
    display: flex;
    flex-wrap: wrap;
    gap: 8px;
    align-items: center;
    margin-bottom: 8px;
}
.badge {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.7rem;
    font-weight: 600;
    letter-spacing: 0.4px;
}
.badge-pos { background: rgba(16,185,129,0.15); color: #34d399; border: 1px solid rgba(16,185,129,0.3); }
.badge-neg { background: rgba(239,68,68,0.15);  color: #f87171; border: 1px solid rgba(239,68,68,0.3); }
.badge-neu { background: rgba(100,116,139,0.15);color: #94a3b8; border: 1px solid rgba(100,116,139,0.3); }
.badge-event { background: rgba(99,102,241,0.15); color: #a5b4fc; border: 1px solid rgba(99,102,241,0.3); }
.badge-time  { background: rgba(30,41,59,0.8);    color: #64748b; border: 1px solid rgba(255,255,255,0.05); }

.impact-bar-wrap { margin: 6px 0 4px; }
.impact-bar-label { font-size: 0.68rem; color: #475569; margin-bottom: 2px; }
.impact-bar-outer {
    background: rgba(255,255,255,0.06);
    border-radius: 4px;
    height: 5px;
    overflow: hidden;
}
.impact-bar-inner {
    height: 100%;
    border-radius: 4px;
}

.kf-table { font-size: 0.78rem; color: #94a3b8; margin-top: 6px; }
.kf-table td { padding: 1px 8px 1px 0; }
.kf-key   { color: #64748b; }
.kf-val   { color: #e2e8f0; font-weight: 500; }

/* ── Live price card ── */
.price-card {
    background: rgba(15,23,42,0.85);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 20px;
    margin: 10px 0;
}
.price-main { font-size: 2rem; font-weight: 700; color: #e2e8f0; }
.price-change-pos { color: #34d399; font-size: 1rem; font-weight: 600; }
.price-change-neg { color: #f87171; font-size: 1rem; font-weight: 600; }

/* ── Signal recommendation ── */
.signal-card {
    background: rgba(15,23,42,0.85);
    border: 1px solid rgba(255,255,255,0.08);
    border-radius: 14px;
    padding: 18px;
    text-align: center;
}
.signal-rec {
    font-size: 1.5rem;
    font-weight: 700;
    letter-spacing: 1px;
}
.rec-strong-buy  { color: #34d399; }
.rec-buy         { color: #6ee7b7; }
.rec-hold        { color: #fbbf24; }
.rec-sell        { color: #f97316; }
.rec-strong-sell { color: #f87171; }

/* ── Sidebar ── */
section[data-testid="stSidebar"] {
    background: rgba(10,14,26,0.95) !important;
    border-right: 1px solid rgba(255,255,255,0.06);
}

/* ── Button overrides ── */
.stButton > button {
    background: rgba(99,102,241,0.12) !important;
    color: #a5b4fc !important;
    border: 1px solid rgba(99,102,241,0.3) !important;
    border-radius: 8px !important;
    font-size: 0.8rem !important;
    font-weight: 500 !important;
    transition: all 0.2s !important;
}
.stButton > button:hover {
    background: rgba(99,102,241,0.25) !important;
    border-color: rgba(99,102,241,0.6) !important;
}

/* ── Divider ── */
hr { border-color: rgba(255,255,255,0.06) !important; }

/* ── Streamlit metric override ── */
[data-testid="stMetricValue"] { color: #e2e8f0 !important; }
</style>
"""

# ══════════════════════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════════════════════

SENTIMENT_CSS = {"Positive": "pos", "Negative": "neg", "Neutral": "neu"}
SENTIMENT_BADGE = {"Positive": "badge-pos", "Negative": "badge-neg", "Neutral": "badge-neu"}
SENTIMENT_ICON  = {"Positive": "▲", "Negative": "▼", "Neutral": "●"}
SENTIMENT_COLOR = {"Positive": "#10b981", "Negative": "#ef4444", "Neutral": "#64748b"}

PLOTLY_THEME = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(family="Inter", color="#94a3b8"),
    xaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
    yaxis=dict(gridcolor="rgba(255,255,255,0.04)", zerolinecolor="rgba(255,255,255,0.06)"),
)


def apply_theme(fig, height=300, margin=None):
    if margin is None:
        margin = dict(l=10, r=10, t=30, b=10)
    fig.update_layout(**PLOTLY_THEME, height=height, margin=margin,
                      legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8")))
    return fig


@st.cache_data(ttl=60)
def load_insights(limit=60):
    try:
        conn = sqlite3.connect("insights.db")
        df = pd.read_sql_query(
            "SELECT * FROM insights ORDER BY timestamp DESC LIMIT ?", conn, params=(limit,)
        )
        conn.close()
        return df
    except Exception as e:
        logging.error(f"DB read error: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_stock_price(ticker):
    return get_stock_fetcher().get_stock_price(ticker)


@st.cache_data(ttl=300)
def fetch_technicals(ticker):
    return get_stock_fetcher().get_technical_indicators(ticker, period="3mo")


# ── Chart builders ─────────────────────────────────────────────────────────────

def build_sentiment_history_chart(df, company_name):
    df = df.copy()
    df["date"] = pd.to_datetime(df["timestamp"]).dt.date
    counts = df.groupby(["date", "sentiment"]).size().reset_index(name="count")
    fig = px.bar(
        counts, x="date", y="count", color="sentiment",
        title=f"Sentiment Timeline — {company_name}",
        color_discrete_map={k: SENTIMENT_COLOR[k] for k in SENTIMENT_COLOR},
        barmode="group",
    )
    fig.update_traces(marker_line_width=0)
    return apply_theme(fig, height=320, margin=dict(l=10, r=10, t=40, b=10))


def build_donut(sentiment_counts):
    fig = px.pie(
        values=sentiment_counts.values,
        names=sentiment_counts.index,
        hole=0.62,
        color=sentiment_counts.index,
        color_discrete_map={k: SENTIMENT_COLOR[k] for k in SENTIMENT_COLOR},
    )
    fig.update_traces(textposition="none", hovertemplate="%{label}: %{value}<extra></extra>")
    return apply_theme(fig, height=220)


def build_event_bar(latest_insights):
    ect = latest_insights["event_type"].fillna("General").value_counts().head(6)
    fig = px.bar(
        x=ect.values, y=ect.index, orientation="h",
        color=ect.index,
        color_discrete_sequence=["#6366f1", "#8b5cf6", "#06b6d4", "#10b981", "#f59e0b", "#ef4444"],
    )
    fig.update_traces(marker_line_width=0)
    fig.update_layout(showlegend=False)
    return apply_theme(fig, height=200, margin=dict(l=10, r=10, t=10, b=10))


def build_impact_histogram(latest_insights):
    fig = px.histogram(
        latest_insights, x="impact_score", nbins=20,
        color_discrete_sequence=["#6366f1"],
    )
    fig.update_traces(marker_line_width=0)
    return apply_theme(fig, height=180, margin=dict(l=10, r=10, t=10, b=10))


def build_technical_chart(tech_df, ticker):
    fig = make_subplots(
        rows=2, cols=1, shared_xaxes=True,
        row_heights=[0.7, 0.3],
        vertical_spacing=0.04,
    )
    # Price + MAs + Bollinger
    fig.add_trace(go.Scatter(
        x=tech_df["Date"], y=tech_df["Close"],
        name="Close", line=dict(color="#6366f1", width=2)
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=tech_df["Date"], y=tech_df["MA_20"],
        name="MA 20", line=dict(color="#f59e0b", width=1, dash="dot")
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=tech_df["Date"], y=tech_df["MA_50"],
        name="MA 50", line=dict(color="#8b5cf6", width=1, dash="dash")
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=tech_df["Date"], y=tech_df["BB_Upper"],
        name="BB Upper", line=dict(color="#475569", width=1),
        fill=None,
    ), row=1, col=1)
    fig.add_trace(go.Scatter(
        x=tech_df["Date"], y=tech_df["BB_Lower"],
        name="BB Lower", line=dict(color="#475569", width=1),
        fill="tonexty", fillcolor="rgba(71,85,105,0.08)",
    ), row=1, col=1)

    # RSI
    fig.add_trace(go.Scatter(
        x=tech_df["Date"], y=tech_df["RSI"],
        name="RSI", line=dict(color="#06b6d4", width=2)
    ), row=2, col=1)
    fig.add_hline(y=70, line=dict(color="#ef4444", width=1, dash="dot"), row=2, col=1)
    fig.add_hline(y=30, line=dict(color="#10b981", width=1, dash="dot"), row=2, col=1)

    fig.update_layout(
        **PLOTLY_THEME,
        height=420,
        margin=dict(l=10, r=10, t=40, b=10),
        title=f"Technical Analysis — {ticker}",
        legend=dict(bgcolor="rgba(0,0,0,0)", font=dict(color="#94a3b8", size=10)),
    )
    fig.update_yaxes(gridcolor="rgba(255,255,255,0.04)")
    return fig


# ── Rendering helpers ──────────────────────────────────────────────────────────

def render_kpi_row(df):
    total = len(df)
    pos = (df["sentiment"] == "Positive").sum()
    neg = (df["sentiment"] == "Negative").sum()
    avg_impact = df["impact_score"].mean() if "impact_score" in df.columns else 0.0

    c1, c2, c3, c4 = st.columns(4)
    for col, css, label, value, delta in [
        (c1, "kpi-total",  "Total Insights",    str(total), "last 60 articles"),
        (c2, "kpi-pos",    "Positive",          f"{pos/total*100:.0f}%" if total else "–", f"{pos} mentions"),
        (c3, "kpi-neg",    "Negative",          f"{neg/total*100:.0f}%" if total else "–", f"{neg} mentions"),
        (c4, "kpi-impact", "Avg Impact Score",  f"{avg_impact:.3f}", "confidence × event weight"),
    ]:
        with col:
            st.markdown(
                f"""<div class="kpi-card {css}">
                      <div class="kpi-label">{label}</div>
                      <div class="kpi-value">{value}</div>
                      <div class="kpi-delta">{delta}</div>
                    </div>""",
                unsafe_allow_html=True,
            )


def render_insight_card(data):
    sentiment = data.get("sentiment", "Neutral")
    css_class  = SENTIMENT_CSS.get(sentiment, "neu")
    badge_css  = SENTIMENT_BADGE.get(sentiment, "badge-neu")
    icon       = SENTIMENT_ICON.get(sentiment, "●")
    confidence = data.get("confidence", 0)
    impact     = float(data.get("impact_score", 0) or 0)
    event_type = data.get("event_type") or "General"
    title      = data.get("article_title", "(No Title)")
    company    = data.get("company_name", "N/A")
    link       = data.get("link", "#")
    try:
        ts = pd.to_datetime(data.get("timestamp")).strftime("%d %b  %H:%M")
    except Exception:
        ts = "—"

    # Impact bar fill (capped at 100%)
    bar_pct = min(impact * 100, 100)
    bar_color = "#10b981" if sentiment == "Positive" else ("#ef4444" if sentiment == "Negative" else "#64748b")

    # Key figures
    kf_html = ""
    kf_json = data.get("key_figures")
    if kf_json and kf_json != "null":
        try:
            kf = json.loads(kf_json)
            priority = [("profit_change_percent", "Profit Δ"), ("revenue_change_percent", "Revenue Δ"),
                        ("profit_amount", "Profit"), ("revenue_amount", "Revenue"),
                        ("deal_size", "Deal Size")]
            rows = "".join(
                f'<tr><td class="kf-key">{lbl}</td><td class="kf-val">{kf[k]}</td></tr>'
                for k, lbl in priority if k in kf
            )
            if rows:
                kf_html = f'<table class="kf-table">{rows}</table>'
        except Exception:
            pass

    card_html = f"""
    <div class="insight-card {css_class}">
        <div class="insight-title">{title}</div>
        <div class="insight-meta">
            <span class="badge badge-pos" style="background:rgba(99,102,241,0.12);color:#a5b4fc;border:1px solid rgba(99,102,241,0.3)">🏢 {company}</span>
            <span class="badge {badge_css}">{icon} {sentiment} &nbsp;{confidence:.0%}</span>
            <span class="badge badge-event">⚡ {event_type}</span>
            <span class="badge badge-time">🕑 {ts}</span>
        </div>
        <div class="impact-bar-wrap">
            <div class="impact-bar-label">Impact Score: {impact:.3f}</div>
            <div class="impact-bar-outer">
                <div class="impact-bar-inner" style="width:{bar_pct:.1f}%;background:{bar_color};"></div>
            </div>
        </div>
        {kf_html}
    </div>
    """
    st.markdown(card_html, unsafe_allow_html=True)
    st.link_button("🔗 Read Article", link)


def render_live_price(ticker, company_name):
    stock = fetch_stock_price(ticker)
    if not stock:
        st.warning(f"Could not fetch live price for **{ticker}**")
        return

    change = stock.get("change", 0)
    change_pct = stock.get("change_percent", 0)
    price = stock.get("current_price", "–")
    direction = "▲" if change > 0 else ("▼" if change < 0 else "▶")
    chg_css = "price-change-pos" if change >= 0 else "price-change-neg"

    mktcap = stock.get("market_cap", "N/A")
    mktcap_str = f"₹{mktcap/1e7:.1f} Cr" if isinstance(mktcap, (int, float)) else "N/A"
    pe = stock.get("pe_ratio", "N/A")
    pe_str = f"{pe:.1f}x" if isinstance(pe, float) else "N/A"

    st.markdown(
        f"""<div class="price-card">
              <div style="font-size:0.75rem;color:#64748b;text-transform:uppercase;letter-spacing:1px">{company_name} · {ticker}.NS</div>
              <div style="display:flex;align-items:baseline;gap:14px;margin-top:6px">
                <div class="price-main">₹{price:,}</div>
                <div class="{chg_css}">{direction} {change:+.2f} ({change_pct:+.2f}%)</div>
              </div>
              <div style="display:flex;gap:18px;flex-wrap:wrap;margin-top:12px;font-size:0.78rem;color:#64748b">
                <span>Low <span style="color:#e2e8f0">₹{stock.get('day_low','–')}</span></span>
                <span>High <span style="color:#e2e8f0">₹{stock.get('day_high','–')}</span></span>
                <span>Prev Close <span style="color:#e2e8f0">₹{stock.get('previous_close','–')}</span></span>
                <span>Volume <span style="color:#e2e8f0">{stock.get('volume',0):,}</span></span>
                <span>P/E <span style="color:#e2e8f0">{pe_str}</span></span>
                <span>Mkt Cap <span style="color:#e2e8f0">{mktcap_str}</span></span>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )


def render_trading_signal(ticker, sentiment_hist_df):
    """Compute and display a trading signal panel."""
    analyzer, generator = get_analyzers()
    if sentiment_hist_df.empty:
        return

    latest_row = sentiment_hist_df.iloc[0]
    sentiment_data = {
        "sentiment": latest_row.get("sentiment", "Neutral"),
        "confidence": float(latest_row.get("confidence", 0.3)),
    }

    stock_data = fetch_stock_price(ticker)
    stock_payload = {}
    if stock_data:
        stock_payload = {
            "change_percent": stock_data.get("change_percent", 0),
            "volume": stock_data.get("volume", 0),
        }

    tech_df = fetch_technicals(ticker)
    result = generator.generate_trading_signal(sentiment_data, stock_payload, tech_df)

    rec = result["recommendation"]
    strength = result["signal_strength"]
    confidence = result["confidence_level"]
    rec_css = {
        "Strong Buy": "rec-strong-buy", "Buy": "rec-buy",
        "Hold": "rec-hold", "Sell": "rec-sell", "Strong Sell": "rec-strong-sell"
    }.get(rec, "rec-hold")

    signal_breakdown = result["individual_signals"]

    st.markdown(
        f"""<div class="signal-card">
              <div style="font-size:0.7rem;color:#475569;text-transform:uppercase;letter-spacing:1px;margin-bottom:4px">AI Trading Signal</div>
              <div class="signal-rec {rec_css}">{rec}</div>
              <div style="font-size:0.78rem;color:#64748b;margin-top:6px">
                Strength: <span style="color:#e2e8f0">{strength:.2f}</span> &nbsp;|&nbsp;
                Confidence: <span style="color:#e2e8f0">{confidence:.2f}</span>
              </div>
            </div>""",
        unsafe_allow_html=True,
    )

    st.markdown("<div style='margin-top:10px'></div>", unsafe_allow_html=True)
    for src, val in signal_breakdown.items():
        label = src.replace("_", " ").title()
        col = "#34d399" if val > 0 else ("#f87171" if val < 0 else "#64748b")
        st.markdown(
            f"<div style='display:flex;justify-content:space-between;font-size:0.78rem;color:#64748b;margin:2px 0'>"
            f"<span>{label}</span><span style='color:{col};font-weight:600'>{val:+.3f}</span></div>",
            unsafe_allow_html=True,
        )


def render_company_drilldown(company_name, ticker):
    """The full detail view when a company card is clicked."""
    st.markdown(
        f"<div class='section-header'>🔍 Detailed View — {company_name}</div>",
        unsafe_allow_html=True,
    )

    left, right = st.columns([1.8, 1])

    with left:
        # Sentiment history chart
        df_hist = get_historical_sentiment(ticker)
        if not df_hist.empty:
            st.plotly_chart(build_sentiment_history_chart(df_hist, company_name),
                            use_container_width=True)
        else:
            st.info("No historical sentiment data available.")

        # Technical chart
        tech_df = fetch_technicals(ticker)
        if tech_df is not None and not tech_df.empty:
            st.plotly_chart(build_technical_chart(tech_df, ticker), use_container_width=True)
        else:
            st.info("Technical indicator data unavailable.")

    with right:
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        render_live_price(ticker, company_name)
        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        df_hist = get_historical_sentiment(ticker)
        render_trading_signal(ticker, df_hist)

    if st.button("⬅ Back to Latest Insights"):
        st.session_state.active_company = None
        st.rerun()


# ══════════════════════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════

def render_sidebar():
    with st.sidebar:
        st.markdown(
            "<div style='font-size:1.1rem;font-weight:700;color:#a5b4fc;margin-bottom:4px'>⚙️ Control Panel</div>",
            unsafe_allow_html=True,
        )
        st.caption(f"Last refreshed: {st.session_state.last_refresh}")
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.cache_data.clear()
            st.session_state.last_refresh = datetime.now().strftime("%H:%M:%S")
            st.rerun()

        st.markdown("---")
        st.markdown("<div class='section-header'>🔎 Stock Lookup</div>", unsafe_allow_html=True)
        ticker_input = st.text_input(
            "NSE Ticker (e.g. RELIANCE, TCS)",
            placeholder="Enter ticker…",
            label_visibility="collapsed",
        ).strip().upper()
        if ticker_input:
            with st.spinner("Fetching live data…"):
                render_live_price(ticker_input, ticker_input)
                # also show mini signal based on advanced analyzer on ticker alone
                tech_df = fetch_technicals(ticker_input)
                if tech_df is not None and not tech_df.empty:
                    latest_rsi = tech_df["RSI"].dropna().iloc[-1] if "RSI" in tech_df else 50
                    latest_close = tech_df["Close"].iloc[-1]
                    ma20 = tech_df["MA_20"].dropna().iloc[-1] if "MA_20" in tech_df else latest_close
                    if latest_close > ma20:
                        mini_sentiment = {"sentiment": "Positive", "confidence": 0.6}
                    elif latest_close < ma20:
                        mini_sentiment = {"sentiment": "Negative", "confidence": 0.6}
                    else:
                        mini_sentiment = {"sentiment": "Neutral", "confidence": 0.3}
                    stock_data = fetch_stock_price(ticker_input)
                    stock_payload = {}
                    if stock_data:
                        stock_payload = {"change_percent": stock_data.get("change_percent", 0),
                                         "volume": stock_data.get("volume", 0)}
                    _, generator = get_analyzers()
                    sig = generator.generate_trading_signal(mini_sentiment, stock_payload, tech_df)
                    rec = sig["recommendation"]
                    rec_css = {
                        "Strong Buy": "rec-strong-buy", "Buy": "rec-buy",
                        "Hold": "rec-hold", "Sell": "rec-sell", "Strong Sell": "rec-strong-sell"
                    }.get(rec, "rec-hold")
                    st.markdown(
                        f"""<div class="signal-card" style="margin-top:8px">
                              <div style="font-size:0.65rem;color:#475569;text-transform:uppercase;letter-spacing:1px">Signal</div>
                              <div class="signal-rec {rec_css}" style="font-size:1.1rem">{rec}</div>
                            </div>""",
                        unsafe_allow_html=True,
                    )

        st.markdown("---")
        st.markdown("<div class='section-header'>📡 Live Feeds</div>", unsafe_allow_html=True)
        for name, cfg in FEEDS_TO_PROCESS.items():
            weight = cfg.get("weight", 1.0)
            st.markdown(
                f"<div style='display:flex;justify-content:space-between;font-size:0.78rem;"
                f"color:#64748b;margin:4px 0'>"
                f"<span>{name}</span>"
                f"<span style='color:#a5b4fc;font-weight:600'>w={weight}</span></div>",
                unsafe_allow_html=True,
            )


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    st.markdown(CUSTOM_CSS, unsafe_allow_html=True)

    # ── Header ──
    st.markdown(
        '<div class="dash-header">📡 AI Stock Insight Agent</div>'
        '<div class="dash-subtitle">Real-time NSE market intelligence · Powered by NLP + Knowledge Graph</div>',
        unsafe_allow_html=True,
    )
    st.markdown("<div style='margin:12px 0 4px'></div>", unsafe_allow_html=True)

    render_sidebar()

    # ── Load data ──
    df = load_insights(limit=60)
    if df.empty:
        st.info("👋 No insights yet. The background worker may still be collecting data.")
        return

    # ── KPI row ──
    render_kpi_row(df)
    st.markdown("<div style='margin:18px 0 4px'></div>", unsafe_allow_html=True)

    # ── Main layout: feed (left) + analytics (right) ──
    feed_col, analytics_col = st.columns([2.2, 1], gap="large")

    # ┌─ DRILL-DOWN VIEW or FEED ───────────────────────────────────────────────
    with feed_col:
        if st.session_state.active_company:
            ac = st.session_state.active_company
            render_company_drilldown(ac["name"], ac["ticker"])
        else:
            st.markdown("<div class='section-header'>💡 Latest Insights</div>", unsafe_allow_html=True)
            for _, row in df.iterrows():
                render_insight_card(row)

    # ┌─ ANALYTICS COLUMN ──────────────────────────────────────────────────────
    with analytics_col:
        st.markdown("<div class='section-header'>📊 At a Glance</div>", unsafe_allow_html=True)

        # Sentiment donut
        sentiment_counts = df["sentiment"].value_counts()
        st.plotly_chart(build_donut(sentiment_counts), use_container_width=True)

        st.markdown("---")
        st.markdown("<div class='section-header'>🏆 Top Companies</div>", unsafe_allow_html=True)
        company_counts = df["company_name"].value_counts().head(6)
        for company, count in company_counts.items():
            ticker = df[df["company_name"] == company]["ticker"].iloc[0]
            btn_label = f"{company}  ({count})"
            if st.button(btn_label, key=f"btn_{ticker}", use_container_width=True):
                st.session_state.active_company = {"name": company, "ticker": ticker}
                st.rerun()

        st.markdown("---")
        st.markdown("<div class='section-header'>⚡ Event Types</div>", unsafe_allow_html=True)
        st.plotly_chart(build_event_bar(df), use_container_width=True)

        st.markdown("---")
        st.markdown("<div class='section-header'>📈 Impact Distribution</div>", unsafe_allow_html=True)
        if "impact_score" in df.columns:
            st.plotly_chart(build_impact_histogram(df), use_container_width=True)


if __name__ == "__main__":
    initialize_db()
    main()