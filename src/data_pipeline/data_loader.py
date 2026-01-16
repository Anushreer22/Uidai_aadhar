# src/data_pipeline/data_loader.py
import pandas as pd
import numpy as np
import os
import glob
import logging
from typing import List, Dict, Optional

logger = logging.getLogger(__name__)

class AadhaarDataLoader:
    """Load Aadhaar enrolment and update datasets"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.raw_path = config['data']['raw_path']
        
    def load_all_files(self) -> pd.DataFrame:
        """Load all CSV files from raw directory"""
        all_files = glob.glob(os.path.join(self.raw_path, "*.csv"))
        
        if not all_files:
            logger.warning(f"No CSV files found in {self.raw_path}")
            return self._create_better_sample_data()
        
        data_frames = []
        for file in all_files:
            try:
                df = self._load_single_file(file)
                data_frames.append(df)
                logger.info(f"Loaded {len(df)} records from {file}")
            except Exception as e:
                logger.error(f"Error loading {file}: {e}")
        
        if not data_frames:
            raise ValueError("No data files could be loaded")
        
        # Combine all data
        combined_df = pd.concat(data_frames, ignore_index=True)
        logger.info(f"Combined total: {len(combined_df)} records")
        
        return combined_df
    
    def _load_single_file(self, filepath: str) -> pd.DataFrame:
        """Load a single CSV file"""
        try:
            df = pd.read_csv(filepath, low_memory=False)
            return df
        except Exception as e:
            logger.error(f"Failed to load {filepath}: {e}")
            raise
    
    def _create_better_sample_data(self) -> pd.DataFrame:
        """Create better sample data with proper column names"""
        logger.info("Creating better sample data for demonstration")
        
        # Create sample data with the expected column names
        states = ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 'Delhi']
        
        # Generate 6 months of daily data
        dates = pd.date_range('2023-01-01', '2023-06-30', freq='D')
        
        data = []
        for date in dates:
            for state in states:
                # Base enrolments
                base = np.random.randint(1000, 5000)
                
                # Add anomalies
                if state == 'Maharashtra' and date.month == 3:
                    base = int(base * 2.5)  # March anomaly
                elif state == 'Delhi' and date.month == 4:
                    base = int(base * 3.0)  # April anomaly
                elif state == 'Karnataka' and date.month == 5:
                    base = int(base * 0.4)  # May drop
                
                record = {
                    'Date': date.strftime('%Y-%m-%d'),
                    'State_Name': state,
                    'District_Name': f'{state.split()[0]}_District',
                    'Total_Enrolments': base,
                    'Total_Updates': int(base * 0.15)
                }
                
                # Add age groups with some variance
                record['Age_Group_0_18'] = int(base * np.random.uniform(0.2, 0.3))
                record['Age_Group_19_40'] = int(base * np.random.uniform(0.4, 0.5))
                record['Age_Group_41_60'] = int(base * np.random.uniform(0.2, 0.25))
                record['Age_Group_60_Plus'] = base - record['Age_Group_0_18'] - record['Age_Group_19_40'] - record['Age_Group_41_60']
                
                data.append(record)
        
        df = pd.DataFrame(data)
        
        # Save sample data
        os.makedirs(self.raw_path, exist_ok=True)
        sample_path = os.path.join(self.raw_path, 'aadhaar_demo.csv')
        df.to_csv(sample_path, index=False)
        logger.info(f"Sample data saved to {sample_path}")
        
        return df