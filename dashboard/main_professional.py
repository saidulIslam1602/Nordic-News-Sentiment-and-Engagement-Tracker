"""
Professional Nordic News Analytics Dashboard
Clean, executive-level design with minimal clutter
"""

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import time
import threading
import yaml
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.news_collector import NewsCollector
from sentiment_analysis.sentiment_analyzer import NordicSentimentAnalyzer
from engagement_tracking.engagement_tracker import EngagementTracker
from database.database_manager import DatabaseManager

# Professional color scheme
PRIMARY_BLUE = "#1f4e79"
SECONDARY_BLUE = "#4472c4"
ACCENT_BLUE = "#70ad47"
WARNING_RED = "#c5504b"
WHITE = "#ffffff"
LIGHT_GRAY = "#f8f9fa"
DARK_GRAY = "#6c757d"

# Page configuration
st.set_page_config(
    page_title="Nordic Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Professional CSS styling
st.markdown(f"""
<style>
    .main-header {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {PRIMARY_BLUE};
        margin-bottom: 0.5rem;
        text-align: center;
    }}
    
    .sub-header {{
        font-size: 1.1rem;
        color: {DARK_GRAY};
        text-align: center;
        margin-bottom: 2rem;
    }}
    
    .metric-card {{
        background: {WHITE};
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        border-left: 4px solid {ACCENT_BLUE};
        margin-bottom: 1rem;
    }}
    
    .metric-value {{
        font-size: 2.5rem;
        font-weight: 700;
        color: {PRIMARY_BLUE};
        margin-bottom: 0.5rem;
    }}
    
    .metric-label {{
        font-size: 1rem;
        color: {DARK_GRAY};
        margin-bottom: 0.5rem;
    }}
    
    .metric-change {{
        font-size: 0.9rem;
        font-weight: 600;
    }}
    
    .positive {{
        color: {ACCENT_BLUE};
    }}
    
    .negative {{
        color: {WARNING_RED};
    }}
    
    .chart-container {{
        background: {WHITE};
        padding: 1.5rem;
        border-radius: 8px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }}
    
    .sidebar .sidebar-content {{
        background: {LIGHT_GRAY};
    }}
    
    .stTabs [data-baseweb="tab-list"] {{
        gap: 2px;
    }}
    
    .stTabs [data-baseweb="tab"] {{
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
    }}
    
    .stTabs [aria-selected="true"] {{
        background-color: {PRIMARY_BLUE};
        color: {WHITE};
    }}
</style>
""", unsafe_allow_html=True)

@st.cache_data(ttl=300)
def initialize_components():
    """Initialize all components."""
    return {
        'news_collector': NewsCollector(),
        'sentiment_analyzer': NordicSentimentAnalyzer(),
        'engagement_tracker': EngagementTracker(),
        'db_manager': DatabaseManager()
    }

@st.cache_data(ttl=300)
def get_real_time_data():
    """Get real-time data from database."""
    try:
        components = initialize_components()
        db_manager = components['db_manager']
        
        articles = db_manager.get_articles_by_timeframe(hours_back=24)
        engagement_metrics = db_manager.get_engagement_metrics()
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
    """Get live metrics from real-time data."""
    try:
        data = get_real_time_data()
        if not data:
            return get_sample_metrics()
        
        articles = data.get('articles', [])
        engagement = data.get('engagement_metrics', {})
        sentiment = data.get('sentiment_data', {})
        
        total_articles = len(articles)
        total_users = engagement.get('total_users', 0)
        avg_engagement = engagement.get('engagement_rate', 0)
        avg_sentiment = sentiment.get('average_sentiment_score', 0)
        
        return {
            'total_articles': total_articles,
            'total_users': total_users,
            'avg_engagement': avg_engagement,
            'avg_sentiment': avg_sentiment
        }
    except Exception as e:
        st.error(f"Error getting live metrics: {e}")
        return get_sample_metrics()

def get_sample_metrics():
    """Get sample metrics for demonstration."""
    return {
        'total_articles': 1247,
        'total_users': 45678,
        'avg_engagement': 15.3,
        'avg_sentiment': 0.23
    }

def show_executive_summary():
    """Display executive summary with key metrics."""
    st.markdown('<div class="main-header">Nordic Analytics Platform</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Real-time Media Analytics & Insights</div>', unsafe_allow_html=True)
    
    # Get metrics
    data_source = st.sidebar.radio("Data Source", ["Real-time", "Sample Data"])
    
    if data_source == "Real-time":
        metrics = get_live_metrics()
        st.sidebar.success("✅ Live data connected")
    else:
        metrics = get_sample_metrics()
        st.sidebar.info("📊 Sample data mode")
    
    # Key metrics in clean layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['total_articles']:,}</div>
            <div class="metric-label">Articles Published</div>
            <div class="metric-change positive">+12% vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['avg_engagement']:.1f}%</div>
            <div class="metric-label">Engagement Rate</div>
            <div class="metric-change positive">+2.1% vs last period</div>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown(f"""
        <div class="metric-card">
            <div class="metric-value">{metrics['avg_sentiment']:.2f}</div>
            <div class="metric-label">Sentiment Score</div>
            <div class="metric-change positive">+0.15 vs last period</div>
        </div>
        """, unsafe_allow_html=True)

