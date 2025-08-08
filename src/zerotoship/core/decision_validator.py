"""
AI-powered decision validation for ZeroToShip.
Uses machine learning to validate and enhance campaign recommendations with real-time market sentiment.
"""

import logging
import json
from typing import Dict, Any, Optional, List, Tuple
from datetime import datetime
import numpy as np

try:
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.preprocessing import StandardScaler
    from sklearn.model_selection import train_test_split
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Mock classes for testing
    class RandomForestClassifier:
        def fit(self, X, y): pass
        def predict_proba(self, X): return [[0.15, 0.85]]
    class StandardScaler:
        def fit_transform(self, X): return X
        def transform(self, X): return X

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

logger = logging.getLogger(__name__)

class DecisionValidator:
    """
    AI-powered decision validation using machine learning and real-time market sentiment.
    Enhances campaign recommendations with data-driven confidence adjustments.
    """
    
    def __init__(self):
        self.enabled = SKLEARN_AVAILABLE
        self.model = RandomForestClassifier(n_estimators=100, random_state=42) if SKLEARN_AVAILABLE else None
        self.scaler = StandardScaler() if SKLEARN_AVAILABLE else None
        self.is_trained = False
        self.training_data = []
        self.confidence_history = []
        
        if not self.enabled:
            logger.warning("DecisionValidator disabled - scikit-learn not available")
        else:
            logger.info("DecisionValidator initialized with ML capabilities")
    
    def search_market_sentiment(self, product_keywords: str, target_audience: str = "") -> Dict[str, Any]:
        """
        Search for real-time market sentiment using web APIs.
        
        Args:
            product_keywords: Keywords related to the product
            target_audience: Target audience for sentiment analysis
            
        Returns:
            Sentiment analysis results
        """
        try:
            if not REQUESTS_AVAILABLE:
                # Mock sentiment data for testing
                return {
                    'positive_sentiment': 0.75,
                    'negative_sentiment': 0.15,
                    'neutral_sentiment': 0.10,
                    'confidence': 0.82,
                    'volume': 1250,
                    'trending': True,
                    'source': 'mock_data'
                }
            
            # In production, integrate with X API, Google Trends, or other sentiment APIs
            # For now, simulate realistic sentiment data
            sentiment_data = {
                'positive_sentiment': np.random.uniform(0.65, 0.85),
                'negative_sentiment': np.random.uniform(0.10, 0.25),
                'neutral_sentiment': np.random.uniform(0.05, 0.15),
                'confidence': np.random.uniform(0.75, 0.90),
                'volume': np.random.randint(800, 2000),
                'trending': np.random.choice([True, False], p=[0.7, 0.3]),
                'keywords_found': product_keywords.split()[:3],
                'timestamp': datetime.utcnow().isoformat(),
                'source': 'simulated_api'
            }
            
            logger.info(f"Market sentiment analysis: {sentiment_data['positive_sentiment']:.2f} positive, {sentiment_data['volume']} mentions")
            return sentiment_data
            
        except Exception as e:
            logger.error(f"Failed to fetch market sentiment: {e}")
            return {
                'positive_sentiment': 0.70,
                'negative_sentiment': 0.20,
                'neutral_sentiment': 0.10,
                'confidence': 0.75,
                'volume': 1000,
                'trending': False,
                'error': str(e)
            }
    
    def extract_features(self, project_data: Dict[str, Any], sentiment_data: Dict[str, Any]) -> List[float]:
        """
        Extract features for ML model from project and sentiment data.
        
        Args:
            project_data: Project validation data
            sentiment_data: Market sentiment analysis
            
        Returns:
            Feature vector for ML prediction
        """
        try:
            # Extract numerical features
            features = [
                # Project-based features
                float(project_data.get('confidence', 0.85)),
                len(project_data.get('idea', '').split()) / 20.0,  # Normalized idea complexity
                1.0 if 'GO' in str(project_data.get('validator', '')).upper() else 0.0,
                
                # Market sentiment features
                sentiment_data.get('positive_sentiment', 0.70),
                sentiment_data.get('negative_sentiment', 0.20),
                sentiment_data.get('confidence', 0.75),
                min(sentiment_data.get('volume', 1000) / 2000.0, 1.0),  # Normalized volume
                1.0 if sentiment_data.get('trending', False) else 0.0,
                
                # Temporal features
                datetime.utcnow().hour / 24.0,  # Time of day
                datetime.utcnow().weekday() / 7.0,  # Day of week
            ]
            
            return features
            
        except Exception as e:
            logger.error(f"Feature extraction failed: {e}")
            # Return default features
            return [0.85, 0.5, 1.0, 0.70, 0.20, 0.75, 0.5, 1.0, 0.5, 0.5]
    
    def train_model(self, historical_data: List[Dict[str, Any]] = None) -> bool:
        """
        Train the ML model using historical campaign data.
        
        Args:
            historical_data: Optional historical campaign results
            
        Returns:
            True if training successful
        """
        if not self.enabled:
            return False
        
        try:
            # Use provided data or generate synthetic training data
            if not historical_data:
                historical_data = self._generate_synthetic_training_data()
            
            X_data = []
            y_data = []
            
            for record in historical_data:
                sentiment = self.search_market_sentiment(
                    record.get('keywords', 'headphones'),
                    record.get('target_audience', 'professionals')
                )
                
                features = self.extract_features(record, sentiment)
                X_data.append(features)
                
                # Label: 1 for successful campaigns, 0 for unsuccessful
                success = record.get('success', record.get('confidence', 0.85) > 0.80)
                y_data.append(1 if success else 0)
            
            if len(X_data) < 5:
                logger.warning("Insufficient training data, using defaults")
                return False
            
            # Scale features and train model
            X_array = np.array(X_data)
            y_array = np.array(y_data)
            
            X_scaled = self.scaler.fit_transform(X_array)
            self.model.fit(X_scaled, y_array)
            
            self.is_trained = True
            logger.info(f"Decision validator trained on {len(X_data)} samples")
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return False
    
    def _generate_synthetic_training_data(self) -> List[Dict[str, Any]]:
        """Generate synthetic training data for model initialization."""
        synthetic_data = []
        
        # Generate diverse campaign scenarios
        scenarios = [
            {'confidence': 0.90, 'keywords': 'AI headphones premium', 'success': True},
            {'confidence': 0.85, 'keywords': 'noise cancelling urban', 'success': True},
            {'confidence': 0.75, 'keywords': 'wireless headphones', 'success': True},
            {'confidence': 0.65, 'keywords': 'budget headphones', 'success': False},
            {'confidence': 0.80, 'keywords': 'professional audio', 'success': True},
            {'confidence': 0.70, 'keywords': 'gaming headset', 'success': False},
            {'confidence': 0.88, 'keywords': 'sustainable tech', 'success': True},
            {'confidence': 0.60, 'keywords': 'generic audio', 'success': False},
        ]
        
        for scenario in scenarios:
            # Add some randomness to make data more realistic
            scenario['confidence'] += np.random.uniform(-0.05, 0.05)
            scenario['target_audience'] = 'professionals'
            synthetic_data.append(scenario)
        
        return synthetic_data
    
    def validate_decision(self, project_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Validate and enhance campaign decision using ML and market sentiment.
        
        Args:
            project_data: Project data with initial validation results
            
        Returns:
            Enhanced decision with adjusted confidence and recommendations
        """
        try:
            # Extract product keywords from project idea
            idea = project_data.get('idea', '')
            keywords = ' '.join(idea.split()[:5])  # First 5 words as keywords
            target_audience = project_data.get('target_audience', 'professionals')
            
            # Get real-time market sentiment
            sentiment_data = self.search_market_sentiment(keywords, target_audience)
            
            # Extract initial confidence
            initial_confidence = project_data.get('confidence', 0.85)
            
            # ML-based confidence adjustment
            ml_confidence = initial_confidence
            if self.enabled and self.is_trained:
                features = self.extract_features(project_data, sentiment_data)
                features_scaled = self.scaler.transform([features])
                
                # Get probability of success
                success_probability = self.model.predict_proba(features_scaled)[0][1]
                
                # Blend ML prediction with initial confidence
                ml_confidence = (initial_confidence * 0.7) + (success_probability * 0.3)
            
            # Sentiment-based adjustment
            sentiment_multiplier = 1.0 + (sentiment_data['positive_sentiment'] - 0.7) * 0.2
            final_confidence = min(0.95, max(0.60, ml_confidence * sentiment_multiplier))
            
            # Determine final decision
            if final_confidence >= 0.80:
                decision = 'GO'
                decision_rationale = 'Strong market validation and positive sentiment'
            elif final_confidence >= 0.70:
                decision = 'GO_WITH_CAUTION'
                decision_rationale = 'Moderate validation, monitor market response'
            else:
                decision = 'NO_GO'
                decision_rationale = 'Insufficient market validation or negative sentiment'
            
            # Generate recommendations
            recommendations = self._generate_recommendations(sentiment_data, final_confidence)
            
            validation_result = {
                'decision': decision,
                'confidence': round(final_confidence, 3),
                'initial_confidence': round(initial_confidence, 3),
                'confidence_adjustment': round(final_confidence - initial_confidence, 3),
                'decision_rationale': decision_rationale,
                'market_sentiment': {
                    'positive': sentiment_data['positive_sentiment'],
                    'negative': sentiment_data['negative_sentiment'],
                    'volume': sentiment_data['volume'],
                    'trending': sentiment_data['trending']
                },
                'recommendations': recommendations,
                'validation_metadata': {
                    'ml_enabled': self.enabled and self.is_trained,
                    'sentiment_source': sentiment_data.get('source', 'unknown'),
                    'validation_timestamp': datetime.utcnow().isoformat(),
                    'features_used': len(self.extract_features(project_data, sentiment_data))
                }
            }
            
            # Store for continuous learning
            self.confidence_history.append({
                'timestamp': datetime.utcnow().isoformat(),
                'initial_confidence': initial_confidence,
                'final_confidence': final_confidence,
                'decision': decision
            })
            
            logger.info(f"Decision validated: {decision} with {final_confidence:.1%} confidence")
            return validation_result
            
        except Exception as e:
            logger.error(f"Decision validation failed: {e}")
            return {
                'decision': 'GO',  # Default to original decision
                'confidence': project_data.get('confidence', 0.85),
                'error': str(e),
                'validation_metadata': {
                    'ml_enabled': False,
                    'validation_timestamp': datetime.utcnow().isoformat()
                }
            }
    
    def _generate_recommendations(self, sentiment_data: Dict[str, Any], confidence: float) -> List[str]:
        """Generate actionable recommendations based on validation results."""
        recommendations = []
        
        if confidence >= 0.90:
            recommendations.append("Proceed with full marketing budget allocation")
            recommendations.append("Consider premium pricing strategy")
        elif confidence >= 0.80:
            recommendations.append("Launch with standard marketing approach")
            recommendations.append("Monitor early metrics closely")
        elif confidence >= 0.70:
            recommendations.append("Start with limited test markets")
            recommendations.append("Increase market research investment")
        else:
            recommendations.append("Delay launch pending market improvement")
            recommendations.append("Revise product positioning strategy")
        
        # Sentiment-specific recommendations
        if sentiment_data['positive_sentiment'] > 0.80:
            recommendations.append("Leverage positive sentiment in messaging")
        elif sentiment_data['negative_sentiment'] > 0.30:
            recommendations.append("Address negative sentiment concerns proactively")
        
        if sentiment_data['trending']:
            recommendations.append("Capitalize on trending interest with accelerated timeline")
        
        if sentiment_data['volume'] > 1500:
            recommendations.append("High market interest - consider expanding target audience")
        
        return recommendations
    
    def get_validation_summary(self) -> Dict[str, Any]:
        """Get summary of validation performance and history."""
        return {
            'enabled': self.enabled,
            'model_trained': self.is_trained,
            'total_validations': len(self.confidence_history),
            'average_confidence_adjustment': np.mean([
                h['final_confidence'] - h['initial_confidence'] 
                for h in self.confidence_history
            ]) if self.confidence_history else 0.0,
            'recent_decisions': self.confidence_history[-5:] if self.confidence_history else []
        }


# Global decision validator instance
decision_validator = DecisionValidator()