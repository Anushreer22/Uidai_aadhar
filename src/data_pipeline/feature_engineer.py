# src/data_pipeline/feature_engineer.py
import pandas as pd
import numpy as np
from datetime import datetime
import logging
from typing import Tuple, Dict

logger = logging.getLogger(__name__)

class AadhaarFeatureEngineer:
    """Create features for analysis and ML"""
    
    def __init__(self, config: Dict):
        self.config = config
    
    def create_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
        """Create all features from cleaned data"""
        logger.info("Creating features")
        
        if df.empty:
            logger.warning("Empty dataframe provided")
            return pd.DataFrame(), pd.DataFrame(), pd.DataFrame()
        
        # Step 1: Create time-based features
        df_with_time = self._create_time_features(df)
        
        # Step 2: Create aggregated metrics
        aggregated_df = self._create_aggregated_features(df_with_time)
        
        # Step 3: Create ML-ready features
        ml_df = self._create_ml_features(aggregated_df)
        
        logger.info(f"Feature engineering complete.")
        logger.info(f"  - Processed data: {len(df_with_time)} records")
        logger.info(f"  - Aggregated data: {len(aggregated_df)} records")
        logger.info(f"  - ML data: {len(ml_df)} records with {ml_df.shape[1]} features")
        
        return df_with_time, aggregated_df, ml_df
    
    def _create_time_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Extract temporal patterns from date"""
        logger.info("Creating time-based features")
        
        if 'date' not in df.columns:
            logger.warning("No date column found")
            return df
        
        df = df.copy()
        
        # Basic time features
        df['year'] = df['date'].dt.year
        df['month'] = df['date'].dt.month
        df['day_of_week'] = df['date'].dt.dayofweek
        df['is_weekend'] = (df['day_of_week'] >= 5).astype(int)
        
        return df
    
    def _create_aggregated_features(self, df: pd.DataFrame) -> pd.DataFrame:
        """Create state-level monthly aggregates"""
        logger.info("Creating aggregated features")
        
        if 'state' not in df.columns or 'date' not in df.columns:
            logger.warning("Missing required columns for aggregation")
            return pd.DataFrame()
        
        # Create year-month column
        df['year_month'] = df['date'].dt.to_period('M')
        
        # Group by state and month
        agg_dict = {}
        
        # Count enrolment column
        enrolment_col = None
        for col in ['enrolment_count', 'Total_Enrolments', 'enrolments']:
            if col in df.columns:
                enrolment_col = col
                break
        
        if enrolment_col:
            agg_dict[enrolment_col] = ['sum', 'mean', 'std']
        
        # Count update column
        update_col = None
        for col in ['update_count', 'Total_Updates', 'updates']:
            if col in df.columns:
                update_col = col
                break
        
        if update_col:
            agg_dict[update_col] = 'sum'
        
        if not agg_dict:
            logger.warning("No numeric columns found for aggregation")
            # Try to find any numeric columns
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            for col in numeric_cols[:2]:  # Take first 2 numeric columns
                agg_dict[col] = 'sum'
        
        if not agg_dict:
            return pd.DataFrame()
        
        # Perform aggregation
        aggregated = df.groupby(['state', 'year_month']).agg(agg_dict)
        
        # Flatten column names
        if isinstance(aggregated.columns, pd.MultiIndex):
            aggregated.columns = ['_'.join(col).strip() for col in aggregated.columns.values]
        
        aggregated = aggregated.reset_index()
        
        # Convert year_month to string
        aggregated['year_month'] = aggregated['year_month'].astype(str)
        
        # Calculate derived metrics
        sum_cols = [col for col in aggregated.columns if '_sum' in col]
        if sum_cols:
            primary_sum = sum_cols[0]  # Use first sum column
            
            # Month-over-month growth
            aggregated['mom_growth'] = aggregated.groupby('state')[primary_sum].pct_change()
            
            # Z-score
            aggregated['z_score'] = aggregated.groupby('state')[primary_sum].transform(
                lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
            )
            
            # Update ratio if we have both enrolment and update sums
            if len(sum_cols) >= 2:
                enrolment_sum = sum_cols[0]
                update_sum = sum_cols[1]
                aggregated['update_ratio'] = aggregated[update_sum] / aggregated[enrolment_sum].replace(0, 1)
        
        logger.info(f"Aggregated {len(aggregated)} state-month records")
        return aggregated
    
    def _create_ml_features(self, aggregated_df: pd.DataFrame) -> pd.DataFrame:
        """Create features for machine learning models"""
        logger.info("Creating ML features")
        
        if aggregated_df.empty:
            logger.warning("Empty aggregated dataframe")
            return pd.DataFrame()
        
        if len(aggregated_df) < 10:
            logger.warning(f"Not enough data for ML: {len(aggregated_df)} records")
            return pd.DataFrame()
        
        ml_df = aggregated_df.copy()
        
        # Ensure we have required columns
        required_cols = ['state', 'year_month']
        if not all(col in ml_df.columns for col in required_cols):
            logger.warning(f"Missing required columns: {required_cols}")
            return pd.DataFrame()
        
        # Create date from year_month
        try:
            ml_df['date'] = pd.to_datetime(ml_df['year_month'] + '-01')
        except:
            ml_df['date'] = pd.to_datetime(ml_df['year_month'])
        
        # Find numeric columns for features
        numeric_cols = ml_df.select_dtypes(include=[np.number]).columns.tolist()
        numeric_cols = [col for col in numeric_cols if col not in ['year', 'month', 'quarter']]
        
        if len(numeric_cols) < 3:
            logger.warning(f"Not enough numeric columns for ML: {numeric_cols}")
            # Create some basic features
            if 'mom_growth' in ml_df.columns:
                numeric_cols.append('mom_growth')
            if 'z_score' in ml_df.columns:
                numeric_cols.append('z_score')
        
        # Create lag features for the primary metric
        sum_cols = [col for col in ml_df.columns if '_sum' in col]
        if sum_cols:
            primary_metric = sum_cols[0]
            for lag in [1, 2, 3]:
                ml_df[f'lag_{lag}'] = ml_df.groupby('state')[primary_metric].shift(lag)
                numeric_cols.append(f'lag_{lag}')
        
        # Create month feature
        ml_df['month'] = ml_df['date'].dt.month
        numeric_cols.append('month')
        
        # State encoding
        from sklearn.preprocessing import LabelEncoder
        le = LabelEncoder()
        ml_df['state_code'] = le.fit_transform(ml_df['state'])
        numeric_cols.append('state_code')
        
        # Keep only selected columns
        keep_cols = ['state', 'year_month', 'date'] + numeric_cols
        ml_df = ml_df[keep_cols]
        
        # Drop rows with NaN values
        ml_df = ml_df.dropna()
        
        logger.info(f"Created ML features: {ml_df.shape}")
        
        return ml_df