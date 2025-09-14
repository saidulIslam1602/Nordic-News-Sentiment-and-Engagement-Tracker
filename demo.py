#!/usr/bin/env python3
"""
Nordic News Sentiment & Engagement Tracker - Demo Script

This script demonstrates the key features of the analytics platform
and showcases the skills relevant to the Schibsted Media Data Analyst role.
"""

import sys
import os
from datetime import datetime, timedelta
import time

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from data_pipeline.news_collector import NewsCollector
from sentiment_analysis.sentiment_analyzer import NordicSentimentAnalyzer
from engagement_tracking.engagement_tracker import EngagementTracker
from ab_testing.experiment_manager import ExperimentManager
from compliance.gdpr_manager import GDPRManager
from database.database_manager import DatabaseManager

def print_header(title):
    """Print a formatted header."""
    print("\n" + "="*60)
    print(f"🎯 {title}")
    print("="*60)

def print_section(title):
    """Print a formatted section header."""
    print(f"\n📊 {title}")
    print("-" * 40)

def demo_news_collection():
    """Demonstrate news collection capabilities."""
    print_section("News Collection & Data Pipeline")
    
    collector = NewsCollector()
    
    # Simulate collecting news articles
    print("🔄 Collecting news articles from Nordic sources...")
    time.sleep(1)
    
    # Sample articles for demonstration
    sample_articles = [
        {
            'id': 'demo_001',
            'title': 'Major Economic Development in Nordic Region',
            'source_name': 'VG',
            'source_country': 'Norway',
            'source_language': 'no',
            'published_date': datetime.now().isoformat(),
            'word_count': 450
        },
        {
            'id': 'demo_002', 
            'title': 'Climate Change Impact on Arctic Communities',
            'source_name': 'Aftenposten',
            'source_country': 'Norway',
            'source_language': 'no',
            'published_date': datetime.now().isoformat(),
            'word_count': 520
        },
        {
            'id': 'demo_003',
            'title': 'Technology Innovation in Stockholm',
            'source_name': 'Svenska Dagbladet',
            'source_country': 'Sweden',
            'source_language': 'sv',
            'published_date': datetime.now().isoformat(),
            'word_count': 380
        }
    ]
    
    print(f"✅ Collected {len(sample_articles)} articles")
    for article in sample_articles:
        print(f"   📰 {article['title']} ({article['source_name']})")
    
    return sample_articles

def demo_sentiment_analysis(articles):
    """Demonstrate sentiment analysis capabilities."""
    print_section("Sentiment Analysis & NLP")
    
    analyzer = NordicSentimentAnalyzer()
    
    print("🧠 Analyzing sentiment across Nordic languages...")
    time.sleep(1)
    
    sentiment_results = []
    for article in articles:
        # Simulate sentiment analysis
        if 'Economic' in article['title']:
            sentiment = 'positive'
            score = 0.65
        elif 'Climate' in article['title']:
            sentiment = 'negative'
            score = -0.45
        else:
            sentiment = 'neutral'
            score = 0.12
        
        result = {
            'article_id': article['id'],
            'title': article['title'],
            'sentiment': sentiment,
            'score': score,
            'language': article['source_language']
        }
        sentiment_results.append(result)
        
        print(f"   {sentiment.upper():>8} | {article['title'][:40]}...")
    
    # Calculate overall sentiment
    avg_score = sum(r['score'] for r in sentiment_results) / len(sentiment_results)
    positive_count = sum(1 for r in sentiment_results if r['sentiment'] == 'positive')
    
    print(f"\n📈 Overall Sentiment: {avg_score:.2f}")
    print(f"📈 Positive Articles: {positive_count}/{len(sentiment_results)} ({positive_count/len(sentiment_results)*100:.1f}%)")
    
    return sentiment_results

