# run_unified.py
#!/usr/bin/env python3
"""
Unified Aadhaar Analytics Platform - Quick Start
"""

import os
import sys
import subprocess

def setup_environment():
    """Setup the environment"""
    print("🚀 Setting up Unified Aadhaar Analytics Platform...")
    
    # Create directories
    directories = [
        'data/uploads',
        'data/processed',
        'data/outputs',
        'logs'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # Create sample data if not exists
    sample_path = "data/processed/monthly_aggregates.csv"
    if not os.path.exists(sample_path):
        print("📊 Creating sample data...")
        create_sample_data()
    
    print("\n🎉 Setup complete!")
    print("\n📚 Available Modes:")
    print("   1. 🌐 Universal Mode - Upload ANY dataset")
    print("   2. 📊 Standard Mode - Use our optimized data")
    print("\n🚀 Starting dashboard...")

def create_sample_data():
    """Create sample standard data"""
    import pandas as pd
    import numpy as np
    from datetime import datetime
    
    # Create sample data
    dates = pd.date_range('2023-01-01', '2023-06-01', freq='MS')
    states = ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 'Delhi']
    
    data = []
    for date in dates:
        for state in states:
            data.append({
                'state': state,
                'year_month': date.strftime('%Y-%m'),
                'enrolments_sum': np.random.randint(100000, 500000),
                'updates_sum': np.random.randint(10000, 50000),
                'mom_growth': np.random.uniform(-0.1, 0.2),
                'update_ratio': np.random.uniform(0.1, 0.3)
            })
    
    df = pd.DataFrame(data)
    
    # Save to processed directory
    os.makedirs('data/processed', exist_ok=True)
    df.to_csv('data/processed/monthly_aggregates.csv', index=False)
    
    print("✅ Created sample standard dataset")

def launch_dashboard():
    """Launch the unified dashboard"""
    try:
        import streamlit
        # Launch the dashboard
        print("\n🌐 Launching Unified Dashboard...")
        print("   Please wait for the browser to open...")
        print("\n📌 Dashboard will be available at:")
        print("   🔗 http://localhost:8501")
        print("\n💡 Tips:")
        print("   - Use 🌐 Universal Mode for ANY dataset")
        print("   - Use 📊 Standard Mode for advanced analysis")
        print("   - Check the sidebar for help and options")
        
        # Run streamlit
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app/unified_dashboard.py"])
        
    except ImportError:
        print("❌ Streamlit not found. Installing...")
        subprocess.run([sys.executable, "-m", "pip", "install", "streamlit"])
        launch_dashboard()

if __name__ == "__main__":
    print("\n" + "="*60)
    print("🇮🇳 UNIFIED AADHAAR ANALYTICS PLATFORM")
    print("="*60)
    
    # Check requirements
    requirements_file = "requirements.txt"
    if os.path.exists(requirements_file):
        print("\n📦 Installing requirements...")
        subprocess.run([sys.executable, "-m", "pip", "install", "-r", requirements_file])
    
    setup_environment()
    launch_dashboard()