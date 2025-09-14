"""
Database Manager

Handles database operations for the Nordic News Sentiment & Engagement Tracker.
Supports Microsoft SQL Server (MSSQL) for both development and production.
"""

import pyodbc
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
    - Microsoft SQL Server (MSSQL) for development and production
    - Article storage and retrieval
    - Sentiment analysis data storage
    - Engagement metrics tracking
    - Data migration and backup
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the database manager."""
        self.config = self._load_config(config_path)
        self.db_config = self.config.get('database', {}).get('development', {})
        self.db_type = self.db_config.get('type', 'mssql')
        self.server = self.db_config.get('server', 'localhost')
        self.port = self.db_config.get('port', 1433)
        self.database = self.db_config.get('database', 'nordic_news_dev')
        self.username = self.db_config.get('username', 'sa')
        self.password = os.getenv('MSSQL_PASSWORD', self.db_config.get('password', ''))
        self.driver = self.db_config.get('driver', 'ODBC Driver 17 for SQL Server')
        
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
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='articles' AND xtype='U')
                    CREATE TABLE articles (
                        id NVARCHAR(255) PRIMARY KEY,
                        title NVARCHAR(MAX) NOT NULL,
                        url NVARCHAR(1000),
                        summary NVARCHAR(MAX),
                        content NVARCHAR(MAX),
                        published_date DATETIME2,
                        source_name NVARCHAR(255),
                        source_country NVARCHAR(100),
                        source_language NVARCHAR(10),
                        author NVARCHAR(255),
                        tags NVARCHAR(MAX),
                        word_count INT,
                        collected_at DATETIME2,
                        created_at DATETIME2 DEFAULT GETDATE()
                    )
                """)
                
                # Create unique index for URL separately
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_articles_url_unique')
                    CREATE UNIQUE INDEX idx_articles_url_unique ON articles (url) WHERE url IS NOT NULL
                """)
                
                # Create sentiment_analysis table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sentiment_analysis' AND xtype='U')
                    CREATE TABLE sentiment_analysis (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        article_id NVARCHAR(255),
                        sentiment_label NVARCHAR(50),
                        compound_score FLOAT,
                        positive_score FLOAT,
                        negative_score FLOAT,
                        neutral_score FLOAT,
                        confidence FLOAT,
                        method NVARCHAR(100),
                        language NVARCHAR(10),
                        analyzed_at DATETIME2,
                        created_at DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
                # Create engagement_events table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='engagement_events' AND xtype='U')
                    CREATE TABLE engagement_events (
                        id NVARCHAR(255) PRIMARY KEY,
                        user_id NVARCHAR(255),
                        article_id NVARCHAR(255),
                        event_type NVARCHAR(100),
                        timestamp DATETIME2,
                        session_id NVARCHAR(255),
                        country NVARCHAR(100),
                        device_type NVARCHAR(50),
                        metadata NVARCHAR(MAX),
                        created_at DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
                # Create article_metrics table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='article_metrics' AND xtype='U')
                    CREATE TABLE article_metrics (
                        article_id NVARCHAR(255) PRIMARY KEY,
                        total_views INT DEFAULT 0,
                        unique_users INT DEFAULT 0,
                        clicks INT DEFAULT 0,
                        shares INT DEFAULT 0,
                        avg_time_on_page FLOAT DEFAULT 0,
                        ctr FLOAT DEFAULT 0,
                        share_rate FLOAT DEFAULT 0,
                        content_score FLOAT DEFAULT 0,
                        last_updated DATETIME2,
                        created_at DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (article_id) REFERENCES articles (id)
                    )
                """)
                
                # Create ab_tests table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ab_tests' AND xtype='U')
                    CREATE TABLE ab_tests (
                        id NVARCHAR(255) PRIMARY KEY,
                        name NVARCHAR(255) NOT NULL,
                        description NVARCHAR(MAX),
                        status NVARCHAR(50),
                        traffic_split FLOAT,
                        start_date DATETIME2,
                        end_date DATETIME2,
                        created_at DATETIME2 DEFAULT GETDATE()
                    )
                """)
                
                # Create ab_test_results table
                cursor.execute("""
                    IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ab_test_results' AND xtype='U')
                    CREATE TABLE ab_test_results (
                        id INT IDENTITY(1,1) PRIMARY KEY,
                        test_id NVARCHAR(255),
                        variant NVARCHAR(100),
                        metric_name NVARCHAR(100),
                        metric_value FLOAT,
                        sample_size INT,
                        confidence_level FLOAT,
                        p_value FLOAT,
                        is_significant BIT,
                        created_at DATETIME2 DEFAULT GETDATE(),
                        FOREIGN KEY (test_id) REFERENCES ab_tests (id)
                    )
                """)
                
                # Create indexes for better performance
                cursor.execute("IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_articles_published_date') CREATE INDEX idx_articles_published_date ON articles (published_date)")
                cursor.execute("IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_articles_source') CREATE INDEX idx_articles_source ON articles (source_name)")
                cursor.execute("IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_sentiment_article_id') CREATE INDEX idx_sentiment_article_id ON sentiment_analysis (article_id)")
                cursor.execute("IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_engagement_article_id') CREATE INDEX idx_engagement_article_id ON engagement_events (article_id)")
                cursor.execute("IF NOT EXISTS (SELECT * FROM sys.indexes WHERE name = 'idx_engagement_timestamp') CREATE INDEX idx_engagement_timestamp ON engagement_events (timestamp)")
                
                conn.commit()
                logger.info("Database initialized successfully")
                
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _get_connection_string(self) -> str:
        """Get MSSQL connection string."""
        return (
            f"DRIVER={{{self.driver}}};"
            f"SERVER={self.server},{self.port};"
            f"DATABASE={self.database};"
            f"UID={self.username};"
            f"PWD={self.password};"
            "TrustServerCertificate=yes;"
        )
    
    @contextmanager
    def get_connection(self):
        """Get database connection with proper error handling."""
        conn = None
        try:
            if self.db_type == 'mssql':
                conn = pyodbc.connect(self._get_connection_string())
                conn.autocommit = False
            else:
                raise NotImplementedError(f"Database type {self.db_type} not supported")
            
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
                    MERGE articles AS target
                    USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS source (
                        id, title, url, summary, content, published_date,
                        source_name, source_country, source_language, author,
                        tags, word_count, collected_at
                    )
                    ON target.id = source.id
                    WHEN MATCHED THEN
                        UPDATE SET title = source.title, url = source.url, summary = source.summary,
                                 content = source.content, published_date = source.published_date,
                                 source_name = source.source_name, source_country = source.source_country,
                                 source_language = source.source_language, author = source.author,
                                 tags = source.tags, word_count = source.word_count, collected_at = source.collected_at
                    WHEN NOT MATCHED THEN
                        INSERT (id, title, url, summary, content, published_date,
                               source_name, source_country, source_language, author,
                               tags, word_count, collected_at)
                        VALUES (source.id, source.title, source.url, source.summary, source.content, source.published_date,
                               source.source_name, source.source_country, source.source_language, source.author,
                               source.tags, source.word_count, source.collected_at);
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
                    MERGE article_metrics AS target
                    USING (VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)) AS source (
                        article_id, total_views, unique_users, clicks, shares,
                        avg_time_on_page, ctr, share_rate, content_score, last_updated
                    )
                    ON target.article_id = source.article_id
                    WHEN MATCHED THEN
                        UPDATE SET total_views = source.total_views, unique_users = source.unique_users,
                                 clicks = source.clicks, shares = source.shares,
                                 avg_time_on_page = source.avg_time_on_page, ctr = source.ctr,
                                 share_rate = source.share_rate, content_score = source.content_score,
                                 last_updated = source.last_updated
                    WHEN NOT MATCHED THEN
                        INSERT (article_id, total_views, unique_users, clicks, shares,
                               avg_time_on_page, ctr, share_rate, content_score, last_updated)
                        VALUES (source.article_id, source.total_views, source.unique_users, source.clicks, source.shares,
                               source.avg_time_on_page, source.ctr, source.share_rate, source.content_score, source.last_updated);
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
                        CAST(analyzed_at AS DATE) as date,
                        sentiment_label,
                        COUNT(*) as count,
                        AVG(compound_score) as avg_score
                    FROM sentiment_analysis 
                    WHERE analyzed_at >= DATEADD(day, -{}, GETDATE())
                    GROUP BY CAST(analyzed_at AS DATE), sentiment_label
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
                        CAST(timestamp AS DATE) as date,
                        event_type,
                        COUNT(*) as count
                    FROM engagement_events 
                    WHERE timestamp >= DATEADD(day, -{}, GETDATE())
                    GROUP BY CAST(timestamp AS DATE), event_type
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
                
                # Get total events in last 24 hours
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM engagement_events
                    WHERE timestamp >= DATEADD(hour, -24, GETDATE())
                """)
                total_events = cursor.fetchone()[0] or 0
                
                # Calculate engagement rate based on event types
                cursor.execute("""
                    SELECT 
                        COUNT(CASE WHEN event_type = 'click' THEN 1 END) as clicks,
                        COUNT(CASE WHEN event_type = 'view' THEN 1 END) as views,
                        COUNT(*) as total_events
                    FROM engagement_events
                    WHERE timestamp >= DATEADD(hour, -24, GETDATE())
                """)
                result = cursor.fetchone()
                clicks = result[0] or 0
                views = result[1] or 0
                total_events = result[2] or 0
                
                # Calculate engagement rate
                if views > 0:
                    engagement_rate = (clicks / views) * 100
                else:
                    engagement_rate = 0
                
                return {
                    'total_users': total_users,
                    'avg_engagement_rate': engagement_rate,
                    'avg_time_on_page': 0,  # Not available in current schema
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
                    WHERE created_at >= DATEADD(hour, -24, GETDATE())
                    GROUP BY sentiment_label
                """)
                sentiment_counts = dict(cursor.fetchall())
                
                # Get average sentiment score
                cursor.execute("""
                    SELECT AVG(compound_score)
                    FROM sentiment_analysis
                    WHERE created_at >= DATEADD(hour, -24, GETDATE())
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
            if self.db_type == 'mssql':
                with self.get_connection() as conn:
                    cursor = conn.cursor()
                    backup_query = f"BACKUP DATABASE [{self.database}] TO DISK = '{backup_path}'"
                    cursor.execute(backup_query)
                    conn.commit()
                    logger.info(f"Database backed up to {backup_path}")
                    return True
            else:
                logger.warning(f"Backup not implemented for {self.db_type}")
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