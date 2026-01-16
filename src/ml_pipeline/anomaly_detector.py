import numpy as np
import pandas as pd
from typing import Dict, List
from sklearn.ensemble import IsolationForest
from sklearn.preprocessing import StandardScaler
from sklearn.neighbors import LocalOutlierFactor
import logging
import warnings
warnings.filterwarnings('ignore')

logger = logging.getLogger(__name__)

class AadhaarAnomalyDetector:
    """Detect anomalies in enrolment patterns"""
    
    def __init__(self, config: Dict):
        self.config = config
        ml_config = config.get('ml', {}).get('anomaly_detection', {})
        
        self.model_type = ml_config.get('model', 'isolation_forest')
        self.contamination = ml_config.get('contamination', 0.1)
        self.random_state = ml_config.get('random_state', 42)
        
        # Initialize models
        if self.model_type == 'isolation_forest':
            self.model = IsolationForest(
                contamination=self.contamination,
                random_state=self.random_state,
                n_estimators=100,
                max_samples='auto'
            )
        elif self.model_type == 'local_outlier_factor':
            self.model = LocalOutlierFactor(
                contamination=self.contamination,
                novelty=True
            )
        else:
            raise ValueError(f"Unknown model type: {self.model_type}")
        
        self.scaler = StandardScaler()
        self.is_fitted = False
    
    def detect(self, features_df: pd.DataFrame) -> pd.DataFrame:
        """Detect anomalies in the data"""
        logger.info("Starting anomaly detection")
        
        if features_df.empty:
            logger.warning("Empty dataframe provided")
            return pd.DataFrame()
        
        # Prepare features
        feature_cols = self._get_feature_columns(features_df)
        if not feature_cols:
            logger.warning("No valid features found for anomaly detection")
            features_df['is_anomaly'] = 0
            features_df['anomaly_score'] = 0
            return features_df
        
        X = features_df[feature_cols].fillna(0)
        
        # Scale features
        X_scaled = self.scaler.fit_transform(X)
        
        # Fit and predict
        if self.model_type == 'local_outlier_factor':
            # LOF requires separate fit and predict for novelty detection
            self.model.fit(X_scaled)
            predictions = self.model.predict(X_scaled)
            anomaly_scores = -self.model.negative_outlier_factor_
        else:
            # Isolation Forest
            predictions = self.model.fit_predict(X_scaled)
            anomaly_scores = -self.model.score_samples(X_scaled)
        
        # Convert predictions: -1 = anomaly, 1 = normal
        features_df['is_anomaly'] = np.where(predictions == -1, 1, 0)
        features_df['anomaly_score'] = anomaly_scores
        
        # Calculate confidence levels
        features_df['anomaly_confidence'] = self._calculate_confidence(anomaly_scores)
        
        self.is_fitted = True
        
        anomaly_count = features_df['is_anomaly'].sum()
        logger.info(f"Detected {anomaly_count} anomalies ({anomaly_count/len(features_df)*100:.1f}%)")
        
        return features_df
    
    def _get_feature_columns(self, df: pd.DataFrame) -> List[str]:
        """Select appropriate features for anomaly detection"""
        # Priority features for anomaly detection
        priority_features = [
            'enrolment_count_sum',
            'mom_growth',
            'enrolment_zscore',
            'update_ratio',
            'volatility'
        ]
        
        # Check which priority features exist
        available_features = [f for f in priority_features if f in df.columns]
        
        # If not enough priority features, use all numeric columns
        if len(available_features) < 3:
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            # Exclude columns that are not useful
            exclude_cols = ['year', 'month', 'quarter', 'state_encoded']
            available_features = [col for col in numeric_cols if col not in exclude_cols]
        
        # Limit to 10 features to avoid curse of dimensionality
        if len(available_features) > 10:
            available_features = available_features[:10]
        
        logger.info(f"Using {len(available_features)} features for anomaly detection")
        
        return available_features
    
    def _calculate_confidence(self, scores: np.ndarray) -> np.ndarray:
        """Calculate confidence levels based on anomaly scores"""
        # Normalize scores to 0-1 range
        if len(scores) == 0 or np.std(scores) == 0:
            return np.zeros_like(scores)
        
        normalized_scores = (scores - np.min(scores)) / (np.max(scores) - np.min(scores))
        
        # Convert to confidence levels
        confidence_levels = []
        for score in normalized_scores:
            if score > 0.8:
                confidence_levels.append('VERY_HIGH')
            elif score > 0.6:
                confidence_levels.append('HIGH')
            elif score > 0.4:
                confidence_levels.append('MEDIUM')
            else:
                confidence_levels.append('LOW')
        
        return np.array(confidence_levels)
    
    def explain_anomalies(self, df: pd.DataFrame) -> pd.DataFrame:
        """Generate explanations for detected anomalies"""
        logger.info("Generating anomaly explanations")
        
        if 'is_anomaly' not in df.columns:
            return pd.DataFrame()
        
        anomalies = df[df['is_anomaly'] == 1].copy()
        
        if anomalies.empty:
            return pd.DataFrame()
        
        explanations = []
        
        for idx, row in anomalies.iterrows():
            explanation = {
                'state': row.get('state', 'Unknown'),
                'period': row.get('year_month', 'Unknown'),
                'anomaly_score': round(row.get('anomaly_score', 0), 3),
                'confidence': row.get('anomaly_confidence', 'MEDIUM'),
                'primary_reason': '',
                'supporting_factors': [],
                'recommended_action': 'Review data quality and verify with field teams'
            }
            
            # Determine primary reason based on feature values
            reasons = []
            
            # Check enrolment volume
            if 'enrolment_zscore' in row and abs(row['enrolment_zscore']) > 3:
                reasons.append(f"Extreme enrolment volume (z-score: {row['enrolment_zscore']:.2f})")
            
            # Check growth rate
            if 'mom_growth' in row and abs(row['mom_growth']) > 0.5:
                direction = "increase" if row['mom_growth'] > 0 else "decrease"
                reasons.append(f"Sudden {direction} ({abs(row['mom_growth'])*100:.1f}% change)")
            
            # Check update ratio
            if 'update_ratio' in row:
                if row['update_ratio'] > 0.5:
                    reasons.append(f"High update ratio ({row['update_ratio']:.2f})")
                elif row['update_ratio'] < 0.05:
                    reasons.append(f"Low update ratio ({row['update_ratio']:.2f})")
            
            # Check volatility
            if 'volatility' in row and row['volatility'] > 0.5:
                reasons.append(f"High volatility ({row['volatility']:.2f})")
            
            if reasons:
                explanation['primary_reason'] = reasons[0]
                explanation['supporting_factors'] = reasons[1:] if len(reasons) > 1 else []
            
            # Set recommended action based on severity
            if row.get('anomaly_score', 0) > 0.8:
                explanation['recommended_action'] = 'Immediate investigation required'
            elif row.get('anomaly_score', 0) > 0.6:
                explanation['recommended_action'] = 'Priority review recommended'
            
            explanations.append(explanation)
        
        return pd.DataFrame(explanations)