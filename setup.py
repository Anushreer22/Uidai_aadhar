# setup.py
import os
import shutil
from pathlib import Path

def create_project_structure():
    """Create the complete project structure"""
    
    # Base directories
    directories = [
        'data/raw',
        'data/processed',
        'data/outputs',
        'logs',
        'config',
        'src/data_pipeline',
        'src/ml_pipeline',
        'src/insights',
        'src/visualization',
        'src/utils',
        'app',
        'tests'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
        print(f"✅ Created: {directory}")
    
    # Create __init__.py files
    init_files = [
        'src/__init__.py',
        'src/data_pipeline/__init__.py',
        'src/ml_pipeline/__init__.py',
        'src/insights/__init__.py',
        'src/visualization/__init__.py',
        'src/utils/__init__.py',
        'app/__init__.py'
    ]
    
    for init_file in init_files:
        Path(init_file).touch()
        print(f"✅ Created: {init_file}")
    
    # Create config file
    config_content = """project:
  name: "Aadhaar Enrolment Analytics"
  version: "1.0.0"

data:
  raw_path: "data/raw"
  processed_path: "data/processed"
  output_path: "data/outputs"

ml:
  anomaly_detection:
    contamination: 0.1
    random_state: 42
  clustering:
    n_clusters: 5

dashboard:
  port: 8501
  theme: "light"
"""
    
    with open('config/config.yaml', 'w') as f:
        f.write(config_content)
    print("✅ Created: config/config.yaml")
    
    # Create requirements.txt
    requirements = """pandas>=2.0.0
numpy>=1.24.0
scikit-learn>=1.3.0
plotly>=5.17.0
streamlit>=1.28.0
pyyaml>=6.0.0
"""
    
    with open('requirements.txt', 'w') as f:
        f.write(requirements)
    print("✅ Created: requirements.txt")