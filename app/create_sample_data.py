# create_sample_data.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

def create_realistic_aadhaar_data():
    """Create realistic Aadhaar sample data"""
    print("📊 Creating realistic Aadhaar sample data...")
    
    # Indian states with realistic populations
    states = [
        'Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 'Delhi',
        'West Bengal', 'Rajasthan', 'Gujarat', 'Madhya Pradesh', 'Bihar',
        'Andhra Pradesh', 'Telangana', 'Kerala', 'Odisha', 'Assam'
    ]
    
    # Generate 12 months of data (2023)
    start_date = datetime(2023, 1, 1)
    dates = []
    for i in range(365):  # Full year
        dates.append(start_date + timedelta(days=i))
    
    data = []
    for date in dates:
        for state in states:
            # Base enrolments with realistic patterns
            base_enrolments = 0
            
            # State-specific base rates
            state_rates = {
                'Maharashtra': 8000,
                'Uttar Pradesh': 12000,
                'Karnataka': 6000,
                'Tamil Nadu': 7000,
                'Delhi': 4000,
                'West Bengal': 5000,
                'Rajasthan': 4500,
                'Gujarat': 5000,
                'Madhya Pradesh': 4000,
                'Bihar': 3000,
                'Andhra Pradesh': 4000,
                'Telangana': 3500,
                'Kerala': 3000,
                'Odisha': 2500,
                'Assam': 2000
            }
            
            base_enrolments = state_rates.get(state, 3000)
            
            # Weekend effect (60% of weekday volume)
            if date.weekday() >= 5:  # Saturday/Sunday
                base_enrolments = int(base_enrolments * 0.6)
            
            # Monthly patterns (peaks in Jan, Apr, Jul, Oct)
            if date.month in [1, 4, 7, 10]:
                base_enrolments = int(base_enrolments * 1.3)
            
            # Add some randomness
            base_enrolments += np.random.randint(-500, 500)
            base_enrolments = max(100, base_enrolments)  # Minimum 100
            
            # Create artificial anomalies
            anomaly_multiplier = 1.0
            if state == 'Maharashtra' and date.month == 3:
                anomaly_multiplier = 2.5  # March anomaly in Maharashtra
            elif state == 'Delhi' and date.month == 6:
                anomaly_multiplier = 3.0  # June anomaly in Delhi
            elif state == 'Karnataka' and date.month == 9:
                anomaly_multiplier = 0.3  # September drop in Karnataka
            
            enrolment_count = int(base_enrolments * anomaly_multiplier)
            update_count = int(enrolment_count * np.random.uniform(0.1, 0.3))
            
            # Age distribution
            age_0_18 = int(enrolment_count * np.random.uniform(0.2, 0.3))
            age_19_40 = int(enrolment_count * np.random.uniform(0.4, 0.5))
            age_41_60 = int(enrolment_count * np.random.uniform(0.2, 0.25))
            age_60_plus = enrolment_count - age_0_18 - age_19_40 - age_41_60
            
            data.append({
                'Date': date.strftime('%Y-%m-%d'),
                'State_Name': state,
                'District_Name': f'{state.split()[0]}_District_{np.random.randint(1, 8)}',
                'Pincode': f'{np.random.randint(100000, 999999)}',
                'Total_Enrolments': enrolment_count,
                'Total_Updates': update_count,
                'Age_Group_0_18': age_0_18,
                'Age_Group_19_40': age_19_40,
                'Age_Group_41_60': age_41_60,
                'Age_Group_60_Plus': age_60_plus
            })
    
    df = pd.DataFrame(data)
    
    # Save to raw directory
    os.makedirs('data/raw', exist_ok=True)
    df.to_csv('data/raw/aadhaar_sample_2023.csv', index=False)
    
    print(f"✅ Created realistic sample data with {len(df)} records")
    print(f"✅ Saved to: data/raw/aadhaar_sample_2023.csv")
    
    # Also save a smaller version for faster processing
    df_sample = df.iloc[:1000].copy()
    df_sample.to_csv('data/raw/aadhaar_small.csv', index=False)
    print(f"✅ Created small sample: data/raw/aadhaar_small.csv")
    
    return df

if __name__ == "__main__":
    create_realistic_aadhaar_data()