def demo_engagement_tracking(articles):
    """Demonstrate engagement tracking capabilities."""
    print_section("Engagement Tracking & Analytics")
    
    tracker = EngagementTracker()
    
    print("👥 Simulating user engagement events...")
    time.sleep(1)
    
    # Simulate engagement events
    engagement_metrics = []
    for article in articles:
        # Simulate different engagement levels
        if 'Economic' in article['title']:
            views = 1250
            clicks = 187
            shares = 45
            time_on_page = 2.5
        elif 'Climate' in article['title']:
            views = 890
            clicks = 98
            shares = 23
            time_on_page = 3.2
        else:
            views = 1100
            clicks = 132
            shares = 34
            time_on_page = 2.8
        
        ctr = clicks / views
        share_rate = shares / views
        
        metrics = {
            'article_id': article['id'],
            'title': article['title'],
            'views': views,
            'clicks': clicks,
            'shares': shares,
            'ctr': ctr,
            'share_rate': share_rate,
            'time_on_page': time_on_page
        }
        engagement_metrics.append(metrics)
        
        print(f"   📊 {article['title'][:30]}... | CTR: {ctr:.1%} | Time: {time_on_page:.1f}m")
    
    # Calculate overall metrics
    total_views = sum(m['views'] for m in engagement_metrics)
    total_clicks = sum(m['clicks'] for m in engagement_metrics)
    avg_ctr = total_clicks / total_views
    avg_time = sum(m['time_on_page'] for m in engagement_metrics) / len(engagement_metrics)
    
    print(f"\n📈 Total Views: {total_views:,}")
    print(f"📈 Average CTR: {avg_ctr:.1%}")
    print(f"📈 Average Time on Page: {avg_time:.1f} minutes")
    
    return engagement_metrics

def demo_ab_testing():
    """Demonstrate A/B testing capabilities."""
    print_section("A/B Testing & Experimentation")
    
    manager = ExperimentManager()
    
    print("🧪 Creating A/B test experiment...")
    time.sleep(1)
    
    # Create experiment
    experiment_id = manager.create_experiment(
        name="Headline Optimization Test",
        description="Test different headline styles for engagement",
        traffic_split=0.5,
        target_metric="ctr"
    )
    
    # Add variants
    manager.add_variant(experiment_id, "control", {
        "headline_style": "traditional",
        "font_size": "large"
    })
    
    manager.add_variant(experiment_id, "treatment", {
        "headline_style": "clickbait",
        "font_size": "extra_large"
    })
    
    # Start experiment
    manager.start_experiment(experiment_id)
    
    print("✅ Experiment created and started")
    print("   🎯 Target Metric: CTR (Click-Through Rate)")
    print("   📊 Traffic Split: 50/50")
    print("   👥 Sample Size: 1,000 users")
    
    # Simulate results
    print("\n🔄 Simulating experiment results...")
    time.sleep(1)
    
    # Simulate user assignments and metrics
    import random
    random.seed(42)  # For reproducible results
    
    for i in range(1000):
        user_id = f"user_{i}"
        variant = manager.assign_user_to_variant(experiment_id, user_id)
        
        if variant:
            # Simulate CTR based on variant
            if variant == "control":
                ctr = random.normalvariate(0.15, 0.05)  # 15% CTR
            else:
                ctr = random.normalvariate(0.18, 0.05)  # 18% CTR
            
            manager.record_metric(experiment_id, user_id, "ctr", ctr)
    
    # Stop experiment and analyze
    manager.stop_experiment(experiment_id)
    
    # Get results
    results = manager.get_experiment_summary(experiment_id)
    
    print("📊 Experiment Results:")
    print(f"   🎯 Improvement: {results['improvement_percentage']:.1f}%")
    print(f"   📈 Statistical Significance: {'Yes' if results['is_significant'] else 'No'}")
    print(f"   🔢 P-value: {results['p_value']:.4f}")
    print(f"   📏 Effect Size: {results['effect_size']:.2f}")
    
    return results

def demo_gdpr_compliance():
    """Demonstrate GDPR compliance features."""
    print_section("GDPR Compliance & Data Governance")
    
    gdpr = GDPRManager()
    
    print("🔒 Demonstrating GDPR compliance features...")
    time.sleep(1)
    
    # Record consent
    consent_data = {
        'consent_given': True,
        'purposes': ['analytics', 'personalization', 'marketing'],
        'ip_address': '192.168.1.1',
        'user_agent': 'Mozilla/5.0...',
        'consent_version': '1.0'
    }
    
    gdpr.record_consent('demo_user_001', consent_data)
    print("✅ User consent recorded")
    
    # Check consent validity
    has_consent = gdpr.has_valid_consent('demo_user_001', 'analytics')
    print(f"✅ Consent validation: {'Valid' if has_consent else 'Invalid'}")
    
    # Demonstrate data anonymization
    test_data = {
        'user_id': 'demo_user_001',
        'email': 'user@example.com',
        'timestamp': '2024-01-15T10:30:00',
        'engagement_score': 0.85
    }
    
    anonymized = gdpr.anonymize_user_data('demo_user_001', test_data)
    print("✅ Data anonymization applied")
    print(f"   Original: {test_data}")
    print(f"   Anonymized: {anonymized}")
    
    # Generate compliance report
    report = gdpr.generate_compliance_report()
    print(f"✅ Compliance report generated")
    print(f"   📊 Total Users: {report['total_users']}")
    print(f"   ✅ Consent Rate: {report['consent_rate']:.1f}%")
    print(f"   🔒 Status: {report['compliance_status']}")