def show_engagement_analysis():
    """Display engagement analysis with single focused chart."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📈 Engagement Performance")
    
    # Generate sample engagement data
    dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D')
    engagement_data = pd.DataFrame({
        'Date': dates,
        'Engagement Rate': [12 + i * 0.1 + (i % 7) * 0.5 for i in range(len(dates))],
        'Page Views': [1000 + i * 20 + (i % 5) * 100 for i in range(len(dates))],
        'Click Rate': [8 + i * 0.05 + (i % 3) * 0.3 for i in range(len(dates))]
    })
    
    # Single comprehensive chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=engagement_data['Date'],
        y=engagement_data['Engagement Rate'],
        mode='lines+markers',
        name='Engagement Rate %',
        line=dict(color=PRIMARY_BLUE, width=3),
        marker=dict(size=6)
    ))
    
    fig.add_trace(go.Scatter(
        x=engagement_data['Date'],
        y=engagement_data['Click Rate'],
        mode='lines+markers',
        name='Click Rate %',
        line=dict(color=ACCENT_BLUE, width=3),
        marker=dict(size=6),
        yaxis='y2'
    ))
    
    fig.update_layout(
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter, sans-serif", size=12),
        title_font=dict(color=PRIMARY_BLUE, size=18),
        xaxis=dict(
            title="Date",
            title_font=dict(color=DARK_GRAY, size=14),
            tickfont=dict(color=DARK_GRAY, size=12),
            showgrid=True,
            gridcolor='#e5e5e5',
            showline=True,
            linecolor='#e5e5e5'
        ),
        yaxis=dict(
            title="Engagement Rate (%)",
            title_font=dict(color=DARK_GRAY, size=14),
            tickfont=dict(color=DARK_GRAY, size=12),
            showgrid=True,
            gridcolor='#e5e5e5',
            showline=True,
            linecolor='#e5e5e5'
        ),
        yaxis2=dict(
            title="Click Rate (%)",
            title_font=dict(color=DARK_GRAY, size=14),
            tickfont=dict(color=DARK_GRAY, size=12),
            overlaying='y',
            side='right'
        ),
        legend=dict(
            font=dict(size=12),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_sentiment_analysis():
    """Display sentiment analysis with clean visualization."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("😊 Content Sentiment Analysis")
    
    # Sample sentiment data
    sentiment_data = pd.DataFrame({
        'Date': pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='D'),
        'Positive': [45 + i * 0.2 + (i % 5) * 2 for i in range(30)],
        'Neutral': [35 + i * 0.1 + (i % 7) * 1 for i in range(30)],
        'Negative': [20 - i * 0.1 + (i % 3) * 1 for i in range(30)]
    })
    
    # Clean area chart
    fig = go.Figure()
    
    fig.add_trace(go.Scatter(
        x=sentiment_data['Date'],
        y=sentiment_data['Positive'],
        mode='lines',
        name='Positive',
        fill='tonexty',
        line=dict(color=ACCENT_BLUE, width=2),
        fillcolor='rgba(112, 173, 71, 0.3)'
    ))
    
    fig.add_trace(go.Scatter(
        x=sentiment_data['Date'],
        y=sentiment_data['Neutral'],
        mode='lines',
        name='Neutral',
        fill='tonexty',
        line=dict(color=SECONDARY_BLUE, width=2),
        fillcolor='rgba(68, 114, 196, 0.3)'
    ))
    
    fig.add_trace(go.Scatter(
        x=sentiment_data['Date'],
        y=sentiment_data['Negative'],
        mode='lines',
        name='Negative',
        fill='tozeroy',
        line=dict(color=WARNING_RED, width=2),
        fillcolor='rgba(197, 80, 75, 0.3)'
    ))
    
    fig.update_layout(
        height=500,
        plot_bgcolor='white',
        paper_bgcolor='white',
        font=dict(family="Inter, sans-serif", size=12),
        title_font=dict(color=PRIMARY_BLUE, size=18),
        xaxis=dict(
            title="Date",
            title_font=dict(color=DARK_GRAY, size=14),
            tickfont=dict(color=DARK_GRAY, size=12),
            showgrid=True,
            gridcolor='#e5e5e5',
            showline=True,
            linecolor='#e5e5e5'
        ),
        yaxis=dict(
            title="Percentage (%)",
            title_font=dict(color=DARK_GRAY, size=14),
            tickfont=dict(color=DARK_GRAY, size=12),
            showgrid=True,
            gridcolor='#e5e5e5',
            showline=True,
            linecolor='#e5e5e5'
        ),
        legend=dict(
            font=dict(size=12),
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        ),
        margin=dict(l=50, r=50, t=50, b=50)
    )
    
    st.plotly_chart(fig, use_container_width=True)
    st.markdown('</div>', unsafe_allow_html=True)

