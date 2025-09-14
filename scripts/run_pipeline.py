#!/usr/bin/env python3
"""
Data Pipeline Runner

Runs the complete data pipeline for collecting news, analyzing sentiment,
and tracking engagement metrics.
"""

import sys
import os
import time
import logging
import threading
import signal
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
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/pipeline.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

# Global variables for real-time processing
real_time_components = {}
is_real_time_running = False

def run_news_collection():
    """Run news collection pipeline."""
    logger.info("Starting news collection...")
    
    try:
        collector = NewsCollector()
        articles = collector.collect_news_articles(hours_back=24)
        
        logger.info(f"Collected {len(articles)} articles")
        return articles
        
    except Exception as e:
        logger.error(f"Error in news collection: {e}")
        return []

def run_sentiment_analysis(articles):
    """Run sentiment analysis on collected articles."""
    logger.info("Starting sentiment analysis...")
    
    try:
        analyzer = NordicSentimentAnalyzer()
        db = DatabaseManager()
        
        analyzed_count = 0
        for article in articles:
            # Analyze sentiment
            sentiment_result = analyzer.analyze_sentiment(
                article['content'],
                language=article['source_language']
            )
            
            # Save to database
            if db.save_sentiment_analysis(article['id'], sentiment_result):
                analyzed_count += 1
        
        logger.info(f"Analyzed sentiment for {analyzed_count} articles")
        return analyzed_count
        
    except Exception as e:
        logger.error(f"Error in sentiment analysis: {e}")
        return 0

def run_engagement_tracking():
    """Run engagement tracking and metrics calculation."""
    logger.info("Starting engagement tracking...")
    
    try:
        tracker = EngagementTracker()
        db = DatabaseManager()
        
        # Get all articles
        articles = db.get_articles(limit=1000)
        
        updated_count = 0
        for article in articles:
            # Get engagement metrics
            metrics = tracker.get_article_metrics(article['id'])
            if metrics:
                # Calculate content score
                content_score = tracker.calculate_content_score(article['id'])
                metrics['content_score'] = content_score
                
                # Update database
                if db.update_article_metrics(article['id'], metrics):
                    updated_count += 1
        
        logger.info(f"Updated metrics for {updated_count} articles")
        return updated_count
        
    except Exception as e:
        logger.error(f"Error in engagement tracking: {e}")
        return 0

def run_data_quality_checks():
    """Run data quality checks and validation."""
    logger.info("Running data quality checks...")
    
    try:
        db = DatabaseManager()
        stats = db.get_database_stats()
        
        # Check for missing data
        issues = []
        
        if stats.get('total_articles', 0) == 0:
            issues.append("No articles found")
        
        if stats.get('total_sentiment_analyses', 0) == 0:
            issues.append("No sentiment analyses found")
        
        if stats.get('total_engagement_events', 0) == 0:
            issues.append("No engagement events found")
        
        if issues:
            logger.warning(f"Data quality issues found: {', '.join(issues)}")
        else:
            logger.info("Data quality checks passed")
        
        return len(issues) == 0
        
    except Exception as e:
        logger.error(f"Error in data quality checks: {e}")
        return False

def generate_pipeline_report():
    """Generate a pipeline execution report."""
    logger.info("Generating pipeline report...")
    
    try:
        db = DatabaseManager()
        stats = db.get_database_stats()
        
        report = {
            'timestamp': datetime.now().isoformat(),
            'total_articles': stats.get('total_articles', 0),
            'total_sentiment_analyses': stats.get('total_sentiment_analyses', 0),
            'total_engagement_events': stats.get('total_engagement_events', 0),
            'unique_users': stats.get('unique_users', 0),
            'average_sentiment_score': stats.get('average_sentiment_score', 0)
        }
        
        # Save report
        import json
        with open('logs/pipeline_report.json', 'w') as f:
            json.dump(report, f, indent=2)
        
        logger.info("Pipeline report generated")
        return report
        
    except Exception as e:
        logger.error(f"Error generating pipeline report: {e}")
        return {}

def main():
    """Main pipeline execution function."""
    logger.info("Starting Nordic News Analytics Pipeline")
    start_time = time.time()
    
    try:
        # Step 1: News Collection
        articles = run_news_collection()
        
        # Step 2: Sentiment Analysis
        analyzed_count = run_sentiment_analysis(articles)
        
        # Step 3: Engagement Tracking
        updated_count = run_engagement_tracking()
        
        # Step 4: Data Quality Checks
        quality_ok = run_data_quality_checks()
        
        # Step 5: Generate Report
        report = generate_pipeline_report()
        
        # Summary
        execution_time = time.time() - start_time
        logger.info(f"Pipeline completed in {execution_time:.2f} seconds")
        logger.info(f"Articles processed: {len(articles)}")
        logger.info(f"Sentiment analyses: {analyzed_count}")
        logger.info(f"Metrics updated: {updated_count}")
        logger.info(f"Data quality: {'PASS' if quality_ok else 'FAIL'}")
        
        return True
        
    except Exception as e:
        logger.error(f"Pipeline failed: {e}")
        return False

