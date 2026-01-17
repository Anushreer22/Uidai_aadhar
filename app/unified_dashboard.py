# app/unified_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os

# Page configuration
st.set_page_config(
    page_title="Aadhaar Analytics | Unified Dashboard",
    page_icon="🔐",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Enhanced CSS with better contrast
st.markdown("""
<style>
    /* Main background */
    .stApp {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Headers with gradient text */
    .gradient-text {
        background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        font-weight: 800;
    }
    
    /* Glass effect cards */
    .glass-card {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        border: 1px solid rgba(255, 255, 255, 0.3);
        box-shadow: 0 8px 32px rgba(31, 38, 135, 0.15);
        padding: 1.5rem;
        transition: all 0.3s ease;
    }
    
    .glass-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 40px rgba(31, 38, 135, 0.25);
    }
    
    /* Sidebar styling */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #0f1a3a 0%, #1a2b5a 100%);
    }
    
    [data-testid="stSidebar"] h1, 
    [data-testid="stSidebar"] h2, 
    [data-testid="stSidebar"] h3,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] label {
        color: white !important;
    }
    
    /* Custom buttons */
    .stButton > button {
        background: linear-gradient(90deg, #FF9933 0%, #FFB74D 100%);
        color: white !important;
        border: none;
        padding: 0.75rem 2rem;
        border-radius: 12px;
        font-weight: 600;
        transition: all 0.3s ease;
        width: 100%;
    }
    
    .stButton > button:hover {
        transform: scale(1.05);
        box-shadow: 0 8px 25px rgba(255, 153, 51, 0.4);
    }
    
    /* Metric cards */
    .metric-card {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white !important;
        padding: 1.5rem;
        border-radius: 16px;
        text-align: center;
        position: relative;
        overflow: hidden;
    }
    
    .metric-card::before {
        content: '';
        position: absolute;
        top: -50%;
        left: -50%;
        width: 200%;
        height: 200%;
        background: linear-gradient(45deg, transparent, rgba(255,255,255,0.1), transparent);
        transform: rotate(45deg);
        transition: all 0.5s ease;
    }
    
    /* Status badges */
    .badge {
        display: inline-block;
        padding: 6px 16px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 4px;
        color: white !important;
    }
    
    .badge-success {
        background: linear-gradient(90deg, #138808, #4CAF50);
    }
    
    .badge-warning {
        background: linear-gradient(90deg, #FF9933, #FF9800);
    }
    
    .badge-danger {
        background: linear-gradient(90deg, #FF5252, #F44336);
    }
    
    .badge-info {
        background: linear-gradient(90deg, #2196F3, #03A9F4);
    }
    
    /* Animations */
    @keyframes float {
        0% { transform: translateY(0px); }
        50% { transform: translateY(-10px); }
        100% { transform: translateY(0px); }
    }
    
    .floating {
        animation: float 3s ease-in-out infinite;
    }
    
    /* Tabs styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background: white;
        border-radius: 10px 10px 0 0;
        padding: 12px 24px;
        font-weight: 600;
        transition: all 0.3s ease;
        color: #333 !important;
    }
    
    .stTabs [data-baseweb="tab"]:hover {
        background: linear-gradient(90deg, #FF9933, #FFB74D);
        color: white !important;
    }
    
    /* Upload area */
    .upload-area {
        border: 2px dashed #FF9933;
        border-radius: 20px;
        padding: 40px;
        text-align: center;
        background: rgba(255, 153, 51, 0.05);
        transition: all 0.3s ease;
    }
    
    .upload-area:hover {
        background: rgba(255, 153, 51, 0.1);
        border-color: #138808;
    }
    
    /* Risk indicators */
    .risk-indicator {
        padding: 0.5rem 1rem;
        border-radius: 10px;
        font-weight: 600;
        margin: 0.25rem 0;
    }
    
    .risk-critical { background: linear-gradient(90deg, #FF5252, #F44336); color: white; }
    .risk-high { background: linear-gradient(90deg, #FF9800, #FFB74D); color: white; }
    .risk-medium { background: linear-gradient(90deg, #FFC107, #FFD54F); color: #333; }
    .risk-low { background: linear-gradient(90deg, #4CAF50, #81C784); color: white; }
</style>
""", unsafe_allow_html=True)

class AadhaarDashboard:
    def __init__(self):
        # Initialize session state
        if 'mode' not in st.session_state:
            st.session_state.mode = "standard"
        if 'data' not in st.session_state:
            st.session_state.data = None
        if 'risk_data' not in st.session_state:
            st.session_state.risk_data = None
        if 'uploaded_data' not in st.session_state:
            st.session_state.uploaded_data = None
    
    def create_sample_data(self):
        """Create enhanced sample Aadhaar data with all features"""
        np.random.seed(42)
        dates = pd.date_range('2023-01-01', '2023-12-01', freq='MS')
        states = ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 
                  'Delhi', 'Gujarat', 'Rajasthan', 'West Bengal', 'Bihar', 'Telangana']
        
        data = []
        for date in dates:
            for state in states:
                base_enrol = np.random.randint(50000, 300000)
                season_factor = 1 + 0.2 * np.sin(2 * np.pi * date.month / 12)
                state_factor = 1 + (states.index(state) * 0.1)
                
                enrolments = int(base_enrol * season_factor * state_factor)
                updates = int(enrolments * np.random.uniform(0.05, 0.2))
                successful_enrol = int(enrolments * np.random.uniform(0.85, 0.98))
                pending = enrolments - successful_enrol
                
                # Add some anomalies
                is_anomaly = 0
                anomaly_score = np.random.uniform(0, 0.3)
                
                if state == 'Maharashtra' and date.month == 3:
                    enrolments = int(enrolments * 3)
                    is_anomaly = 1
                    anomaly_score = 0.95
                
                if state == 'Delhi' and date.month == 6:
                    successful_enrol = int(successful_enrol * 0.7)
                    is_anomaly = 1
                    anomaly_score = 0.8
                
                data.append({
                    'state': state,
                    'year_month': date.strftime('%Y-%m'),
                    'date': date,
                    'enrolments': enrolments,
                    'successful_enrolments': successful_enrol,
                    'pending_enrolments': pending,
                    'updates': updates,
                    'update_ratio': updates / max(enrolments, 1),
                    'success_rate': successful_enrol / max(enrolments, 1),
                    'mom_growth': np.random.uniform(-0.15, 0.25),
                    'is_anomaly': is_anomaly,
                    'anomaly_score': anomaly_score,
                    'population_coverage': np.random.uniform(0.6, 0.95)
                })
        
        return pd.DataFrame(data)
    
    def create_risk_data(self):
        """Create comprehensive risk assessment data"""
        states = ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 
                  'Delhi', 'Gujarat', 'Rajasthan', 'West Bengal', 'Bihar', 'Telangana']
        
        risk_data = []
        for state in states:
            risk_score = np.random.beta(2, 5)
            fraud_risk = np.random.beta(1, 10)
            data_quality = np.random.beta(8, 2)
            operational_risk = np.random.beta(3, 7)
            
            overall_risk = (risk_score * 0.4 + fraud_risk * 0.3 + 
                          (1 - data_quality) * 0.2 + operational_risk * 0.1)
            
            if overall_risk >= 0.7:
                risk_level = 'CRITICAL'
                icon = '🔴'
            elif overall_risk >= 0.5:
                risk_level = 'HIGH'
                icon = '🟠'
            elif overall_risk >= 0.3:
                risk_level = 'MEDIUM'
                icon = '🟡'
            elif overall_risk >= 0.1:
                risk_level = 'LOW'
                icon = '🟢'
            else:
                risk_level = 'VERY_LOW'
                icon = '🔵'
            
            risk_data.append({
                'state': state,
                'risk_score': overall_risk,
                'risk_level': risk_level,
                'icon': icon,
                'fraud_risk': fraud_risk,
                'data_quality': data_quality,
                'operational_risk': operational_risk,
                'trend': np.random.choice(['📈 Increasing', '📉 Decreasing', '➡️ Stable'], 
                                         p=[0.3, 0.2, 0.5])
            })
        
        return pd.DataFrame(risk_data)
    
    def load_data(self):
        """Load or create data"""
        if st.session_state.data is None:
            st.session_state.data = self.create_sample_data()
            st.session_state.risk_data = self.create_risk_data()
    
    def show_header(self):
        """Show beautiful application header"""
        col1, col2, col3 = st.columns([1, 2, 1])
        
        with col2:
            st.markdown("""
            <div style="text-align: center; margin-bottom: 2rem;">
                <h1 class="gradient-text" style="font-size: 3.5rem; margin-bottom: 0.5rem;">
                    🔐 Aadhaar Analytics
                </h1>
                <p style="color: #666; font-size: 1.2rem; margin-top: 0; font-weight: 500;">
                    Unified Dashboard for Data Intelligence & Monitoring
                </p>
                <div style="display: flex; justify-content: center; gap: 1rem; margin-top: 1.5rem;">
                    <span class="badge badge-success">Real-time</span>
                    <span class="badge badge-info">AI-Powered</span>
                    <span class="badge badge-warning">Secure</span>
                    <span class="badge badge-danger">Critical Monitoring</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def show_sidebar(self):
        """Show modern sidebar with all controls"""
        with st.sidebar:
            # Sidebar header
            st.markdown("""
            <div style="background: linear-gradient(90deg, #FF9933 0%, #138808 100%); 
                        padding: 1.5rem; border-radius: 12px; margin-bottom: 2rem; 
                        border: 2px solid rgba(255, 255, 255, 0.3);">
                <h2 style="color: white; margin: 0; text-align: center; font-size: 1.8rem;">
                    📊 Dashboard Controls
                </h2>
                <p style="color: white; text-align: center; margin: 0.5rem 0 0 0; 
                         font-size: 1rem; font-weight: 500; opacity: 0.95;">
                    Ministry of Electronics & IT
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            # Mode selection
            st.markdown("### 🎯 Analysis Mode")
            
            col1, col2 = st.columns(2)
            with col1:
                standard_selected = st.button(
                    "📊 Standard",
                    use_container_width=True,
                    type="primary" if st.session_state.mode == "standard" else "secondary",
                    help="Pre-loaded analytics dashboard"
                )
                if standard_selected and st.session_state.mode != "standard":
                    st.session_state.mode = "standard"
                    st.rerun()
            
            with col2:
                universal_selected = st.button(
                    "🌐 Universal",
                    use_container_width=True,
                    type="primary" if st.session_state.mode == "universal" else "secondary",
                    help="Upload any CSV file for analysis"
                )
                if universal_selected and st.session_state.mode != "universal":
                    st.session_state.mode = "universal"
                    st.rerun()
            
            st.divider()
            
            # Data stats
            st.markdown("### 📈 Data Statistics")
            
            if st.session_state.data is not None:
                df = st.session_state.data
                
                col1, col2 = st.columns(2)
                with col1:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">📊</div>
                        <h3 style="margin: 0; font-size: 1.8rem; color: white !important;">{len(df):,}</h3>
                        <p style="margin: 0; color: rgba(255, 255, 255, 0.9) !important; font-weight: 500;">Total Records</p>
                    </div>
                    """, unsafe_allow_html=True)
                
                with col2:
                    st.markdown(f"""
                    <div class="metric-card">
                        <div style="font-size: 1.2rem; margin-bottom: 0.5rem;">🌍</div>
                        <h3 style="margin: 0; font-size: 1.8rem; color: white !important;">{df['state'].nunique()}</h3>
                        <p style="margin: 0; color: rgba(255, 255, 255, 0.9) !important; font-weight: 500;">States</p>
                    </div>
                    """, unsafe_allow_html=True)
            
            st.divider()
            
            # Quick actions
            st.markdown("### ⚡ Quick Actions")
            
            action_col1, action_col2 = st.columns(2)
            
            with action_col1:
                refresh_btn = st.button("🔄 Refresh", 
                                       use_container_width=True,
                                       type="primary",
                                       help="Reload sample data")
                if refresh_btn:
                    st.session_state.data = self.create_sample_data()
                    st.session_state.risk_data = self.create_risk_data()
                    st.success("Data refreshed successfully!")
                    st.rerun()
            
            with action_col2:
                sample_btn = st.button("📊 Sample", 
                                      use_container_width=True,
                                      type="secondary",
                                      help="Load sample data")
                if sample_btn:
                    st.info("Loading sample data...")
                    self.load_data()
                    st.rerun()
            
            # Export button - FIXED: removed use_container_width
            if st.session_state.data is not None:
                csv = st.session_state.data.to_csv(index=False)
                st.download_button(
                    label="📥 Export CSV",
                    data=csv,
                    file_name="aadhaar_analytics.csv",
                    mime="text/csv",
                    use_container_width=True,
                    type="primary",
                    help="Download current data as CSV"
                )
            
            st.divider()
            
            # Live stats
            st.markdown("### 📡 Live Status")
            
            col_status1, col_status2 = st.columns(2)
            with col_status1:
                st.markdown("""
                <div style="text-align: center; padding: 1rem; background: rgba(255, 255, 255, 0.1); border-radius: 12px;">
                    <div style="font-size: 1.5rem; color: #4CAF50;">✅</div>
                    <div style="color: white; font-weight: 500; font-size: 0.9rem;">System</div>
                    <div style="color: #4CAF50; font-weight: bold; font-size: 0.9rem;">Operational</div>
                </div>
                """, unsafe_allow_html=True)
            
            with col_status2:
                st.markdown("""
                <div style="text-align: center; padding: 1rem; background: rgba(255, 255, 255, 0.1); border-radius: 12px;">
                    <div style="font-size: 1.5rem; color: #2196F3;">⚡</div>
                    <div style="color: white; font-weight: 500; font-size: 0.9rem;">Last Updated</div>
                    <div style="color: #2196F3; font-weight: bold; font-size: 0.9rem;">Just now</div>
                </div>
                """, unsafe_allow_html=True)
    
    def create_metric_card_main(self, title, value, change=None, icon="📊"):
        """Create a beautiful metric card for main content"""
        change_html = ""
        if change:
            change_type = "🟢" if change >= 0 else "🔴"
            change_html = f'<div style="font-size: 0.9rem; margin-top: 0.5rem; color: #666;">{change_type} {abs(change):.1f}%</div>'
        
        return f"""
        <div class="glass-card" style="text-align: center;">
            <div style="font-size: 2.5rem; margin-bottom: 0.5rem;">{icon}</div>
            <h3 style="margin: 0; color: #2c3e50; font-weight: 600;">{title}</h3>
            <div style="font-size: 2rem; font-weight: bold; margin: 0.5rem 0; 
                     background: linear-gradient(90deg, #FF9933, #138808);
                     -webkit-background-clip: text;
                     -webkit-text-fill-color: transparent;">
                {value}
            </div>
            {change_html}
        </div>
        """
    
    def run_universal_mode(self):
        """Run universal upload mode with all features"""
        st.markdown("""
        <div class="glass-card" style="margin-bottom: 2rem;">
            <h2 style="margin-top: 0; color: #333;">🌐 Universal Upload Mode</h2>
            <p style="color: #666; font-size: 1.1rem; font-weight: 500;">
                Upload any Aadhaar-related CSV file for instant analysis and visualization
            </p>
        </div>
        """, unsafe_allow_html=True)
        
        # File upload with drag and drop effect
        uploaded_file = st.file_uploader(
            "📁 Drag & drop or click to upload",
            type=['csv', 'xlsx', 'json'],
            help="Upload any Aadhaar data file (CSV, Excel, JSON) for analysis",
            key="universal_upload"
        )
        
        if uploaded_file is not None:
            try:
                # Show loading animation
                with st.spinner('✨ Analyzing your data...'):
                    if uploaded_file.name.endswith('.csv'):
                        df = pd.read_csv(uploaded_file)
                    elif uploaded_file.name.endswith('.xlsx'):
                        df = pd.read_excel(uploaded_file)
                    elif uploaded_file.name.endswith('.json'):
                        df = pd.read_json(uploaded_file)
                    else:
                        st.error("❌ Unsupported file format")
                        return
                
                st.session_state.uploaded_data = df
                
                # Success message with animation
                st.success(f"""
                ✅ **Successfully loaded {len(df):,} records**  
                📂 **File:** {uploaded_file.name}  
                📊 **Columns:** {len(df.columns)}
                """)
                
                # Data preview in glass card - FIXED: replaced use_container_width
                with st.expander("📋 **Data Preview**", expanded=True):
                    st.dataframe(df.head(10), width='stretch', height=300)
                
                # Statistics in columns
                st.markdown("### 📈 **Quick Statistics**")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.markdown(self.create_metric_card_main(
                        "Total Records", 
                        f"{len(df):,}", 
                        icon="📄"
                    ), unsafe_allow_html=True)
                
                with col2:
                    st.markdown(self.create_metric_card_main(
                        "Columns", 
                        len(df.columns), 
                        icon="📊"
                    ), unsafe_allow_html=True)
                
                with col3:
                    numeric_cols = len(df.select_dtypes(include=[np.number]).columns)
                    st.markdown(self.create_metric_card_main(
                        "Numeric", 
                        numeric_cols, 
                        icon="🔢"
                    ), unsafe_allow_html=True)
                
                with col4:
                    missing = df.isna().sum().sum()
                    st.markdown(self.create_metric_card_main(
                        "Missing", 
                        f"{missing:,}", 
                        icon="⚠️"
                    ), unsafe_allow_html=True)
                
                # Data profiling
                st.markdown("### 🔍 **Data Profiling**")
                
                profile_tab1, profile_tab2 = st.tabs(["📋 Column Details", "🎯 Insights"])
                
                with profile_tab1:
                    for col in df.columns[:5]:  # Show first 5 columns
                        with st.expander(f"**{col}** ({df[col].dtype})", icon="📌"):
                            col1, col2 = st.columns(2)
                            with col1:
                                st.metric("Unique", df[col].nunique())
                                st.metric("Missing", df[col].isna().sum())
                            with col2:
                                if pd.api.types.is_numeric_dtype(df[col]):
                                    st.metric("Mean", f"{df[col].mean():.2f}")
                                    st.metric("Std Dev", f"{df[col].std():.2f}")
                
                with profile_tab2:
                    # Generate insights
                    insights = []
                    
                    # Check for missing values
                    missing_pct = (df.isna().sum().sum() / (len(df) * len(df.columns))) * 100
                    if missing_pct > 10:
                        insights.append(("warning", "⚠️ High Missing Values", 
                                       f"{missing_pct:.1f}% of data is missing"))
                    
                    # Check for duplicates
                    duplicates = df.duplicated().sum()
                    if duplicates > 0:
                        insights.append(("info", "🔍 Duplicates Found", 
                                       f"{duplicates:,} duplicate rows"))
                    
                    # Display insights
                    if insights:
                        for icon, title, desc in insights:
                            if "warning" in icon:
                                st.warning(f"{icon} **{title}**\n\n{desc}")
                            else:
                                st.info(f"{icon} **{title}**\n\n{desc}")
                    
            except Exception as e:
                st.error(f"❌ Error loading file: {str(e)}")
        else:
            # Show upload instructions
            st.markdown("""
            <div class="upload-area">
                <div style="font-size: 5rem; margin-bottom: 1rem; color: #FF9933;" class="floating">📁</div>
                <h3 style="color: #333; margin-bottom: 1rem;">Ready to Analyze Your Data?</h3>
                <p style="color: #666; max-width: 600px; margin: 0 auto 2rem auto; font-size: 1.1rem;">
                    Upload any Aadhaar-related data file to get instant insights, 
                    visualizations, and analytics.
                </p>
                <div style="margin-top: 2rem;">
                    <div style="display: inline-block; padding: 1rem 2rem; 
                              background: linear-gradient(90deg, #2196F3, #03A9F4); 
                              color: white; border-radius: 12px; font-weight: bold; font-size: 1.1rem;">
                        📁 Supported: CSV, Excel, JSON
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def run_standard_mode(self):
        """Run standard analysis mode with all features restored"""
        self.load_data()
        df = st.session_state.data
        risk_df = st.session_state.risk_data
        
        # Header with mode indicator
        st.markdown("""
        <div class="glass-card" style="margin-bottom: 2rem; border-left: 5px solid #FF9933;">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div>
                    <h2 style="margin: 0; color: #333;">📊 Standard Analysis Mode</h2>
                    <p style="color: #666; margin: 0.5rem 0 0 0; font-weight: 500;">
                        Comprehensive Aadhaar analytics with AI-powered insights
                    </p>
                </div>
                <div style="display: flex; gap: 1rem; align-items: center;">
                    <span class="badge badge-warning">UIDAI SECURE</span>
                    <span class="badge badge-success">LIVE DATA</span>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Enhanced KPI Cards
        st.markdown("### 🎯 **Key Performance Indicators**")
        
        kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
        
        with kpi_col1:
            total_enrol = df['enrolments'].sum() / 1_000_000
            st.markdown(self.create_metric_card_main(
                "Total Enrolments", 
                f"{total_enrol:.1f}M", 
                change=12.5,
                icon="👥"
            ), unsafe_allow_html=True)
        
        with kpi_col2:
            total_success = df['successful_enrolments'].sum() / 1_000_000
            st.markdown(self.create_metric_card_main(
                "Successful", 
                f"{total_success:.1f}M", 
                change=8.3,
                icon="✅"
            ), unsafe_allow_html=True)
        
        with kpi_col3:
            coverage = df['population_coverage'].mean() * 100
            st.markdown(self.create_metric_card_main(
                "Coverage", 
                f"{coverage:.1f}%", 
                change=2.1,
                icon="📈"
            ), unsafe_allow_html=True)
        
        with kpi_col4:
            anomalies = df['is_anomaly'].sum()
            st.markdown(self.create_metric_card_main(
                "Anomalies", 
                anomalies, 
                change=-3.2 if anomalies > 0 else None,
                icon="⚠️"
            ), unsafe_allow_html=True)
        
        # Main content tabs with all features
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📈 **Dashboard**", 
            "🌍 **Geographic**", 
            "🚨 **Anomalies**", 
            "⚠️ **Risks**", 
            "💡 **Insights**"
        ])
        
        with tab1:
            self.show_enhanced_dashboard(df)
        
        with tab2:
            self.show_geographic_view(df)
        
        with tab3:
            self.show_enhanced_anomalies(df)
        
        with tab4:
            self.show_enhanced_risks(risk_df)
        
        with tab5:
            self.show_enhanced_insights(df, risk_df)
    
    def show_enhanced_dashboard(self, df):
        """Show enhanced dashboard with interactive charts"""
        col1, col2 = st.columns(2)
        
        with col1:
            # Time series with area chart
            monthly = df.groupby('date')[['enrolments', 'successful_enrolments']].sum().reset_index()
            fig = px.area(monthly, x='date', y=['enrolments', 'successful_enrolments'],
                         title="📈 Monthly Enrolment Trends",
                         color_discrete_map={'enrolments': '#FF9933', 'successful_enrolments': '#138808'},
                         labels={'value': 'Enrolments', 'variable': 'Type'})
            fig.update_layout(
                plot_bgcolor='rgba(255,255,255,0.9)',
                paper_bgcolor='rgba(255,255,255,0)',
                hovermode='x unified',
                font=dict(color='#333')
            )
            # FIXED: replaced use_container_width with width parameter
            st.plotly_chart(fig, use_container_width=False, width='stretch')
        
        with col2:
            # Success rate gauge
            success_rate = (df['successful_enrolments'].sum() / df['enrolments'].sum()) * 100
            
            fig = go.Figure(go.Indicator(
                mode="gauge+number+delta",
                value=success_rate,
                domain={'x': [0, 1], 'y': [0, 1]},
                title={'text': "🎯 Overall Success Rate", 'font': {'size': 20, 'color': '#333'}},
                delta={'reference': 90, 'increasing': {'color': "#138808"}},
                gauge={
                    'axis': {'range': [None, 100], 'tickwidth': 1, 'tickcolor': "#333"},
                    'bar': {'color': "#FF9933"},
                    'steps': [
                        {'range': [0, 70], 'color': 'lightgray'},
                        {'range': [70, 90], 'color': 'gray'},
                        {'range': [90, 100], 'color': 'darkgray'}
                    ],
                    'threshold': {
                        'line': {'color': "red", 'width': 4},
                        'thickness': 0.75,
                        'value': 95
                    }
                }
            ))
            fig.update_layout(
                height=400,
                font=dict(color='#333'),
                paper_bgcolor='rgba(255,255,255,0)'
            )
            # FIXED: replaced use_container_width with width parameter
            st.plotly_chart(fig, use_container_width=False, width='stretch')
        
        # State performance
        st.markdown("### 🏆 **Top Performing States**")
        
        col3, col4 = st.columns(2)
        
        with col3:
            state_totals = df.groupby('state')['enrolments'].sum().reset_index()
            state_totals = state_totals.sort_values('enrolments', ascending=False).head(8)
            
            fig = px.bar(state_totals, x='enrolments', y='state', orientation='h',
                        title="📊 Total Enrolments by State",
                        color='enrolments',
                        color_continuous_scale='Viridis')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            # FIXED: replaced use_container_width with width parameter
            st.plotly_chart(fig, use_container_width=False, width='stretch')
        
        with col4:
            state_success = df.groupby('state')['success_rate'].mean().reset_index()
            state_success = state_success.sort_values('success_rate', ascending=False).head(8)
            
            fig = px.bar(state_success, x='success_rate', y='state', orientation='h',
                        title="✅ Success Rate by State",
                        color='success_rate',
                        color_continuous_scale='Blues')
            fig.update_layout(yaxis={'categoryorder': 'total ascending'})
            # FIXED: replaced use_container_width with width parameter
            st.plotly_chart(fig, use_container_width=False, width='stretch')
    
    def show_geographic_view(self, df):
        """Show geographic visualization"""
        # Create sample geographic data
        geo_data = df.groupby('state').agg({
            'enrolments': 'sum',
            'success_rate': 'mean',
            'population_coverage': 'mean'
        }).reset_index()
        
        # Add mock coordinates
        state_coords = {
            'Maharashtra': [19.7515, 75.7139],
            'Uttar Pradesh': [26.8467, 80.9462],
            'Karnataka': [15.3173, 75.7139],
            'Tamil Nadu': [11.1271, 78.6569],
            'Delhi': [28.7041, 77.1025],
            'Gujarat': [22.2587, 71.1924],
            'Rajasthan': [27.0238, 74.2179],
            'West Bengal': [22.9868, 87.8550],
            'Bihar': [25.0961, 85.3131],
            'Telangana': [18.1124, 79.0193]
        }
        
        geo_data['lat'] = geo_data['state'].map(lambda x: state_coords.get(x, [20.5937])[0])
        geo_data['lon'] = geo_data['state'].map(lambda x: state_coords.get(x, [20.5937, 78.9629])[1])
        geo_data['size'] = geo_data['enrolments'] / geo_data['enrolments'].max() * 100
        
        fig = px.scatter_geo(geo_data,
                            lat='lat',
                            lon='lon',
                            size='size',
                            color='success_rate',
                            hover_name='state',
                            hover_data=['enrolments', 'success_rate', 'population_coverage'],
                            title='🌍 Geographic Distribution of Aadhaar Enrolments',
                            color_continuous_scale='Viridis',
                            projection='natural earth')
        
        fig.update_geos(
            showland=True,
            landcolor="lightgray",
            showcountries=True,
            showcoastlines=True
        )
        
        # FIXED: replaced use_container_width with width parameter
        st.plotly_chart(fig, use_container_width=False, width='stretch')
    
    def show_enhanced_anomalies(self, df):
        """Show enhanced anomaly analysis"""
        anomalies = df[df['is_anomaly'] == 1]
        
        if not anomalies.empty:
            # Anomaly summary cards
            st.markdown("### 🚨 **Anomaly Detection Summary**")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown(self.create_metric_card_main(
                    "Total Anomalies", 
                    len(anomalies), 
                    icon="🚨"
                ), unsafe_allow_html=True)
            
            with col2:
                st.markdown(self.create_metric_card_main(
                    "States Affected", 
                    anomalies['state'].nunique(), 
                    icon="🌍"
                ), unsafe_allow_html=True)
            
            with col3:
                avg_score = anomalies['anomaly_score'].mean() * 100
                st.markdown(self.create_metric_card_main(
                    "Avg. Severity", 
                    f"{avg_score:.1f}%", 
                    icon="⚠️"
                ), unsafe_allow_html=True)
            
            # Anomaly details
            st.markdown("### 📋 **Detected Anomalies**")
            
            display_df = anomalies[['state', 'year_month', 'enrolments', 
                                  'success_rate', 'anomaly_score']].copy()
            display_df['anomaly_score'] = display_df['anomaly_score'].apply(lambda x: f"{x*100:.1f}%")
            display_df['success_rate'] = display_df['success_rate'].apply(lambda x: f"{x*100:.1f}%")
            display_df = display_df.sort_values('enrolments', ascending=False)
            
            # FIXED: replaced use_container_width with width parameter
            st.dataframe(
                display_df.style.background_gradient(subset=['enrolments'], cmap='Oranges'),
                width='stretch',
                height=300
            )
        else:
            st.markdown("""
            <div class="glass-card" style="text-align: center; padding: 4rem;">
                <div style="font-size: 4rem; color: #4CAF50;">✅</div>
                <h3 style="color: #4CAF50;">No Anomalies Detected</h3>
                <p style="color: #666; font-size: 1.1rem;">
                    All systems are operating within normal parameters.
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    def show_enhanced_risks(self, risk_df):
        """Show enhanced risk analysis"""
        st.markdown("### ⚠️ **Risk Assessment Dashboard**")
        
        # Risk distribution
        col1, col2 = st.columns([2, 1])
        
        with col1:
            fig = px.pie(risk_df, names='risk_level', values='risk_score',
                        title="Risk Level Distribution",
                        hole=0.4,
                        color_discrete_sequence=['#FF5252', '#FF9800', '#FFC107', '#4CAF50', '#2196F3'])
            fig.update_traces(textposition='inside', textinfo='percent+label')
            fig.update_layout(
                font=dict(color='#333', size=12),
                showlegend=True
            )
            # FIXED: replaced use_container_width with width parameter
            st.plotly_chart(fig, use_container_width=False, width='stretch')
        
        with col2:
            # Risk breakdown
            st.markdown("### 📊 Risk Levels")
            for risk_level, color_class in [('CRITICAL', 'risk-critical'), ('HIGH', 'risk-high'), 
                                          ('MEDIUM', 'risk-medium'), ('LOW', 'risk-low'), ('VERY_LOW', 'risk-low')]:
                count = len(risk_df[risk_df['risk_level'] == risk_level])
                if count > 0:
                    st.markdown(f"""
                    <div class="{color_class} risk-indicator">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <span>{risk_level}</span>
                            <span style="font-size: 0.9rem; opacity: 0.9;">{count}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
    
    def show_enhanced_insights(self, df, risk_df):
        """Show enhanced insights with recommendations - IN MAIN CONTENT"""
        st.markdown("### 💡 **AI-Generated Insights**")
        
        # Calculate insights
        insights = []
        
        # Overall performance
        success_rate = (df['successful_enrolments'].sum() / df['enrolments'].sum()) * 100
        
        if success_rate > 90:
            insights.append(("success", "✅ Excellent Performance", 
                           f"Overall success rate: {success_rate:.1f}%",
                           "Maintain current operational excellence"))
        
        # Anomalies
        anomaly_count = df['is_anomaly'].sum()
        if anomaly_count > 0:
            insights.append(("warning", "⚠️ Anomalies Detected",
                           f"{anomaly_count} anomalies need review",
                           "Investigate detected anomalies in Anomalies tab"))
        
        # Risks
        if risk_df is not None:
            critical_states = risk_df[risk_df['risk_level'] == 'CRITICAL']
            if not critical_states.empty:
                insights.append(("danger", "🔴 Critical Risk Detected",
                               f"{len(critical_states)} states at critical risk level",
                               "Immediate action required - check Risks tab"))
        
        # Display insights
        if insights:
            for insight_type, title, description, action in insights:
                if insight_type == "danger":
                    st.error(f"""
                    **{title}**
                    
                    {description}
                    
                    **Action:** {action}
                    """)
                elif insight_type == "warning":
                    st.warning(f"""
                    **{title}**
                    
                    {description}
                    
                    **Action:** {action}
                    """)
                else:
                    st.success(f"""
                    **{title}**
                    
                    {description}
                    
                    **Action:** {action}
                    """)
        else:
            st.info("""
            🎉 **All Systems Optimal**
            
            All key performance indicators are within acceptable ranges.
            Continue regular monitoring and standard operating procedures.
            """)
        
        # Recommendations section
        st.markdown("### 🎯 **Recommended Actions**")
        
        col_rec1, col_rec2, col_rec3 = st.columns(3)
        
        with col_rec1:
            st.markdown("""
            <div class="glass-card">
                <h4>🔄 Immediate Actions</h4>
                <ul style="color: #555;">
                    <li>Review critical anomalies</li>
                    <li>Verify high-risk state data</li>
                    <li>Update field team priorities</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_rec2:
            st.markdown("""
            <div class="glass-card">
                <h4>📈 Short-term Goals</h4>
                <ul style="color: #555;">
                    <li>Increase coverage to 85%</li>
                    <li>Reduce anomaly rate by 30%</li>
                    <li>Improve data quality scores</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_rec3:
            st.markdown("""
            <div class="glass-card">
                <h4>🎯 Long-term Strategy</h4>
                <ul style="color: #555;">
                    <li>Implement AI monitoring</li>
                    <li>Automate reporting systems</li>
                    <li>Expand to 100% coverage</li>
                </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def run(self):
        """Main function to run the dashboard"""
        # Show header
        self.show_header()
        
        # Show sidebar - ONLY CONTROLS
        self.show_sidebar()
        
        # Mode indicator
        mode_name = "Standard Analysis" if st.session_state.mode == "standard" else "Universal Upload"
        mode_icon = "📊" if st.session_state.mode == "standard" else "🌐"
        
        st.markdown(f"""
        <div style="background: rgba(248, 249, 250, 0.9); padding: 1rem 1.5rem; border-radius: 12px; 
                    border-left: 4px solid #138808; margin: 1rem 0 2rem 0; backdrop-filter: blur(10px);">
            <div style="display: flex; justify-content: space-between; align-items: center;">
                <div style="display: flex; align-items: center; gap: 1rem;">
                    <div style="font-size: 1.8rem; background: linear-gradient(90deg, #FF9933, #138808); 
                              -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                        {mode_icon}
                    </div>
                    <div>
                        <h3 style="margin: 0; color: #333 !important;">{mode_name}</h3>
                        <p style="margin: 0; color: #666 !important; font-size: 0.9rem; font-weight: 500;">
                            {mode_icon} Active • Real-time monitoring enabled
                        </p>
                    </div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # Run the selected mode
        if st.session_state.mode == "standard":
            self.run_standard_mode()
        else:
            self.run_universal_mode()
        
        # Enhanced footer
        st.markdown("""
        <div style="margin-top: 3rem; padding: 2rem; 
                   background: linear-gradient(90deg, #1a237e 0%, #283593 100%);
                   color: white; border-radius: 20px; text-align: center;">
            <h3 style="color: white; margin-bottom: 1rem; font-size: 1.5rem;">🔐 Aadhaar Analytics Platform</h3>
            <div style="display: flex; justify-content: center; gap: 2rem; margin-bottom: 1rem; 
                      flex-wrap: wrap; font-size: 0.9rem;">
                <div style="color: rgba(255, 255, 255, 0.9);">Ministry of Electronics & IT</div>
                <div style="color: rgba(255, 255, 255, 0.7);">•</div>
                <div style="color: rgba(255, 255, 255, 0.9);">Government of India</div>
                <div style="color: rgba(255, 255, 255, 0.7);">•</div>
                <div style="color: rgba(255, 255, 255, 0.9);">UIDAI Certified</div>
            </div>
            <div style="color: rgba(255, 255, 255, 0.8); font-size: 0.8rem; margin-top: 0.5rem;">
                Version 2.0 • Secure Analytics Platform • For Authorized Use Only
            </div>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main entry point"""
    os.makedirs("data", exist_ok=True)
    dashboard = AadhaarDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()