"""
AI-powered anomaly detection for ZeroToShip monitoring.
Uses TensorFlow to detect performance anomalies and predict potential system failures.
"""

import numpy as np
import logging
from typing import Dict, List, Optional, Tuple, Any
from datetime import datetime, timedelta
import asyncio
import json

try:
    import tensorflow as tf
    from tensorflow import keras
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. AI anomaly detection disabled.")

try:
    from sklearn.preprocessing import StandardScaler
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False
    # Create a mock StandardScaler
    class StandardScaler:
        def fit_transform(self, data):
            return data
        def transform(self, data):
            return data

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("Warning: requests not available. Prometheus integration limited.")

logger = logging.getLogger(__name__)

class AnomalyDetector:
    """AI-powered anomaly detection for ZeroToShip metrics."""
    
    def __init__(self, prometheus_url: str = "http://localhost:9090"):
        self.prometheus_url = prometheus_url
        self.enabled = TENSORFLOW_AVAILABLE and REQUESTS_AVAILABLE and SKLEARN_AVAILABLE
        self.model = None
        self.scaler = StandardScaler()
        self.is_trained = False
        self.anomaly_threshold = 0.7
        
        if not self.enabled:
            logger.warning("Anomaly detection disabled - missing dependencies")
            return
        
        # Initialize the LSTM model for time series anomaly detection
        self._build_model()
        logger.info("Anomaly detector initialized")
    
    def _build_model(self):
        """Build LSTM model for time series anomaly detection."""
        if not TENSORFLOW_AVAILABLE:
            return
            
        self.model = keras.Sequential([
            keras.layers.LSTM(50, return_sequences=True, input_shape=(10, 4)),  # 10 timesteps, 4 features
            keras.layers.Dropout(0.2),
            keras.layers.LSTM(50, return_sequences=False),
            keras.layers.Dropout(0.2),
            keras.layers.Dense(25),
            keras.layers.Dense(1, activation='sigmoid')  # Anomaly probability
        ])
        
        self.model.compile(
            optimizer='adam',
            loss='binary_crossentropy',
            metrics=['accuracy']
        )
        
        logger.info("LSTM anomaly detection model built successfully")
    
    async def query_prometheus(self, query: str, time_range: str = "1h") -> Optional[List[Dict]]:
        """Query Prometheus for metrics data."""
        if not REQUESTS_AVAILABLE:
            return None
            
        try:
            url = f"{self.prometheus_url}/api/v1/query_range"
            params = {
                'query': query,
                'start': (datetime.utcnow() - timedelta(hours=1)).isoformat() + 'Z',
                'end': datetime.utcnow().isoformat() + 'Z',
                'step': '1m'
            }
            
            response = requests.get(url, params=params, timeout=10)
            response.raise_for_status()
            
            data = response.json()
            if data['status'] == 'success':
                return data['data']['result']
            else:
                logger.error(f"Prometheus query failed: {data}")
                return None
                
        except Exception as e:
            logger.error(f"Failed to query Prometheus: {e}")
            return None
    
    def _prepare_training_data(self, metrics_data: List[Dict]) -> Tuple[np.ndarray, np.ndarray]:
        """Prepare training data from Prometheus metrics."""
        sequences = []
        labels = []
        
        for metric in metrics_data:
            values = metric.get('values', [])
            if len(values) < 10:  # Need at least 10 data points
                continue
                
            # Extract features: timestamp, value, rate of change, moving average
            features = []
            for i, (timestamp, value) in enumerate(values):
                try:
                    val = float(value)
                    timestamp_val = float(timestamp)
                    
                    # Calculate rate of change
                    rate_of_change = 0
                    if i > 0:
                        prev_val = float(values[i-1][1])
                        rate_of_change = (val - prev_val) / prev_val if prev_val != 0 else 0
                    
                    # Calculate moving average (last 3 points)
                    moving_avg = val
                    if i >= 2:
                        last_3 = [float(values[j][1]) for j in range(max(0, i-2), i+1)]
                        moving_avg = np.mean(last_3)
                    
                    features.append([timestamp_val, val, rate_of_change, moving_avg])
                    
                except (ValueError, IndexError):
                    continue
            
            # Create sequences of 10 timesteps
            for i in range(len(features) - 10):
                sequence = features[i:i+10]
                sequences.append(sequence)
                
                # Simple anomaly labeling: high rate of change or extreme values
                current_val = sequence[-1][1]
                rate_change = abs(sequence[-1][2])
                is_anomaly = rate_change > 2.0 or current_val > np.percentile([f[1] for f in features], 95)
                labels.append(1 if is_anomaly else 0)
        
        if not sequences:
            return np.array([]), np.array([])
            
        return np.array(sequences), np.array(labels)
    
    async def train_model(self, hours_back: int = 24):
        """Train the anomaly detection model using historical data."""
        if not self.enabled or not self.model:
            logger.warning("Cannot train model - anomaly detection disabled")
            return False
        
        logger.info(f"Training anomaly detection model with {hours_back} hours of data")
        
        # Query multiple metrics for training
        metrics_queries = [
            'zerotoship_workflow_duration_seconds',
            'zerotoship_crew_duration_seconds',
            'zerotoship_celery_task_duration_seconds',
            'zerotoship_errors_total'
        ]
        
        all_training_data = []
        all_labels = []
        
        for query in metrics_queries:
            data = await self.query_prometheus(query, f"{hours_back}h")
            if data:
                sequences, labels = self._prepare_training_data(data)
                if len(sequences) > 0:
                    all_training_data.append(sequences)
                    all_labels.append(labels)
        
        if not all_training_data:
            logger.warning("No training data available")
            return False
        
        # Combine all training data
        X_train = np.vstack(all_training_data)
        y_train = np.hstack(all_labels)
        
        if len(X_train) < 10:
            logger.warning("Insufficient training data")
            return False
        
        # Normalize features
        X_train_reshaped = X_train.reshape(-1, X_train.shape[-1])
        X_train_scaled = self.scaler.fit_transform(X_train_reshaped)
        X_train_scaled = X_train_scaled.reshape(X_train.shape)
        
        # Train the model
        try:
            history = self.model.fit(
                X_train_scaled, y_train,
                epochs=50,
                batch_size=32,
                validation_split=0.2,
                verbose=0
            )
            
            self.is_trained = True
            logger.info(f"Model trained successfully. Final accuracy: {history.history['accuracy'][-1]:.4f}")
            return True
            
        except Exception as e:
            logger.error(f"Model training failed: {e}")
            return False
    
    async def detect_anomalies(self) -> Dict[str, Any]:
        """Detect anomalies in current system metrics."""
        if not self.enabled or not self.is_trained:
            return {'enabled': False, 'reason': 'Model not trained or dependencies missing'}
        
        # Query recent metrics
        current_metrics = {}
        anomalies_detected = []
        
        metrics_to_check = [
            ('workflow_latency', 'rate(zerotoship_workflow_duration_seconds_sum[5m]) / rate(zerotoship_workflow_duration_seconds_count[5m])'),
            ('crew_latency', 'rate(zerotoship_crew_duration_seconds_sum[5m]) / rate(zerotoship_crew_duration_seconds_count[5m])'),
            ('error_rate', 'rate(zerotoship_errors_total[5m])'),
            ('active_workflows', 'zerotoship_active_workflows')
        ]
        
        for metric_name, query in metrics_to_check:
            data = await self.query_prometheus(query, "10m")
            if data and len(data) > 0:
                recent_values = data[0].get('values', [])[-10:]  # Last 10 data points
                
                if len(recent_values) >= 10:
                    # Prepare data for model
                    features = []
                    for i, (timestamp, value) in enumerate(recent_values):
                        try:
                            val = float(value)
                            timestamp_val = float(timestamp)
                            
                            rate_of_change = 0
                            if i > 0:
                                prev_val = float(recent_values[i-1][1])
                                rate_of_change = (val - prev_val) / prev_val if prev_val != 0 else 0
                            
                            moving_avg = val
                            if i >= 2:
                                last_3 = [float(recent_values[j][1]) for j in range(max(0, i-2), i+1)]
                                moving_avg = np.mean(last_3)
                            
                            features.append([timestamp_val, val, rate_of_change, moving_avg])
                        except (ValueError, IndexError):
                            continue
                    
                    if len(features) == 10:
                        # Scale features and predict
                        features_array = np.array([features])
                        features_scaled = self.scaler.transform(features_array.reshape(-1, 4))
                        features_scaled = features_scaled.reshape(features_array.shape)
                        
                        anomaly_probability = self.model.predict(features_scaled, verbose=0)[0][0]
                        
                        current_metrics[metric_name] = {
                            'current_value': features[-1][1],
                            'anomaly_probability': float(anomaly_probability),
                            'is_anomaly': anomaly_probability > self.anomaly_threshold
                        }
                        
                        if anomaly_probability > self.anomaly_threshold:
                            anomalies_detected.append({
                                'metric': metric_name,
                                'probability': float(anomaly_probability),
                                'current_value': features[-1][1],
                                'severity': 'high' if anomaly_probability > 0.9 else 'medium'
                            })
        
        return {
            'enabled': True,
            'timestamp': datetime.utcnow().isoformat(),
            'anomalies_detected': anomalies_detected,
            'metrics_analysis': current_metrics,
            'total_anomalies': len(anomalies_detected)
        }
    
    async def get_health_score(self) -> Dict[str, Any]:
        """Calculate overall system health score."""
        anomaly_result = await self.detect_anomalies()
        
        if not anomaly_result.get('enabled', False):
            return {'health_score': 0.5, 'status': 'unknown', 'reason': 'Monitoring disabled'}
        
        total_anomalies = anomaly_result.get('total_anomalies', 0)
        metrics_count = len(anomaly_result.get('metrics_analysis', {}))
        
        if metrics_count == 0:
            return {'health_score': 0.5, 'status': 'unknown', 'reason': 'No metrics available'}
        
        # Calculate health score (1.0 = perfect, 0.0 = critical)
        anomaly_ratio = total_anomalies / metrics_count if metrics_count > 0 else 0
        health_score = max(0.0, 1.0 - (anomaly_ratio * 2))  # Penalize anomalies heavily
        
        # Determine status
        if health_score >= 0.8:
            status = 'healthy'
        elif health_score >= 0.6:
            status = 'warning'
        elif health_score >= 0.3:
            status = 'degraded'
        else:
            status = 'critical'
        
        return {
            'health_score': health_score,
            'status': status,
            'anomalies_detected': total_anomalies,
            'metrics_analyzed': metrics_count,
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def start_monitoring_loop(self, interval_seconds: int = 60):
        """Start continuous anomaly monitoring loop."""
        if not self.enabled:
            logger.warning("Cannot start monitoring - anomaly detection disabled")
            return
        
        logger.info(f"Starting anomaly monitoring loop (interval: {interval_seconds}s)")
        
        while True:
            try:
                # Retrain model periodically (every 6 hours)
                current_time = datetime.utcnow()
                if not self.is_trained or (current_time.hour % 6 == 0 and current_time.minute < 5):
                    await self.train_model()
                
                # Detect anomalies
                result = await self.detect_anomalies()
                
                if result.get('total_anomalies', 0) > 0:
                    logger.warning(f"Detected {result['total_anomalies']} anomalies: {result['anomalies_detected']}")
                
                # Get health score
                health = await self.get_health_score()
                logger.info(f"System health: {health['status']} (score: {health['health_score']:.2f})")
                
                await asyncio.sleep(interval_seconds)
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(interval_seconds)


# Global anomaly detector instance
anomaly_detector = AnomalyDetector()