def initialize_real_time_components():
    """Initialize components for real-time processing."""
    global real_time_components
    
    try:
        real_time_components = {
            'news_collector': NewsCollector(),
            'sentiment_analyzer': NordicSentimentAnalyzer(),
            'engagement_tracker': EngagementTracker(),
            'db_manager': DatabaseManager()
        }
        
        # Set up callback for news collection
        real_time_components['news_collector'].add_callback(process_new_articles)
        
        logger.info("Real-time components initialized successfully")
        return True
        
    except Exception as e:
        logger.error(f"Failed to initialize real-time components: {e}")
        return False

def process_new_articles(articles):
    """Process newly collected articles in real-time."""
    global real_time_components
    
    if not real_time_components:
        logger.error("Real-time components not initialized")
        return
    
    try:
        logger.info(f"Processing {len(articles)} new articles in real-time...")
        
        # Process sentiment analysis
        sentiment_analyzer = real_time_components['sentiment_analyzer']
        for article in articles:
            try:
                # Analyze sentiment
                sentiment_result = sentiment_analyzer.analyze_article(article)
                article.update(sentiment_result)
                
                # Store in database
                db_manager = real_time_components['db_manager']
                db_manager.store_article(article)
                
            except Exception as e:
                logger.error(f"Error processing article {article.get('title', 'Unknown')}: {e}")
                continue
        
        # Update engagement metrics
        engagement_tracker = real_time_components['engagement_tracker']
        engagement_tracker.update_metrics()
        
        logger.info(f"Successfully processed {len(articles)} articles in real-time")
        
    except Exception as e:
        logger.error(f"Error in real-time article processing: {e}")

def start_real_time_pipeline(collection_interval_minutes=15):
    """Start the real-time data pipeline."""
    global is_real_time_running
    
    if is_real_time_running:
        logger.warning("Real-time pipeline is already running")
        return False
    
    try:
        # Initialize components
        if not initialize_real_time_components():
            return False
        
        # Start real-time news collection
        news_collector = real_time_components['news_collector']
        news_collector.start_real_time_collection(collection_interval_minutes)
        
        is_real_time_running = True
        logger.info(f"Real-time pipeline started with {collection_interval_minutes} minute intervals")
        
        return True
        
    except Exception as e:
        logger.error(f"Failed to start real-time pipeline: {e}")
        return False

def stop_real_time_pipeline():
    """Stop the real-time data pipeline."""
    global is_real_time_running, real_time_components
    
    if not is_real_time_running:
        logger.warning("Real-time pipeline is not running")
        return
    
    try:
        # Stop news collection
        if real_time_components and 'news_collector' in real_time_components:
            real_time_components['news_collector'].stop_real_time_collection()
        
        is_real_time_running = False
        logger.info("Real-time pipeline stopped")
        
    except Exception as e:
        logger.error(f"Error stopping real-time pipeline: {e}")

def get_real_time_stats():
    """Get real-time pipeline statistics."""
    global real_time_components, is_real_time_running
    
    if not real_time_components:
        return {"error": "Components not initialized"}
    
    stats = {
        "is_running": is_real_time_running,
        "news_collection": real_time_components['news_collector'].get_collection_stats(),
        "timestamp": datetime.now().isoformat()
    }
    
    return stats

def signal_handler(signum, frame):
    """Handle shutdown signals gracefully."""
    logger.info("Received shutdown signal, stopping real-time pipeline...")
    stop_real_time_pipeline()
    sys.exit(0)

def run_real_time_mode():
    """Run the pipeline in real-time mode."""
    # Set up signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    logger.info("Starting Nordic News Analytics in Real-Time Mode")
    logger.info("Press Ctrl+C to stop")
    
    # Start real-time pipeline
    if not start_real_time_pipeline():
        logger.error("Failed to start real-time pipeline")
        return False
    
    try:
        # Keep the main thread alive
        while is_real_time_running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Received keyboard interrupt")
    finally:
        stop_real_time_pipeline()
    
    logger.info("Real-time pipeline shutdown complete")
    return True

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Nordic News Analytics Pipeline')
    parser.add_argument('--real-time', action='store_true', 
                       help='Run in real-time mode')
    parser.add_argument('--interval', type=int, default=15,
                       help='Collection interval in minutes (real-time mode only)')
    
    args = parser.parse_args()
    
    if args.real_time:
        success = run_real_time_mode()
    else:
        success = main()
    
    sys.exit(0 if success else 1)