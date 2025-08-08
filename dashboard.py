import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime, timedelta
import json
import time
from scraper import scrape_news
from nlp_processor import extract_tickers
from inference_engine import generate_insight, analyze_sentiment

# Page config
st.set_page_config(
    page_title="AI Stock Insight Agent",
    page_icon="📊",
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
        background: white;
        padding: 1rem;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .insight-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.5rem;
        border-radius: 15px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'insights_history' not in st.session_state:
    st.session_state.insights_history = []
if 'last_update' not in st.session_state:
    st.session_state.last_update = None

def main():
    st.markdown('<h1 class="main-header">🎯 AI Stock Insight Agent</h1>', unsafe_allow_html=True)
    
    # Sidebar
    with st.sidebar:
        st.header("⚙️ Control Panel")
        
        # Auto-refresh toggle
        auto_refresh = st.checkbox("🔄 Auto Refresh", value=False)
        refresh_interval = st.selectbox("Refresh Interval", [30, 60, 300, 600], index=1)
        
        # News source selector
        news_sources = {
            "Economic Times - Markets": "https://economictimes.indiatimes.com/markets/rssfeeds/1977021501.cms",
            "Business Standard": "https://www.business-standard.com/rss/markets-106.rss",
        }
        selected_source = st.selectbox("📰 News Source", list(news_sources.keys()))
        
        # Manual refresh button
        if st.button("🔄 Fetch Latest News", type="primary"):
            fetch_and_analyze_news()
        
        # Settings
        st.subheader("🎛️ Analysis Settings")
        max_articles = st.slider("Max Articles", 1, 10, 3)
        sentiment_threshold = st.slider("Sentiment Confidence", 0.1, 1.0, 0.7)
    
    # Main content area
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col1:
        st.header("📈 Latest Market Insights")
        insights_container = st.container()
    
    with col2:
        st.header("📊 Sentiment Analysis")
        sentiment_container = st.container()
    
    with col3:
        st.header("🏢 Top Companies")
        companies_container = st.container()
    
    # Auto-refresh logic
    if auto_refresh:
        if (st.session_state.last_update is None or 
            (datetime.now() - st.session_state.last_update).seconds > refresh_interval):
            fetch_and_analyze_news()
            st.session_state.last_update = datetime.now()
        
        # Show countdown
        if st.session_state.last_update:
            next_update = st.session_state.last_update + timedelta(seconds=refresh_interval)
            remaining = (next_update - datetime.now()).seconds
            st.sidebar.info(f"⏰ Next update in: {remaining}s")
        
        time.sleep(1)
        st.rerun()
    
    # Display insights
    display_insights(insights_container, sentiment_container, companies_container)

def fetch_and_analyze_news():
    """Fetch and analyze latest news"""
    with st.spinner("🔍 Analyzing latest market news..."):
        try:
            # Fetch news
            articles = scrape_news(limit=3)
            
            if not articles:
                st.warning("No articles found")
                return
            
            new_insights = []
            
            for article in articles:
                # Extract tickers
                tickers = extract_tickers(article['content'])
                
                if tickers:
                    # Analyze sentiment
                    sentiment = analyze_sentiment(article['content'])
                    
                    # Generate insight
                    insight = generate_insight(article['title'], tickers, sentiment)
                    
                    new_insights.append({
                        'timestamp': datetime.now(),
                        'title': article['title'],
                        'url': article['link'],
                        'tickers': tickers,
                        'sentiment': sentiment,
                        'insight': insight,
                        'content_preview': article['content'][:200] + "..."
                    })
            
            # Add to history
            st.session_state.insights_history.extend(new_insights)
            
            # Keep only last 20 insights
            st.session_state.insights_history = st.session_state.insights_history[-20:]
            
            st.success(f"✅ Analyzed {len(new_insights)} articles")
            
        except Exception as e:
            st.error(f"❌ Error fetching news: {str(e)}")

def display_insights(insights_container, sentiment_container, companies_container):
    """Display insights and analytics"""
    
    if not st.session_state.insights_history:
        insights_container.info("👋 Click 'Fetch Latest News' to start analyzing market insights!")
        return
    
    # Latest insights
    with insights_container:
        for i, insight_data in enumerate(reversed(st.session_state.insights_history[-5:])):
            
            # Sentiment color mapping
            sentiment_colors = {
                'Positive': '#28a745',
                'Negative': '#dc3545', 
                'Neutral': '#6c757d'
            }
            
            color = sentiment_colors.get(insight_data['sentiment'], '#6c757d')
            
            st.markdown(f"""
            <div style="border-left: 4px solid {color}; padding-left: 1rem; margin: 1rem 0; background: #f8f9fa; border-radius: 5px;">
                <h4>📰 {insight_data['title']}</h4>
                <p><strong>🏢 Companies:</strong> {', '.join([f"{k} ({v})" for k, v in insight_data['tickers'].items()])}</p>
                <p><strong>😊 Sentiment:</strong> <span style="color: {color}; font-weight: bold;">{insight_data['sentiment']}</span></p>
                <p><strong>⏰ Time:</strong> {insight_data['timestamp'].strftime('%H:%M:%S')}</p>
                <details>
                    <summary>🔍 View Details</summary>
                    <p>{insight_data['content_preview']}</p>
                    <a href="{insight_data['url']}" target="_blank">🔗 Read Full Article</a>
                </details>
            </div>
            """, unsafe_allow_html=True)
    
    # Sentiment distribution
    with sentiment_container:
        if len(st.session_state.insights_history) > 0:
            sentiments = [item['sentiment'] for item in st.session_state.insights_history]
            sentiment_counts = pd.Series(sentiments).value_counts()
            
            fig = px.pie(
                values=sentiment_counts.values,
                names=sentiment_counts.index,
                color_discrete_map={
                    'Positive': '#28a745',
                    'Negative': '#dc3545',
                    'Neutral': '#6c757d'
                }
            )
            fig.update_layout(height=300)
            st.plotly_chart(fig, use_container_width=True)
    
    # Top companies
    with companies_container:
        if len(st.session_state.insights_history) > 0:
            all_companies = []
            for item in st.session_state.insights_history:
                all_companies.extend(item['tickers'].keys())
            
            company_counts = pd.Series(all_companies).value_counts().head(5)
            
            for company, count in company_counts.items():
                st.markdown(f"""
                <div class="metric-card">
                    <h4>{company}</h4>
                    <p>Mentioned {count} times</p>
                </div>
                """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()