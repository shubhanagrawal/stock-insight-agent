import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import time
import logging

# Make sure these helper files exist and contain the necessary functions
from scraper import scrape_news
from nlp_processor import extract_tickers
from inference_engine import generate_insight, analyze_sentiment
from database import initialize_db, save_insight, get_historical_sentiment

# Set up logging to see the pipeline output in the console
logging.basicConfig(level=logging.INFO, format='%(levelname)s:%(name)s: %(message)s')

# Page config
st.set_page_config(
    page_title="AI Stock Insight Agent",
    page_icon="🎯",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        text-align: center;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 2rem;
    }
    .metric-card {
        background: #FFFFFF;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'insights_history' not in st.session_state:
    st.session_state.insights_history = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = None
if 'active_chart' not in st.session_state:
    st.session_state.active_chart = None

def fetch_and_analyze_news(source_url, article_limit):
    """Main pipeline to fetch, process, and analyze news articles."""
    st.session_state.active_chart = None # Clear any active chart on new fetch
    with st.spinner("🔍 Analyzing latest market news..."):
        # ... (Your existing fetch_and_analyze_news function code is correct)
        # No changes needed here.
        logging.info("🚀 Starting the AI Insight Agent run...")
        try:
            articles = scrape_news(url=source_url, limit=article_limit)
            if not articles:
                st.warning("Could not fetch any articles.")
                logging.warning("Could not fetch any articles. Exiting run.")
                return

            new_insights = []
            
            for article in articles:
                logging.info(f"Processing article: \"{article['title']}\"")
                tickers = extract_tickers(article['content'])
                if not tickers:
                    logging.warning("No actionable tickers found. Moving to next article.")
                    continue
                logging.info(f"🎯 Tickers Extracted: {tickers}")

                sentiment_result = analyze_sentiment(article['content'])
                logging.info(f"Sentiment analysis complete: {sentiment_result}")

                insight = generate_insight(article['title'], tickers, sentiment_result)
                logging.info("📊 Final Insight Generated.")
                
                save_insight(article['title'], tickers, sentiment_result)
                
                new_insights.append({
                    'timestamp': datetime.now(),
                    'title': article['title'],
                    'url': article['link'],
                    'tickers': tickers,
                    'sentiment': sentiment_result['sentiment'],
                    'confidence': sentiment_result.get('confidence', 0.0),
                    'content_preview': article['content'][:250] + "..."
                })

            st.session_state.insights_history.extend(new_insights)
            st.session_state.insights_history = st.session_state.insights_history[-20:]
            
            st.success(f"✅ Analyzed {len(new_insights)} new articles.")
            logging.info("✅ Agent run complete.")

        except Exception as e:
            st.error(f"❌ An error occurred: {str(e)}")
            logging.error(f"An error occurred during the pipeline: {str(e)}")


# In dashboard.py -> plot_sentiment_history()

def plot_sentiment_history(df, company_name):
    """Creates a Plotly bar chart for historical sentiment."""
    df['date'] = df['timestamp'].dt.date
    sentiment_counts = df.groupby(['date', 'sentiment']).size().reset_index(name='count')
    
    fig = px.bar(
        sentiment_counts,
        x='date',
        y='count',
        color='sentiment',
        title=f'Historical Sentiment for {company_name}',
        labels={'date': 'Date', 'count': 'Number of Mentions', 'sentiment': 'Sentiment'},
        
        # --- ADD THIS LINE ---
        color_discrete_map={'Positive': '#28a745', 'Negative': '#dc3545', 'Neutral': '#6c757d'},
        # --------------------

        barmode='group'
    )
    fig.update_layout(xaxis_title='Date', yaxis_title='Number of Mentions')
    return fig


def display_insights(insights_container, sentiment_container, companies_container):
    """Renders the collected insights and analytics in the UI."""
    # --- Display Historical Chart if one is active ---
    if st.session_state.active_chart:
        company_name = st.session_state.active_chart['name']
        chart_fig = st.session_state.active_chart['fig']
        with insights_container:
            st.subheader(f"Sentiment History for {company_name}")
            st.plotly_chart(chart_fig, use_container_width=True)
            if st.button("Back to Latest Insights", key="back"):
                st.session_state.active_chart = None
                st.rerun()
    
    # --- Display Latest Insights if no chart is active ---
    elif not st.session_state.insights_history:
        insights_container.info("👋 Click 'Fetch Latest News' to start analyzing!")
    else:
        with insights_container:
            st.subheader("💡 Latest Insights")
            for data in reversed(st.session_state.insights_history[-5:]):
                # ... (This part is the same as your previous working code)
                sentiment_colors = {'Positive': '#28a745', 'Negative': '#dc3545', 'Neutral': '#6c757d'}
                color = sentiment_colors.get(data['sentiment'], '#6c757d')
                
                companies_list = list(data['tickers'].keys())
                display_companies = ', '.join(companies_list[:3])
                if len(companies_list) > 3:
                    display_companies += f", and {len(companies_list) - 3} more..."

                confidence_score = data.get('confidence', 0.0)
                confidence_percent = f"{confidence_score:.0%}"

                st.markdown(f"""
                <div style="border-left: 4px solid {color}; padding: 1rem; margin: 1rem 0; background: #f8f9fa; border-radius: 5px;">
                    <h4>{data['title']}</h4>
                    <p><strong>🏢 Companies:</strong> {display_companies}</p>
                    <p><strong>Sentiment:</strong> <span style="color: {color}; font-weight: bold;">{data['sentiment']}</span> ({confidence_percent} confidence)</p>
                    <p style="margin-bottom: 10px;"><strong>⏰ Time:</strong> {data['timestamp'].strftime('%H:%M:%S')}</p>
                    <a href="{data['url']}" target="_blank" style="text-decoration: none; font-weight: bold;">🔗 Read Full Article</a>
                    <details style="margin-top: 10px;">
                        <summary>📄 View Content Preview</summary>
                        <p style="margin-top: 5px;">{data['content_preview']}</p>
                    </details>
                </div>
                """, unsafe_allow_html=True)
    
    # --- Analytics Column (Pie Chart & Top Companies) ---
    sentiments = [item['sentiment'] for item in st.session_state.insights_history]
    if sentiments:
        with sentiment_container:
            st.subheader("Sentiment")
            sentiment_counts = pd.Series(sentiments).value_counts()
            fig = px.pie(values=sentiment_counts.values, names=sentiment_counts.index,
                         color_discrete_map={'Positive': '#28a745', 'Negative': '#dc3545', 'Neutral': '#6c757d'})
            fig.update_layout(height=250, margin=dict(l=0, r=0, t=0, b=0))
            st.plotly_chart(fig, use_container_width=True)
        
        with companies_container:
            st.subheader("Top Companies")
            all_companies = {name: ticker for item in st.session_state.insights_history for name, ticker in item['tickers'].items()}
            
            if all_companies:
                company_series = pd.Series([name for item in st.session_state.insights_history for name in item['tickers'].keys()])
                company_counts = company_series.value_counts().head(5)

                for company, count in company_counts.items():
                    ticker = all_companies.get(company)
                    if st.button(f"{company} ({count} mentions)", key=ticker, use_container_width=True):
                        df_history = get_historical_sentiment(ticker)
                        if not df_history.empty:
                            fig = plot_sentiment_history(df_history, company)
                            st.session_state.active_chart = {'name': company, 'fig': fig}
                            st.rerun()
                        else:
                            st.warning(f"No historical data found for {company}.")


def main():
    """Main function to define the Streamlit App layout and logic."""
    st.markdown('<h1 class="main-header">AI Stock Insight Agent V2</h1>', unsafe_allow_html=True)
    
    with st.sidebar:
        # ... (Your sidebar code is correct and needs no changes)
        st.header("⚙️ Control Panel")
        news_sources = {
            "ET Markets - Stocks": "https://economictimes.indiatimes.com/markets/stocks/rssfeeds/2146842.cms",
            "Moneycontrol - Top News": "https://www.moneycontrol.com/rss/MCtopnews.xml",
            "Livemint - Companies": "https://www.livemint.com/rss/companies",
            "The Hindu BusinessLine - Markets": "https://www.thehindubusinessline.com/markets/?service=rss",
            "Financial Express - Market": "https://www.financialexpress.com/market/rss",
            "Business Standard - Companies": "https://www.business-standard.com/rss/companies-101.rss",
        }
        selected_source_name = st.selectbox("📰 News Source", list(news_sources.keys()))
        selected_source_url = news_sources[selected_source_name]

        st.subheader("🎛️ Analysis Settings")
        max_articles = st.slider("Max Articles to Process", 1, 10, 3)

        if st.button("🔄 Fetch Latest News", type="primary"):
            fetch_and_analyze_news(selected_source_url, max_articles)
        
        st.subheader("⚙️ Auto-Refresh")
        auto_refresh = st.checkbox("Enable Auto-Refresh")
        refresh_interval = st.selectbox("Refresh Interval (seconds)", [60, 180, 300, 600], index=1)


    col1, col2 = st.columns([3, 1])
    with col1:
        insights_container = st.container()
    with col2:
        st.header("📊 At a Glance")
        sentiment_container = st.container()
        companies_container = st.container()

    if auto_refresh:
        # ... (Your auto-refresh logic is correct and needs no changes)
        if (st.session_state.last_update is None or
            (datetime.now() - st.session_state.last_update).total_seconds() > refresh_interval):
            fetch_and_analyze_news(selected_source_url, max_articles)
            st.session_state.last_update = datetime.now()
        
        if st.session_state.last_update:
            next_update_time = st.session_state.last_update + timedelta(seconds=refresh_interval)
            remaining_seconds = max(0, (next_update_time - datetime.now()).total_seconds())
            st.sidebar.info(f"Next refresh in: {int(remaining_seconds)}s")
        
        time.sleep(1)
        st.rerun()

    display_insights(insights_container, sentiment_container, companies_container)

if __name__ == "__main__":
    initialize_db()
    main()