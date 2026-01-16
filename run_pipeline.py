# run_fixed_pipeline.py
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import sys

print("🚀 STARTING FIXED AADHAAR ANALYTICS PIPELINE")
print("="*60)

# Step 1: Create better sample data
print("\n📊 STEP 1: Creating realistic sample data...")

# Create sample data
states = ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 'Delhi', 'West Bengal']
dates = pd.date_range('2023-01-01', '2023-12-31', freq='D')

data = []
for date in dates:
    for state in states:
        # Base with state variations
        base_rates = {
            'Maharashtra': 8000,
            'Uttar Pradesh': 12000,
            'Karnataka': 6000,
            'Tamil Nadu': 7000,
            'Delhi': 4000,
            'West Bengal': 5000
        }
        
        base = base_rates.get(state, 5000)
        
        # Weekend effect
        if date.weekday() >= 5:
            base = int(base * 0.6)
        
        # Monthly patterns
        if date.month in [1, 4, 7, 10]:
            base = int(base * 1.3)
        
        # Add anomalies
        anomaly = 1.0
        if state == 'Maharashtra' and date.month == 3:
            anomaly = 2.5  # March spike
        elif state == 'Delhi' and date.month == 6:
            anomaly = 3.0  # June spike
        elif state == 'Karnataka' and date.month == 9:
            anomaly = 0.3  # September drop
        
        enrolments = int(base * anomaly + np.random.randint(-500, 500))
        updates = int(enrolments * np.random.uniform(0.1, 0.3))
        
        data.append({
            'Date': date.strftime('%Y-%m-%d'),
            'State_Name': state,
            'District_Name': f'{state.split()[0]}_District',
            'Total_Enrolments': enrolments,
            'Total_Updates': updates,
            'Age_Group_0_18': int(enrolments * 0.25),
            'Age_Group_19_40': int(enrolments * 0.45),
            'Age_Group_41_60': int(enrolments * 0.22),
            'Age_Group_60_Plus': int(enrolments * 0.08)
        })

raw_df = pd.DataFrame(data)
print(f"   ✓ Created {len(raw_df)} records")

# Save raw data
os.makedirs('data/raw', exist_ok=True)
raw_df.to_csv('data/raw/aadhaar_data.csv', index=False)
print("   ✓ Saved raw data")

# Step 2: Clean data
print("\n🧹 STEP 2: Cleaning data...")

# Standardize column names
column_mapping = {
    'Date': 'date',
    'State_Name': 'state',
    'District_Name': 'district',
    'Total_Enrolments': 'enrolment_count',
    'Total_Updates': 'update_count'
}
cleaned_df = raw_df.rename(columns=column_mapping)

# Convert dates
cleaned_df['date'] = pd.to_datetime(cleaned_df['date'])
print(f"   ✓ Cleaned {len(cleaned_df)} records")

# Step 3: Create features
print("\n🔧 STEP 3: Creating features...")

# Time features
cleaned_df['year'] = cleaned_df['date'].dt.year
cleaned_df['month'] = cleaned_df['date'].dt.month
cleaned_df['day_of_week'] = cleaned_df['date'].dt.dayofweek
cleaned_df['is_weekend'] = (cleaned_df['day_of_week'] >= 5).astype(int)

# Monthly aggregates
cleaned_df['year_month'] = cleaned_df['date'].dt.to_period('M')
monthly_df = cleaned_df.groupby(['state', 'year_month']).agg({
    'enrolment_count': ['sum', 'mean', 'std'],
    'update_count': 'sum'
}).reset_index()

# Flatten columns
monthly_df.columns = ['state', 'year_month', 'enrolments_sum', 'enrolments_mean', 'enrolments_std', 'updates_sum']

# Calculate growth and ratios
monthly_df['mom_growth'] = monthly_df.groupby('state')['enrolments_sum'].pct_change()
monthly_df['update_ratio'] = monthly_df['updates_sum'] / monthly_df['enrolments_sum'].replace(0, 1)

# Add z-score
monthly_df['z_score'] = monthly_df.groupby('state')['enrolments_sum'].transform(
    lambda x: (x - x.mean()) / x.std() if x.std() > 0 else 0
)

print(f"   ✓ Created monthly aggregates: {len(monthly_df)} records")

# Step 4: Anomaly detection
print("\n🚨 STEP 4: Detecting anomalies...")

from sklearn.ensemble import IsolationForest

# Prepare features for anomaly detection
features = monthly_df[['enrolments_sum', 'mom_growth', 'z_score', 'update_ratio']].fillna(0)

# Fit Isolation Forest
iso_forest = IsolationForest(contamination=0.1, random_state=42)
anomalies = iso_forest.fit_predict(features)

monthly_df['is_anomaly'] = np.where(anomalies == -1, 1, 0)
monthly_df['anomaly_score'] = -iso_forest.score_samples(features)

anomaly_count = monthly_df['is_anomaly'].sum()
print(f"   ✓ Detected {anomaly_count} anomalies")

