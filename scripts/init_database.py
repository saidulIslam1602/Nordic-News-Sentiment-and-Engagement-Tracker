#!/usr/bin/env python3
"""
Database Initialization Script

Initializes the Nordic News Sentiment & Engagement Tracker database
with sample data for demonstration purposes.
"""

import sys
import os
from datetime import datetime, timedelta
import random

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from database.database_manager import DatabaseManager
from data_pipeline.news_collector import NewsCollector
from sentiment_analysis.sentiment_analyzer import NordicSentimentAnalyzer
from engagement_tracking.engagement_tracker import EngagementTracker

def create_sample_data():
    """Create sample data for demonstration."""
    print("Creating sample data...")
    
    # Initialize components
    db = DatabaseManager()
    news_collector = NewsCollector()
    sentiment_analyzer = NordicSentimentAnalyzer()
    engagement_tracker = EngagementTracker()
    
    # Sample articles
    sample_articles = [
        {
            'id': 'art_001',
            'title': 'Major Economic Development in Nordic Region',
            'url': 'https://example.com/economic-development',
            'summary': 'A significant economic development has been announced in the Nordic region, promising growth and stability.',
            'content': 'The Nordic region has announced a major economic development initiative that will boost regional cooperation and economic growth. This development comes after months of negotiations between Nordic countries and represents a significant step forward in regional integration.',
            'published_date': (datetime.now() - timedelta(hours=2)).isoformat(),
            'source_name': 'VG',
            'source_country': 'Norway',
            'source_language': 'no',
            'author': 'Economic Reporter',
            'tags': ['economy', 'nordic', 'development'],
            'word_count': 45,
            'collected_at': datetime.now().isoformat()
        },
        {
            'id': 'art_002',
            'title': 'Climate Change Impact on Arctic Communities',
            'url': 'https://example.com/climate-arctic',
            'summary': 'New research reveals the growing impact of climate change on Arctic communities in the Nordic region.',
            'content': 'A comprehensive study published today shows that climate change is having an increasingly severe impact on Arctic communities across the Nordic region. The research highlights rising temperatures, melting ice, and changing weather patterns that are affecting traditional ways of life.',
            'published_date': (datetime.now() - timedelta(hours=4)).isoformat(),
            'source_name': 'Aftenposten',
            'source_country': 'Norway',
            'source_language': 'no',
            'author': 'Climate Reporter',
            'tags': ['climate', 'arctic', 'environment'],
            'word_count': 52,
            'collected_at': datetime.now().isoformat()
        },
        {
            'id': 'art_003',
            'title': 'Technology Innovation in Stockholm',
            'url': 'https://example.com/tech-stockholm',
            'summary': 'Stockholm continues to lead in technology innovation with new startup ecosystem developments.',
            'content': 'Stockholm has reinforced its position as a leading technology hub in Europe with the launch of several new initiatives supporting startup innovation. The city\'s ecosystem continues to attract international talent and investment.',
            'published_date': (datetime.now() - timedelta(hours=6)).isoformat(),
            'source_name': 'Svenska Dagbladet',
            'source_country': 'Sweden',
            'source_language': 'sv',
            'author': 'Tech Reporter',
            'tags': ['technology', 'startup', 'innovation'],
            'word_count': 38,
            'collected_at': datetime.now().isoformat()
        },
        {
            'id': 'art_004',
            'title': 'Cultural Festival in Copenhagen',
            'url': 'https://example.com/culture-copenhagen',
            'summary': 'Copenhagen hosts a vibrant cultural festival celebrating Nordic arts and traditions.',
            'content': 'The annual Nordic Cultural Festival in Copenhagen has opened to great fanfare, showcasing the rich artistic traditions of the Nordic countries. The festival features music, dance, visual arts, and culinary experiences from across the region.',
            'published_date': (datetime.now() - timedelta(hours=8)).isoformat(),
            'source_name': 'Berlingske',
            'source_country': 'Denmark',
            'source_language': 'da',
            'author': 'Culture Reporter',
            'tags': ['culture', 'festival', 'arts'],
            'word_count': 41,
            'collected_at': datetime.now().isoformat()
        },
        {
            'id': 'art_005',
            'title': 'Sports Victory in Helsinki',
            'url': 'https://example.com/sports-helsinki',
            'summary': 'Helsinki celebrates a major sports victory with record-breaking performance.',
            'content': 'Helsinki is celebrating a historic sports victory as local athletes achieved record-breaking performances in international competition. The victory represents a significant milestone for Finnish sports and has brought the nation together in celebration.',
            'published_date': (datetime.now() - timedelta(hours=10)).isoformat(),
            'source_name': 'Helsingin Sanomat',
            'source_country': 'Finland',
            'source_language': 'fi',
            'author': 'Sports Reporter',
            'tags': ['sports', 'victory', 'achievement'],
            'word_count': 43,
            'collected_at': datetime.now().isoformat()
        }
    ]
    
    # Save articles to database
    for article in sample_articles:
        db.save_article(article)
        print(f"Saved article: {article['title']}")
    
    # Generate sentiment analysis for articles
    for article in sample_articles:
        sentiment_result = sentiment_analyzer.analyze_sentiment(
            article['content'], 
            language=article['source_language']
        )
        db.save_sentiment_analysis(article['id'], sentiment_result)
        print(f"Analyzed sentiment for: {article['title']}")
    
    # Generate sample engagement events
    event_types = ['page_view', 'click', 'share', 'time_on_page']
    countries = ['Norway', 'Sweden', 'Denmark', 'Finland']
    device_types = ['mobile', 'desktop', 'tablet']
    
    for article in sample_articles:
        # Generate 50-200 events per article
        num_events = random.randint(50, 200)
        
        for i in range(num_events):
            event = {
                'event_id': f"evt_{article['id']}_{i}",
                'user_id': f"user_{random.randint(1, 1000)}",
                'article_id': article['id'],
                'event_type': random.choice(event_types),
                'timestamp': (datetime.now() - timedelta(
                    hours=random.randint(0, 24),
                    minutes=random.randint(0, 59)
                )).isoformat(),
                'session_id': f"sess_{random.randint(1, 500)}",
                'country': random.choice(countries),
                'device_type': random.choice(device_types),
                'metadata': {
                    'referrer': random.choice(['google.com', 'facebook.com', 'direct', 'twitter.com']),
                    'duration': random.randint(10, 300) if random.choice(event_types) == 'time_on_page' else None
                }
            }
            
            engagement_tracker.track_event(event)
    
    print("Generated sample engagement events")
    
    # Calculate and save article metrics
    for article in sample_articles:
        metrics = engagement_tracker.get_article_metrics(article['id'])
        if metrics:
            content_score = engagement_tracker.calculate_content_score(article['id'])
            metrics['content_score'] = content_score
            db.update_article_metrics(article['id'], metrics)
            print(f"Updated metrics for: {article['title']} (Score: {content_score})")
    
    print("Sample data creation completed!")

def main():
    """Main function."""
    print("Initializing Nordic News Sentiment & Engagement Tracker Database...")
    
    try:
        # Create sample data
        create_sample_data()
        
        # Display database stats
        db = DatabaseManager()
        stats = db.get_database_stats()
        
        print("\nDatabase Statistics:")
        print(f"Total Articles: {stats.get('total_articles', 0)}")
        print(f"Total Sentiment Analyses: {stats.get('total_sentiment_analyses', 0)}")
        print(f"Total Engagement Events: {stats.get('total_engagement_events', 0)}")
        print(f"Unique Users: {stats.get('unique_users', 0)}")
        print(f"Average Sentiment Score: {stats.get('average_sentiment_score', 0)}")
        
        print("\nDatabase initialization completed successfully!")
        print("You can now run the dashboard with: streamlit run dashboard/main.py")
        
    except Exception as e:
        print(f"Error during initialization: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()