"""
Unit tests for the sentiment analyzer module.
"""

import unittest
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sentiment_analysis.sentiment_analyzer import NordicSentimentAnalyzer


class TestSentimentAnalyzer(unittest.TestCase):
    """Test cases for the NordicSentimentAnalyzer class."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.analyzer = NordicSentimentAnalyzer()
    
    def test_analyze_sentiment_positive(self):
        """Test sentiment analysis with positive text."""
        text = "This is a great article about Nordic news!"
        result = self.analyzer.analyze_sentiment(text)
        
        self.assertIsInstance(result, dict)
        self.assertIn('sentiment_label', result)
        self.assertIn('compound_score', result)
        self.assertIn('confidence', result)
        self.assertEqual(result['sentiment_label'], 'positive')
    
    def test_analyze_sentiment_negative(self):
        """Test sentiment analysis with negative text."""
        text = "This is terrible news for the economy."
        result = self.analyzer.analyze_sentiment(text)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['sentiment_label'], 'negative')
    
    def test_analyze_sentiment_neutral(self):
        """Test sentiment analysis with neutral text."""
        text = "This is a neutral statement about the weather."
        result = self.analyzer.analyze_sentiment(text)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['sentiment_label'], 'neutral')
    
    def test_analyze_sentiment_empty_text(self):
        """Test sentiment analysis with empty text."""
        result = self.analyzer.analyze_sentiment("")
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['sentiment_label'], 'neutral')
        self.assertEqual(result['compound_score'], 0.0)
    
    def test_analyze_sentiment_norwegian(self):
        """Test sentiment analysis with Norwegian text."""
        text = "Dette er en fantastisk artikkel om nordiske nyheter!"
        result = self.analyzer.analyze_sentiment(text, language='no')
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result['language'], 'no')
    
    def test_analyze_batch(self):
        """Test batch sentiment analysis."""
        texts = [
            "Great news!",
            "Bad news.",
            "Neutral statement."
        ]
        results = self.analyzer.analyze_batch(texts)
        
        self.assertEqual(len(results), 3)
        self.assertIsInstance(results[0], dict)
    
    def test_get_sentiment_trends(self):
        """Test sentiment trend analysis."""
        articles = [
            {'sentiment_score': 0.5},
            {'sentiment_score': 0.3},
            {'sentiment_score': 0.7}
        ]
        trends = self.analyzer.get_sentiment_trends(articles)
        
        self.assertIsInstance(trends, dict)
        self.assertIn('trend', trends)
        self.assertIn('average_score', trends)


if __name__ == '__main__':
    unittest.main()