# Step 5: Clustering
print("\n🔍 STEP 5: Clustering states...")

from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

# State-level features
state_features = monthly_df.groupby('state').agg({
    'enrolments_sum': 'mean',
    'mom_growth': 'mean',
    'anomaly_score': 'mean'
}).reset_index()

# Scale and cluster
scaler = StandardScaler()
X = state_features[['enrolments_sum', 'mom_growth', 'anomaly_score']].fillna(0)
X_scaled = scaler.fit_transform(X)

kmeans = KMeans(n_clusters=3, random_state=42)
state_features['cluster'] = kmeans.fit_predict(X_scaled)

print(f"   ✓ Created {state_features['cluster'].nunique()} clusters")

# Step 6: Risk scoring
print("\n⚠️ STEP 6: Calculating risk scores...")

# Simple risk calculation
state_risk = monthly_df.groupby('state').agg({
    'is_anomaly': ['sum', 'mean'],
    'anomaly_score': 'max'
}).reset_index()

state_risk.columns = ['state', 'anomaly_count', 'anomaly_frequency', 'max_anomaly_score']

# Normalize scores
state_risk['count_risk'] = state_risk['anomaly_count'] / state_risk['anomaly_count'].max()
state_risk['freq_risk'] = state_risk['anomaly_frequency']
state_risk['severity_risk'] = state_risk['max_anomaly_score'] / state_risk['max_anomaly_score'].max()

# Combined risk
state_risk['risk_score'] = (state_risk['count_risk'] * 0.3 + 
                           state_risk['freq_risk'] * 0.4 + 
                           state_risk['severity_risk'] * 0.3)

# Risk levels
def get_risk_level(score):
    if score >= 0.7:
        return 'CRITICAL'
    elif score >= 0.5:
        return 'HIGH'
    elif score >= 0.3:
        return 'MEDIUM'
    else:
        return 'LOW'

state_risk['risk_level'] = state_risk['risk_score'].apply(get_risk_level)
state_risk = state_risk.sort_values('risk_score', ascending=False)

print(f"   ✓ Calculated risk for {len(state_risk)} states")

# Step 7: Generate insights
print("\n💡 STEP 7: Generating insights...")

insights = {
    'metadata': {
        'generated_at': datetime.now().isoformat(),
        'total_records': len(raw_df),
        'states_analyzed': len(states),
        'period': f"{dates[0].strftime('%Y-%m-%d')} to {dates[-1].strftime('%Y-%m-%d')}"
    },
    'summary': {
        'total_enrolments': monthly_df['enrolments_sum'].sum(),
        'total_anomalies': anomaly_count,
        'anomaly_rate': f"{(anomaly_count/len(monthly_df)*100):.1f}%",
        'top_risky_state': state_risk.iloc[0]['state'] if not state_risk.empty else None,
        'critical_states': len(state_risk[state_risk['risk_level'] == 'CRITICAL'])
    },
    'recommendations': [
        {
            'action': 'Investigate anomalies',
            'description': f'Review {anomaly_count} detected anomalies',
            'priority': 'HIGH' if anomaly_count > 10 else 'MEDIUM'
        },
        {
            'action': 'Address high-risk states',
            'description': f'Focus on states with critical risk levels',
            'priority': 'HIGH'
        }
    ]
}

print("   ✓ Generated insights")

# Step 8: Save outputs
print("\n💾 STEP 8: Saving outputs...")

timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
output_dir = f"data/outputs/{timestamp}"
os.makedirs(output_dir, exist_ok=True)
os.makedirs('data/processed', exist_ok=True)

# Save processed data
cleaned_df.to_csv(f'{output_dir}/cleaned_data.csv', index=False)
monthly_df.to_csv(f'{output_dir}/monthly_aggregates.csv', index=False)
state_features.to_csv(f'{output_dir}/clusters.csv', index=False)
state_risk.to_csv(f'{output_dir}/risk_scores.csv', index=False)

# Also save to processed folder for dashboard
monthly_df.to_csv('data/processed/monthly_aggregates.csv', index=False)
state_risk.to_csv('data/processed/risk_scores.csv', index=False)

# Save insights
import json
with open(f'{output_dir}/insights.json', 'w') as f:
    json.dump(insights, f, indent=2, default=str)

print(f"   ✓ Saved all outputs to {output_dir}")

print("\n" + "="*60)
print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
print("="*60)
print(f"\n📊 Summary:")
print(f"   • Total records: {len(raw_df):,}")
print(f"   • Monthly aggregates: {len(monthly_df)}")
print(f"   • Anomalies detected: {anomaly_count}")
print(f"   • States clustered: {len(state_features)}")
print(f"   • Critical risk states: {insights['summary']['critical_states']}")
print(f"\n📁 Outputs saved to: {output_dir}")
print(f"\n🚀 To launch dashboard:")
print("   streamlit run app/fixed_dashboard.py")
print("="*60)