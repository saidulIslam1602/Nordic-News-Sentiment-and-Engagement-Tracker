"""
News Collection Module

Collects news articles from Nordic media sources using RSS feeds and web scraping.
Handles multiple languages and implements rate limiting and error handling.
"""

import requests
import feedparser
import time
import logging
import threading
import schedule
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Callable
from bs4 import BeautifulSoup
import yaml
import os
from urllib.parse import urljoin, urlparse
import hashlib
import json

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NewsCollector:
    """
    Collects news articles from Nordic media sources.
    
    Features:
    - RSS feed parsing
    - Web scraping for full article content
    - Multi-language support
    - Rate limiting and error handling
    - Data validation and cleaning
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the news collector with configuration."""
        self.config = self._load_config(config_path)
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Nordic News Analytics Bot 1.0 (Research Purpose)'
        })
        self.rate_limit_delay = 1.0  # seconds between requests
        
        # Real-time processing attributes
        self.is_running = False
        self.collection_thread = None
        self.callbacks = []
        self.last_collection_time = None
        self.collected_articles = []
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
        except yaml.YAMLError as e:
            logger.error(f"Error parsing configuration: {e}")
            return {}
    
    def collect_news_articles(self, hours_back: int = 24) -> List[Dict]:
        """
        Collect news articles from all configured sources.
        
        Args:
            hours_back: Number of hours to look back for articles
            
        Returns:
            List of article dictionaries with metadata and content
        """
        articles = []
        cutoff_time = datetime.now() - timedelta(hours=hours_back)
        
        for country, sources in self.config.get('news_sources', {}).items():
            logger.info(f"Collecting articles from {country} sources...")
            
            for source in sources:
                try:
                    source_articles = self._collect_from_source(source, cutoff_time)
                    articles.extend(source_articles)
                    logger.info(f"Collected {len(source_articles)} articles from {source['name']}")
                    
                    # Rate limiting
                    time.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    logger.error(f"Error collecting from {source['name']}: {e}")
                    continue
        
        logger.info(f"Total articles collected: {len(articles)}")
        return articles
    
    def _collect_from_source(self, source: Dict, cutoff_time: datetime) -> List[Dict]:
        """Collect articles from a single news source."""
        articles = []
        
        try:
            # Parse RSS feed
            feed = feedparser.parse(source['url'])
            
            if feed.bozo:
                logger.warning(f"RSS feed parsing issues for {source['name']}")
            
            for entry in feed.entries:
                try:
                    article = self._process_rss_entry(entry, source, cutoff_time)
                    if article:
                        articles.append(article)
                except Exception as e:
                    logger.error(f"Error processing entry from {source['name']}: {e}")
                    continue
                    
        except Exception as e:
            logger.error(f"Error parsing RSS feed for {source['name']}: {e}")
        
        return articles
    
    def _process_rss_entry(self, entry, source: Dict, cutoff_time: datetime) -> Optional[Dict]:
        """Process a single RSS entry into an article dictionary."""
        try:
            # Parse publication date
            pub_date = self._parse_date(entry.get('published', ''))
            if pub_date and pub_date < cutoff_time:
                return None
            
            # Extract basic information
            article = {
                'id': self._generate_article_id(entry.get('link', '')),
                'title': entry.get('title', '').strip(),
                'url': entry.get('link', ''),
                'summary': entry.get('summary', '').strip(),
                'published_date': pub_date.isoformat() if pub_date else None,
                'source_name': source['name'],
                'source_country': source['country'],
                'source_language': source['language'],
                'author': entry.get('author', ''),
                'tags': [tag.term for tag in entry.get('tags', [])],
                'collected_at': datetime.now().isoformat()
            }
            
            # Clean and validate data
            article = self._clean_article_data(article)
            
            # Try to get full content
            full_content = self._scrape_full_content(article['url'])
            if full_content:
                article['content'] = full_content
                article['word_count'] = len(full_content.split())
            else:
                article['content'] = article['summary']
                article['word_count'] = len(article['summary'].split())
            
            return article
            
        except Exception as e:
            logger.error(f"Error processing RSS entry: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> Optional[datetime]:
        """Parse various date formats from RSS feeds."""
        if not date_str:
            return None
        
        # Common date formats in RSS feeds
        formats = [
            '%a, %d %b %Y %H:%M:%S %z',
            '%a, %d %b %Y %H:%M:%S %Z',
            '%Y-%m-%dT%H:%M:%S%z',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%d %H:%M:%S'
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(date_str, fmt)
            except ValueError:
                continue
        
        # Try feedparser's date parsing
        try:
            import feedparser
            parsed = feedparser._parse_date(date_str)
            if parsed:
                return datetime(*parsed[:6])
        except:
            pass
        
        return None
    
    def _generate_article_id(self, url: str) -> str:
        """Generate a unique ID for an article based on its URL."""
        return hashlib.md5(url.encode('utf-8')).hexdigest()
    
    def _clean_article_data(self, article: Dict) -> Dict:
        """Clean and validate article data."""
        # Remove HTML tags from summary
        if article['summary']:
            soup = BeautifulSoup(article['summary'], 'html.parser')
            article['summary'] = soup.get_text().strip()
        
        # Clean title
        if article['title']:
            soup = BeautifulSoup(article['title'], 'html.parser')
            article['title'] = soup.get_text().strip()
        
        # Validate URL
        if article['url']:
            parsed_url = urlparse(article['url'])
            if not parsed_url.scheme or not parsed_url.netloc:
                article['url'] = None
        
        return article
    
    def _scrape_full_content(self, url: str) -> Optional[str]:
        """Scrape full article content from the URL."""
        if not url:
            return None
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Remove script and style elements
            for script in soup(["script", "style"]):
                script.decompose()
            
            # Try to find article content
            content_selectors = [
                'article',
                '.article-content',
                '.article-body',
                '.content',
                '.post-content',
                'main',
                '.main-content'
            ]
            
            content = None
            for selector in content_selectors:
                elements = soup.select(selector)
                if elements:
                    content = ' '.join([elem.get_text() for elem in elements])
                    break
            
            if not content:
                # Fallback: get all paragraph text
                paragraphs = soup.find_all('p')
                content = ' '.join([p.get_text() for p in paragraphs])
            
            # Clean up content
            content = ' '.join(content.split())  # Remove extra whitespace
            return content[:5000] if content else None  # Limit content length
            
        except Exception as e:
            logger.debug(f"Could not scrape content from {url}: {e}")
            return None

    def add_callback(self, callback: Callable[[List[Dict]], None]):
        """Add a callback function to be called when new articles are collected."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: Callable[[List[Dict]], None]):
        """Remove a callback function."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    def _notify_callbacks(self, articles: List[Dict]):
        """Notify all registered callbacks with new articles."""
        for callback in self.callbacks:
            try:
                callback(articles)
            except Exception as e:
                logger.error(f"Error in callback: {e}")
    
    def start_real_time_collection(self, interval_minutes: int = 15):
        """Start real-time news collection in a separate thread."""
        if self.is_running:
            logger.warning("Real-time collection is already running")
            return
        
        self.is_running = True
        self.collection_thread = threading.Thread(
            target=self._real_time_collection_loop,
            args=(interval_minutes,),
            daemon=True
        )
        self.collection_thread.start()
        logger.info(f"Started real-time collection with {interval_minutes} minute intervals")
    
    def stop_real_time_collection(self):
        """Stop real-time news collection."""
        self.is_running = False
        if self.collection_thread and self.collection_thread.is_alive():
            self.collection_thread.join(timeout=5)
        logger.info("Stopped real-time collection")
    
    def _real_time_collection_loop(self, interval_minutes: int):
        """Main loop for real-time collection."""
        while self.is_running:
            try:
                logger.info("Starting real-time news collection cycle...")
                
                # Collect articles from the last interval
                articles = self.collect_news_articles(hours_back=interval_minutes/60)
                
                if articles:
                    logger.info(f"Collected {len(articles)} new articles")
                    self.collected_articles.extend(articles)
                    self.last_collection_time = datetime.now()
                    
                    # Notify callbacks
                    self._notify_callbacks(articles)
                else:
                    logger.info("No new articles found")
                
                # Wait for next collection cycle
                time.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in real-time collection loop: {e}")
                time.sleep(60)  # Wait 1 minute before retrying
    
    def get_latest_articles(self, limit: int = 100) -> List[Dict]:
        """Get the latest collected articles."""
        return self.collected_articles[-limit:] if self.collected_articles else []
    
    def get_collection_stats(self) -> Dict:
        """Get real-time collection statistics."""
        return {
            'is_running': self.is_running,
            'total_articles_collected': len(self.collected_articles),
            'last_collection_time': self.last_collection_time,
            'callbacks_registered': len(self.callbacks)
        }
    
    def collect_recent_articles(self, minutes_back: int = 30) -> List[Dict]:
        """Collect articles from the last N minutes for real-time updates."""
        try:
            all_articles = []
            current_time = datetime.now()
            
            for source in self.config.get('sources', []):
                try:
                    # Parse RSS feed
                    feed = feedparser.parse(source['rss_url'])
                    
                    for entry in feed.entries:
                        try:
                            # Parse publication date
                            pub_date = self._parse_date(entry.get('published', ''))
                            
                            # Check if article is within the time window
                            if pub_date and (current_time - pub_date).total_seconds() <= minutes_back * 60:
                                article = self._process_article(entry, source)
                                if article:
                                    all_articles.append(article)
                                    
                        except Exception as e:
                            logger.debug(f"Error processing entry: {e}")
                            continue
                    
                    time.sleep(self.rate_limit_delay)
                    
                except Exception as e:
                    logger.error(f"Error processing source {source['name']}: {e}")
                    continue
            
            # Sort by publication date (newest first)
            all_articles.sort(key=lambda x: x.get('published_date', datetime.min), reverse=True)
            
            logger.info(f"Collected {len(all_articles)} recent articles from last {minutes_back} minutes")
            return all_articles
            
        except Exception as e:
            logger.error(f"Error in recent article collection: {e}")
            return []


def main():
    """Main function for testing the news collector."""
    collector = NewsCollector()
    articles = collector.collect_news_articles(hours_back=24)
    
    print(f"Collected {len(articles)} articles")
    for article in articles[:3]:  # Show first 3 articles
        print(f"\nTitle: {article['title']}")
        print(f"Source: {article['source_name']} ({article['source_country']})")
        print(f"Published: {article['published_date']}")
        print(f"Content length: {article.get('word_count', 0)} words")


if __name__ == "__main__":
    main()