import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any
import json
import logging

logger = logging.getLogger(__name__)

class AadhaarInsightGenerator:
    """Generate actionable insights from analysis results"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def generate_all_insights(self, 
                            cleaned_data: pd.DataFrame,
                            aggregated_data: pd.DataFrame,
                            anomalies: pd.DataFrame,
                            risk_scores: pd.DataFrame,
                            clusters: pd.DataFrame) -> Dict[str, Any]:
        """Generate comprehensive insights"""
        logger.info("Generating insights")
        
        insights = {
            'metadata': {
                'generated_at': datetime.now().isoformat(),
                'data_period': self._get_data_period(cleaned_data),
                'total_records': len(cleaned_data),
                'states_covered': len(cleaned_data['state'].unique()) if 'state' in cleaned_data.columns else 0
            },
            'executive_summary': self._generate_executive_summary(aggregated_data, anomalies, risk_scores),
            'trend_insights': self._generate_trend_insights(aggregated_data),
            'anomaly_insights': self._generate_anomaly_insights(anomalies),
            'risk_insights': self._generate_risk_insights(risk_scores),
            'cluster_insights': self._generate_cluster_insights(clusters),
            'recommendations': self._generate_recommendations(aggregated_data, anomalies, risk_scores)
        }
        
        logger.info(f"Generated {len(insights['recommendations'])} recommendations")
        
        return insights
    
    def _get_data_period(self, df: pd.DataFrame) -> Dict:
        """Get data period information"""
        if 'date' not in df.columns:
            return {'start': None, 'end': None, 'duration_days': 0}
        
        start_date = df['date'].min()
        end_date = df['date'].max()
        duration = (end_date - start_date).days
        
        return {
            'start': start_date.strftime('%Y-%m-%d'),
            'end': end_date.strftime('%Y-%m-%d'),
            'duration_days': duration
        }
    
    def _generate_executive_summary(self, aggregated_data: pd.DataFrame, 
                                  anomalies: pd.DataFrame, 
                                  risk_scores: pd.DataFrame) -> Dict:
        """Generate executive summary"""
        summary = {}
        
        # Overall statistics
        if 'enrolment_count_sum' in aggregated_data.columns:
            total_enrolments = aggregated_data['enrolment_count_sum'].sum()
            avg_monthly = aggregated_data.groupby('year_month')['enrolment_count_sum'].sum().mean()
            summary['total_enrolments'] = total_enrolments
            summary['avg_monthly_enrolments'] = avg_monthly
        
        # Growth statistics
        if 'mom_growth' in aggregated_data.columns:
            avg_growth = aggregated_data['mom_growth'].mean() * 100
            growth_trend = "positive" if avg_growth > 0 else "negative"
            summary['avg_growth_rate'] = f"{avg_growth:.1f}%"
            summary['growth_trend'] = growth_trend
        
        # Anomaly statistics
        if 'is_anomaly' in anomalies.columns:
            anomaly_count = anomalies['is_anomaly'].sum()
            anomaly_rate = anomaly_count / len(anomalies) * 100
            summary['anomalies_detected'] = anomaly_count
            summary['anomaly_rate'] = f"{anomaly_rate:.1f}%"
        
        # Risk statistics
        if not risk_scores.empty:
            critical_count = len(risk_scores[risk_scores['risk_level'] == 'CRITICAL'])
            high_count = len(risk_scores[risk_scores['risk_level'] == 'HIGH'])
            summary['critical_risk_states'] = critical_count
            summary['high_risk_states'] = high_count
        
        # Key findings
        summary['key_findings'] = []
        
        if 'total_enrolments' in summary and summary['total_enrolments'] > 10000000:
            summary['key_findings'].append("Large-scale enrolment operations detected")
        
        if 'anomaly_rate' in summary and anomaly_rate > 5:
            summary['key_findings'].append("Higher than expected anomaly rate")
        
        if 'critical_risk_states' in summary and critical_count > 0:
            summary['key_findings'].append(f"{critical_count} states require immediate attention")
        
        return summary
    
    def _generate_trend_insights(self, aggregated_data: pd.DataFrame) -> List[Dict]:
        """Generate trend-based insights"""
        insights = []
        
        if aggregated_data.empty:
            return insights
        
        # 1. Overall trend insight
        if 'enrolment_count_sum' in aggregated_data.columns:
            monthly_totals = aggregated_data.groupby('year_month')['enrolment_count_sum'].sum()
            if len(monthly_totals) > 1:
                latest = monthly_totals.iloc[-1]
                previous = monthly_totals.iloc[-2]
                growth_pct = ((latest - previous) / previous * 100) if previous > 0 else 0
                
                if abs(growth_pct) > 10:
                    direction = "increased" if growth_pct > 0 else "decreased"
                    insights.append({
                        'type': 'trend',
                        'title': f'Significant Monthly {direction.title()}',
                        'description': f'Enrolments {direction} by {abs(growth_pct):.1f}% from previous month',
                        'severity': 'HIGH' if abs(growth_pct) > 20 else 'MEDIUM',
                        'confidence': 'HIGH'
                    })
        
        # 2. Seasonal pattern insight
        if 'month' in aggregated_data.columns:
            monthly_avg = aggregated_data.groupby('month')['enrolment_count_sum'].mean()
            if not monthly_avg.empty:
                peak_month = monthly_avg.idxmax()
                trough_month = monthly_avg.idxmin()
                peak_value = monthly_avg.max()
                trough_value = monthly_avg.min()
                
                if peak_value > trough_value * 1.5:  # 50% difference
                    month_names = ['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 
                                  'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec']
                    insights.append({
                        'type': 'seasonality',
                        'title': 'Clear Seasonal Pattern Detected',
                        'description': f'Peak in {month_names[peak_month-1]}, lowest in {month_names[trough_month-1]}',
                        'severity': 'MEDIUM',
                        'confidence': 'HIGH'
                    })
        
        # 3. State performance insight
        if 'state' in aggregated_data.columns and 'enrolment_count_sum' in aggregated_data.columns:
            state_totals = aggregated_data.groupby('state')['enrolment_count_sum'].sum()
            if len(state_totals) > 1:
                top_state = state_totals.nlargest(1).index[0]
                bottom_state = state_totals.nsmallest(1).index[0]
                
                if state_totals[top_state] > state_totals[bottom_state] * 10:  # 10x difference
                    insights.append({
                        'type': 'performance',
                        'title': 'Significant State Disparity',
                        'description': f'{top_state} has significantly higher enrolments than {bottom_state}',
                        'severity': 'MEDIUM',
                        'confidence': 'HIGH'
                    })
        
        return insights
    
    def _generate_anomaly_insights(self, anomalies: pd.DataFrame) -> List[Dict]:
        """Generate insights from anomalies"""
        insights = []
        
        if anomalies.empty or 'is_anomaly' not in anomalies.columns:
            return insights
        
        anomaly_data = anomalies[anomalies['is_anomaly'] == 1]
        
        if anomaly_data.empty:
            return insights
        
        # 1. Temporal clustering of anomalies
        if 'date' in anomaly_data.columns:
            anomaly_data['month'] = pd.to_datetime(anomaly_data['date']).dt.to_period('M')
            monthly_counts = anomaly_data.groupby('month').size()
            
            if not monthly_counts.empty:
                peak_month = monthly_counts.idxmax()
                peak_count = monthly_counts.max()
                
                if peak_count > monthly_counts.mean() * 2:  # 2x above average
                    insights.append({
                        'type': 'temporal_anomaly',
                        'title': 'Anomaly Cluster Detected',
                        'description': f'Concentration of anomalies in {peak_month} ({peak_count} anomalies)',
                        'severity': 'HIGH',
                        'confidence': 'MEDIUM'
                    })
        
        # 2. Geographic concentration of anomalies
        if 'state' in anomaly_data.columns:
            state_counts = anomaly_data.groupby('state').size()
            if not state_counts.empty:
                top_state = state_counts.nlargest(1).index[0]
                top_count = state_counts.max()
                
                if top_count > state_counts.mean() * 3:  # 3x above average
                    insights.append({
                        'type': 'geographic_anomaly',
                        'title': 'Geographic Anomaly Concentration',
                        'description': f'{top_state} has {top_count} anomalies, significantly above average',
                        'severity': 'HIGH',
                        'confidence': 'HIGH'
                    })
        
        # 3. High severity anomalies
        if 'anomaly_score' in anomaly_data.columns:
            high_severity = anomaly_data[anomaly_data['anomaly_score'] > 0.8]
            if len(high_severity) > 0:
                insights.append({
                    'type': 'severity',
                    'title': 'High Severity Anomalies Detected',
                    'description': f'{len(high_severity)} anomalies with very high severity scores',
                    'severity': 'CRITICAL',
                    'confidence': 'HIGH'
                })
        
        return insights
    
    def _generate_risk_insights(self, risk_scores: pd.DataFrame) -> List[Dict]:
        """Generate insights from risk scores"""
        insights = []
        
        if risk_scores.empty:
            return insights
        
        # 1. Critical risk states
        critical_states = risk_scores[risk_scores['risk_level'] == 'CRITICAL']
        if not critical_states.empty:
            state_list = ', '.join(critical_states['state'].head(3).tolist())
            insights.append({
                'type': 'risk',
                'title': 'Critical Risk States Identified',
                'description': f'{len(critical_states)} states at critical risk level: {state_list}',
                'severity': 'CRITICAL',
                'confidence': 'HIGH'
            })
        
        # 2. Risk concentration
        if 'risk_score' in risk_scores.columns:
            risk_std = risk_scores['risk_score'].std()
            if risk_std > 0.3:  # High variability
                insights.append({
                    'type': 'risk_distribution',
                    'title': 'Wide Risk Distribution',
                    'description': 'Significant variability in risk scores across states',
                    'severity': 'MEDIUM',
                    'confidence': 'HIGH'
                })
        
        return insights
    
    def _generate_cluster_insights(self, clusters: pd.DataFrame) -> List[Dict]:
        """Generate insights from clustering"""
        insights = []
        
        if clusters.empty or 'cluster' not in clusters.columns:
            return insights
        
        # 1. Cluster size imbalance
        cluster_sizes = clusters['cluster'].value_counts()
        if len(cluster_sizes) > 1:
            largest = cluster_sizes.max()
            smallest = cluster_sizes.min()
            
            if largest > smallest * 5:  # 5x difference
                insights.append({
                    'type': 'cluster_imbalance',
                    'title': 'Uneven State Distribution Across Clusters',
                    'description': f'Largest cluster has {largest} states, smallest has {smallest}',
                    'severity': 'LOW',
                    'confidence': 'HIGH'
                })
        
        # 2. High-performing cluster
        if 'total_enrolments' in clusters.columns:
            cluster_avg = clusters.groupby('cluster')['total_enrolments'].mean()
            if not cluster_avg.empty:
                top_cluster = cluster_avg.idxmax()
                top_avg = cluster_avg.max()
                bottom_avg = cluster_avg.min()
                
                if top_avg > bottom_avg * 2:  # 2x difference
                    insights.append({
                        'type': 'cluster_performance',
                        'title': 'High-Performance Cluster Identified',
                        'description': f'Cluster {top_cluster+1} shows significantly higher enrolment volumes',
                        'severity': 'MEDIUM',
                        'confidence': 'HIGH'
                    })
        
        return insights
    
    def _generate_recommendations(self, aggregated_data: pd.DataFrame,
                                anomalies: pd.DataFrame,
                                risk_scores: pd.DataFrame) -> List[Dict]:
        """Generate actionable recommendations"""
        recommendations = []
        
        # 1. Based on anomalies
        if 'is_anomaly' in anomalies.columns:
            anomaly_count = anomalies['is_anomaly'].sum()
            if anomaly_count > 0:
                recommendations.append({
                    'category': 'Data Quality',
                    'action': 'Anomaly Investigation',
                    'description': f'Investigate {anomaly_count} detected anomalies',
                    'priority': 'HIGH' if anomaly_count > 50 else 'MEDIUM',
                    'timeline': '2 weeks',
                    'responsible': 'Data Quality Team'
                })
        
        # 2. Based on risk scores
        if not risk_scores.empty:
            critical_states = risk_scores[risk_scores['risk_level'] == 'CRITICAL']
            if not critical_states.empty():
                state_list = ', '.join(critical_states['state'].head(3).tolist())
                recommendations.append({
                    'category': 'Risk Management',
                    'action': 'Immediate Risk Mitigation',
                    'description': f'Address critical risk in {len(critical_states)} states: {state_list}',
                    'priority': 'CRITICAL',
                    'timeline': '48 hours',
                    'responsible': 'Risk Management Team'
                })
        
        # 3. Based on trends
        if 'mom_growth' in aggregated_data.columns:
            negative_growth = aggregated_data[aggregated_data['mom_growth'] < -0.1]  # >10% decline
            if not negative_growth.empty:
                recommendations.append({
                    'category': 'Operations',
                    'action': 'Performance Review',
                    'description': 'Review operations in regions showing negative growth',
                    'priority': 'MEDIUM',
                    'timeline': '1 month',
                    'responsible': 'Operations Team'
                })
        
        # 4. General recommendations
        recommendations.extend([
            {
                'category': 'Monitoring',
                'action': 'Regular Dashboard Review',
                'description': 'Review dashboard metrics weekly for early issue detection',
                'priority': 'LOW',
                'timeline': 'Weekly',
                'responsible': 'All Teams'
            },
            {
                'category': 'Improvement',
                'action': 'Model Retraining',
                'description': 'Retrain ML models quarterly with latest data',
                'priority': 'MEDIUM',
                'timeline': 'Quarterly',
                'responsible': 'Data Science Team'
            }
        ])
        
        return recommendations
    
    def save_insights(self, insights: Dict, output_path: str):
        """Save insights to JSON file"""
        with open(output_path, 'w') as f:
            json.dump(insights, f, indent=2, default=str)
        
        logger.info(f"Insights saved to {output_path}")