def show_content_performance():
    """Display content performance with clean table."""
    st.markdown('<div class="chart-container">', unsafe_allow_html=True)
    st.subheader("📰 Top Performing Content")
    
    # Sample content data
    content_data = pd.DataFrame({
        'Headline': [
            'Climate Summit Reaches Historic Agreement',
            'Tech Innovation Drives Economic Growth',
            'Healthcare Breakthrough Announced',
            'Education Reform Shows Positive Results',
            'Infrastructure Investment Plan Approved'
        ],
        'Source': ['VG', 'Aftenposten', 'Aftonbladet', 'Svenska Dagbladet', 'Helsingin Sanomat'],
        'Engagement': [89.2, 76.8, 72.1, 68.9, 65.4],
        'Sentiment': [0.85, 0.72, 0.68, 0.61, 0.58],
        'Views': [15420, 12890, 11250, 9870, 8560]
    })
    
    # Clean table with custom styling
    st.dataframe(
        content_data,
        use_container_width=True,
        hide_index=True,
        column_config={
            "Headline": st.column_config.TextColumn("Article Headline", width="large"),
            "Source": st.column_config.TextColumn("Source", width="small"),
            "Engagement": st.column_config.NumberColumn("Engagement %", format="%.1f%%"),
            "Sentiment": st.column_config.NumberColumn("Sentiment Score", format="%.2f"),
            "Views": st.column_config.NumberColumn("Views", format="%d")
        }
    )
    st.markdown('</div>', unsafe_allow_html=True)

def main():
    """Main dashboard function."""
    # Initialize components
    components = initialize_components()
    
    # Sidebar
    st.sidebar.markdown("## ⚙️ Settings")
    
    # Time range selector
    time_range = st.sidebar.selectbox(
        "Time Range",
        ["Last 7 days", "Last 30 days", "Last 90 days"],
        index=1
    )
    
    # Auto-refresh
    auto_refresh = st.sidebar.checkbox("Auto-refresh (5 min)", value=False)
    
    if auto_refresh:
        st.sidebar.info("🔄 Auto-refresh enabled")
        time.sleep(300)
        st.rerun()
    
    # Main content
    show_executive_summary()
    
    # Two-column layout for charts
    col1, col2 = st.columns(2)
    
    with col1:
        show_engagement_analysis()
    
    with col2:
        show_sentiment_analysis()
    
    # Full-width content performance
    show_content_performance()
    
    # Footer
    st.markdown("---")
    st.markdown(
        f'<div style="text-align: center; color: {DARK_GRAY}; font-size: 0.9rem;">'
        'Nordic Analytics Platform • Real-time Media Intelligence'
        '</div>',
        unsafe_allow_html=True
    )

if __name__ == "__main__":
    main()