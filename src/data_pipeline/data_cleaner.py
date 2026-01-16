import pandas as pd
import numpy as np
from datetime import datetime
import re
import logging
from typing import Dict, List

logger = logging.getLogger(__name__)

class AadhaarDataCleaner:
    """Clean and standardize Aadhaar data"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.column_mappings = config['data']['column_mappings']
        
    def clean(self, df: pd.DataFrame) -> pd.DataFrame:
        """Execute complete cleaning pipeline"""
        logger.info("Starting data cleaning pipeline")
        
        # Step 1: Standardize column names
        df = self._standardize_columns(df)
        
        # Step 2: Handle missing values
        df = self._handle_missing_values(df)
        
        # Step 3: Clean and validate dates
        df = self._clean_dates(df)
        
        # Step 4: Standardize geographic data
        df = self._clean_geographic_data(df)
        
        # Step 5: Validate numeric ranges
        df = self._validate_numeric_ranges(df)
        
        # Step 6: Remove duplicates
        df = self._remove_duplicates(df)
        
        logger.info(f"Cleaning complete. Final records: {len(df)}")
        
        return df
    
    def _standardize_columns(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize column names based on mappings"""
        logger.info("Standardizing column names")
        
        column_mapping = {}
        for standard_name, possible_names in self.column_mappings.items():
            for possible_name in possible_names:
                if possible_name in df.columns:
                    column_mapping[possible_name] = standard_name
                    break
        
        if column_mapping:
            df = df.rename(columns=column_mapping)
            logger.info(f"Renamed columns: {column_mapping}")
        
        return df
    
    def _handle_missing_values(self, df: pd.DataFrame) -> pd.DataFrame:
        """Intelligent handling of missing values"""
        logger.info("Handling missing values")
        
        # Track original count
        original_count = len(df)
        
        # Handle date column
        if 'date' in df.columns:
            df = df[df['date'].notna()]
        
        # Numeric columns: fill with median
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    median_val = df[col].median()
                    df[col] = df[col].fillna(median_val)
                    logger.info(f"Filled {missing_count} missing values in {col} with median: {median_val}")
        
        # Categorical columns: fill with mode or 'Unknown'
        categorical_cols = ['state', 'district', 'pincode']
        for col in categorical_cols:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                if missing_count > 0:
                    if not df[col].mode().empty:
                        mode_val = df[col].mode()[0]
                        df[col] = df[col].fillna(mode_val)
                        logger.info(f"Filled {missing_count} missing values in {col} with mode: {mode_val}")
                    else:
                        df[col] = df[col].fillna('Unknown')
        
        # Remove rows with excessive missing data
        threshold = 0.5  # Remove if more than 50% missing
        cols_to_check = [c for c in df.columns if c not in ['source_file']]
        df = df[df[cols_to_check].isna().mean(axis=1) < threshold]
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} rows with excessive missing data")
        
        return df
    
    def _clean_dates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Clean and validate date column"""
        if 'date' not in df.columns:
            return df
        
        logger.info("Cleaning date column")
        
        # Convert to datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce', infer_datetime_format=True)
        
        # Filter invalid dates
        original_count = len(df)
        df = df[df['date'].notna()]
        
        # Ensure dates are within reasonable range (Aadhaar started in 2009)
        df = df[df['date'] >= pd.Timestamp('2009-01-01')]
        df = df[df['date'] <= pd.Timestamp.now()]
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} rows with invalid dates")
        
        return df
    
    def _clean_geographic_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize state and district names"""
        logger.info("Cleaning geographic data")
        
        if 'state' in df.columns:
            # Standardize state names
            state_corrections = {
                'DELHI': 'NCT of Delhi',
                'NEW DELHI': 'NCT of Delhi',
                'PONDICHERRY': 'Puducherry',
                'ORISSA': 'Odisha',
                'UTTARANCHAL': 'Uttarakhand',
                'JAMMU & KASHMIR': 'Jammu and Kashmir'
            }
            
            # Convert to title case and apply corrections
            df['state'] = df['state'].str.title()
            df['state'] = df['state'].replace(state_corrections)
        
        if 'district' in df.columns:
            # Clean district names
            df['district'] = df['district'].str.title()
            df['district'] = df['district'].str.replace(r'[^a-zA-Z\s]', '', regex=True)
        
        if 'pincode' in df.columns:
            # Clean pincode (6 digits)
            df['pincode'] = df['pincode'].astype(str).str.strip()
            df['pincode'] = df['pincode'].str.extract(r'(\d{6})')[0]
        
        return df
    
    def _validate_numeric_ranges(self, df: pd.DataFrame) -> pd.DataFrame:
        """Validate numeric columns are within reasonable ranges"""
        logger.info("Validating numeric ranges")
        
        # Enrolment count validation
        if 'enrolment_count' in df.columns:
            # Remove negative values and extreme outliers
            df = df[df['enrolment_count'] >= 0]
            # Cap at reasonable maximum (1M per day per state)
            df['enrolment_count'] = df['enrolment_count'].clip(upper=1000000)
        
        # Update count validation
        if 'update_count' in df.columns:
            df = df[df['update_count'] >= 0]
            # Updates shouldn't exceed enrolments
            if 'enrolment_count' in df.columns:
                mask = df['update_count'] <= df['enrolment_count'] * 5  # Allow up to 5x
                df = df[mask]
        
        # Age group validation
        age_columns = ['age_0_18', 'age_19_40', 'age_41_60', 'age_60_plus']
        existing_age_cols = [col for col in age_columns if col in df.columns]
        
        if existing_age_cols:
            # Ensure non-negative
            for col in existing_age_cols:
                df[col] = df[col].clip(lower=0)
            
            # Ensure sum doesn't exceed enrolment count
            if 'enrolment_count' in df.columns:
                age_sum = df[existing_age_cols].sum(axis=1)
                df = df[age_sum <= df['enrolment_count'] * 1.1]  # Allow 10% tolerance
        
        return df
    
    def _remove_duplicates(self, df: pd.DataFrame) -> pd.DataFrame:
        """Remove duplicate records"""
        logger.info("Removing duplicates")
        
        original_count = len(df)
        
        # Define duplicate columns
        duplicate_cols = ['date', 'state', 'district']
        existing_cols = [col for col in duplicate_cols if col in df.columns]
        
        if existing_cols:
            df = df.drop_duplicates(subset=existing_cols, keep='first')
        
        removed_count = original_count - len(df)
        if removed_count > 0:
            logger.info(f"Removed {removed_count} duplicate records")
        
        return df