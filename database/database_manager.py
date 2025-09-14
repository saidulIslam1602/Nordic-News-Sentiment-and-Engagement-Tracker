"""
Database Manager

Handles database operations for the Nordic News Sentiment & Engagement Tracker.
Supports both SQLite (development) and PostgreSQL (production).
"""

import sqlite3
import logging
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
import yaml
import os
from contextlib import contextmanager

logger = logging.getLogger(__name__)


class DatabaseManager:
    """
    Manages database operations for the Nordic News Analytics platform.
    
    Features:
    - SQLite for development, PostgreSQL for production
    - Article storage and retrieval
    - Sentiment analysis data storage
    - Engagement metrics tracking
    - Data migration and backup
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the database manager."""
        self.config = self._load_config(config_path)
        self.db_type = self.config.get('database', {}).get('development', {}).get('type', 'sqlite')
        self.db_path = self.config.get('database', {}).get('development', {}).get('path', 'data/nordic_news.db')
        
        # Create database directory if it doesn't exist
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        
        # Initialize database
        self._initialize_database()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
    
    def _initialize_database(self):
        """Initialize database tables."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Create articles table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS articles (
                        id TEXT PRIMARY KEY,
                        title TEXT NOT NULL,
                        url TEXT UNIQUE,
                        summary TEXT,
                        content TEXT,
                        published_date TEXT,
                        source_name TEXT,
                        source_country TEXT,
                        source_language TEXT,
                        author TEXT,
                        tags TEXT,
                        word_count INTEGER,
                        collected_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create sentiment_analysis table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS sentiment_analysis (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        article_id TEXT,
                        sentiment_label TEXT,
                        compound_score REAL,
                        positive_score REAL,
                        negative_score REAL,
                        neutral_score REAL,
                        confidence REAL,
                        method TEXT,
                        language TEXT,
                        analyzed_at TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
                # Create engagement_events table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS engagement_events (
                        id TEXT PRIMARY KEY,
                        user_id TEXT,
                        article_id TEXT,
                        event_type TEXT,
                        timestamp TEXT,
                        session_id TEXT,
                        country TEXT,
                        device_type TEXT,
                        metadata TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
                # Create article_metrics table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS article_metrics (
                        article_id TEXT PRIMARY KEY,
                        total_views INTEGER DEFAULT 0,
                        unique_users INTEGER DEFAULT 0,
                        clicks INTEGER DEFAULT 0,
                        shares INTEGER DEFAULT 0,
                        avg_time_on_page REAL DEFAULT 0,
                        ctr REAL DEFAULT 0,
                        share_rate REAL DEFAULT 0,
                        content_score REAL DEFAULT 0,
                        last_updated TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
                # Create ab_tests table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ab_tests (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        description TEXT,
                        status TEXT,
                        traffic_split REAL,
                        start_date TEXT,
                        end_date TEXT,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                # Create ab_test_results table
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS ab_test_results (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        test_id TEXT,
                        variant TEXT,
                        metric_name TEXT,
                        metric_value REAL,
                        sample_size INTEGER,
                        confidence_level REAL,
                        p_value REAL,
                        is_significant BOOLEAN,
                        created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (test_id) REFERENCES ab_tests (id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_published_date ON articles (published_date)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_articles_source ON articles (source_name)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_sentiment_article_id ON sentiment_analysis (article_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagement_article_id ON engagement_events (article_id)")
                cursor.execute("CREATE INDEX IF NOT EXISTS idx_engagement_timestamp ON engagement_events (timestamp)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            if self.db_type == 'sqlite':
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
            else:
                # PostgreSQL connection would go here
                raise NotImplementedError("PostgreSQL support not implemented yet")
            
            yield conn
        except Exception as e:
            if conn:
                conn.rollback()
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                conn.close()
    
    def save_article(self, article: Dict) -> bool:
        """Save an article to the database."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO articles (
                        id, title, url, summary, content, published_date,
                        source_name, source_country, source_language, author,
                        tags, word_count, collected_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article['id'],
                    article['title'],
                    article['url'],
                    article['summary'],
                    article['content'],
                    article['published_date'],
                    article['source_name'],
                    article['source_country'],
                    article['source_language'],
                    article['author'],
                    json.dumps(article['tags']),
                    article['word_count'],
                    article['collected_at']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            return False
    
    def save_sentiment_analysis(self, article_id: str, sentiment_data: Dict) -> bool:
        """Save sentiment analysis results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO sentiment_analysis (
                        article_id, sentiment_label, compound_score,
                        positive_score, negative_score, neutral_score,
                        confidence, method, language, analyzed_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_id,
                    sentiment_data['sentiment_label'],
                    sentiment_data['compound_score'],
                    sentiment_data['positive_score'],
                    sentiment_data['negative_score'],
                    sentiment_data['neutral_score'],
                    sentiment_data['confidence'],
                    sentiment_data['method'],
                    sentiment_data['language'],
                    sentiment_data['timestamp']
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving sentiment analysis: {e}")
            return False
    
    def save_engagement_event(self, event: Dict) -> bool:
        """Save an engagement event."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO engagement_events (
                        id, user_id, article_id, event_type, timestamp,
                        session_id, country, device_type, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    event['event_id'],
                    event['user_id'],
                    event['article_id'],
                    event['event_type'],
                    event['timestamp'],
                    event['session_id'],
                    event['country'],
                    event['device_type'],
                    json.dumps(event['metadata'])
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving engagement event: {e}")
            return False
    
    def update_article_metrics(self, article_id: str, metrics: Dict) -> bool:
        """Update article engagement metrics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT OR REPLACE INTO article_metrics (
                        article_id, total_views, unique_users, clicks, shares,
                        avg_time_on_page, ctr, share_rate, content_score, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    article_id,
                    metrics.get('total_views', 0),
                    metrics.get('unique_users', 0),
                    metrics.get('clicks', 0),
                    metrics.get('shares', 0),
                    metrics.get('avg_time_on_page', 0),
                    metrics.get('ctr', 0),
                    metrics.get('share_rate', 0),
                    metrics.get('content_score', 0),
                    datetime.now().isoformat()
                ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error updating article metrics: {e}")
            return False
    
    def get_articles(self, limit: int = 100, offset: int = 0, 
                    source: Optional[str] = None, 
                    language: Optional[str] = None) -> List[Dict]:
        """Get articles with optional filtering."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = "SELECT * FROM articles WHERE 1=1"
                params = []
                
                if source:
                    query += " AND source_name = ?"
                    params.append(source)
                
                if language:
                    query += " AND source_language = ?"
                    params.append(language)
                
                query += " ORDER BY published_date DESC LIMIT ? OFFSET ?"
                params.extend([limit, offset])
                
                cursor.execute(query, params)
                rows = cursor.fetchall()
                
                articles = []
                for row in rows:
                    article = dict(row)
                    article['tags'] = json.loads(article['tags']) if article['tags'] else []
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting articles: {e}")
            return []
    
    def get_article_sentiment(self, article_id: str) -> Optional[Dict]:
        """Get sentiment analysis for a specific article."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM sentiment_analysis 
                    WHERE article_id = ? 
                    ORDER BY analyzed_at DESC 
                    LIMIT 1
                """, (article_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting article sentiment: {e}")
            return None
    
    def get_article_metrics(self, article_id: str) -> Optional[Dict]:
        """Get engagement metrics for a specific article."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT * FROM article_metrics 
                    WHERE article_id = ?
                """, (article_id,))
                
                row = cursor.fetchone()
                return dict(row) if row else None
                
        except Exception as e:
            logger.error(f"Error getting article metrics: {e}")
            return None
    
    def get_sentiment_trends(self, days: int = 7) -> List[Dict]:
        """Get sentiment trends over time."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        DATE(analyzed_at) as date,
                        sentiment_label,
                        COUNT(*) as count,
                        AVG(compound_score) as avg_score
                    FROM sentiment_analysis 
                    WHERE analyzed_at >= datetime('now', '-{} days')
                    GROUP BY DATE(analyzed_at), sentiment_label
                    ORDER BY date DESC
                """.format(days))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting sentiment trends: {e}")
            return []
    
    def get_engagement_trends(self, days: int = 7) -> List[Dict]:
        """Get engagement trends over time."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        DATE(timestamp) as date,
                        event_type,
                        COUNT(*) as count
                    FROM engagement_events 
                    WHERE timestamp >= datetime('now', '-{} days')
                    GROUP BY DATE(timestamp), event_type
                    ORDER BY date DESC
                """.format(days))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting engagement trends: {e}")
            return []
    
    def get_top_articles(self, metric: str = 'ctr', limit: int = 10) -> List[Dict]:
        """Get top performing articles by metric."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT 
                        a.id,
                        a.title,
                        a.source_name,
                        a.published_date,
                        m.{}
                    FROM articles a
                    JOIN article_metrics m ON a.id = m.article_id
                    ORDER BY m.{} DESC
                    LIMIT ?
                """.format(metric, metric), (limit,))
                
                rows = cursor.fetchall()
                return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting top articles: {e}")
            return []
    
    def get_database_stats(self) -> Dict:
        """Get database statistics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                stats = {}
                
                # Count articles
                cursor.execute("SELECT COUNT(*) FROM articles")
                stats['total_articles'] = cursor.fetchone()[0]
                
                # Count sentiment analyses
                cursor.execute("SELECT COUNT(*) FROM sentiment_analysis")
                stats['total_sentiment_analyses'] = cursor.fetchone()[0]
                
                # Count engagement events
                cursor.execute("SELECT COUNT(*) FROM engagement_events")
                stats['total_engagement_events'] = cursor.fetchone()[0]
                
                # Count unique users
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM engagement_events")
                stats['unique_users'] = cursor.fetchone()[0]
                
                # Average sentiment score
                cursor.execute("SELECT AVG(compound_score) FROM sentiment_analysis")
                avg_sentiment = cursor.fetchone()[0]
                stats['average_sentiment_score'] = round(avg_sentiment, 3) if avg_sentiment else 0
                
                return stats
                
        except Exception as e:
            logger.error(f"Error getting database stats: {e}")
            return {}
    
    def get_articles_by_timeframe(self, hours_back: int = 24) -> List[Dict]:
        """Get articles from the last N hours."""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours_back)
            
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                query = """
                SELECT a.*, s.compound_score, s.sentiment_label, s.confidence
                FROM articles a
                LEFT JOIN sentiment_analysis s ON a.id = s.article_id
                WHERE a.published_date >= ?
                ORDER BY a.published_date DESC
                """
                
                cursor.execute(query, (cutoff_time,))
                rows = cursor.fetchall()
                
                articles = []
                for row in rows:
                    article = {
                        'id': row[0],
                        'title': row[1],
                        'content': row[2],
                        'url': row[3],
                        'source_name': row[4],
                        'source_country': row[5],
                        'language': row[6],
                        'published_date': row[7],
                        'word_count': row[8],
                        'created_at': row[9],
                        'sentiment_score': row[10],
                        'sentiment_label': row[11],
                        'confidence': row[12]
                    }
                    articles.append(article)
                
                return articles
                
        except Exception as e:
            logger.error(f"Error getting articles by timeframe: {e}")
            return []
    
    def get_engagement_metrics(self) -> Dict:
        """Get current engagement metrics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total users
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM engagement_events")
                total_users = cursor.fetchone()[0] or 0
                
                # Get average engagement rate (using available columns)
                cursor.execute("""
                    SELECT AVG(engagement_score), AVG(time_on_page), COUNT(*)
                    FROM engagement_events
                    WHERE timestamp >= datetime('now', '-24 hours')
                """)
                result = cursor.fetchone()
                avg_ctr = result[0] or 0
                avg_time = result[1] or 0
                total_events = result[2] or 0
                
                return {
                    'total_users': total_users,
                    'avg_engagement_rate': avg_ctr * 100,  # Convert to percentage
                    'avg_time_on_page': avg_time,
                    'total_events_24h': total_events
                }
                
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {e}")
            return {
                'total_users': 0,
                'avg_engagement_rate': 0,
                'avg_time_on_page': 0,
                'total_events_24h': 0
            }
    
    def get_sentiment_data(self) -> Dict:
        """Get sentiment analysis data."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get sentiment distribution
                cursor.execute("""
                    SELECT sentiment_label, COUNT(*) as count
                    FROM sentiment_analysis
                    WHERE created_at >= datetime('now', '-24 hours')
                    GROUP BY sentiment_label
                """)
                sentiment_counts = dict(cursor.fetchall())
                
                # Get average sentiment score
                cursor.execute("""
                    SELECT AVG(compound_score)
                    FROM sentiment_analysis
                    WHERE created_at >= datetime('now', '-24 hours')
                """)
                avg_sentiment = cursor.fetchone()[0] or 0
                
                return {
                    'sentiment_distribution': sentiment_counts,
                    'avg_sentiment_score': avg_sentiment,
                    'total_analyses': sum(sentiment_counts.values())
                }
                
        except Exception as e:
            logger.error(f"Error getting sentiment data: {e}")
            return {
                'sentiment_distribution': {},
                'avg_sentiment_score': 0,
                'total_analyses': 0
            }
    
    def backup_database(self, backup_path: str) -> bool:
        """Create a backup of the database."""
        try:
            if self.db_type == 'sqlite':
                import shutil
                shutil.copy2(self.db_path, backup_path)
                logger.info(f"Database backed up to {backup_path}")
                return True
            else:
                logger.warning("Backup not implemented for PostgreSQL")
                return False
        except Exception as e:
            logger.error(f"Error creating backup: {e}")
            return False


def main():
    """Main function for testing the database manager."""
    db = DatabaseManager()
    
    # Test database operations
    print("Database initialized successfully")
    
    # Get database stats
    stats = db.get_database_stats()
    print(f"Database stats: {stats}")
    
    # Test article saving
    test_article = {
        'id': 'test_001',
        'title': 'Test Article',
        'url': 'https://example.com/test',
        'summary': 'This is a test article',
        'content': 'This is the full content of the test article.',
        'published_date': datetime.now().isoformat(),
        'source_name': 'Test Source',
        'source_country': 'Norway',
        'source_language': 'no',
        'author': 'Test Author',
        'tags': ['test', 'example'],
        'word_count': 10,
        'collected_at': datetime.now().isoformat()
    }
    
    success = db.save_article(test_article)
    print(f"Article saved: {success}")
    
    # Test sentiment analysis saving
    test_sentiment = {
        'sentiment_label': 'positive',
        'compound_score': 0.5,
        'positive_score': 0.7,
        'negative_score': 0.1,
        'neutral_score': 0.2,
        'confidence': 0.8,
        'method': 'vader',
        'language': 'en',
        'timestamp': datetime.now().isoformat()
    }
    
    success = db.save_sentiment_analysis('test_001', test_sentiment)
    print(f"Sentiment analysis saved: {success}")
    
    # Get articles
    articles = db.get_articles(limit=5)
    print(f"Retrieved {len(articles)} articles")


if __name__ == "__main__":
    main()