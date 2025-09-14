#!/usr/bin/env python3
"""
Real-Time Nordic News Analytics Demo

Demonstrates the real-time data processing capabilities of the Nordic News
Sentiment & Engagement Tracker system.
"""

import sys
import os
import time
import logging
from datetime import datetime

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from data_pipeline.news_collector import NewsCollector
from sentiment_analysis.sentiment_analyzer import NordicSentimentAnalyzer
from engagement_tracking.engagement_tracker import EngagementTracker
from database.database_manager import DatabaseManager

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)

def demo_real_time_collection():
    """Demonstrate real-time news collection."""
    print("🚀 Starting Real-Time Nordic News Analytics Demo")
    print("=" * 60)
    
    # Initialize components
    print("📊 Initializing components...")
    news_collector = NewsCollector()
    sentiment_analyzer = NordicSentimentAnalyzer()
    engagement_tracker = EngagementTracker()
    db_manager = DatabaseManager()
    
    print("✅ Components initialized successfully!")
    
    # Set up callback for real-time processing
    def process_articles_callback(articles):
        print(f"\n🔄 Processing {len(articles)} new articles...")
        
        for i, article in enumerate(articles[:3]):  # Show first 3 articles
            print(f"  📰 {i+1}. {article['title'][:80]}...")
            print(f"     Source: {article['source_name']} ({article['source_country']})")
            print(f"     Published: {article['published_date']}")
        
        if len(articles) > 3:
            print(f"     ... and {len(articles) - 3} more articles")
        
        # Process sentiment analysis
        print("  🧠 Analyzing sentiment...")
        for article in articles:
            try:
                sentiment_result = sentiment_analyzer.analyze_article(article)
                article.update(sentiment_result)
            except Exception as e:
                print(f"     ⚠️ Error analyzing article: {e}")
        
        # Store in database
        print("  💾 Storing in database...")
        for article in articles:
            try:
                db_manager.store_article(article)
            except Exception as e:
                print(f"     ⚠️ Error storing article: {e}")
        
        print("  ✅ Processing complete!")
    
    # Add callback
    news_collector.add_callback(process_articles_callback)
    
    # Start real-time collection
    print("\n🔄 Starting real-time collection (15-minute intervals)...")
    print("   Press Ctrl+C to stop")
    
    try:
        news_collector.start_real_time_collection(interval_minutes=15)
        
        # Keep running and show stats
        while True:
            time.sleep(30)  # Check every 30 seconds
            stats = news_collector.get_collection_stats()
            print(f"\n📈 Collection Stats:")
            print(f"   Running: {stats['is_running']}")
            print(f"   Total Articles: {stats['total_articles_collected']}")
            print(f"   Last Collection: {stats['last_collection_time']}")
            print(f"   Callbacks: {stats['callbacks_registered']}")
            
    except KeyboardInterrupt:
        print("\n🛑 Stopping real-time collection...")
        news_collector.stop_real_time_collection()
        print("✅ Demo completed!")

def demo_manual_collection():
    """Demonstrate manual collection of recent articles."""
    print("🔍 Manual Collection Demo")
    print("=" * 40)
    
    news_collector = NewsCollector()
    
    # Collect recent articles (last 30 minutes)
    print("📰 Collecting articles from last 30 minutes...")
    articles = news_collector.collect_recent_articles(minutes_back=30)
    
    print(f"✅ Found {len(articles)} recent articles")
    
    if articles:
        print("\n📋 Recent Articles:")
        for i, article in enumerate(articles[:5]):  # Show first 5
            print(f"  {i+1}. {article['title']}")
            print(f"     Source: {article['source_name']}")
            print(f"     Published: {article['published_date']}")
            print()
    
    return articles

def demo_dashboard_integration():
    """Demonstrate dashboard integration with real-time data."""
    print("📊 Dashboard Integration Demo")
    print("=" * 40)
    
    # Import dashboard functions
    from dashboard.main import get_real_time_data, get_live_metrics
    
    print("🔄 Fetching real-time data...")
    data = get_real_time_data()
    
    if data:
        print("✅ Real-time data fetched successfully!")
        print(f"   Articles: {len(data['articles'])}")
        print(f"   Last Updated: {data['last_updated']}")
        
        print("\n📈 Live Metrics:")
        metrics = get_live_metrics()
        for key, value in metrics.items():
            print(f"   {key}: {value}")
    else:
        print("⚠️ No real-time data available (using sample data)")
        print("   This is normal if the database is empty or not running")

def main():
    """Main demo function."""
    print("🎯 Nordic News Analytics - Real-Time Demo")
    print("=" * 50)
    print()
    
    # Show options
    print("Choose demo mode:")
    print("1. Manual Collection (quick demo)")
    print("2. Real-Time Collection (continuous)")
    print("3. Dashboard Integration (data fetching)")
    print("4. Full Pipeline Test")
    
    try:
        choice = input("\nEnter choice (1-4): ").strip()
        
        if choice == "1":
            demo_manual_collection()
        elif choice == "2":
            demo_real_time_collection()
        elif choice == "3":
            demo_dashboard_integration()
        elif choice == "4":
            print("🔄 Running full pipeline test...")
            from scripts.run_pipeline import main as run_pipeline
            success = run_pipeline()
            print(f"Pipeline {'✅ SUCCESS' if success else '❌ FAILED'}")
        else:
            print("❌ Invalid choice")
            
    except KeyboardInterrupt:
        print("\n👋 Demo interrupted by user")
    except Exception as e:
        print(f"❌ Demo error: {e}")

if __name__ == "__main__":
    main()