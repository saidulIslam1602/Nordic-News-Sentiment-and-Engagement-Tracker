"""
Engagement Tracking System

Tracks user engagement metrics for Nordic news content including:
- Click-through rates (CTR)
- Time on page
- Bounce rates
- Social sharing
- User journey analysis
"""

import logging
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
import pandas as pd
import numpy as np
from dataclasses import dataclass
import yaml
import os

logger = logging.getLogger(__name__)


@dataclass
class EngagementEvent:
    """Represents a single engagement event."""
    event_id: str
    user_id: str
    article_id: str
    event_type: str
    timestamp: datetime
    metadata: Dict
    session_id: str
    country: str
    device_type: str


class EngagementTracker:
    """
    Tracks and analyzes user engagement with Nordic news content.
    
    Features:
    - Real-time engagement metrics
    - User behavior analysis
    - Content performance scoring
    - A/B testing support
    - GDPR-compliant data handling
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the engagement tracker."""
        self.config = self._load_config(config_path)
        self.events = []
        self.user_sessions = {}
        self.article_metrics = {}
        
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
    
    def track_event(self, event_data: Dict) -> bool:
        """
        Track a new engagement event.
        
        Args:
            event_data: Dictionary containing event information
        
        Returns:
            True if event was successfully tracked
        """
        try:
            # Validate event data
            if not self._validate_event_data(event_data):
                return False
            
            # Create engagement event
            event = EngagementEvent(
                event_id=event_data.get('event_id', self._generate_event_id()),
                user_id=event_data.get('user_id', 'anonymous'),
                article_id=event_data.get('article_id'),
                event_type=event_data.get('event_type'),
                timestamp=datetime.fromisoformat(event_data.get('timestamp', datetime.now().isoformat())),
                metadata=event_data.get('metadata', {}),
                session_id=event_data.get('session_id', ''),
                country=event_data.get('country', 'unknown'),
                device_type=event_data.get('device_type', 'unknown')
            )
            
            # Store event
            self.events.append(event)
            
            # Update session tracking
            self._update_session_tracking(event)
            
            # Update article metrics
            self._update_article_metrics(event)
            
            logger.debug(f"Tracked {event.event_type} event for article {event.article_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error tracking event: {e}")
            return False
    
    def _validate_event_data(self, event_data: Dict) -> bool:
        """Validate event data before processing."""
        required_fields = ['article_id', 'event_type']
        return all(field in event_data for field in required_fields)
    
    def _generate_event_id(self) -> str:
        """Generate a unique event ID."""
        return f"evt_{int(time.time() * 1000)}_{len(self.events)}"
    
    def _update_session_tracking(self, event: EngagementEvent):
        """Update user session tracking."""
        if event.session_id not in self.user_sessions:
            self.user_sessions[event.session_id] = {
                'user_id': event.user_id,
                'start_time': event.timestamp,
                'last_activity': event.timestamp,
                'events': [],
                'articles_viewed': set(),
                'country': event.country,
                'device_type': event.device_type
            }
        
        session = self.user_sessions[event.session_id]
        session['last_activity'] = event.timestamp
        session['events'].append(event.event_id)
        session['articles_viewed'].add(event.article_id)
    
    def _update_article_metrics(self, event: EngagementEvent):
        """Update article-level engagement metrics."""
        if event.article_id not in self.article_metrics:
            self.article_metrics[event.article_id] = {
                'total_views': 0,
                'unique_users': set(),
                'clicks': 0,
                'shares': 0,
                'time_on_page': [],
                'bounce_rate': 0,
                'ctr': 0,
                'last_updated': event.timestamp
            }
        
        metrics = self.article_metrics[event.article_id]
        metrics['unique_users'].add(event.user_id)
        metrics['last_updated'] = event.timestamp
        
        # Update specific metrics based on event type
        if event.event_type == 'page_view':
            metrics['total_views'] += 1
        elif event.event_type == 'click':
            metrics['clicks'] += 1
        elif event.event_type == 'share':
            metrics['shares'] += 1
        elif event.event_type == 'time_on_page':
            time_spent = event.metadata.get('duration', 0)
            if time_spent is not None:
                metrics['time_on_page'].append(time_spent)
        
        # Calculate derived metrics
        self._calculate_article_metrics(metrics)
    
    def _calculate_article_metrics(self, metrics: Dict):
        """Calculate derived metrics for an article."""
        # Ensure all required fields exist with default values
        if 'total_views' not in metrics:
            metrics['total_views'] = 0
        if 'clicks' not in metrics:
            metrics['clicks'] = 0
        if 'shares' not in metrics:
            metrics['shares'] = 0
        if 'time_on_page' not in metrics:
            metrics['time_on_page'] = []
        
        if metrics['total_views'] > 0:
            metrics['ctr'] = metrics['clicks'] / metrics['total_views']
            metrics['share_rate'] = metrics['shares'] / metrics['total_views']
        else:
            metrics['ctr'] = 0
            metrics['share_rate'] = 0
        
        if metrics['time_on_page'] and len(metrics['time_on_page']) > 0:
            # Filter out None values
            valid_times = [t for t in metrics['time_on_page'] if t is not None]
            if valid_times:
                metrics['avg_time_on_page'] = np.mean(valid_times)
                metrics['median_time_on_page'] = np.median(valid_times)
            else:
                metrics['avg_time_on_page'] = 0
                metrics['median_time_on_page'] = 0
        else:
            metrics['avg_time_on_page'] = 0
            metrics['median_time_on_page'] = 0
    
    def get_article_metrics(self, article_id: str) -> Optional[Dict]:
        """Get engagement metrics for a specific article."""
        if article_id not in self.article_metrics:
            return None
        
        metrics = self.article_metrics[article_id].copy()
        metrics['unique_users'] = len(metrics['unique_users'])
        return metrics
    
    def get_top_performing_articles(self, limit: int = 10, 
                                  metric: str = 'ctr') -> List[Dict]:
        """
        Get top performing articles by engagement metric.
        
        Args:
            limit: Number of articles to return
            metric: Metric to sort by ('ctr', 'total_views', 'shares', 'avg_time_on_page')
        
        Returns:
            List of article metrics sorted by the specified metric
        """
        if not self.article_metrics:
            return []
        
        # Prepare data for sorting
        article_data = []
        for article_id, metrics in self.article_metrics.items():
            data = {
                'article_id': article_id,
                'unique_users': len(metrics['unique_users']),
                **{k: v for k, v in metrics.items() if k != 'unique_users'}
            }
            article_data.append(data)
        
        # Sort by specified metric
        if metric in ['ctr', 'total_views', 'shares', 'avg_time_on_page']:
            article_data.sort(key=lambda x: x.get(metric, 0), reverse=True)
        
        return article_data[:limit]
    
    def get_engagement_trends(self, time_window: str = '24h') -> Dict:
        """
        Get engagement trends over the specified time window.
        
        Args:
            time_window: Time window for analysis ('1h', '24h', '7d', '30d')
        
        Returns:
            Dictionary with trend analysis
        """
        # Calculate time cutoff
        now = datetime.now()
        if time_window == '1h':
            cutoff = now - timedelta(hours=1)
        elif time_window == '24h':
            cutoff = now - timedelta(hours=24)
        elif time_window == '7d':
            cutoff = now - timedelta(days=7)
        elif time_window == '30d':
            cutoff = now - timedelta(days=30)
        else:
            cutoff = now - timedelta(hours=24)
        
        # Filter events by time window
        recent_events = [e for e in self.events if e.timestamp >= cutoff]
        
        if not recent_events:
            return {'total_events': 0, 'trend': 'neutral'}
        
        # Calculate metrics
        total_events = len(recent_events)
        unique_users = len(set(e.user_id for e in recent_events))
        unique_articles = len(set(e.article_id for e in recent_events))
        
        # Event type distribution
        event_types = {}
        for event in recent_events:
            event_types[event.event_type] = event_types.get(event.event_type, 0) + 1
        
        # Calculate engagement rate
        page_views = event_types.get('page_view', 0)
        clicks = event_types.get('click', 0)
        engagement_rate = (clicks / page_views) if page_views > 0 else 0
        
        return {
            'time_window': time_window,
            'total_events': total_events,
            'unique_users': unique_users,
            'unique_articles': unique_articles,
            'engagement_rate': engagement_rate,
            'event_types': event_types,
            'trend': 'positive' if engagement_rate > 0.1 else 'neutral'
        }
    
    def get_user_journey(self, user_id: str) -> List[Dict]:
        """
        Get the user journey for a specific user.
        
        Args:
            user_id: User identifier
        
        Returns:
            List of events in chronological order
        """
        user_events = [e for e in self.events if e.user_id == user_id]
        user_events.sort(key=lambda x: x.timestamp)
        
        journey = []
        for event in user_events:
            journey.append({
                'event_id': event.event_id,
                'article_id': event.article_id,
                'event_type': event.event_type,
                'timestamp': event.timestamp.isoformat(),
                'session_id': event.session_id,
                'metadata': event.metadata
            })
        
        return journey
    
    def calculate_content_score(self, article_id: str) -> float:
        """
        Calculate a composite content performance score.
        
        Args:
            article_id: Article identifier
        
        Returns:
            Content score between 0 and 100
        """
        metrics = self.get_article_metrics(article_id)
        if not metrics:
            return 0.0
        
        # Weighted scoring system
        ctr_weight = 0.3
        time_weight = 0.25
        share_weight = 0.2
        views_weight = 0.15
        unique_users_weight = 0.1
        
        # Normalize metrics (assuming max values)
        ctr_score = min(metrics.get('ctr', 0) * 100, 100)  # CTR as percentage
        time_score = min(metrics.get('avg_time_on_page', 0) / 60, 100)  # Time in minutes
        share_score = min(metrics.get('shares', 0) * 10, 100)  # Shares * 10
        views_score = min(metrics.get('total_views', 0) / 100, 100)  # Views / 100
        users_score = min(metrics.get('unique_users', 0) / 50, 100)  # Users / 50
        
        # Calculate weighted score
        content_score = (
            ctr_score * ctr_weight +
            time_score * time_weight +
            share_score * share_weight +
            views_score * views_weight +
            users_score * unique_users_weight
        )
        
        return round(content_score, 2)
    
    def export_metrics(self, format: str = 'json') -> str:
        """
        Export engagement metrics in the specified format.
        
        Args:
            format: Export format ('json', 'csv')
        
        Returns:
            Exported data as string
        """
        if format == 'json':
            return json.dumps({
                'article_metrics': {
                    aid: {
                        'unique_users': len(metrics['unique_users']),
                        **{k: v for k, v in metrics.items() if k != 'unique_users'}
                    }
                    for aid, metrics in self.article_metrics.items()
                },
                'export_timestamp': datetime.now().isoformat()
            }, indent=2)
        
        elif format == 'csv':
            # Convert to DataFrame for CSV export
            data = []
            for article_id, metrics in self.article_metrics.items():
                row = {
                    'article_id': article_id,
                    'unique_users': len(metrics['unique_users']),
                    **{k: v for k, v in metrics.items() if k != 'unique_users'}
                }
                data.append(row)
            
            df = pd.DataFrame(data)
            return df.to_csv(index=False)
        
        else:
            raise ValueError(f"Unsupported format: {format}")


