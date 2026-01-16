# src/data_pipeline/universal_processor.py
import pandas as pd
import numpy as np
from datetime import datetime
import re
from typing import Dict, List, Optional

class UniversalDataProcessor:
    """
    Schema-agnostic processor for ANY Aadhaar-style dataset
    Automatically detects and maps columns
    """
    
    def __init__(self):
        self.column_patterns = {
            'date': [
                r'date', r'Date', r'DATE', r'timestamp', r'Timestamp', 
                r'enrolment_date', r'enrollment_date', r'time', r'Time'
            ],
            'state': [
                r'state', r'State', r'STATE', r'state_name', r'State_Name',
                r'STATE_NAME', r'region', r'Region', r'location'
            ],
            'district': [
                r'district', r'District', r'DISTRICT', r'district_name',
                r'district_name', r'area', r'Area', r'zone', r'Zone'
            ],
            'pincode': [
                r'pincode', r'Pincode', r'PINCODE', r'pin', r'Pin', r'PIN',
                r'postal_code', r'postal', r'zip', r'Zip'
            ],
            'enrolment_count': [
                r'enrolment', r'Enrolment', r'enrollment', r'Enrollment',
                r'enrolments', r'enrollments', r'count', r'Count', r'total',
                r'volume', r'Volume', r'number', r'Number'
            ],
            'update_count': [
                r'update', r'Update', r'updates', r'Updates', r'modification',
                r'Modification', r'change', r'Change', r'correction'
            ],
            'age_0_18': [
                r'age_0_18', r'age0_18', r'age_0_to_18', r'0_18', r'under_18',
                r'minor', r'Minor', r'children', r'Children'
            ],
            'age_19_40': [
                r'age_19_40', r'age19_40', r'age_19_to_40', r'19_40',
                r'adult', r'Adult', r'young_adult', r'young'
            ],
            'age_41_60': [
                r'age_41_60', r'age41_60', r'age_41_to_60', r'41_60',
                r'middle_age', r'middle', r'mid_age'
            ],
            'age_60_plus': [
                r'age_60_plus', r'age60_plus', r'age_60\+', r'60_plus',
                r'senior', r'Senior', r'elderly', r'Elderly', r'old'
            ]
        }
        
    def auto_detect_schema(self, df: pd.DataFrame) -> Dict:
        """
        Automatically detect and map columns from ANY dataset
        """
        print("🔍 Auto-detecting schema...")
        
        column_mapping = {}
        detected_patterns = {}
        
        for standard_name, patterns in self.column_patterns.items():
            for pattern in patterns:
                # Check exact matches
                exact_matches = [col for col in df.columns if re.match(f'^{pattern}$', col, re.IGNORECASE)]
                
                # Check partial matches
                partial_matches = [col for col in df.columns if re.search(pattern, col, re.IGNORECASE)]
                
                # Combine matches
                all_matches = list(set(exact_matches + partial_matches))
                
                if all_matches:
                    # Take the first match
                    original_column = all_matches[0]
                    column_mapping[original_column] = standard_name
                    detected_patterns[standard_name] = {
                        'original': original_column,
                        'confidence': 'HIGH' if exact_matches else 'MEDIUM',
                        'matches': all_matches
                    }
                    break
        
        # Detect date columns by data type
        for col in df.columns:
            if col not in column_mapping:
                # Check if column contains date-like data
                sample = df[col].dropna().head(10)
                if len(sample) > 0:
                    # Try to parse as date
                    try:
                        pd.to_datetime(sample, errors='raise')
                        if 'date' not in column_mapping.values():
                            column_mapping[col] = 'date'
                            detected_patterns['date'] = {
                                'original': col,
                                'confidence': 'HIGH',
                                'type': 'auto_detected_date'
                            }
                    except:
                        pass
        
        # Detect numeric count columns
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            if col not in column_mapping:
                col_lower = col.lower()
                if any(keyword in col_lower for keyword in ['total', 'count', 'sum', 'number']):
                    if 'enrolment_count' not in column_mapping.values():
                        column_mapping[col] = 'enrolment_count'
                        detected_patterns['enrolment_count'] = {
                            'original': col,
                            'confidence': 'MEDIUM',
                            'type': 'auto_detected_numeric'
                        }
        
        print(f"✅ Detected {len(column_mapping)} columns:")
        for std, info in detected_patterns.items():
            print(f"   {std}: {info['original']} ({info['confidence']})")
        
        return {
            'mapping': column_mapping,
            'detected': detected_patterns,
            'original_columns': list(df.columns),
            'detected_columns': list(column_mapping.values())
        }
    
    def process_any_dataset(self, filepath: str) -> pd.DataFrame:
        """
        Process ANY CSV file automatically
        """
        print(f"📂 Processing: {filepath}")
        
        # Load data with flexible encoding
        encodings = ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']
        df = None
        
        for encoding in encodings:
            try:
                df = pd.read_csv(filepath, encoding=encoding, low_memory=False)
                print(f"   ✓ Loaded with {encoding} encoding")
                break
            except:
                continue
        
        if df is None:
            raise ValueError(f"Could not read file {filepath}")
        
        # Auto-detect schema
        schema = self.auto_detect_schema(df)
        
        # Rename columns
        df_standardized = df.rename(columns=schema['mapping'])
        
        # Fill missing standard columns
        missing_columns = []
        for required in ['date', 'state', 'enrolment_count']:
            if required not in df_standardized.columns:
                missing_columns.append(required)
                # Create placeholder
                if required == 'date':
                    df_standardized['date'] = pd.date_range('2023-01-01', periods=len(df_standardized))
                elif required == 'state':
                    df_standardized['state'] = 'Unknown_State'
                elif required == 'enrolment_count':
                    df_standardized['enrolment_count'] = 1
        
        if missing_columns:
            print(f"⚠️ Missing columns created: {missing_columns}")
        
        # Standardize data types
        df_standardized = self._standardize_data_types(df_standardized)
        
        print(f"✅ Processed {len(df_standardized)} records with {len(df_standardized.columns)} columns")
        
        return df_standardized, schema
    
    def _standardize_data_types(self, df: pd.DataFrame) -> pd.DataFrame:
        """Standardize data types"""
        df = df.copy()
        
        # Date column
        if 'date' in df.columns:
            df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Numeric columns
        numeric_patterns = ['count', 'sum', 'total', 'number', 'age']
        for col in df.columns:
            if any(pattern in col.lower() for pattern in numeric_patterns):
                try:
                    df[col] = pd.to_numeric(df[col], errors='coerce')
                except:
                    pass
        
        # String columns
        string_cols = ['state', 'district', 'pincode']
        for col in string_cols:
            if col in df.columns:
                df[col] = df[col].astype(str)
        
        return df
    
    def generate_data_report(self, df: pd.DataFrame, schema: Dict) -> Dict:
        """Generate data quality report"""
        report = {
            'file_info': {
                'total_records': len(df),
                'total_columns': len(df.columns),
                'date_range': None,
                'states_count': 0
            },
            'column_analysis': {},
            'data_quality': {},
            'recommendations': []
        }
        
        # Column analysis
        for col in df.columns:
            col_info = {
                'dtype': str(df[col].dtype),
                'missing_count': df[col].isna().sum(),
                'missing_percentage': df[col].isna().mean() * 100,
                'unique_values': df[col].nunique(),
                'sample_values': df[col].dropna().head(3).tolist() if df[col].dtype == 'object' else None
            }
            report['column_analysis'][col] = col_info
        
        # Date range
        if 'date' in df.columns:
            report['file_info']['date_range'] = {
                'min': df['date'].min().strftime('%Y-%m-%d') if not pd.isna(df['date'].min()) else None,
                'max': df['date'].max().strftime('%Y-%m-%d') if not pd.isna(df['date'].max()) else None
            }
        
        # States count
        if 'state' in df.columns:
            report['file_info']['states_count'] = df['state'].nunique()
        
        # Data quality issues
        quality_issues = []
        for col, info in report['column_analysis'].items():
            if info['missing_percentage'] > 50:
                quality_issues.append(f"Column '{col}' has {info['missing_percentage']:.1f}% missing values")
        
        report['data_quality']['issues'] = quality_issues
        report['data_quality']['score'] = 100 - len(quality_issues) * 10
        
        # Recommendations
        if quality_issues:
            report['recommendations'].append("Consider data imputation for columns with high missing values")
        
        if 'date' not in df.columns:
            report['recommendations'].append("No date column found. Temporal analysis will be limited")
        
        return report