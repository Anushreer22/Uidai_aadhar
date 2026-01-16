import pandas as pd
import numpy as np
from typing import Dict
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import silhouette_score
import plotly.graph_objects as go
import plotly.express as px
import logging

logger = logging.getLogger(__name__)

class StateClusterer:
    """Cluster states based on enrolment patterns"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.n_clusters = config.get('ml', {}).get('clustering', {}).get('n_clusters', 5)
        self.kmeans = KMeans(n_clusters=self.n_clusters, random_state=42, n_init=10)
        self.scaler = StandardScaler()
        self.cluster_labels = None
        self.cluster_centers = None
    
    def cluster(self, df: pd.DataFrame) -> pd.DataFrame:
        """Perform clustering on state-level features"""
        logger.info(f"Starting clustering with {self.n_clusters} clusters")
        
        if df.empty or 'state' not in df.columns:
            logger.warning("Invalid dataframe for clustering")
            return pd.DataFrame()
        
        # Prepare state-level aggregated features
        state_features = self._prepare_state_features(df)
        
        if state_features.empty:
            logger.warning("No features available for clustering")
            return pd.DataFrame()
        
        # Scale features
        feature_cols = [col for col in state_features.columns if col != 'state']
        X = state_features[feature_cols]
        X_scaled = self.scaler.fit_transform(X)
        
        # Perform clustering
        self.cluster_labels = self.kmeans.fit_predict(X_scaled)
        self.cluster_centers = self.kmeans.cluster_centers_
        
        # Assign clusters to states
        state_features['cluster'] = self.cluster_labels
        state_features['cluster_label'] = state_features['cluster'].apply(
            lambda x: f'Cluster {x+1}'
        )
        
        # Calculate silhouette score
        if len(np.unique(self.cluster_labels)) > 1:
            silhouette_avg = silhouette_score(X_scaled, self.cluster_labels)
            logger.info(f"Clustering complete. Silhouette score: {silhouette_avg:.3f}")
        else:
            logger.info("Clustering complete (single cluster)")
        
        # Add cluster descriptions
        state_features = self._add_cluster_descriptions(state_features)
        
        return state_features
    
    def _prepare_state_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Aggregate features at state level"""
        logger.info("Preparing state-level features")
        
        # Group by state and calculate statistics
        aggregation = {}
        
        if 'enrolment_count_sum' in df.columns:
            aggregation['total_enrolments'] = ('enrolment_count_sum', 'sum')
            aggregation['avg_enrolments'] = ('enrolment_count_sum', 'mean')
            aggregation['std_enrolments'] = ('enrolment_count_sum', 'std')
        
        if 'update_count_sum' in df.columns:
            aggregation['total_updates'] = ('update_count_sum', 'sum')
            aggregation['avg_update_ratio'] = ('update_ratio', 'mean')
        
        if 'mom_growth' in df.columns:
            aggregation['avg_growth'] = ('mom_growth', 'mean')
            aggregation['growth_volatility'] = ('mom_growth', 'std')
        
        if 'anomaly_score' in df.columns:
            aggregation['anomaly_frequency'] = ('is_anomaly', 'mean')
            aggregation['avg_anomaly_score'] = ('anomaly_score', 'mean')
        
        # Age distribution features
        age_cols = ['age_0_18_sum', 'age_19_40_sum', 'age_41_60_sum', 'age_60_plus_sum']
        existing_age_cols = [col for col in age_cols if col in df.columns]
        
        for col in existing_age_cols:
            age_group = col.replace('_sum', '')
            aggregation[f'{age_group}_pct'] = (col, 'sum')
        
        # Perform aggregation
        state_features = []
        for col, (source_col, agg_func) in aggregation.items():
            if source_col in df.columns:
                if agg_func == 'sum':
                    state_feature = df.groupby('state')[source_col].sum().reset_index()
                elif agg_func == 'mean':
                    state_feature = df.groupby('state')[source_col].mean().reset_index()
                elif agg_func == 'std':
                    state_feature = df.groupby('state')[source_col].std().reset_index()
                
                state_feature.columns = ['state', col]
                
                if state_features:
                    # Merge with existing features
                    state_features[0] = pd.merge(state_features[0], state_feature, on='state', how='outer')
                else:
                    state_features.append(state_feature)
        
        if not state_features:
            return pd.DataFrame()
        
        state_features = state_features[0]
        
        # Calculate age percentages if age data exists
        if any('_pct' in col for col in state_features.columns):
            age_pct_cols = [col for col in state_features.columns if '_pct' in col]
            total_age = state_features[age_pct_cols].sum(axis=1)
            for col in age_pct_cols:
                state_features[col] = state_features[col] / total_age
        
        # Fill NaN values
        state_features = state_features.fillna(0)
        
        logger.info(f"Created {len(state_features.columns)} features for {len(state_features)} states")
        
        return state_features
    
    def _add_cluster_descriptions(self, df: pd.DataFrame) -> pd.DataFrame:
        """Add descriptive labels to clusters"""
        logger.info("Adding cluster descriptions")
        
        if 'cluster' not in df.columns:
            return df
        
        # Calculate cluster statistics
        cluster_stats = []
        feature_cols = [col for col in df.columns if col not in ['state', 'cluster', 'cluster_label']]
        
        for cluster_num in range(self.n_clusters):
            cluster_data = df[df['cluster'] == cluster_num]
            
            if cluster_data.empty:
                continue
            
            stats = {
                'cluster': cluster_num,
                'state_count': len(cluster_data),
                'states': ', '.join(cluster_data['state'].head(5).tolist())
            }
            
            # Calculate average values for key metrics
            key_metrics = ['total_enrolments', 'avg_enrolments', 'avg_update_ratio', 
                          'avg_growth', 'anomaly_frequency']
            
            for metric in key_metrics:
                if metric in cluster_data.columns:
                    stats[f'avg_{metric}'] = cluster_data[metric].mean()
            
            cluster_stats.append(stats)
        
        # Create cluster descriptions
        cluster_descriptions = []
        for stats in cluster_stats:
            desc = f"Cluster {stats['cluster']+1}: "
            
            # Determine cluster type based on metrics
            if 'avg_total_enrolments' in stats:
                if stats['avg_total_enrolments'] > df['total_enrolments'].quantile(0.75):
                    desc += "High Volume, "
                elif stats['avg_total_enrolments'] < df['total_enrolments'].quantile(0.25):
                    desc += "Low Volume, "
                else:
                    desc += "Medium Volume, "
            
            if 'avg_avg_growth' in stats:
                if stats['avg_avg_growth'] > 0.1:
                    desc += "Rapid Growth, "
                elif stats['avg_avg_growth'] < -0.05:
                    desc += "Declining, "
                else:
                    desc += "Stable, "
            
            if 'avg_anomaly_frequency' in stats:
                if stats['avg_anomaly_frequency'] > 0.2:
                    desc += "High Anomalies"
                else:
                    desc += "Low Anomalies"
            
            desc = desc.rstrip(', ')
            cluster_descriptions.append(desc)
        
        # Add descriptions to dataframe
        cluster_desc_map = {i: desc for i, desc in enumerate(cluster_descriptions)}
        df['cluster_description'] = df['cluster'].map(cluster_desc_map)
        
        return df
    
    def visualize_clusters(self, df: pd.DataFrame, output_path: str = None):
        """Create visualization of clusters"""
        if df.empty or 'cluster' not in df.columns:
            return None
        
        # Create 2D visualization using PCA
        from sklearn.decomposition import PCA
        
        feature_cols = [col for col in df.columns if col not in ['state', 'cluster', 'cluster_label', 'cluster_description']]
        X = df[feature_cols].fillna(0)
        
        # Reduce to 2D for visualization
        pca = PCA(n_components=2)
        X_2d = pca.fit_transform(X)
        
        df_vis = df.copy()
        df_vis['x'] = X_2d[:, 0]
        df_vis['y'] = X_2d[:, 1]
        
        # Create scatter plot
        fig = px.scatter(
            df_vis,
            x='x',
            y='y',
            color='cluster_label',
            hover_data=['state', 'cluster_description'],
            title='State Clustering Visualization',
            labels={'x': 'Principal Component 1', 'y': 'Principal Component 2'}
        )
        
        # Add state labels
        for idx, row in df_vis.iterrows():
            fig.add_annotation(
                x=row['x'],
                y=row['y'],
                text=row['state'],
                showarrow=False,
                font=dict(size=8)
            )
        
        if output_path:
            fig.write_html(output_path)
            logger.info(f"Cluster visualization saved to {output_path}")
        
        return fig