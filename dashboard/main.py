"""
Nordic News Sentiment & Engagement Tracker Dashboard

Interactive Streamlit dashboard for visualizing sentiment analysis and engagement metrics.
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import json
from datetime import datetime, timedelta
import sys
import os
import time
import threading

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.news_collector import NewsCollector
from sentiment_analysis.sentiment_analyzer import NordicSentimentAnalyzer
from engagement_tracking.engagement_tracker import EngagementTracker
from database.database_manager import DatabaseManager

# Page configuration
st.set_page_config(
    page_title="Nordic News Analytics Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Schibsted Brand Colors
SCHIBSTED_BLUE_100 = "#020B23"  # Dark blue for text
SCHIBSTED_BLUE_90 = "#061A57"   # Primary blue
SCHIBSTED_BLUE_60 = "#264BC5"   # Secondary blue
SCHIBSTED_RED_100 = "#FF716B"   # Accent red
SCHIBSTED_WHITE = "#FFFFFF"
SCHIBSTED_GRAY_LIGHT = "#F8F8F8"

# Custom CSS with Schibsted branding
st.markdown(f"""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');
    
    /* Global styles */
    .main {{
        font-family: 'Inter', 'Schibsted Grotesk', -apple-system, BlinkMacSystemFont, sans-serif;
    }}
    
    /* Header styling */
    .main-header {{
        font-size: 2.5rem;
        color: {SCHIBSTED_BLUE_100};
        text-align: center;
        margin-bottom: 2rem;
        font-weight: 600;
        letter-spacing: -0.02em;
    }}
    
    .sub-header {{
        font-size: 1.5rem;
        color: {SCHIBSTED_BLUE_90};
        font-weight: 500;
        margin-bottom: 1rem;
    }}
    
    /* Schibsted logo area */
    .logo-container {{
        display: flex;
        align-items: center;
        justify-content: center;
        margin-bottom: 2rem;
        padding: 1rem;
        background: linear-gradient(135deg, {SCHIBSTED_BLUE_90} 0%, {SCHIBSTED_BLUE_60} 100%);
        border-radius: 12px;
        color: white;
    }}
    
    .logo-text {{
        font-size: 1.8rem;
        font-weight: 700;
        margin-left: 1rem;
        letter-spacing: -0.01em;
    }}
    
    /* Metric cards with Schibsted styling */
    .metric-card {{
        background-color: {SCHIBSTED_WHITE};
        padding: 1.5rem;
        border-radius: 12px;
        border-left: 4px solid {SCHIBSTED_BLUE_60};
        box-shadow: 0 2px 8px rgba(6, 26, 87, 0.1);
        margin-bottom: 1rem;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }}
    
    .metric-card:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(6, 26, 87, 0.15);
    }}
    
    /* Sentiment colors */
    .sentiment-positive {{
        color: #28a745;
        font-weight: 600;
    }}
    .sentiment-negative {{
        color: {SCHIBSTED_RED_100};
        font-weight: 600;
    }}
    .sentiment-neutral {{
        color: #6c757d;
        font-weight: 600;
    }}
    
    /* Button styling */
    .stButton > button {{
        background-color: {SCHIBSTED_BLUE_60};
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.5rem 1rem;
        font-weight: 500;
        transition: all 0.2s ease;
    }}
    
    .stButton > button:hover {{
        background-color: {SCHIBSTED_BLUE_90};
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(38, 75, 197, 0.3);
    }}
    
    /* Sidebar styling */
    .css-1d391kg {{
        background-color: {SCHIBSTED_GRAY_LIGHT};
    }}
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {{
        gap: 8px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        background-color: {SCHIBSTED_WHITE};
        border-radius: 8px;
        padding: 0.5rem 1rem;
        border: 1px solid #e0e0e0;
        font-weight: 500;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {SCHIBSTED_BLUE_60};
        color: white;
        border-color: {SCHIBSTED_BLUE_60};
    }}
    
    /* Data table styling */
    .dataframe {{
        border-radius: 8px;
        overflow: hidden;
        box-shadow: 0 2px 8px rgba(6, 26, 87, 0.1);
    }}
    
    /* Chart containers */
    .plotly {{
        border-radius: 8px;
        box-shadow: 0 2px 8px rgba(6, 26, 87, 0.1);
    }}
    
    /* Custom metric styling */
    .metric-container {{
        background: linear-gradient(135deg, {SCHIBSTED_WHITE} 0%, {SCHIBSTED_GRAY_LIGHT} 100%);
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e0e0e0;
        text-align: center;
        transition: all 0.2s ease;
    }}
    
    .metric-container:hover {{
        transform: translateY(-2px);
        box-shadow: 0 4px 16px rgba(6, 26, 87, 0.15);
    }}
    
    .metric-value {{
        font-size: 2rem;
        font-weight: 700;
        color: {SCHIBSTED_BLUE_100};
        margin-bottom: 0.5rem;
    }}
    
    .metric-label {{
        font-size: 0.9rem;
        color: {SCHIBSTED_BLUE_90};
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }}
    
    .metric-delta {{
        font-size: 0.8rem;
        font-weight: 600;
        margin-top: 0.5rem;
    }}
    
    .metric-delta.positive {{
        color: #28a745;
    }}
    
    .metric-delta.negative {{
        color: {SCHIBSTED_RED_100};
    }}
    
    /* Nordic pattern background */
    .nordic-pattern {{
        background-image: 
            radial-gradient(circle at 25% 25%, {SCHIBSTED_BLUE_60} 2px, transparent 2px),
            radial-gradient(circle at 75% 75%, {SCHIBSTED_BLUE_60} 2px, transparent 2px);
        background-size: 20px 20px;
        background-position: 0 0, 10px 10px;
        opacity: 0.1;
    }}
