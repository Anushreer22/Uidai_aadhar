# run.py
import subprocess
import sys

def check_dependencies():
    """Check and install required packages"""
    required = ['streamlit', 'pandas', 'numpy', 'plotly']
    missing = []
    
    for package in required:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"📦 Installing missing packages: {', '.join(missing)}")
        subprocess.check_call([sys.executable, "-m", "pip", "install"] + missing)
    
    return True

def main():
    print("\n" + "="*60)
    print("🇮🇳 AADHAAR ANALYTICS DASHBOARD")
    print("="*60)
    
    print("\n📦 Checking dependencies...")
    check_dependencies()
    
    print("\n✅ All dependencies installed!")
    print("\n🚀 Starting dashboard...")
    print("\n🌐 Open your browser and visit:")
    print("   http://localhost:8501")
    print("\n💡 Features:")
    print("   • 📊 Standard Mode: Pre-loaded analytics")
    print("   • 🌐 Universal Mode: Upload any CSV file")
    print("   • 📈 Interactive visualizations")
    print("   • 🚨 Anomaly detection")
    print("   • 💡 AI-powered insights")
    print("\n" + "="*60)
    
    # Launch Streamlit
    subprocess.run([sys.executable, "-m", "streamlit", "run", "app/unified_dashboard.py"])

if __name__ == "__main__":
    main()