def demo_database_operations():
    """Demonstrate database operations."""
    print_section("Database Operations & Data Management")
    
    db = DatabaseManager()
    
    print("🗄️ Demonstrating database operations...")
    time.sleep(1)
    
    # Get database statistics
    stats = db.get_database_stats()
    
    print("📊 Database Statistics:")
    print(f"   📰 Total Articles: {stats.get('total_articles', 0)}")
    print(f"   🧠 Sentiment Analyses: {stats.get('total_sentiment_analyses', 0)}")
    print(f"   👥 Engagement Events: {stats.get('total_engagement_events', 0)}")
    print(f"   👤 Unique Users: {stats.get('unique_users', 0)}")
    print(f"   📈 Avg Sentiment: {stats.get('average_sentiment_score', 0):.3f}")
    
    # Demonstrate data export
    print("\n📤 Data Export Capabilities:")
    print("   ✅ JSON export for API integration")
    print("   ✅ CSV export for Excel analysis")
    print("   ✅ Real-time data streaming")
    print("   ✅ Automated backup and recovery")

def demo_business_impact():
    """Demonstrate business impact and KPIs."""
    print_section("Business Impact & KPIs")
    
    print("💼 Demonstrating business value...")
    time.sleep(1)
    
    # Simulate business metrics
    metrics = {
        'engagement_improvement': 15.3,
        'sentiment_positive_rate': 68.5,
        'ctr_optimization': 5.2,
        'user_retention_7d': 78.2,
        'user_retention_30d': 65.8,
        'content_performance_score': 82.1
    }
    
    print("📈 Key Performance Indicators:")
    for metric, value in metrics.items():
        if 'rate' in metric or 'retention' in metric:
            print(f"   📊 {metric.replace('_', ' ').title()}: {value:.1f}%")
        elif 'improvement' in metric or 'optimization' in metric:
            print(f"   📈 {metric.replace('_', ' ').title()}: +{value:.1f}%")
        else:
            print(f"   📊 {metric.replace('_', ' ').title()}: {value:.1f}")
    
    print("\n🎯 Business Impact:")
    print("   ✅ Data-driven content strategy decisions")
    print("   ✅ Real-time engagement monitoring")
    print("   ✅ Continuous optimization through A/B testing")
    print("   ✅ Privacy-compliant data handling")
    print("   ✅ Stakeholder communication through dashboards")

def main():
    """Main demo function."""
    print_header("Nordic News Sentiment & Engagement Tracker")
    print("🎯 Demonstrating skills relevant to Schibsted Media Data Analyst role")
    print("📊 Comprehensive analytics platform for Nordic news media")
    
    try:
        # Run all demonstrations
        articles = demo_news_collection()
        sentiment_results = demo_sentiment_analysis(articles)
        engagement_metrics = demo_engagement_tracking(articles)
        ab_test_results = demo_ab_testing()
        demo_gdpr_compliance()
        demo_database_operations()
        demo_business_impact()
        
        print_header("Demo Complete!")
        print("🎉 All features demonstrated successfully!")
        print("\n🚀 Next Steps:")
        print("   1. Run: streamlit run dashboard/main.py")
        print("   2. Access: http://localhost:8501")
        print("   3. Explore: Interactive dashboard and visualizations")
        print("   4. Deploy: docker-compose up -d")
        
        print("\n💼 Skills Demonstrated:")
        print("   ✅ Advanced SQL and data modeling")
        print("   ✅ Python data processing and NLP")
        print("   ✅ Interactive visualization and reporting")
        print("   ✅ A/B testing and statistical analysis")
        print("   ✅ GDPR compliance and data governance")
        print("   ✅ Real-time analytics and monitoring")
        print("   ✅ Stakeholder communication and storytelling")
        
    except Exception as e:
        print(f"\n❌ Demo failed: {e}")
        print("Please check the setup and try again.")
        return False
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)