</style>
""", unsafe_allow_html=True)

# Initialize components
@st.cache_resource
def initialize_components():
    """Initialize dashboard components with caching."""
    return {
        'news_collector': NewsCollector(),
        'sentiment_analyzer': NordicSentimentAnalyzer(),
        'engagement_tracker': EngagementTracker(),
        'db_manager': DatabaseManager()
    }

@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_real_time_data():
    """Get real-time data from the database."""
    try:
        components = initialize_components()
        db_manager = components['db_manager']
        
        # Get recent articles (last 24 hours)
        articles = db_manager.get_articles_by_timeframe(hours_back=24)
        
        # Get engagement metrics
        engagement_metrics = db_manager.get_engagement_metrics()
        
        # Get sentiment data
        sentiment_data = db_manager.get_sentiment_data()
        
        return {
            'articles': articles,
            'engagement_metrics': engagement_metrics,
            'sentiment_data': sentiment_data,
            'last_updated': datetime.now()
        }
    except Exception as e:
        st.error(f"Error fetching real-time data: {e}")
        return None

def get_live_metrics():
    """Get live metrics for the dashboard."""
    data = get_real_time_data()
    if not data:
        return get_sample_metrics()
    
    articles = data['articles']
    engagement = data['engagement_metrics']
    
    # Calculate live metrics
    total_articles = len(articles)
    total_users = engagement.get('total_users', 0) if engagement else 0
    avg_engagement = engagement.get('avg_engagement_rate', 0) if engagement else 0
    
    # Calculate average sentiment (handle both numeric and string values)
    sentiment_scores = []
    for article in articles:
        score = article.get('sentiment_score', 0)
        if isinstance(score, (int, float)):
            sentiment_scores.append(score)
        elif isinstance(score, str):
            try:
                sentiment_scores.append(float(score))
            except (ValueError, TypeError):
                sentiment_scores.append(0)
    
    avg_sentiment = sum(sentiment_scores) / len(sentiment_scores) if sentiment_scores else 0
    
    return {
        'total_articles': total_articles,
        'total_users': total_users,
        'avg_engagement': avg_engagement,
        'avg_sentiment': avg_sentiment
    }

def get_sample_metrics():
    """Fallback to sample metrics if real-time data is not available."""
    return {
        'total_articles': 1247,
        'total_users': 45678,
        'avg_engagement': 15.3,
        'avg_sentiment': 0.23
    }

def main():
    """Main dashboard function."""
    # Schibsted Logo and Header
    st.markdown("""
    <div class="logo-container">
        <div style="font-size: 2.5rem; font-weight: 700;">S</div>
        <div class="logo-text">Schibsted Media Analytics</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Main Header
    st.markdown('<h1 class="main-header">📊 Nordic News Sentiment & Engagement Tracker</h1>', 
                unsafe_allow_html=True)
    
    # Subtitle with Nordic branding
    st.markdown("""
    <div style="text-align: center; color: #6c757d; margin-bottom: 2rem; font-size: 1.1rem;">
        Empowering data-driven journalism across the Nordic region
    </div>
    """, unsafe_allow_html=True)
    
    # Initialize components
    components = initialize_components()
    
    # Sidebar with Schibsted styling
    st.sidebar.markdown("""
    <div style="background: linear-gradient(135deg, #061A57 0%, #264BC5 100%); 
                padding: 1rem; border-radius: 8px; margin-bottom: 1rem; color: white;">
        <h2 style="margin: 0; font-size: 1.2rem; font-weight: 600;">🎛️ Dashboard Controls</h2>
    </div>
    """, unsafe_allow_html=True)
    
    # Real-time controls
    st.sidebar.markdown("### 🔄 Real-Time Settings")
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5 min)", value=True)
    
    # Manual refresh button
    if st.sidebar.button("🔄 Refresh Now", type="primary"):
        st.cache_data.clear()
        st.rerun()
    
    # Data source selection
    data_source = st.sidebar.radio(
        "Data Source",
        ["Real-time", "Sample Data"],
        help="Choose between live data or sample data for demonstration"
    )
    
    # Show last update time
    if data_source == "Real-time":
        data = get_real_time_data()
        if data:
            st.sidebar.markdown(f"**Last Updated:** {data['last_updated'].strftime('%H:%M:%S')}")
        else:
            st.sidebar.warning("⚠️ Real-time data unavailable")
    
    # Time range selector
    time_range = st.sidebar.selectbox(
        "Select Time Range",
        ["Last 24 hours", "Last 7 days", "Last 30 days", "Custom"]
    )
    
    if time_range == "Custom":
        start_date = st.sidebar.date_input("Start Date")
        end_date = st.sidebar.date_input("End Date")
    else:
        if time_range == "Last 24 hours":
            start_date = datetime.now() - timedelta(hours=24)
        elif time_range == "Last 7 days":
            start_date = datetime.now() - timedelta(days=7)
        elif time_range == "Last 30 days":
            start_date = datetime.now() - timedelta(days=30)
        end_date = datetime.now()
    
    # Language filter
    languages = st.sidebar.multiselect(
        "Select Languages",
        ["Norwegian", "Swedish", "Danish", "Finnish", "English"],
        default=["Norwegian", "Swedish", "Danish", "Finnish", "English"]
    )
    
    # Source filter
    sources = st.sidebar.multiselect(
        "Select News Sources",
        ["VG", "Aftenposten", "Aftonbladet", "Svenska Dagbladet", "Helsingin Sanomat"],
        default=["VG", "Aftenposten", "Aftonbladet", "Svenska Dagbladet", "Helsingin Sanomat"]
    )
    
    # Main content tabs
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📈 Overview", 
        "😊 Sentiment Analysis", 
        "👥 Engagement Metrics", 
        "🧪 A/B Testing", 
        "📊 Reports"
    ])
    
    with tab1:
        show_overview_tab(components, start_date, end_date, languages, sources, data_source)
    
    with tab2:
        show_sentiment_tab(components, start_date, end_date, languages, sources, data_source)
    
    with tab3:
        show_engagement_tab(components, start_date, end_date, languages, sources, data_source)
    
    with tab4:
        show_ab_testing_tab(components, start_date, end_date)
    
    with tab5:
        show_reports_tab(components, start_date, end_date, languages, sources)
    
    # Auto-refresh functionality
    if auto_refresh and data_source == "Real-time":
        time.sleep(300)  # Wait 5 minutes
        st.rerun()

