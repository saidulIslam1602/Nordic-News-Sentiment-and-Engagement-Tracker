#!/usr/bin/env python3
"""
MSSQL Database Setup Script

This script sets up the Microsoft SQL Server database for the Nordic News Tracker.
It creates the database and initializes all required tables.
"""

import pyodbc
import os
import sys
import yaml
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

def get_mssql_connection(server, port, database="master", username="sa", password="", driver="ODBC Driver 17 for SQL Server"):
    """Get MSSQL connection string."""
    connection_string = (
        f"DRIVER={{{driver}}};"
        f"SERVER={server},{port};"
        f"DATABASE={database};"
        f"UID={username};"
        f"PWD={password};"
        "TrustServerCertificate=yes;"
    )
    return pyodbc.connect(connection_string)

def create_database(server, port, database_name, username, password, driver):
    """Create the database if it doesn't exist."""
    try:
        # Connect to master database to create new database
        conn = get_mssql_connection(server, port, "master", username, password, driver)
        conn.autocommit = True  # Enable autocommit for CREATE DATABASE
        cursor = conn.cursor()
        
        # Check if database exists
        cursor.execute(f"SELECT name FROM sys.databases WHERE name = '{database_name}'")
        if cursor.fetchone():
            print(f"Database '{database_name}' already exists.")
        else:
            # Create database
            cursor.execute(f"CREATE DATABASE [{database_name}]")
            print(f"Database '{database_name}' created successfully.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error creating database: {e}")
        return False

def setup_tables(server, port, database_name, username, password, driver):
    """Set up all required tables."""
    try:
        # Connect to the target database
        conn = get_mssql_connection(server, port, database_name, username, password, driver)
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
        print("All tables and indexes created successfully.")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error setting up tables: {e}")
        return False

def main():
    """Main setup function."""
    print("Setting up MSSQL database for Nordic News Tracker...")
    
    # Load configuration
    config_path = project_root / "config" / "config.yaml"
    try:
        with open(config_path, 'r', encoding='utf-8') as file:
            config = yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Configuration file not found: {config_path}")
        return False
    
    # Get database configuration
    db_config = config.get('database', {}).get('development', {})
    server = db_config.get('server', 'localhost')
    port = db_config.get('port', 1433)
    database_name = db_config.get('database', 'nordic_news_dev')
    username = db_config.get('username', 'sa')
    password = os.getenv('MSSQL_PASSWORD', db_config.get('password', ''))
    driver = db_config.get('driver', 'ODBC Driver 17 for SQL Server')
    
    if not password:
        print("Error: MSSQL_PASSWORD environment variable not set.")
        print("Please set it with: export MSSQL_PASSWORD=your_password")
        return False
    
    # Test connection to master database
    try:
        conn = get_mssql_connection(server, port, "master", username, password, driver)
        conn.close()
        print("✓ Successfully connected to MSSQL server")
    except Exception as e:
        print(f"✗ Failed to connect to MSSQL server: {e}")
        print("Please ensure:")
        print("1. SQL Server is running")
        print("2. ODBC Driver 17 for SQL Server is installed")
        print("3. Connection details are correct")
        return False
    
    # Create database
    if not create_database(server, port, database_name, username, password, driver):
        return False
    
    # Setup tables
    if not setup_tables(server, port, database_name, username, password, driver):
        return False
    
    print("✓ Database setup completed successfully!")
    print(f"Database: {database_name}")
    print(f"Server: {server}:{port}")
    print("You can now run the application with MSSQL backend.")
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)