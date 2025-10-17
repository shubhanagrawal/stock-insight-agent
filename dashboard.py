import streamlit as st
import pandas as pd
import plotly.express as px
import sqlite3
import logging
import json

# Import only the functions needed to READ from the database
from database import get_historical_sentiment, initialize_db

# --- Setup ---
st.set_page_config(page_title="AI Stock Insight Agent", page_icon="🎯", layout="wide")
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')

# --- Session State ---
# Initialize the 'active_chart' key to prevent AttributeError on first run
if 'active_chart' not in st.session_state:
    st.session_state.active_chart = None

# --- UI Functions ---
def plot_sentiment_history(df, company_name):
    """Creates a Plotly bar chart for historical sentiment."""
    df['date'] = pd.to_datetime(df['timestamp']).dt.date
    sentiment_counts = df.groupby(['date', 'sentiment']).size().reset_index(name='count')
    fig = px.bar(sentiment_counts, x='date', y='count', color='sentiment', title=f'Historical Sentiment for {company_name}',
                 labels={'date': 'Date', 'count': 'Number of Mentions'},
                 color_discrete_map={'Positive': '#28a745', 'Negative': '#dc3545', 'Neutral': '#6c757d'}, barmode='group')
    return fig

def display_dashboard(insights_container, analytics_col):
    """Renders the main dashboard UI by fetching the latest data from the database."""
    conn = None
    try:
        conn = sqlite3.connect("insights.db")
        # Fetch the 40 most recent insights to populate the UI
        query = "SELECT * FROM insights ORDER BY timestamp DESC LIMIT 40"
        latest_insights = pd.read_sql_query(query, conn)
    except Exception as e:
        logging.error(f"Failed to read from database: {e}")
        latest_insights = pd.DataFrame()
    finally:
        if conn:
            conn.close()

    # --- Main Insights Feed ---
    with insights_container:
        if st.session_state.active_chart:
            st.subheader(f"Sentiment History for {st.session_state.active_chart['name']}")
            st.plotly_chart(st.session_state.active_chart['fig'], use_container_width=True)
            if st.button("⬅️ Back to Latest Insights"):
                st.session_state.active_chart = None
                st.rerun()
        elif latest_insights.empty:
            st.info("👋 No insights found. The background worker may be running or collecting data.")
        else:
            st.subheader("💡 Latest Insights")
            for _, data in latest_insights.iterrows():
                # Use a native Streamlit container for a clean, professional card layout
                with st.container(border=True):
                    sentiment_colors = {'Positive': 'green', 'Negative': 'red', 'Neutral': 'gray'}
                    color = sentiment_colors.get(data.get('sentiment', 'Neutral'), 'gray')
                    
                    st.subheader(data.get('article_title', '(No Title)'))
                    
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**🏢 Company:** {data.get('company_name', 'N/A')}")
                        st.markdown(f"**Sentiment:** :{color}[{data.get('sentiment', 'Neutral')}] ({data.get('confidence', 0):.0%} confidence)")
                        st.markdown(f"**Event Type:** {data.get('event_type', 'N/A')} | **Impact Score:** {data.get('impact_score', 0):.2f}")
                    with col2:
                        st.link_button("🔗 Read Full Article", data.get('link', '#'))
                        st.write(f"_{pd.to_datetime(data.get('timestamp')).strftime('%H:%M:%S')}_")

                    key_figures_json = data.get('key_figures')
                    if key_figures_json and key_figures_json != 'null':
                        try:
                            key_figures = json.loads(key_figures_json)
                            priority_order = [('profit_change_percent', 'Profit Change'), ('revenue_change_percent', 'Revenue Change')]
                            items = [f"- **{label}:** {key_figures[key]}" for key, label in priority_order if key in key_figures]
                            if items:
                                st.markdown("**📊 Key Figures:**\n" + "\n".join(items))
                        except json.JSONDecodeError:
                            pass # Fail silently if JSON is malformed

    # --- Analytics Column ---
    if not latest_insights.empty:
        with analytics_col:
            st.header("📊 At a Glance")
            
            st.subheader("Sentiment")
            sentiment_counts = latest_insights['sentiment'].value_counts()
            fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index,
                         color_discrete_map={'Positive': '#28a745', 'Negative': '#dc3545', 'Neutral': '#6c757d'})
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
            
            st.subheader("Top Companies")
            company_counts = latest_insights['company_name'].value_counts().head(5)
            for company, count in company_counts.items():
                # Find the ticker for the company to use as a unique key for the button
                ticker = latest_insights[latest_insights['company_name'] == company]['ticker'].iloc[0]
                if st.button(f"{company} ({count} mentions)", key=ticker, use_container_width=True):
                    df_history = get_historical_sentiment(ticker)
                    if not df_history.empty:
                        st.session_state.active_chart = {'name': company, 'fig': plot_sentiment_history(df_history, company)}
                        st.rerun()
                    else:
                        st.warning(f"No historical data for {company}.")

def main():
    """Main function to define the Streamlit App layout and logic."""
    st.markdown('<h1 class="main-header">AI Stock Insight Agent V2</h1>', unsafe_allow_html=True)
    with st.sidebar:
        st.header("⚙️ Control Panel")
        st.info("This dashboard automatically updates as the background agent finds new insights.")
        if st.button("🔄 Refresh Data"):
            st.rerun()

    insights_container, analytics_col = st.columns([3, 1])
    display_dashboard(insights_container, analytics_col)

if __name__ == "__main__":
    initialize_db()
    main()