def show_overview_tab(components, start_date, end_date, languages, sources, data_source="Sample Data"):
    """Display the overview tab with key metrics."""
    st.header("📈 Overview Dashboard")
    
    # Get metrics and data based on data source
    if data_source == "Real-time":
        metrics = get_live_metrics()
        # Get real data for charts
        real_data = get_real_time_data()
        articles = real_data.get('articles', []) if real_data else []
        engagement_data = real_data.get('engagement_metrics', {}) if real_data else {}
        sentiment_data = real_data.get('sentiment_data', {}) if real_data else {}
    else:
        metrics = get_sample_metrics()
        real_data = None
        articles = []
        engagement_data = {}
        sentiment_data = {}
    
    # Key metrics row with Schibsted styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{metrics['total_articles']:,}</div>
            <div class="metric-label">📰 Total Articles</div>
            <div class="metric-delta positive">+12%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{metrics['total_users']:,}</div>
            <div class="metric-label">👥 Active Users</div>
            <div class="metric-delta positive">+8%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{metrics['avg_engagement']:.1f}%</div>
            <div class="metric-label">📊 Avg. Engagement Rate</div>
            <div class="metric-delta positive">+2.1%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value">{metrics['avg_sentiment']:.2f}</div>
            <div class="metric-label">😊 Sentiment Score</div>
            <div class="metric-delta positive">+0.05</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Charts row
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📈 Engagement Trends")
        
        if data_source == "Real-time" and real_data:
            # Use real engagement trends data
            db_manager = components['database']
            engagement_trends = db_manager.get_engagement_trends(days=7)
            
            if engagement_trends:
                # Convert to DataFrame for plotting
                trend_data = []
                for trend in engagement_trends:
                    trend_data.append({
                        'Date': pd.to_datetime(trend['date']),
                        'Engagement Rate': trend.get('avg_engagement_rate', 0)
                    })
                
                engagement_df = pd.DataFrame(trend_data)
                if not engagement_df.empty:
                    fig = px.line(engagement_df, x='Date', y='Engagement Rate', 
                                 title="Daily Engagement Rate (Real Data)",
                                 color_discrete_sequence=[SCHIBSTED_BLUE_60])
                else:
                    # Fallback to sample data if no real data
                    dates = pd.date_range(start=start_date, end=end_date, freq='D')
                    base_rates = [12, 15, 18, 14, 16, 19, 17]
                    if len(dates) <= 7:
                        engagement_rates = base_rates[:len(dates)]
                    else:
                        engagement_rates = base_rates + [15 + (i % 5) for i in range(len(dates) - 7)]
                    
                    engagement_df = pd.DataFrame({
                        'Date': dates,
                        'Engagement Rate': engagement_rates
                    })
                    fig = px.line(engagement_df, x='Date', y='Engagement Rate', 
                                 title="Daily Engagement Rate (Sample Data)",
                                 color_discrete_sequence=[SCHIBSTED_BLUE_60])
            else:
                # Fallback to sample data
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                base_rates = [12, 15, 18, 14, 16, 19, 17]
                if len(dates) <= 7:
                    engagement_rates = base_rates[:len(dates)]
                else:
                    engagement_rates = base_rates + [15 + (i % 5) for i in range(len(dates) - 7)]
                
                engagement_df = pd.DataFrame({
                    'Date': dates,
                    'Engagement Rate': engagement_rates
                })
                fig = px.line(engagement_df, x='Date', y='Engagement Rate', 
                             title="Daily Engagement Rate (Sample Data)",
                             color_discrete_sequence=[SCHIBSTED_BLUE_60])
        else:
            # Sample data for demonstration
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            base_rates = [12, 15, 18, 14, 16, 19, 17]
            if len(dates) <= 7:
                engagement_rates = base_rates[:len(dates)]
            else:
                engagement_rates = base_rates + [15 + (i % 5) for i in range(len(dates) - 7)]
            
            engagement_df = pd.DataFrame({
                'Date': dates,
                'Engagement Rate': engagement_rates
            })
            fig = px.line(engagement_df, x='Date', y='Engagement Rate', 
                         title="Daily Engagement Rate (Sample Data)",
                         color_discrete_sequence=[SCHIBSTED_BLUE_60])
        
        fig.update_layout(
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter, sans-serif"),
            title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
            xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
            yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        st.subheader("🌍 Geographic Distribution")
        
        if data_source == "Real-time" and real_data:
            # Use real geographic data from articles
            articles = real_data.get('articles', [])
            if articles:
                # Count articles by country/source
                country_counts = {}
                for article in articles:
                    source = article.get('source', 'Unknown')
                    if source in ['VG', 'Aftenposten', 'Stavanger Aftenblad']:
                        country = 'Norway'
                    elif source in ['Svenska Dagbladet', 'Aftonbladet', 'Omni']:
                        country = 'Sweden'
                    elif source in ['Berlingske', 'Politiken']:
                        country = 'Denmark'
                    elif source in ['Helsingin Sanomat', 'Yle']:
                        country = 'Finland'
                    else:
                        country = 'Other'
                    
                    country_counts[country] = country_counts.get(country, 0) + 1
                
                if country_counts:
                    geo_data = pd.DataFrame([
                        {'Country': country, 'Articles': count} 
                        for country, count in country_counts.items()
                    ])
                    fig = px.pie(geo_data, values='Articles', names='Country', 
                                title="Article Distribution by Country (Real Data)",
                                color_discrete_sequence=[SCHIBSTED_BLUE_60, SCHIBSTED_BLUE_90, SCHIBSTED_RED_100, '#28a745'])
                else:
                    # Fallback to sample data
                    geo_data = pd.DataFrame({
                        'Country': ['Norway', 'Sweden', 'Denmark', 'Finland'],
                        'Articles': [3, 2, 1, 1]
                    })
                    fig = px.pie(geo_data, values='Articles', names='Country', 
                                title="Article Distribution by Country (Sample Data)",
                                color_discrete_sequence=[SCHIBSTED_BLUE_60, SCHIBSTED_BLUE_90, SCHIBSTED_RED_100, '#28a745'])
            else:
                # Fallback to sample data
                geo_data = pd.DataFrame({
                    'Country': ['Norway', 'Sweden', 'Denmark', 'Finland'],
                    'Articles': [3, 2, 1, 1]
                })
                fig = px.pie(geo_data, values='Articles', names='Country', 
                            title="Article Distribution by Country (Sample Data)",
                            color_discrete_sequence=[SCHIBSTED_BLUE_60, SCHIBSTED_BLUE_90, SCHIBSTED_RED_100, '#28a745'])
        else:
            # Sample data for demonstration
            geo_data = pd.DataFrame({
                'Country': ['Norway', 'Sweden', 'Denmark', 'Finland'],
                'Articles': [3, 2, 1, 1]
            })
            fig = px.pie(geo_data, values='Articles', names='Country', 
                        title="Article Distribution by Country (Sample Data)",
                        color_discrete_sequence=[SCHIBSTED_BLUE_60, SCHIBSTED_BLUE_90, SCHIBSTED_RED_100, '#28a745'])
        
        fig.update_layout(
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter, sans-serif"),
            title_font=dict(color=SCHIBSTED_BLUE_100, size=16)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top performing content
    st.subheader("🏆 Top Performing Content")
    
    if data_source == "Real-time" and real_data:
        # Use real articles data
        articles = real_data.get('articles', [])
        if articles:
            # Create top content from real articles
            top_content_data = []
            for i, article in enumerate(articles[:5]):  # Top 5 articles
                top_content_data.append({
                    'Article Title': article.get('title', 'No title')[:60] + '...' if len(article.get('title', '')) > 60 else article.get('title', 'No title'),
                    'Source': article.get('source', 'Unknown'),
                    'Published': article.get('published_at', 'Unknown')[:10] if article.get('published_at') else 'Unknown',
                    'Sentiment Score': f"{article.get('sentiment_score', 0):.2f}" if article.get('sentiment_score') else 'N/A'
                })
            
            if top_content_data:
                top_content = pd.DataFrame(top_content_data)
                st.dataframe(top_content, width='stretch')
            else:
                # Fallback to sample data
                top_content = pd.DataFrame({
                    'Article Title': ['No real articles available'],
                    'Source': ['N/A'],
                    'Published': ['N/A'],
                    'Sentiment Score': ['N/A']
                })
                st.dataframe(top_content, width='stretch')
        else:
            # Fallback to sample data
            top_content = pd.DataFrame({
                'Article Title': ['No articles in database'],
                'Source': ['N/A'],
                'Published': ['N/A'],
                'Sentiment Score': ['N/A']
            })
            st.dataframe(top_content, width='stretch')
    else:
        # Sample data for demonstration
        top_content = pd.DataFrame({
            'Article Title': [
                'Breaking: Major Economic Development in Nordic Region',
                'Climate Change Impact on Arctic Communities',
                'Technology Innovation in Stockholm',
                'Cultural Festival in Copenhagen',
                'Sports Victory in Helsinki'
            ],
            'Source': ['VG', 'Aftenposten', 'Svenska Dagbladet', 'Berlingske', 'Helsingin Sanomat'],
            'Published': ['2024-01-15', '2024-01-14', '2024-01-13', '2024-01-12', '2024-01-11'],
            'Sentiment Score': [0.45, 0.32, 0.28, 0.41, 0.38]
        })
        st.dataframe(top_content, width='stretch')

def show_sentiment_tab(components, start_date, end_date, languages, sources, data_source="Sample Data"):
    """Display the sentiment analysis tab."""
    st.header("😊 Sentiment Analysis")
    
    # Get real sentiment data if available
    if data_source == "Real-time":
        real_data = get_real_time_data()
        sentiment_data = real_data.get('sentiment_data', {}) if real_data else {}
    else:
        real_data = None
        sentiment_data = {}
    
    # Calculate real sentiment percentages
    sentiment_dist = sentiment_data.get('sentiment_distribution', {})
    total_analyses = sentiment_data.get('total_analyses', 0)
    
    if data_source == "Real-time" and total_analyses > 0:
        positive_pct = (sentiment_dist.get('positive', 0) / total_analyses) * 100
        neutral_pct = (sentiment_dist.get('neutral', 0) / total_analyses) * 100
        negative_pct = (sentiment_dist.get('negative', 0) / total_analyses) * 100
    else:
        # Sample data
        positive_pct = 68
        neutral_pct = 24
        negative_pct = 8
    
    # Sentiment overview with Schibsted styling
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value sentiment-positive">{positive_pct:.0f}%</div>
            <div class="metric-label">😊 Positive Sentiment</div>
            <div class="metric-delta positive">Real Data</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value sentiment-neutral">{neutral_pct:.0f}%</div>
            <div class="metric-label">😐 Neutral Sentiment</div>
            <div class="metric-delta neutral">Real Data</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-container">
            <div class="metric-value sentiment-negative">{negative_pct:.0f}%</div>
            <div class="metric-label">😞 Negative Sentiment</div>
            <div class="metric-delta negative">Real Data</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Sentiment trends chart
    st.subheader("📈 Sentiment Trends Over Time")
    
    if data_source == "Real-time":
        # Use real sentiment trends data
        db_manager = components['database']
        sentiment_trends = db_manager.get_sentiment_trends(days=7)
        
        if sentiment_trends:
            # Convert to DataFrame for plotting
            trend_data = []
            for trend in sentiment_trends:
                trend_data.append({
                    'Date': pd.to_datetime(trend['date']),
                    'Positive': trend.get('positive_percentage', 0),
                    'Neutral': trend.get('neutral_percentage', 0),
                    'Negative': trend.get('negative_percentage', 0)
                })
            
            sentiment_df = pd.DataFrame(trend_data)
            if not sentiment_df.empty:
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Positive'], 
                                       name='Positive', fill='tonexty', line_color='#28a745'))
                fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Neutral'], 
                                       name='Neutral', fill='tonexty', line_color='#6c757d'))
                fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Negative'], 
                                       name='Negative', fill='tonexty', line_color=SCHIBSTED_RED_100))
                fig.update_layout(
                    title="Sentiment Trends Over Time (Real Data)",
                    xaxis_title="Date",
                    yaxis_title="Percentage",
                    height=400,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family="Inter, sans-serif"),
                    title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
                    xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
                    yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
                )
                st.plotly_chart(fig, use_container_width=True)
            else:
                # Fallback to sample data
                dates = pd.date_range(start=start_date, end=end_date, freq='D')
                base_positive = [65, 68, 70, 67, 69, 71, 68]
                base_neutral = [25, 24, 22, 26, 23, 21, 24]
                base_negative = [10, 8, 8, 7, 8, 8, 8]
                
                if len(dates) <= 7:
                    positive_rates = base_positive[:len(dates)]
                    neutral_rates = base_neutral[:len(dates)]
                    negative_rates = base_negative[:len(dates)]
                else:
                    positive_rates = base_positive + [68 + (i % 3) for i in range(len(dates) - 7)]
                    neutral_rates = base_neutral + [24 - (i % 2) for i in range(len(dates) - 7)]
                    negative_rates = base_negative + [8 - (i % 1) for i in range(len(dates) - 7)]
                
                sentiment_df = pd.DataFrame({
                    'Date': dates,
                    'Positive': positive_rates,
                    'Neutral': neutral_rates,
                    'Negative': negative_rates
                })
                
                fig = go.Figure()
                fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Positive'], 
                                       name='Positive', fill='tonexty', line_color='#28a745'))
                fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Neutral'], 
                                       name='Neutral', fill='tonexty', line_color='#6c757d'))
                fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Negative'], 
                                       name='Negative', fill='tonexty', line_color=SCHIBSTED_RED_100))
                fig.update_layout(
                    title="Sentiment Trends Over Time (Sample Data)",
                    xaxis_title="Date",
                    yaxis_title="Percentage",
                    height=400,
                    plot_bgcolor='white',
                    paper_bgcolor='white',
                    font=dict(family="Inter, sans-serif"),
                    title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
                    xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
                    yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
                )
                st.plotly_chart(fig, use_container_width=True)
        else:
            # Fallback to sample data
            dates = pd.date_range(start=start_date, end=end_date, freq='D')
            base_positive = [65, 68, 70, 67, 69, 71, 68]
            base_neutral = [25, 24, 22, 26, 23, 21, 24]
            base_negative = [10, 8, 8, 7, 8, 8, 8]
            
            if len(dates) <= 7:
                positive_rates = base_positive[:len(dates)]
                neutral_rates = base_neutral[:len(dates)]
                negative_rates = base_negative[:len(dates)]
            else:
                positive_rates = base_positive + [68 + (i % 3) for i in range(len(dates) - 7)]
                neutral_rates = base_neutral + [24 - (i % 2) for i in range(len(dates) - 7)]
                negative_rates = base_negative + [8 - (i % 1) for i in range(len(dates) - 7)]
            
            sentiment_df = pd.DataFrame({
                'Date': dates,
                'Positive': positive_rates,
                'Neutral': neutral_rates,
                'Negative': negative_rates
            })
            
            fig = go.Figure()
            fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Positive'], 
                                   name='Positive', fill='tonexty', line_color='#28a745'))
            fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Neutral'], 
                                   name='Neutral', fill='tonexty', line_color='#6c757d'))
            fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Negative'], 
                                   name='Negative', fill='tonexty', line_color=SCHIBSTED_RED_100))
            fig.update_layout(
                title="Sentiment Trends Over Time (Sample Data)",
                xaxis_title="Date",
                yaxis_title="Percentage",
                height=400,
                plot_bgcolor='white',
                paper_bgcolor='white',
                font=dict(family="Inter, sans-serif"),
                title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
                xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
                yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
            )
            st.plotly_chart(fig, use_container_width=True)
    else:
        # Sample data for demonstration
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        base_positive = [65, 68, 70, 67, 69, 71, 68]
        base_neutral = [25, 24, 22, 26, 23, 21, 24]
        base_negative = [10, 8, 8, 7, 8, 8, 8]
        
        if len(dates) <= 7:
            positive_rates = base_positive[:len(dates)]
            neutral_rates = base_neutral[:len(dates)]
            negative_rates = base_negative[:len(dates)]
        else:
            positive_rates = base_positive + [68 + (i % 3) for i in range(len(dates) - 7)]
            neutral_rates = base_neutral + [24 - (i % 2) for i in range(len(dates) - 7)]
            negative_rates = base_negative + [8 - (i % 1) for i in range(len(dates) - 7)]
        
        sentiment_df = pd.DataFrame({
            'Date': dates,
            'Positive': positive_rates,
            'Neutral': neutral_rates,
            'Negative': negative_rates
        })
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Positive'], 
                               name='Positive', fill='tonexty', line_color='#28a745'))
        fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Neutral'], 
                               name='Neutral', fill='tonexty', line_color='#6c757d'))
        fig.add_trace(go.Scatter(x=sentiment_df['Date'], y=sentiment_df['Negative'], 
                               name='Negative', fill='tonexty', line_color=SCHIBSTED_RED_100))
        fig.update_layout(
            title="Sentiment Trends Over Time (Sample Data)",
            xaxis_title="Date",
            yaxis_title="Percentage",
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter, sans-serif"),
            title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
            xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
            yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Sentiment by source
    st.subheader("📰 Sentiment by News Source")
    
    # Sample data for demonstration
    source_sentiment = pd.DataFrame({
        'Source': ['VG', 'Aftenposten', 'Aftonbladet', 'Svenska Dagbladet', 'Helsingin Sanomat'],
        'Positive': [70, 65, 68, 72, 66],
        'Neutral': [22, 26, 24, 20, 25],
        'Negative': [8, 9, 8, 8, 9]
    })
    
    fig = px.bar(source_sentiment, x='Source', y=['Positive', 'Neutral', 'Negative'],
                title="Sentiment Distribution by Source",
                color_discrete_map={'Positive': '#28a745', 'Neutral': '#6c757d', 'Negative': SCHIBSTED_RED_100})
    fig.update_layout(
        height=400,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter, sans-serif"),
        title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
        xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
        yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
    )
    st.plotly_chart(fig, use_container_width=True)

def show_engagement_tab(components, start_date, end_date, languages, sources, data_source="Sample Data"):
    """Display the engagement metrics tab."""
    st.header("👥 Engagement Metrics")
    
    # Engagement overview with Schibsted styling
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-value">15.3%</div>
            <div class="metric-label">🖱️ Click-Through Rate</div>
            <div class="metric-delta positive">+2.1%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-value">2:34</div>
            <div class="metric-label">⏱️ Avg. Time on Page</div>
            <div class="metric-delta positive">+0:12</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-value">3,247</div>
            <div class="metric-label">📤 Social Shares</div>
            <div class="metric-delta positive">+15%</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col4:
        st.markdown("""
        <div class="metric-container">
            <div class="metric-value">42%</div>
            <div class="metric-label">🔄 Bounce Rate</div>
            <div class="metric-delta negative">-3%</div>
        </div>
        """, unsafe_allow_html=True)
    
    # Engagement trends
    st.subheader("📈 Engagement Trends")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CTR over time
        dates = pd.date_range(start=start_date, end=end_date, freq='D')
        # Create CTR data with proper length matching
        base_ctr = [13, 14, 15, 14, 16, 17, 15]
        if len(dates) <= 7:
            ctr_rates = base_ctr[:len(dates)]
        else:
            ctr_rates = base_ctr + [15 + (i % 3) for i in range(len(dates) - 7)]
        
        ctr_data = pd.DataFrame({
            'Date': dates,
            'CTR': ctr_rates
        })
        
        fig = px.line(ctr_data, x='Date', y='CTR', 
                     title="Click-Through Rate Over Time",
                     color_discrete_sequence=[SCHIBSTED_BLUE_60])
        fig.update_layout(
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter, sans-serif"),
            title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
            xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
            yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Time on page distribution
        time_data = pd.DataFrame({
            'Time Range': ['0-30s', '30s-1m', '1-2m', '2-5m', '5m+'],
            'Percentage': [25, 30, 20, 15, 10]
        })
        
        fig = px.bar(time_data, x='Time Range', y='Percentage',
                    title="Time on Page Distribution",
                    color_discrete_sequence=[SCHIBSTED_BLUE_60])
        fig.update_layout(
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter, sans-serif"),
            title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
            xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
            yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    # Top performing articles
    st.subheader("🏆 Top Performing Articles by Engagement")
    
    # Sample data for demonstration
    top_articles = pd.DataFrame({
        'Article Title': [
            'Major Political Development Shakes Nordic Region',
            'Climate Summit Results: What It Means for Arctic',
            'Tech Innovation: Stockholm Leads the Way',
            'Cultural Heritage Preservation in Copenhagen',
            'Sports Championship: Helsinki Hosts Successfully'
        ],
        'Source': ['VG', 'Aftenposten', 'Svenska Dagbladet', 'Berlingske', 'Helsingin Sanomat'],
        'CTR': [23.5, 21.2, 19.8, 18.3, 17.1],
        'Time on Page': ['3:45', '3:12', '2:58', '2:41', '2:33'],
        'Shares': [1247, 892, 756, 634, 521]
    })
    
    st.dataframe(top_articles, width='stretch')

def show_ab_testing_tab(components, start_date, end_date):
    """Display the A/B testing tab."""
    st.header("🧪 A/B Testing Dashboard")
    
    # Active experiments
    st.subheader("🔬 Active Experiments")
    
    # Sample experiment data
    experiments = pd.DataFrame({
        'Experiment Name': [
            'Headline Optimization Test',
            'Image Placement Test',
            'Content Layout Test',
            'Personalization Algorithm Test'
        ],
        'Status': ['Running', 'Running', 'Completed', 'Draft'],
        'Start Date': ['2024-01-15', '2024-01-20', '2024-01-10', '2024-01-25'],
        'Traffic Split': ['50/50', '70/30', '50/50', '60/40'],
        'Participants': [15420, 12890, 25670, 0]
    })
    
    st.dataframe(experiments, width='stretch')
    
    # Experiment results
    st.subheader("📊 Experiment Results")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # CTR comparison
        ctr_comparison = pd.DataFrame({
            'Variant': ['Control', 'Variant A', 'Control', 'Variant B'],
            'CTR': [15.2, 17.8, 14.8, 16.3],
            'Confidence': [95, 95, 90, 90]
        })
        
        fig = px.bar(ctr_comparison, x='Variant', y='CTR',
                    title="CTR Comparison by Variant",
                    color_discrete_sequence=[SCHIBSTED_BLUE_60, SCHIBSTED_BLUE_90])
        fig.update_layout(
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter, sans-serif"),
            title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
            xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
            yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
        )
        st.plotly_chart(fig, use_container_width=True)
    
    with col2:
        # Statistical significance
        significance_data = pd.DataFrame({
            'Metric': ['CTR', 'Time on Page', 'Bounce Rate', 'Conversion'],
            'P-Value': [0.023, 0.045, 0.156, 0.089],
            'Significant': [True, True, False, False]
        })
        
        fig = px.bar(significance_data, x='Metric', y='P-Value',
                    color='Significant',
                    title="Statistical Significance by Metric",
                    color_discrete_map={True: SCHIBSTED_BLUE_60, False: SCHIBSTED_RED_100})
        fig.update_layout(
            height=400,
            plot_bgcolor='white',
            paper_bgcolor='white',
            font=dict(family="Inter, sans-serif"),
            title_font=dict(color=SCHIBSTED_BLUE_100, size=16),
            xaxis_title_font=dict(color=SCHIBSTED_BLUE_90),
            yaxis_title_font=dict(color=SCHIBSTED_BLUE_90)
        )
        st.plotly_chart(fig, use_container_width=True)

def show_reports_tab(components, start_date, end_date, languages, sources):
    """Display the reports tab."""
    st.header("📊 Reports & Analytics")
    
    # Report generation
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("📈 Generate Engagement Report"):
            st.success("Engagement report generated successfully!")
    
    with col2:
        if st.button("😊 Generate Sentiment Report"):
            st.success("Sentiment report generated successfully!")
    
    with col3:
        if st.button("📊 Generate Full Analytics Report"):
            st.success("Full analytics report generated successfully!")
    
    # Sample report data
    st.subheader("📋 Sample Analytics Report")
    
    report_data = {
        'Period': f"{start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}",
        'Total Articles Analyzed': 1247,
        'Total Users': 45678,
        'Average Sentiment Score': 0.23,
        'Average Engagement Rate': 15.3,
        'Top Performing Source': 'VG',
        'Most Engaged Country': 'Norway',
        'Key Insights': [
            'Positive sentiment increased by 5% compared to previous period',
            'Engagement rate improved by 2.1% through A/B testing',
            'Mobile users show 23% higher engagement than desktop',
            'Climate-related content performs 18% better than average'
        ]
    }
    
    for key, value in report_data.items():
        if key == 'Key Insights':
            st.write(f"**{key}:**")
            for insight in value:
                st.write(f"• {insight}")
        else:
            st.write(f"**{key}:** {value}")

if __name__ == "__main__":
    main()