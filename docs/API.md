# Nordic News Sentiment & Engagement Tracker - API Documentation

## Overview

The Nordic News Analytics platform provides a comprehensive API for accessing sentiment analysis, engagement metrics, and A/B testing data. The API follows RESTful principles and supports JSON responses.

## Base URL

```
Development: http://localhost:8501/api/v1
Production: https://api.nordicnewsanalytics.com/v1
```

## Authentication

Currently, the API uses simple API key authentication. Include your API key in the request headers:

```http
Authorization: Bearer YOUR_API_KEY
```

## Rate Limiting

- **Rate Limit**: 1000 requests per hour per API key
- **Headers**: Rate limit information is included in response headers
- **Exceeded**: Returns 429 Too Many Requests when limit exceeded

## Endpoints

### News Articles

#### Get Articles
```http
GET /articles
```

**Query Parameters**:
- `limit` (optional): Number of articles to return (default: 100, max: 1000)
- `offset` (optional): Number of articles to skip (default: 0)
- `source` (optional): Filter by news source (e.g., "VG", "Aftenposten")
- `language` (optional): Filter by language (e.g., "no", "sv", "da", "fi")
- `date_from` (optional): Start date (ISO format)
- `date_to` (optional): End date (ISO format)

**Response**:
```json
{
  "articles": [
    {
      "id": "art_001",
      "title": "Major Economic Development in Nordic Region",
      "url": "https://example.com/article",
      "summary": "Article summary...",
      "content": "Full article content...",
      "published_date": "2024-01-15T10:30:00Z",
      "source_name": "VG",
      "source_country": "Norway",
      "source_language": "no",
      "author": "Economic Reporter",
      "tags": ["economy", "nordic"],
      "word_count": 450,
      "collected_at": "2024-01-15T11:00:00Z"
    }
  ],
  "total_count": 1247,
  "page": 1,
  "per_page": 100
}
```

#### Get Article by ID
```http
GET /articles/{article_id}
```

**Response**:
```json
{
  "id": "art_001",
  "title": "Major Economic Development in Nordic Region",
  "url": "https://example.com/article",
  "summary": "Article summary...",
  "content": "Full article content...",
  "published_date": "2024-01-15T10:30:00Z",
  "source_name": "VG",
  "source_country": "Norway",
  "source_language": "no",
  "author": "Economic Reporter",
  "tags": ["economy", "nordic"],
  "word_count": 450,
  "collected_at": "2024-01-15T11:00:00Z"
}
```

### Sentiment Analysis

#### Get Article Sentiment
```http
GET /articles/{article_id}/sentiment
```

**Response**:
```json
{
  "article_id": "art_001",
  "sentiment_label": "positive",
  "compound_score": 0.65,
  "positive_score": 0.75,
  "negative_score": 0.10,
  "neutral_score": 0.15,
  "confidence": 0.85,
  "method": "vader",
  "language": "no",
  "analyzed_at": "2024-01-15T11:05:00Z"
}
```

#### Analyze Text Sentiment
```http
POST /sentiment/analyze
```

**Request Body**:
```json
{
  "text": "This is a great article about Nordic news!",
  "language": "en",
  "method": "auto"
}
```

**Response**:
```json
{
  "text": "This is a great article about Nordic news!",
  "language": "en",
  "method": "vader",
  "sentiment_label": "positive",
  "compound_score": 0.65,
  "positive_score": 0.75,
  "negative_score": 0.10,
  "neutral_score": 0.15,
  "confidence": 0.85,
  "timestamp": "2024-01-15T11:05:00Z"
}
```

#### Get Sentiment Trends
```http
GET /sentiment/trends
```

**Query Parameters**:
- `days` (optional): Number of days to analyze (default: 7)
- `source` (optional): Filter by news source
- `language` (optional): Filter by language

**Response**:
```json
{
  "trends": [
    {
      "date": "2024-01-15",
      "positive_count": 45,
      "negative_count": 12,
      "neutral_count": 23,
      "average_score": 0.23,
      "total_articles": 80
    }
  ],
  "summary": {
    "overall_trend": "positive",
    "average_sentiment": 0.23,
    "total_articles": 560,
    "positive_ratio": 0.68,
    "negative_ratio": 0.15,
    "neutral_ratio": 0.17
  }
}
```

### Engagement Metrics

#### Get Article Engagement
```http
GET /articles/{article_id}/engagement
```

**Response**:
```json
{
  "article_id": "art_001",
  "total_views": 1250,
  "unique_users": 980,
  "clicks": 187,
  "shares": 45,
  "avg_time_on_page": 2.5,
  "ctr": 0.15,
  "share_rate": 0.036,
  "content_score": 78.5,
  "last_updated": "2024-01-15T11:00:00Z"
}
```

#### Get Engagement Trends
```http
GET /engagement/trends
```

**Query Parameters**:
- `days` (optional): Number of days to analyze (default: 7)
- `metric` (optional): Specific metric to analyze (e.g., "ctr", "time_on_page")

**Response**:
```json
{
  "trends": [
    {
      "date": "2024-01-15",
      "total_events": 15420,
      "unique_users": 8750,
      "engagement_rate": 0.153,
      "avg_time_on_page": 2.4,
      "total_shares": 234
    }
  ],
  "summary": {
    "total_events": 108940,
    "unique_users": 45678,
    "avg_engagement_rate": 0.153,
    "avg_time_on_page": 2.4,
    "total_shares": 1647
  }
}
```

#### Get Top Performing Articles
```http
GET /engagement/top-articles
```

**Query Parameters**:
- `metric` (optional): Metric to sort by (default: "ctr")
- `limit` (optional): Number of articles to return (default: 10)
- `timeframe` (optional): Timeframe for analysis (e.g., "24h", "7d", "30d")