def main():
    """Main function for testing the engagement tracker."""
    tracker = EngagementTracker()
    
    # Simulate some engagement events
    test_events = [
        {
            'article_id': 'art_001',
            'event_type': 'page_view',
            'user_id': 'user_001',
            'session_id': 'sess_001',
            'country': 'Norway',
            'device_type': 'mobile',
            'metadata': {'referrer': 'google.com'}
        },
        {
            'article_id': 'art_001',
            'event_type': 'click',
            'user_id': 'user_001',
            'session_id': 'sess_001',
            'country': 'Norway',
            'device_type': 'mobile',
            'metadata': {'element': 'headline'}
        },
        {
            'article_id': 'art_001',
            'event_type': 'time_on_page',
            'user_id': 'user_001',
            'session_id': 'sess_001',
            'country': 'Norway',
            'device_type': 'mobile',
            'metadata': {'duration': 45}
        }
    ]
    
    # Track events
    for event in test_events:
        tracker.track_event(event)
    
    # Get metrics
    metrics = tracker.get_article_metrics('art_001')
    print(f"Article metrics: {metrics}")
    
    # Get trends
    trends = tracker.get_engagement_trends('24h')
    print(f"Engagement trends: {trends}")
    
    # Calculate content score
    score = tracker.calculate_content_score('art_001')
    print(f"Content score: {score}")


if __name__ == "__main__":
    main()