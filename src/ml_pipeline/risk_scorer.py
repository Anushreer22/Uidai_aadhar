import pandas as pd
import numpy as np
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

class AadhaarRiskScorer:
    """Calculate risk scores for states/regions"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.weights = config.get('ml', {}).get('risk_scoring', {}).get('weights', {})
    
    def calculate_risk_scores(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate comprehensive risk scores"""
        logger.info("Calculating risk scores")
        
        if df.empty or 'state' not in df.columns:
            logger.warning("Invalid dataframe for risk scoring")
            return pd.DataFrame()
        
        # Calculate individual risk components
        risk_components = self._calculate_risk_components(df)
        
        if risk_components.empty:
            return pd.DataFrame()
        
        # Apply weights to calculate overall risk score
        risk_components['risk_score'] = self._apply_weights(risk_components)
        
        # Categorize risk levels
        risk_components['risk_level'] = risk_components['risk_score'].apply(
            self._categorize_risk_level
        )
        
        # Add color coding
        risk_components['risk_color'] = risk_components['risk_level'].apply(
            self._get_risk_color
        )
        
        # Sort by risk score
        risk_components = risk_components.sort_values('risk_score', ascending=False)
        
        logger.info(f"Risk scoring complete. Top 3 risky states: {risk_components.head(3)['state'].tolist()}")
        
        return risk_components
    
    def _calculate_risk_components(self, df: pd.DataFrame) -> pd.DataFrame:
        """Calculate individual risk components"""
        risk_data = []
        
        # Group by state
        for state, state_data in df.groupby('state'):
            if state_data.empty:
                continue
            
            risk_entry = {'state': state}
            
            # 1. Volume Risk (based on enrolment volume)
            if 'enrolment_count_sum' in state_data.columns:
                total_enrolments = state_data['enrolment_count_sum'].sum()
                risk_entry['volume_risk'] = self._normalize_score(total_enrolments, 'volume')
            
            # 2. Anomaly Risk (based on anomaly frequency and severity)
            if 'is_anomaly' in state_data.columns:
                anomaly_freq = state_data['is_anomaly'].mean()
                risk_entry['anomaly_frequency_risk'] = self._normalize_score(anomaly_freq, 'frequency')
            
            if 'anomaly_score' in state_data.columns:
                avg_anomaly_score = state_data[state_data['is_anomaly'] == 1]['anomaly_score'].mean()
                if pd.isna(avg_anomaly_score):
                    avg_anomaly_score = 0
                risk_entry['anomaly_severity_risk'] = self._normalize_score(avg_anomaly_score, 'severity')
            
            # 3. Volatility Risk (based on growth volatility)
            if 'mom_growth' in state_data.columns:
                growth_volatility = state_data['mom_growth'].std()
                if pd.isna(growth_volatility):
                    growth_volatility = 0
                risk_entry['volatility_risk'] = self._normalize_score(growth_volatility, 'volatility')
            
            # 4. Consistency Risk (based on data completeness)
            expected_months = len(state_data['year_month'].unique())
            total_months = (state_data['date'].max() - state_data['date'].min()).days / 30
            if total_months > 0:
                completeness_ratio = expected_months / total_months
                risk_entry['consistency_risk'] = 1 - self._normalize_score(completeness_ratio, 'consistency')
            
            # 5. Update Risk (abnormal update patterns)
            if 'update_ratio' in state_data.columns:
                update_ratio_std = state_data['update_ratio'].std()
                if pd.isna(update_ratio_std):
                    update_ratio_std = 0
                risk_entry['update_pattern_risk'] = self._normalize_score(update_ratio_std, 'update_pattern')
            
            risk_data.append(risk_entry)
        
        if not risk_data:
            return pd.DataFrame()
        
        risk_df = pd.DataFrame(risk_data)
        
        # Fill NaN values with 0
        risk_df = risk_df.fillna(0)
        
        return risk_df
    
    def _normalize_score(self, value: float, component_type: str) -> float:
        """Normalize risk component to 0-1 scale"""
        if pd.isna(value):
            return 0
        
        # Component-specific normalization
        normalization_ranges = {
            'volume': (0, 10000000),  # 0-10M enrolments
            'frequency': (0, 1),      # 0-100% anomaly frequency
            'severity': (0, 1),       # 0-1 anomaly score
            'volatility': (0, 0.5),   # 0-50% growth volatility
            'consistency': (0, 1),    # 0-100% data completeness
            'update_pattern': (0, 0.3) # 0-30% update ratio std
        }
        
        min_val, max_val = normalization_ranges.get(component_type, (0, 1))
        
        # Clip value to range
        value = np.clip(value, min_val, max_val)
        
        # Normalize to 0-1
        if max_val - min_val == 0:
            return 0
        
        return (value - min_val) / (max_val - min_val)
    
    def _apply_weights(self, df: pd.DataFrame) -> pd.Series:
        """Apply weights to risk components"""
        # Default weights if not specified
        default_weights = {
            'volume_risk': 0.15,
            'anomaly_frequency_risk': 0.25,
            'anomaly_severity_risk': 0.25,
            'volatility_risk': 0.15,
            'consistency_risk': 0.10,
            'update_pattern_risk': 0.10
        }
        
        # Use configured weights or defaults
        weights = {**default_weights, **self.weights}
        
        # Calculate weighted score
        risk_score = pd.Series(0, index=df.index)
        total_weight = 0
        
        for component, weight in weights.items():
            if component in df.columns:
                risk_score += df[component] * weight
                total_weight += weight
        
        # Normalize by total weight
        if total_weight > 0:
            risk_score = risk_score / total_weight
        
        return risk_score
    
    def _categorize_risk_level(self, score: float) -> str:
        """Categorize risk score into levels"""
        if score >= 0.8:
            return 'CRITICAL'
        elif score >= 0.6:
            return 'HIGH'
        elif score >= 0.4:
            return 'MEDIUM'
        elif score >= 0.2:
            return 'LOW'
        else:
            return 'VERY_LOW'
    
    def _get_risk_color(self, level: str) -> str:
        """Get color code for risk level"""
        color_map = {
            'CRITICAL': '#DC3545',  # Red
            'HIGH': '#FD7E14',      # Orange
            'MEDIUM': '#FFC107',    # Yellow
            'LOW': '#28A745',       # Green
            'VERY_LOW': '#6C757D'   # Gray
        }
        return color_map.get(level, '#6C757D')
    
    def generate_risk_report(self, risk_df: pd.DataFrame) -> Dict:
        """Generate comprehensive risk report"""
        if risk_df.empty:
            return {}
        
        report = {
            'summary': {
                'total_states': len(risk_df),
                'critical_states': len(risk_df[risk_df['risk_level'] == 'CRITICAL']),
                'high_risk_states': len(risk_df[risk_df['risk_level'] == 'HIGH']),
                'average_risk_score': risk_df['risk_score'].mean(),
                'highest_risk_state': risk_df.iloc[0]['state'] if not risk_df.empty else None,
                'highest_risk_score': risk_df.iloc[0]['risk_score'] if not risk_df.empty else None
            },
            'critical_states': risk_df[risk_df['risk_level'] == 'CRITICAL'][['state', 'risk_score']].to_dict('records'),
            'recommendations': self._generate_recommendations(risk_df)
        }
        
        return report
    
    def _generate_recommendations(self, risk_df: pd.DataFrame) -> List[Dict]:
        """Generate recommendations based on risk levels"""
        recommendations = []
        
        # Critical states need immediate attention
        critical_states = risk_df[risk_df['risk_level'] == 'CRITICAL']
        if not critical_states.empty:
            state_list = ', '.join(critical_states['state'].head(5).tolist())
            recommendations.append({
                'priority': 'HIGH',
                'action': 'Immediate Investigation',
                'description': f'Critical risk detected in {len(critical_states)} states: {state_list}',
                'timeline': '48 hours'
            })
        
        # High risk states need priority review
        high_risk_states = risk_df[risk_df['risk_level'] == 'HIGH']
        if not high_risk_states.empty:
            recommendations.append({
                'priority': 'MEDIUM',
                'action': 'Priority Review',
                'description': f'High risk detected in {len(high_risk_states)} states',
                'timeline': '1 week'
            })
        
        # All states need monitoring
        recommendations.append({
            'priority': 'LOW',
            'action': 'Continuous Monitoring',
            'description': 'Regular monitoring of all states with monthly risk assessment',
            'timeline': 'Ongoing'
        })
        
        return recommendations