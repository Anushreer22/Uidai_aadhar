# src/utils/config_loader.py
import yaml
import json
import os
from typing import Dict, Any

def load_config(config_path: str = "config/config.yaml") -> Dict[str, Any]:
    """Load configuration from YAML file"""
    try:
        with open(config_path, 'r') as file:
            config = yaml.safe_load(file)
        print(f"✅ Configuration loaded from {config_path}")
        return config
    except FileNotFoundError:
        print(f"⚠️ Config file not found at {config_path}, using default configuration")
        return get_default_config()
    except Exception as e:
        print(f"❌ Error loading config: {e}, using default configuration")
        return get_default_config()

def get_default_config() -> Dict[str, Any]:
    """Return default configuration if config file is missing"""
    return {
        'project': {
            'name': 'Aadhaar Enrolment Analytics',
            'version': '1.0.0'
        },
        'data': {
            'raw_path': 'data/raw',
            'processed_path': 'data/processed',
            'output_path': 'data/outputs'
        },
        'ml': {
            'anomaly_detection': {
                'contamination': 0.1,
                'random_state': 42
            },
            'clustering': {
                'n_clusters': 5
            }
        },
        'dashboard': {
            'port': 8501,
            'theme': 'light'
        }
    }

def save_config(config: Dict[str, Any], config_path: str = "config/config.yaml"):
    """Save configuration to YAML file"""
    os.makedirs(os.path.dirname(config_path), exist_ok=True)
    with open(config_path, 'w') as file:
        yaml.dump(config, file, default_flow_style=False)
    print(f"✅ Configuration saved to {config_path}")