**Response**:
```json
{
  "articles": [
    {
      "article_id": "art_001",
      "title": "Major Economic Development in Nordic Region",
      "source_name": "VG",
      "ctr": 0.235,
      "total_views": 1250,
      "content_score": 78.5
    }
  ],
  "total_count": 10,
  "metric": "ctr",
  "timeframe": "7d"
}
```

### A/B Testing

#### Get Experiments
```http
GET /experiments
```

**Response**:
```json
{
  "experiments": [
    {
      "id": "exp_001",
      "name": "Headline Optimization Test",
      "description": "Test different headline styles for engagement",
      "status": "running",
      "created_at": "2024-01-10T09:00:00Z",
      "start_date": "2024-01-15T09:00:00Z",
      "end_date": null,
      "variants": ["control", "treatment"],
      "traffic_split": 0.5
    }
  ],
  "total_count": 5
}
```

#### Get Experiment Results
```http
GET /experiments/{experiment_id}/results
```

**Response**:
```json
{
  "experiment_id": "exp_001",
  "experiment_name": "Headline Optimization Test",
  "status": "completed",
  "control_variant": "control",
  "treatment_variant": "treatment",
  "control_mean": 0.152,
  "treatment_mean": 0.178,
  "mean_difference": 0.026,
  "improvement_percentage": 17.1,
  "p_value": 0.023,
  "is_significant": true,
  "effect_size": 0.45,
  "confidence_interval": [0.012, 0.040],
  "sample_sizes": {
    "control": 5000,
    "treatment": 5000
  }
}
```

#### Create Experiment
```http
POST /experiments
```

**Request Body**:
```json
{
  "name": "Content Layout Test",
  "description": "Test different content layouts for engagement",
  "traffic_split": 0.5,
  "test_type": "content_optimization",
  "target_metric": "ctr",
  "minimum_sample_size": 1000,
  "significance_level": 0.05
}
```

**Response**:
```json
{
  "experiment_id": "exp_002",
  "name": "Content Layout Test",
  "description": "Test different content layouts for engagement",
  "status": "draft",
  "created_at": "2024-01-15T11:00:00Z",
  "traffic_split": 0.5,
  "test_type": "content_optimization",
  "target_metric": "ctr"
}
```

### Analytics Reports

#### Generate Report
```http
POST /reports/generate
```

**Request Body**:
```json
{
  "report_type": "engagement",
  "start_date": "2024-01-01T00:00:00Z",
  "end_date": "2024-01-31T23:59:59Z",
  "sources": ["VG", "Aftenposten"],
  "languages": ["no", "sv"],
  "format": "json"
}
```

**Response**:
```json
{
  "report_id": "rpt_001",
  "report_type": "engagement",
  "status": "completed",
  "generated_at": "2024-01-15T11:30:00Z",
  "download_url": "/api/v1/reports/rpt_001/download",
  "expires_at": "2024-01-22T11:30:00Z"
}
```

#### Download Report
```http
GET /reports/{report_id}/download
```

**Response**: File download (JSON, CSV, or PDF format)

## Error Handling

### Error Response Format
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid request parameters",
    "details": {
      "field": "limit",
      "issue": "Value must be between 1 and 1000"
    },
    "timestamp": "2024-01-15T11:00:00Z",
    "request_id": "req_123456"
  }
}
```

### Error Codes
- `400` - Bad Request
- `401` - Unauthorized
- `403` - Forbidden
- `404` - Not Found
- `429` - Too Many Requests
- `500` - Internal Server Error

## SDKs and Libraries

### Python SDK
```python
from nordic_news_api import NordicNewsAPI

api = NordicNewsAPI(api_key="your_api_key")

# Get articles
articles = api.articles.get(limit=10, source="VG")

# Analyze sentiment
sentiment = api.sentiment.analyze("Great article!")

# Get engagement metrics
metrics = api.engagement.get_article_metrics("art_001")
```

### JavaScript SDK
```javascript
import { NordicNewsAPI } from 'nordic-news-api';

const api = new NordicNewsAPI('your_api_key');

// Get articles
const articles = await api.articles.get({ limit: 10, source: 'VG' });

// Analyze sentiment
const sentiment = await api.sentiment.analyze('Great article!');

// Get engagement metrics
const metrics = await api.engagement.getArticleMetrics('art_001');
```

## Webhooks

### Sentiment Analysis Webhook
```http
POST /webhooks/sentiment
```

**Payload**:
```json
{
  "event_type": "sentiment_analysis_completed",
  "article_id": "art_001",
  "sentiment_label": "positive",
  "confidence": 0.85,
  "timestamp": "2024-01-15T11:05:00Z"
}
```

### Engagement Webhook
```http
POST /webhooks/engagement
```

**Payload**:
```json
{
  "event_type": "engagement_threshold_exceeded",
  "article_id": "art_001",
  "metric": "ctr",
  "value": 0.25,
  "threshold": 0.20,
  "timestamp": "2024-01-15T11:05:00Z"
}
```

## Rate Limits

| Endpoint Category | Rate Limit | Burst Limit |
|------------------|------------|-------------|
| Articles | 1000/hour | 100/minute |
| Sentiment | 500/hour | 50/minute |
| Engagement | 2000/hour | 200/minute |
| A/B Testing | 100/hour | 10/minute |
| Reports | 50/hour | 5/minute |

## Pagination

All list endpoints support pagination using `limit` and `offset` parameters:

```http
GET /articles?limit=50&offset=100
```

Response includes pagination metadata:
```json
{
  "data": [...],
  "pagination": {
    "page": 3,
    "per_page": 50,
    "total_count": 1247,
    "total_pages": 25,
    "has_next": true,
    "has_prev": true
  }
}
```