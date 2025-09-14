"""
Sentiment Analysis Engine

Provides multi-language sentiment analysis for Nordic news content.
Supports Norwegian, Swedish, Danish, Finnish, and English.
"""

import logging
import re
from typing import Dict, List, Optional, Tuple
from datetime import datetime
import yaml
import os

# Sentiment analysis libraries
from textblob import TextBlob
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer
import spacy
from transformers import pipeline, AutoTokenizer, AutoModelForSequenceClassification

logger = logging.getLogger(__name__)


class NordicSentimentAnalyzer:
    """
    Multi-language sentiment analyzer for Nordic news content.
    
    Features:
    - Support for Norwegian, Swedish, Danish, Finnish, and English
    - Multiple sentiment analysis models (VADER, TextBlob, Transformers)
    - Topic-based sentiment analysis
    - Brand sentiment monitoring
    - Confidence scoring
    """
    
    def __init__(self, config_path: str = "config/config.yaml"):
        """Initialize the sentiment analyzer with configuration."""
        self.config = self._load_config(config_path)
        self.vader_analyzer = SentimentIntensityAnalyzer()
        self.transformer_models = {}
        self.nlp_models = {}
        
        # Initialize language models
        self._initialize_models()
    
    def _load_config(self, config_path: str) -> Dict:
        """Load configuration from YAML file."""
        try:
            with open(config_path, 'r', encoding='utf-8') as file:
                return yaml.safe_load(file)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {config_path}")
            return {}
    
    def _initialize_models(self):
        """Initialize NLP models for different languages."""
        try:
            # Load spaCy models for Nordic languages
            language_models = {
                'no': 'nb_core_news_sm',  # Norwegian
                'sv': 'sv_core_news_sm',  # Swedish
                'da': 'da_core_news_sm',  # Danish
                'fi': 'fi_core_news_sm',  # Finnish
                'en': 'en_core_web_sm'    # English
            }
            
            for lang_code, model_name in language_models.items():
                try:
                    self.nlp_models[lang_code] = spacy.load(model_name)
                    logger.info(f"Loaded spaCy model for {lang_code}")
                except OSError:
                    logger.warning(f"spaCy model {model_name} not found for {lang_code}")
                    # Fallback to English model
                    if lang_code != 'en':
                        self.nlp_models[lang_code] = spacy.load('en_core_web_sm')
            
            # Initialize transformer models for advanced sentiment analysis
            self._initialize_transformer_models()
            
        except Exception as e:
            logger.error(f"Error initializing models: {e}")
    
    def _initialize_transformer_models(self):
        """Initialize transformer models for advanced sentiment analysis."""
        try:
            # Use a multilingual sentiment analysis model
            model_name = "cardiffnlp/twitter-xlm-roberta-base-sentiment"
            self.transformer_models['multilingual'] = pipeline(
                "sentiment-analysis",
                model=model_name,
                tokenizer=model_name,
                return_all_scores=True
            )
            logger.info("Loaded multilingual transformer model")
        except Exception as e:
            logger.warning(f"Could not load transformer model: {e}")
    
    def analyze_sentiment(self, text: str, language: str = 'en', 
                         method: str = 'auto') -> Dict:
        """
        Analyze sentiment of the given text.
        
        Args:
            text: Text to analyze
            language: Language code (no, sv, da, fi, en)
            method: Analysis method ('vader', 'textblob', 'transformers', 'auto')
        
        Returns:
            Dictionary with sentiment scores and metadata
        """
        if not text or not text.strip():
            return self._empty_sentiment_result()
        
        # Clean and preprocess text
        cleaned_text = self._preprocess_text(text)
        
        # Choose analysis method
        if method == 'auto':
            method = self._choose_best_method(language)
        
        # Perform sentiment analysis
        sentiment_scores = self._analyze_with_method(cleaned_text, language, method)
        
        # Add metadata
        result = {
            'text': text[:200] + '...' if len(text) > 200 else text,
            'language': language,
            'method': method,
            'timestamp': datetime.now().isoformat(),
            'word_count': len(cleaned_text.split()),
            'character_count': len(cleaned_text),
            **sentiment_scores
        }
        
        return result
    
    def _analyze_with_method(self, text: str, language: str, method: str) -> Dict:
        """Analyze sentiment using the specified method."""
        try:
            if method == 'vader':
                return self._analyze_with_vader(text)
            elif method == 'textblob':
                return self._analyze_with_textblob(text, language)
            elif method == 'transformers':
                return self._analyze_with_transformers(text)
            else:
                logger.warning(f"Unknown method {method}, falling back to VADER")
                return self._analyze_with_vader(text)
        except Exception as e:
            logger.error(f"Error in sentiment analysis with {method}: {e}")
            return self._empty_sentiment_result()
    
    def _analyze_with_vader(self, text: str) -> Dict:
        """Analyze sentiment using VADER."""
        scores = self.vader_analyzer.polarity_scores(text)
        
        return {
            'compound_score': scores['compound'],
            'positive_score': scores['pos'],
            'negative_score': scores['neg'],
            'neutral_score': scores['neu'],
            'sentiment_label': self._get_sentiment_label(scores['compound']),
            'confidence': abs(scores['compound'])
        }
    
    def _analyze_with_textblob(self, text: str, language: str) -> Dict:
        """Analyze sentiment using TextBlob."""
        blob = TextBlob(text)
        polarity = blob.sentiment.polarity
        subjectivity = blob.sentiment.subjectivity
        
        return {
            'compound_score': polarity,
            'positive_score': max(0, polarity),
            'negative_score': max(0, -polarity),
            'neutral_score': 1 - abs(polarity),
            'subjectivity': subjectivity,
            'sentiment_label': self._get_sentiment_label(polarity),
            'confidence': abs(polarity)
        }
    
    def _analyze_with_transformers(self, text: str) -> Dict:
        """Analyze sentiment using transformer models."""
        if 'multilingual' not in self.transformer_models:
            logger.warning("Transformer model not available, falling back to VADER")
            return self._analyze_with_vader(text)
        
        try:
            results = self.transformer_models['multilingual'](text)
            
            # Extract scores
            scores = {}
            for result in results:
                label = result['label'].lower()
                score = result['score']
                scores[f"{label}_score"] = score
            
            # Determine primary sentiment
            best_result = max(results, key=lambda x: x['score'])
            sentiment_label = self._map_transformer_label(best_result['label'])
            
            return {
                'compound_score': scores.get('positive_score', 0) - scores.get('negative_score', 0),
                'positive_score': scores.get('positive_score', 0),
                'negative_score': scores.get('negative_score', 0),
                'neutral_score': scores.get('neutral_score', 0),
                'sentiment_label': sentiment_label,
                'confidence': best_result['score']
            }
        except Exception as e:
            logger.error(f"Error in transformer analysis: {e}")
            return self._analyze_with_vader(text)
    
    def _map_transformer_label(self, label: str) -> str:
        """Map transformer model labels to our standard labels."""
        label_mapping = {
            'LABEL_0': 'negative',
            'LABEL_1': 'neutral',
            'LABEL_2': 'positive',
            'NEGATIVE': 'negative',
            'NEUTRAL': 'neutral',
            'POSITIVE': 'positive'
        }
        return label_mapping.get(label.upper(), 'neutral')
    
    def _get_sentiment_label(self, score: float) -> str:
        """Convert numeric score to sentiment label."""
        thresholds = self.config.get('sentiment_analysis', {}).get('thresholds', {})
        positive_threshold = thresholds.get('positive', 0.05)
        negative_threshold = thresholds.get('negative', -0.05)
        
        if score >= positive_threshold:
            return 'positive'
        elif score <= negative_threshold:
            return 'negative'
        else:
            return 'neutral'
    
    def _preprocess_text(self, text: str) -> str:
        """Clean and preprocess text for sentiment analysis."""
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        # Remove URLs
        text = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', text)
        
        # Remove email addresses
        text = re.sub(r'\S+@\S+', '', text)
        
        # Remove special characters but keep Nordic characters
        text = re.sub(r'[^\w\sæøåäöüß]', ' ', text)
        
        return text.strip()
    
    def _choose_best_method(self, language: str) -> str:
        """Choose the best sentiment analysis method for the given language."""
        if language in ['no', 'sv', 'da', 'fi'] and 'multilingual' in self.transformer_models:
            return 'transformers'
        elif language == 'en':
            return 'vader'
        else:
            return 'textblob'
    
    def _empty_sentiment_result(self) -> Dict:
        """Return empty sentiment result for invalid input."""
        return {
            'compound_score': 0.0,
            'positive_score': 0.0,
            'negative_score': 0.0,
            'neutral_score': 1.0,
            'sentiment_label': 'neutral',
            'confidence': 0.0
        }
    
    def analyze_batch(self, texts: List[str], language: str = 'en') -> List[Dict]:
        """Analyze sentiment for a batch of texts."""
        results = []
        for text in texts:
            result = self.analyze_sentiment(text, language)
            results.append(result)
        return results
    
    def get_sentiment_trends(self, articles: List[Dict], 
                           time_window: str = '1d') -> Dict:
        """
        Analyze sentiment trends over time.
        
        Args:
            articles: List of article dictionaries with sentiment data
            time_window: Time window for trend analysis ('1h', '1d', '7d', '30d')
        
        Returns:
            Dictionary with trend analysis results
        """
        if not articles:
            return {'trend': 'neutral', 'change': 0.0, 'confidence': 0.0}
        
        # Extract sentiment scores
        scores = [article.get('sentiment_score', 0) for article in articles]
        
        if not scores:
            return {'trend': 'neutral', 'change': 0.0, 'confidence': 0.0}
        
        # Calculate trend metrics
        avg_score = sum(scores) / len(scores)
        positive_count = sum(1 for s in scores if s > 0.05)
        negative_count = sum(1 for s in scores if s < -0.05)
        neutral_count = len(scores) - positive_count - negative_count
        
        # Determine trend direction
        if positive_count > negative_count:
            trend = 'positive'
        elif negative_count > positive_count:
            trend = 'negative'
        else:
            trend = 'neutral'
        
        return {
            'trend': trend,
            'average_score': avg_score,
            'positive_ratio': positive_count / len(scores),
            'negative_ratio': negative_count / len(scores),
            'neutral_ratio': neutral_count / len(scores),
            'total_articles': len(articles),
            'confidence': abs(avg_score)
        }


def main():
    """Main function for testing the sentiment analyzer."""
    analyzer = NordicSentimentAnalyzer()
    
    # Test with sample texts
    test_texts = [
        "This is a great article about Nordic news!",
        "I'm not sure about this development.",
        "This is terrible news for the economy.",
        "Det er en fantastisk artikkel om nordiske nyheter!",
        "Detta är en bra artikel om nordiska nyheter!"
    ]
    
    for text in test_texts:
        result = analyzer.analyze_sentiment(text)
        print(f"\nText: {text}")
        print(f"Sentiment: {result['sentiment_label']} (score: {result['compound_score']:.3f})")
        print(f"Confidence: {result['confidence']:.3f}")


if __name__ == "__main__":
    main()