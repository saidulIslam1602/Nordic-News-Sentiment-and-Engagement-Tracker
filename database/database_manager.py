"""
Database Manager

Handles database operations for the Nordic News Sentiment & Engagement Tracker.
Supports both Microsoft SQL Server (MSSQL) and SQLite with automatic fallback.
"""

import pyodbc
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
    - Microsoft SQL Server (MSSQL) with SQLite fallback
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
        self.db_path = 'data/nordic_news.db'
        
        # Initialize database with fallback
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
        """Initialize database tables with MSSQL fallback to SQLite."""
        try:
            # Try MSSQL first
            if self.db_type == 'mssql':
                try:
                    # First, try to create the database if it doesn't exist
                    self._ensure_mssql_database_exists()
                    
                    # Then connect to the specific database
                    with self.get_connection() as conn:
                        self._create_tables_mssql(conn)
                    logger.info("Successfully connected to MSSQL database")
                    return
                except Exception as e:
                    logger.warning(f"MSSQL connection failed: {e}. Falling back to SQLite.")
                    self.db_type = 'sqlite'
            
            # Fallback to SQLite
            os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
            with self.get_connection() as conn:
                self._create_tables_sqlite(conn)
            logger.info("Successfully connected to SQLite database")
            
        except Exception as e:
            logger.error(f"Error initializing database: {e}")
            raise
    
    def _ensure_mssql_database_exists(self):
        """Ensure the MSSQL database exists, create it if it doesn't."""
        try:
            # Connect to master database first
            master_conn_string = (
                f"DRIVER={{{self.driver}}};"
                f"SERVER={self.server},{self.port};"
                f"DATABASE=master;"
                f"UID={self.username};"
                f"PWD={self.password};"
                "TrustServerCertificate=yes;"
            )
            
            with pyodbc.connect(master_conn_string, autocommit=True) as master_conn:
                cursor = master_conn.cursor()
                
                # Check if database exists
                cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{self.database}'")
                if not cursor.fetchone():
                    logger.info(f"Creating database '{self.database}'...")
                    cursor.execute(f"CREATE DATABASE [{self.database}]")
                    logger.info(f"Database '{self.database}' created successfully")
                else:
                    logger.info(f"Database '{self.database}' already exists")
                    
        except Exception as e:
            logger.error(f"Error ensuring MSSQL database exists: {e}")
            raise
    
    def _create_tables_mssql(self, conn):
        """Create tables for MSSQL database."""
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
        
        # Create sentiment_analysis table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='sentiment_analysis' AND xtype='U')
            CREATE TABLE sentiment_analysis (
                id INT IDENTITY(1,1) PRIMARY KEY,
                article_id NVARCHAR(255) NOT NULL,
                sentiment_score FLOAT,
                sentiment_label NVARCHAR(50),
                confidence FLOAT,
                language NVARCHAR(10),
                analyzer_used NVARCHAR(100),
                created_at DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        # Create engagement_events table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='engagement_events' AND xtype='U')
            CREATE TABLE engagement_events (
                id INT IDENTITY(1,1) PRIMARY KEY,
                article_id NVARCHAR(255) NOT NULL,
                user_id NVARCHAR(255),
                event_type NVARCHAR(50) NOT NULL,
                timestamp DATETIME2 DEFAULT GETDATE(),
                metadata NVARCHAR(MAX),
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        # Create ab_testing table
        cursor.execute("""
            IF NOT EXISTS (SELECT * FROM sysobjects WHERE name='ab_testing' AND xtype='U')
            CREATE TABLE ab_testing (
                id INT IDENTITY(1,1) PRIMARY KEY,
                test_name NVARCHAR(255) NOT NULL,
                variant NVARCHAR(100) NOT NULL,
                user_id NVARCHAR(255),
                article_id NVARCHAR(255),
                conversion_event NVARCHAR(100),
                timestamp DATETIME2 DEFAULT GETDATE(),
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        conn.commit()
    
    def _create_tables_sqlite(self, conn):
        """Create tables for SQLite database."""
        cursor = conn.cursor()
        
        # Create articles table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS articles (
                id TEXT PRIMARY KEY,
                title TEXT NOT NULL,
                url TEXT,
                summary TEXT,
                content TEXT,
                published_date DATETIME,
                source_name TEXT,
                source_country TEXT,
                source_language TEXT,
                author TEXT,
                tags TEXT,
                word_count INTEGER,
                collected_at DATETIME,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # Create sentiment_analysis table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS sentiment_analysis (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                sentiment_score REAL,
                sentiment_label TEXT,
                confidence REAL,
                language TEXT,
                analyzer_used TEXT,
                created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        # Create engagement_events table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS engagement_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                article_id TEXT NOT NULL,
                user_id TEXT,
                event_type TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                metadata TEXT,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        # Create ab_testing table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS ab_testing (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_name TEXT NOT NULL,
                variant TEXT NOT NULL,
                user_id TEXT,
                article_id TEXT,
                conversion_event TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (article_id) REFERENCES articles(id)
            )
        """)
        
        conn.commit()
    
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
            elif self.db_type == 'sqlite':
                conn = sqlite3.connect(self.db_path)
                conn.row_factory = sqlite3.Row
            else:
                raise NotImplementedError(f"Database type {self.db_type} not supported")
            
            yield conn
        except Exception as e:
            if conn:
                if self.db_type == 'mssql':
                    conn.rollback()
                else:
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
                
                if self.db_type == 'mssql':
                    cursor.execute("""
                        MERGE articles AS target
                        USING (SELECT ? AS id) AS source
                        ON target.id = source.id
                        WHEN MATCHED THEN
                            UPDATE SET title = ?, url = ?, summary = ?, content = ?,
                                     published_date = ?, source_name = ?, source_country = ?,
                                     source_language = ?, author = ?, tags = ?, word_count = ?,
                                     collected_at = ?
                        WHEN NOT MATCHED THEN
                            INSERT (id, title, url, summary, content, published_date,
                                   source_name, source_country, source_language, author,
                                   tags, word_count, collected_at)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
                    """, (
                        article['id'], article['title'], article['url'], article['summary'],
                        article['content'], article['published_date'], article['source_name'],
                        article['source_country'], article['source_language'], article['author'],
                        article['tags'], article['word_count'], article['collected_at'],
                        article['id'], article['title'], article['url'], article['summary'],
                        article['content'], article['published_date'], article['source_name'],
                        article['source_country'], article['source_language'], article['author'],
                        article['tags'], article['word_count'], article['collected_at']
                    ))
                else:
                    cursor.execute("""
                        INSERT OR REPLACE INTO articles 
                        (id, title, url, summary, content, published_date, source_name,
                         source_country, source_language, author, tags, word_count, collected_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        article['id'], article['title'], article['url'], article['summary'],
                        article['content'], article['published_date'], article['source_name'],
                        article['source_country'], article['source_language'], article['author'],
                        article['tags'], article['word_count'], article['collected_at']
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving article: {e}")
            return False
    
    def get_article(self, article_id: str) -> Optional[Dict]:
        """Get an article by ID."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT * FROM articles WHERE id = ?", (article_id,))
                row = cursor.fetchone()
                
                if row:
                    if self.db_type == 'mssql':
                        return dict(zip([column[0] for column in cursor.description], row))
                    else:
                        return dict(row)
                return None
                
        except Exception as e:
            logger.error(f"Error getting article: {e}")
            return None
    
    def get_articles(self, limit: int = 100, offset: int = 0) -> List[Dict]:
        """Get articles with pagination."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT * FROM articles 
                    ORDER BY published_date DESC 
                    LIMIT ? OFFSET ?
                """, (limit, offset))
                rows = cursor.fetchall()
                
                if self.db_type == 'mssql':
                    return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
                else:
                    return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting articles: {e}")
            return []
    
    def get_articles_by_timeframe(self, hours_back: int = 24) -> List[Dict]:
        """Get articles within a specified time window."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'mssql':
                    cursor.execute("""
                        SELECT a.*, s.sentiment_score, s.sentiment_label, s.confidence
                        FROM articles a
                        LEFT JOIN sentiment_analysis s ON a.id = s.article_id
                        WHERE a.collected_at >= DATEADD(hour, -?, GETDATE())
                        ORDER BY a.collected_at DESC
                    """, (hours_back,))
                else:
                    cursor.execute("""
                        SELECT a.*, s.sentiment_score, s.sentiment_label, s.confidence
                        FROM articles a
                        LEFT JOIN sentiment_analysis s ON a.id = s.article_id
                        WHERE a.collected_at >= datetime('now', '-{} hours')
                        ORDER BY a.collected_at DESC
                    """.format(hours_back))
                
                rows = cursor.fetchall()
                
                if self.db_type == 'mssql':
                    return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
                else:
                    return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting articles by timeframe: {e}")
            return []
    
    def save_sentiment_analysis(self, article_id: str, sentiment_data: Dict) -> bool:
        """Save sentiment analysis results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'mssql':
                    cursor.execute("""
                        INSERT INTO sentiment_analysis 
                        (article_id, sentiment_score, sentiment_label, confidence, language, analyzer_used)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        article_id, sentiment_data.get('sentiment_score'),
                        sentiment_data.get('sentiment_label'), sentiment_data.get('confidence'),
                        sentiment_data.get('language'), sentiment_data.get('analyzer_used')
                    ))
                else:
                    cursor.execute("""
                        INSERT INTO sentiment_analysis 
                        (article_id, sentiment_score, sentiment_label, confidence, language, analyzer_used)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """, (
                        article_id, sentiment_data.get('sentiment_score'),
                        sentiment_data.get('sentiment_label'), sentiment_data.get('confidence'),
                        sentiment_data.get('language'), sentiment_data.get('analyzer_used')
                    ))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving sentiment analysis: {e}")
            return False
    
    def save_engagement_event(self, article_id: str, user_id: str, event_type: str, metadata: Dict = None) -> bool:
        """Save an engagement event."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                metadata_json = json.dumps(metadata) if metadata else None
                
                cursor.execute("""
                    INSERT INTO engagement_events (article_id, user_id, event_type, metadata)
                    VALUES (?, ?, ?, ?)
                """, (article_id, user_id, event_type, metadata_json))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving engagement event: {e}")
            return False
    
    def get_engagement_metrics(self) -> Dict:
        """Get engagement metrics."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                # Get total users
                cursor.execute("SELECT COUNT(DISTINCT user_id) FROM engagement_events WHERE user_id IS NOT NULL")
                total_users = cursor.fetchone()[0] or 0
                
                # Get total events
                cursor.execute("SELECT COUNT(*) FROM engagement_events")
                total_events = cursor.fetchone()[0] or 0
                
                # Get engagement rate (clicks/views)
                cursor.execute("""
                    SELECT 
                        SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END) as views,
                        SUM(CASE WHEN event_type = 'click' THEN 1 ELSE 0 END) as clicks
                    FROM engagement_events
                """)
                result = cursor.fetchone()
                views = result[0] or 0
                clicks = result[1] or 0
                engagement_rate = (clicks / views * 100) if views > 0 else 0
                
                # Get average time on page
                cursor.execute("""
                    SELECT AVG(CAST(JSON_EXTRACT(metadata, '$.time_spent') AS REAL))
                    FROM engagement_events 
                    WHERE event_type = 'time_on_page' AND metadata IS NOT NULL
                """)
                avg_time_result = cursor.fetchone()
                avg_time_on_page = avg_time_result[0] if avg_time_result[0] else 0
                
                # Get events in last 24 hours
                if self.db_type == 'mssql':
                    cursor.execute("""
                        SELECT COUNT(*) FROM engagement_events 
                        WHERE timestamp >= DATEADD(hour, -24, GETDATE())
                    """)
                else:
                    cursor.execute("""
                        SELECT COUNT(*) FROM engagement_events 
                        WHERE timestamp >= datetime('now', '-24 hours')
                    """)
                events_24h = cursor.fetchone()[0] or 0
                
                return {
                    'total_users': total_users,
                    'total_events': total_events,
                    'engagement_rate': round(engagement_rate, 2),
                    'avg_time_on_page': round(avg_time_on_page, 2),
                    'total_events_24h': events_24h
                }
                
        except Exception as e:
            logger.error(f"Error getting engagement metrics: {e}")
            return {
                'total_users': 0,
                'total_events': 0,
                'engagement_rate': 0,
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
                    GROUP BY sentiment_label
                """)
                sentiment_dist = dict(cursor.fetchall())
                
                # Get average sentiment score
                cursor.execute("""
                    SELECT AVG(sentiment_score) as avg_score
                    FROM sentiment_analysis
                    WHERE sentiment_score IS NOT NULL
                """)
                avg_score_result = cursor.fetchone()
                avg_sentiment_score = avg_score_result[0] if avg_score_result[0] else 0
                
                return {
                    'sentiment_distribution': sentiment_dist,
                    'average_sentiment_score': round(avg_sentiment_score, 3)
                }
                
        except Exception as e:
            logger.error(f"Error getting sentiment data: {e}")
            return {
                'sentiment_distribution': {},
                'average_sentiment_score': 0
            }
    
    def save_ab_test(self, test_name: str, variant: str, user_id: str, article_id: str = None, conversion_event: str = None) -> bool:
        """Save A/B test data."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    INSERT INTO ab_testing (test_name, variant, user_id, article_id, conversion_event)
                    VALUES (?, ?, ?, ?, ?)
                """, (test_name, variant, user_id, article_id, conversion_event))
                
                conn.commit()
                return True
                
        except Exception as e:
            logger.error(f"Error saving A/B test: {e}")
            return False
    
    def get_ab_test_results(self, test_name: str) -> Dict:
        """Get A/B test results."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                cursor.execute("""
                    SELECT variant, COUNT(*) as participants,
                           SUM(CASE WHEN conversion_event IS NOT NULL THEN 1 ELSE 0 END) as conversions
                    FROM ab_testing
                    WHERE test_name = ?
                    GROUP BY variant
                """, (test_name,))
                
                results = {}
                for row in cursor.fetchall():
                    variant, participants, conversions = row
                    conversion_rate = (conversions / participants * 100) if participants > 0 else 0
                    results[variant] = {
                        'participants': participants,
                        'conversions': conversions,
                        'conversion_rate': round(conversion_rate, 2)
                    }
                
                return results
                
        except Exception as e:
            logger.error(f"Error getting A/B test results: {e}")
            return {}
    
    def get_engagement_trends(self, days: int = 7) -> List[Dict]:
        """Get engagement trends over specified days."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'mssql':
                    cursor.execute("""
                        SELECT 
                            CAST(timestamp AS DATE) as date,
                            event_type,
                            COUNT(*) as count
                        FROM engagement_events
                        WHERE timestamp >= DATEADD(day, -?, GETDATE())
                        GROUP BY CAST(timestamp AS DATE), event_type
                        ORDER BY date DESC
                    """, (days,))
                else:
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
                
                if self.db_type == 'mssql':
                    return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
                else:
                    return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting engagement trends: {e}")
            return []
    
    def get_sentiment_trends(self, days: int = 7) -> List[Dict]:
        """Get sentiment trends over specified days."""
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                
                if self.db_type == 'mssql':
                    cursor.execute("""
                        SELECT 
                            CAST(s.created_at AS DATE) as date,
                            s.sentiment_label,
                            AVG(s.sentiment_score) as avg_score,
                            COUNT(*) as count
                        FROM sentiment_analysis s
                        WHERE s.created_at >= DATEADD(day, -?, GETDATE())
                        GROUP BY CAST(s.created_at AS DATE), s.sentiment_label
                        ORDER BY date DESC
                    """, (days,))
                else:
                    cursor.execute("""
                        SELECT 
                            DATE(s.created_at) as date,
                            s.sentiment_label,
                            AVG(s.sentiment_score) as avg_score,
                            COUNT(*) as count
                        FROM sentiment_analysis s
                        WHERE s.created_at >= datetime('now', '-{} days')
                        GROUP BY DATE(s.created_at), s.sentiment_label
                        ORDER BY date DESC
                    """.format(days))
                
                rows = cursor.fetchall()
                
                if self.db_type == 'mssql':
                    return [dict(zip([column[0] for column in cursor.description], row)) for row in rows]
                else:
                    return [dict(row) for row in rows]
                
        except Exception as e:
            logger.error(f"Error getting sentiment trends: {e}")
            return []
    
    def close(self):
        """Close database connections."""
        pass  # Connections are managed by context manager