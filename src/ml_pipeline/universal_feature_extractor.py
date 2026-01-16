# src/ml_pipeline/universal_feature_extractor.py
import pandas as pd
import numpy as np
from datetime import datetime
from typing import Dict
import warnings
warnings.filterwarnings('ignore')

class UniversalFeatureExtractor:
    """
    Extract features from ANY dataset automatically
    """
    
    def extract_all_features(self, df: pd.DataFrame) -> Dict:
        """
        Extract ALL possible features from any dataset
        """
        print("🔧 Extracting features from dataset...")
        
        features = {
            'temporal': {},
            'geographic': {},
            'demographic': {},
            'statistical': {},
            'anomaly': {},
            'clustering': {}
        }
        
        # 1. TEMPORAL FEATURES (if date exists)
        if 'date' in df.columns:
            features['temporal'] = self._extract_temporal_features(df)
            print(f"   ✓ Temporal features: {len(features['temporal'])}")
        
        # 2. GEOGRAPHIC FEATURES (if state/district exists)
        geographic_features = self._extract_geographic_features(df)
        if geographic_features:
            features['geographic'] = geographic_features
            print(f"   ✓ Geographic features: {len(geographic_features)}")
        
        # 3. DEMOGRAPHIC FEATURES (if age groups exist)
        demographic_features = self._extract_demographic_features(df)
        if demographic_features:
            features['demographic'] = demographic_features
            print(f"   ✓ Demographic features: {len(demographic_features)}")
        
        # 4. STATISTICAL FEATURES (always available)
        features['statistical'] = self._extract_statistical_features(df)
        print(f"   ✓ Statistical features: {len(features['statistical'])}")
        
        # 5. AUTOMATIC ANOMALY DETECTION FEATURES
        features['anomaly'] = self._extract_anomaly_features(df)
        print(f"   ✓ Anomaly detection features: {len(features['anomaly'])}")
        
        # 6. CLUSTERING FEATURES
        features['clustering'] = self._extract_clustering_features(df)
        print(f"   ✓ Clustering features: {len(features['clustering'])}")
        
        total_features = sum(len(v) for v in features.values() if isinstance(v, dict))
        print(f"✅ Total features extracted: {total_features}")
        
        return features
    
    def _extract_temporal_features(self, df: pd.DataFrame) -> Dict:
        """Extract time-based features"""
        features = {}
        
        try:
            # Basic time features
            df_temp = df.copy()
            df_temp['date'] = pd.to_datetime(df_temp['date'])
            
            features['year'] = df_temp['date'].dt.year.tolist()
            features['month'] = df_temp['date'].dt.month.tolist()
            features['day_of_week'] = df_temp['date'].dt.dayofweek.tolist()
            features['is_weekend'] = (df_temp['date'].dt.dayofweek >= 5).astype(int).tolist()
            
            # Seasonal features
            features['quarter'] = df_temp['date'].dt.quarter.tolist()
            features['is_month_start'] = df_temp['date'].dt.is_month_start.astype(int).tolist()
            features['is_month_end'] = df_temp['date'].dt.is_month_end.astype(int).tolist()
            
            # Time gaps if multiple dates
            if len(df_temp['date'].unique()) > 1:
                date_diff = df_temp['date'].diff().dt.days
                features['days_since_previous'] = date_diff.tolist()
            
        except Exception as e:
            print(f"   ⚠️ Temporal feature extraction error: {e}")
        
        return features
    
    def _extract_geographic_features(self, df: pd.DataFrame) -> Dict:
        """Extract location-based features"""
        features = {}
        
        # State features
        if 'state' in df.columns:
            features['state_counts'] = df['state'].value_counts().to_dict()
            features['unique_states'] = df['state'].nunique()
            features['state_frequency'] = (df['state'].value_counts() / len(df)).to_dict()
        
        # District features
        if 'district' in df.columns:
            features['district_counts'] = df['district'].value_counts().to_dict()
            features['unique_districts'] = df['district'].nunique()
        
        # Geographic patterns
        if 'state' in df.columns and 'enrolment_count' in df.columns:
            state_totals = df.groupby('state')['enrolment_count'].sum().to_dict()
            features['state_totals'] = state_totals
            
            # Top states
            top_states = dict(sorted(state_totals.items(), key=lambda x: x[1], reverse=True)[:5])
            features['top_states'] = top_states
        
        return features
    
    def _extract_demographic_features(self, df: pd.DataFrame) -> Dict:
        """Extract age group features"""
        features = {}
        
        age_columns = []
        for col in df.columns:
            if 'age' in col.lower() or any(str(i) in col for i in range(0, 100)):
                age_columns.append(col)
        
        if age_columns:
            features['age_columns_found'] = age_columns
            
            # Calculate age distribution
            for age_col in age_columns:
                if age_col in df.columns:
                    total = df[age_col].sum()
                    if total > 0:
                        features[f'{age_col}_total'] = total
                        features[f'{age_col}_percentage'] = (total / df['enrolment_count'].sum() * 100) if 'enrolment_count' in df.columns else None
            
            # Age group ratios
            if len(age_columns) >= 2:
                for i in range(len(age_columns)-1):
                    col1, col2 = age_columns[i], age_columns[i+1]
                    if col1 in df.columns and col2 in df.columns:
                        ratio = df[col1].sum() / df[col2].sum() if df[col2].sum() > 0 else 0
                        features[f'{col1}_to_{col2}_ratio'] = ratio
        
        return features
    
    def _extract_statistical_features(self, df: pd.DataFrame) -> Dict:
        """Extract statistical features from numeric columns"""
        features = {}
        
        # Find numeric columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        
        for col in numeric_cols:
            if col in df.columns and df[col].notna().any():
                features[f'{col}_mean'] = df[col].mean()
                features[f'{col}_median'] = df[col].median()
                features[f'{col}_std'] = df[col].std()
                features[f'{col}_min'] = df[col].min()
                features[f'{col}_max'] = df[col].max()
                features[f'{col}_sum'] = df[col].sum()
                
                # Skewness and kurtosis
                from scipy.stats import skew, kurtosis
                features[f'{col}_skewness'] = skew(df[col].dropna())
                features[f'{col}_kurtosis'] = kurtosis(df[col].dropna())
                
                # Percentiles
                for p in [25, 50, 75, 90, 95]:
                    features[f'{col}_percentile_{p}'] = np.percentile(df[col].dropna(), p)
        
        # Correlation between numeric columns
        if len(numeric_cols) > 1:
            corr_matrix = df[numeric_cols].corr()
            for i in range(len(numeric_cols)):
                for j in range(i+1, len(numeric_cols)):
                    col1, col2 = numeric_cols[i], numeric_cols[j]
                    features[f'corr_{col1}_{col2}'] = corr_matrix.loc[col1, col2]
        
        return features
    
    def _extract_anomaly_features(self, df: pd.DataFrame) -> Dict:
        """Extract features for anomaly detection"""
        features = {}
        
        # Find primary count column
        count_columns = [col for col in df.columns if any(word in col.lower() 
                         for word in ['count', 'total', 'sum', 'number', 'enrol'])]
        
        if count_columns:
            primary_col = count_columns[0]
            
            # Statistical anomaly features
            values = df[primary_col].dropna()
            if len(values) > 0:
                mean = values.mean()
                std = values.std()
                
                if std > 0:
                    # Z-scores
                    z_scores = (values - mean) / std
                    features['z_scores'] = z_scores.tolist()
                    
                    # Outliers (beyond 2 std)
                    outliers = (abs(z_scores) > 2).sum()
                    features['outlier_count'] = outliers
                    features['outlier_percentage'] = (outliers / len(values)) * 100
                    
                    # Extreme outliers (beyond 3 std)
                    extreme_outliers = (abs(z_scores) > 3).sum()
                    features['extreme_outlier_count'] = extreme_outliers
                
                # IQR method
                Q1 = values.quantile(0.25)
                Q3 = values.quantile(0.75)
                IQR = Q3 - Q1
                
                lower_bound = Q1 - 1.5 * IQR
                upper_bound = Q3 + 1.5 * IQR
                
                iqr_outliers = ((values < lower_bound) | (values > upper_bound)).sum()
                features['iqr_outlier_count'] = iqr_outliers
        
        # Temporal anomalies (if date exists)
        if 'date' in df.columns and primary_col:
            try:
                df_temp = df.copy()
                df_temp['date'] = pd.to_datetime(df_temp['date'])
                df_temp = df_temp.sort_values('date')
                
                # Moving average anomalies
                window = min(7, len(df_temp))
                if window > 1:
                    ma = df_temp[primary_col].rolling(window=window, min_periods=1).mean()
                    residuals = df_temp[primary_col] - ma
                    
                    if residuals.std() > 0:
                        residual_z = (residuals - residuals.mean()) / residuals.std()
                        temporal_outliers = (abs(residual_z) > 2).sum()
                        features['temporal_outlier_count'] = temporal_outliers
            except:
                pass
        
        return features
    
    def _extract_clustering_features(self, df: pd.DataFrame) -> Dict:
        """Extract features for clustering"""
        features = {}
        
        # Grouping features if geographic data exists
        if 'state' in df.columns:
            # State-level aggregation features
            if 'enrolment_count' in df.columns:
                state_features = df.groupby('state').agg({
                    'enrolment_count': ['count', 'sum', 'mean', 'std']
                }).reset_index()
                
                state_features.columns = ['state', 'record_count', 'total_enrolments', 
                                         'avg_enrolments', 'std_enrolments']
                
                features['state_aggregates'] = state_features.to_dict('records')
                
                # Calculate state similarity matrix
                state_pivot = df.pivot_table(values='enrolment_count', 
                                            index='date' if 'date' in df.columns else None,
                                            columns='state', 
                                            aggfunc='sum').fillna(0)
                
                if not state_pivot.empty:
                    from sklearn.metrics.pairwise import cosine_similarity
                    similarity = cosine_similarity(state_pivot.T)
                    
                    features['state_similarity_matrix'] = similarity.tolist()
                    features['state_similarity_pairs'] = []
                    
                    # Get top similar state pairs
                    n_states = len(state_pivot.columns)
                    for i in range(n_states):
                        for j in range(i+1, n_states):
                            state1 = state_pivot.columns[i]
                            state2 = state_pivot.columns[j]
                            sim_score = similarity[i, j]
                            features['state_similarity_pairs'].append({
                                'state1': state1,
                                'state2': state2,
                                'similarity': float(sim_score)
                            })
                    
                    # Sort by similarity
                    features['state_similarity_pairs'].sort(key=lambda x: x['similarity'], reverse=True)
        
        return features