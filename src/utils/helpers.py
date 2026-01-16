# src/utils/helpers.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import json

def create_sample_data() -> pd.DataFrame:
    """Create sample Aadhaar data for testing"""
    print("📊 Creating sample data...")
    
    # Indian states
    states = [
        'Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 'Delhi',
        'West Bengal', 'Rajasthan', 'Gujarat', 'Madhya Pradesh', 'Bihar'
    ]
    
    # Generate 6 months of data
    dates = pd.date_range(start='2023-01-01', end='2023-06-30', freq='D')
    
    data = []
    for date in dates:
        for state in states:
            # Base enrolments with some randomness
            base_enrolments = np.random.randint(1000, 5000)
            
            # Weekend effect (40% lower)
            if date.weekday() >= 5:
                base_enrolments = int(base_enrolments * 0.6)
            
            # Add some anomalies
            if state == 'Maharashtra' and date.month == 3:
                base_enrolments = int(base_enrolments * 2.5)  # March anomaly
            
            # Create record
            record = {
                'date': date,
                'state': state,
                'district': f'{state}_District_{np.random.randint(1, 5)}',
                'enrolment_count': base_enrolments,
                'update_count': int(base_enrolments * np.random.uniform(0.1, 0.3)),
                'age_0_18': int(base_enrolments * np.random.uniform(0.2, 0.3)),
                'age_19_40': int(base_enrolments * np.random.uniform(0.4, 0.5)),
                'age_41_60': int(base_enrolments * np.random.uniform(0.2, 0.25)),
                'age_60_plus': int(base_enrolments * np.random.uniform(0.05, 0.1))
            }
            
            data.append(record)
    
    df = pd.DataFrame(data)
    print(f"✅ Created sample data with {len(df)} records")
    
    return df

def save_dataframe(df: pd.DataFrame, filename: str, directory: str = "data/processed"):
    """Save DataFrame to CSV with proper directory creation"""
    os.makedirs(directory, exist_ok=True)
    filepath = os.path.join(directory, filename)
    df.to_csv(filepath, index=False)
    print(f"✅ Saved {filename} to {filepath}")
    return filepath

def load_dataframe(filename: str, directory: str = "data/processed") -> pd.DataFrame:
    """Load DataFrame from CSV"""
    filepath = os.path.join(directory, filename)
    if os.path.exists(filepath):
        df = pd.read_csv(filepath)
        print(f"✅ Loaded {filename} from {filepath}")
        return df
    else:
        print(f"⚠️ File not found: {filepath}")
        return pd.DataFrame()

def print_data_summary(df: pd.DataFrame, name: str = "DataFrame"):
    """Print summary of DataFrame"""
    print(f"\n📋 {name} Summary:")
    print(f"   Shape: {df.shape}")
    print(f"   Columns: {list(df.columns)}")
    if len(df) > 0:
        print(f"   Date range: {df['date'].min()} to {df['date'].max()}" if 'date' in df.columns else "")
        print(f"   States: {df['state'].nunique()}" if 'state' in df.columns else "")