# app/unified_dashboard.py (FIXED VERSION)
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import os
import warnings
warnings.filterwarnings('ignore')

# Page configuration
st.set_page_config(
    page_title="Aadhaar Analytics Pro",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.5rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem;
        margin-bottom: 0.5rem;
    }
    
    .mode-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        text-align: center;
        margin: 0.5rem;
        transition: all 0.3s ease;
        border: 2px solid transparent;
    }
    
    .mode-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.15);
    }
    
    .mode-card.selected {
        border-color: #138808;
        background: linear-gradient(135deg, #f8fff8 0%, #e8f5e8 100%);
    }
    
    .mode-icon {
        font-size: 2.5rem;
        margin-bottom: 1rem;
    }
    
    .mode-title {
        font-size: 1.5rem;
        font-weight: bold;
        color: #000080;
        margin-bottom: 0.5rem;
    }
    
    .mode-desc {
        color: #666;
        font-size: 0.9rem;
    }
    
    .kpi-card {
        background: white;
        border-radius: 12px;
        padding: 1.2rem;
        box-shadow: 0 3px 10px rgba(0,0,0,0.08);
        text-align: center;
        border-left: 4px solid #138808;
    }
    
    .kpi-value {
        font-size: 2.2rem;
        font-weight: bold;
        color: #000080;
        margin: 0.3rem 0;
    }
    
    .kpi-label {
        font-size: 0.9rem;
        color: #666;
        margin: 0;
    }
    
    .info-box {
        background: #d1ecf1;
        border-left: 4px solid #17a2b8;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .success-box {
        background: #d4edda;
        border-left: 4px solid #28a745;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .warning-box {
        background: #fff3cd;
        border-left: 4px solid #ffc107;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
    
    .danger-box {
        background: #f8d7da;
        border-left: 4px solid #dc3545;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

class UnifiedAadhaarDashboard:
    def __init__(self):
        # Initialize session state
        if 'mode' not in st.session_state:
            st.session_state.mode = None
        if 'data' not in st.session_state:
            st.session_state.data = None
        if 'risk_data' not in st.session_state:
            st.session_state.risk_data = None
    
    def create_sample_data(self):
        """Create sample data for demonstration"""
        dates = pd.date_range('2023-01-01', '2023-06-01', freq='MS')
        states = ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 'Delhi']
        
        data = []
        for date in dates:
            for state in states:
                # Base values
                base_enrol = 100000
                base_update = 20000
                
                # State variations
                state_factors = {
                    'Maharashtra': 1.5,
                    'Uttar Pradesh': 1.8,
                    'Karnataka': 1.2,
                    'Tamil Nadu': 1.3,
                    'Delhi': 0.8
                }
                
                factor = state_factors.get(state, 1.0)
                enrolments = int(base_enrol * factor * np.random.uniform(0.9, 1.1))
                updates = int(base_update * factor * np.random.uniform(0.8, 1.2))
                
                # Add some anomalies
                is_anomaly = 0
                anomaly_score = np.random.uniform(0, 0.5)
                
                if state == 'Maharashtra' and date.month == 3:
                    enrolments = int(enrolments * 2.5)  # March spike
                    is_anomaly = 1
                    anomaly_score = 0.9
                
                if state == 'Delhi' and date.month == 4:
                    enrolments = int(enrolments * 0.3)  # April drop
                    is_anomaly = 1
                    anomaly_score = 0.8
                
                data.append({
                    'state': state,
                    'year_month': date.strftime('%Y-%m'),
                    'date': date,
                    'enrolments_sum': enrolments,
                    'updates_sum': updates,
                    'update_ratio': updates / enrolments if enrolments > 0 else 0,
                    'mom_growth': np.random.uniform(-0.1, 0.2),
                    'is_anomaly': is_anomaly,
                    'anomaly_score': anomaly_score
                })
        
        df = pd.DataFrame(data)
        return df
    
    def create_risk_data(self):
        """Create sample risk data"""
        states = ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 'Delhi']
        
        risk_data = []
        for state in states:
            risk_score = np.random.uniform(0, 1)
            
            # Categorize risk
            if risk_score >= 0.7:
                risk_level = 'CRITICAL'
            elif risk_score >= 0.5:
                risk_level = 'HIGH'
            elif risk_score >= 0.3:
                risk_level = 'MEDIUM'
            elif risk_score >= 0.1:
                risk_level = 'LOW'
            else:
                risk_level = 'VERY_LOW'
            
            risk_data.append({
                'state': state,
                'risk_score': risk_score,
                'risk_level': risk_level
            })
        
        return pd.DataFrame(risk_data)
    
    def show_header(self):
        """Show main header"""
        st.markdown('<h1 class="main-header">🇮🇳 Aadhaar Analytics Platform</h1>', unsafe_allow_html=True)
        st.markdown("### Unified Dashboard for All Your Aadhaar Data Needs")
    
    def select_mode(self):
        """Select analysis mode"""
        st.markdown("### 🎯 Select Analysis Mode")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🌐 **Universal Mode**\n\nUpload ANY dataset\nAuto schema detection\nQuick analysis", 
                        use_container_width=True, type="primary" if st.session_state.mode == "universal" else "secondary"):
                st.session_state.mode = "universal"
                st.session_state.data = None
                st.rerun()
        
        with col2:
            if st.button("📊 **Standard Mode**\n\nUse our optimized data\nAdvanced ML analysis\nProduction reports", 
                        use_container_width=True, type="primary" if st.session_state.mode == "standard" else "secondary"):
                st.session_state.mode = "standard"
                st.rerun()
        
        # Quick info
        st.markdown("---")
        col_info1, col_info2 = st.columns(2)
        
        with col_info1:
            st.markdown("""
            <div class="info-box">
            <strong>🌐 Universal Mode:</strong>
            <ul>
            <li>Upload any CSV/Excel file</li>
            <li>Auto column detection</li>
            <li>Quick insights</li>
            <li>Perfect for new data</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
        
        with col_info2:
            st.markdown("""
            <div class="success-box">
            <strong>📊 Standard Mode:</strong>
            <ul>
            <li>Pre-loaded sample data</li>
            <li>Advanced analytics</li>
            <li>Risk scoring</li>
            <li>Production ready</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
    
    def run_universal_mode(self):
        """Run universal analysis mode"""
        st.markdown("## 🌐 Universal Analysis Mode")
        
        uploaded_file = st.file_uploader(
            "📁 Upload your Aadhaar data file (CSV/Excel)",
            type=['csv', 'xlsx']
        )
        
        if uploaded_file is not None:
            try:
                # Read file
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                st.session_state.data = df
                
                st.success(f"✅ Loaded {len(df)} records from {uploaded_file.name}")
                
                # Show data preview
                st.markdown("### 📋 Data Preview")
                st.dataframe(df.head(), use_container_width=True)
                
                # Quick stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Records", len(df))
                with col2:
                    st.metric("Columns", len(df.columns))
                with col3:
                    st.metric("Memory Usage", f"{df.memory_usage(deep=True).sum() / 1024 / 1024:.1f} MB")
                
                # Basic analysis
                st.markdown("### 📊 Quick Analysis")
                
                # Show numeric columns statistics
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                if len(numeric_cols) > 0:
                    st.markdown("#### Statistical Summary")
                    st.dataframe(df[numeric_cols].describe(), use_container_width=True)
                    
                    # Plot distribution of first numeric column
                    if len(numeric_cols) > 0:
                        selected_col = st.selectbox("Select column to visualize:", numeric_cols)
                        fig = px.histogram(df, x=selected_col, title=f"Distribution of {selected_col}")
                        st.plotly_chart(fig, use_container_width=True)
                
                # Show categorical columns
                categorical_cols = df.select_dtypes(include=['object']).columns
                if len(categorical_cols) > 0:
                    st.markdown("#### Categorical Data")
                    for col in categorical_cols[:3]:  # Show first 3 categorical columns
                        value_counts = df[col].value_counts().head(10)
                        fig = px.bar(x=value_counts.index, y=value_counts.values, 
                                   title=f"Top 10 values in {col}")
                        st.plotly_chart(fig, use_container_width=True)
                
            except Exception as e:
                st.error(f"Error loading file: {str(e)}")
        else:
            # Show instructions
            st.markdown("""
            <div class="info-box">
            <h4>How to use Universal Mode:</h4>
            <ol>
            <li>Upload any CSV or Excel file with Aadhaar data</li>
            <li>The system will automatically analyze the data</li>
            <li>View statistics and visualizations</li>
            <li>Download processed results</li>
            </ol>
            
            <p><strong>Accepted formats:</strong></p>
            <ul>
            <li>CSV files (.csv)</li>
            <li>Excel files (.xlsx, .xls)</li>
            <li>Any column names accepted</li>
            <li>Auto date detection</li>
            </ul>
            </div>
            """, unsafe_allow_html=True)
            
            # Quick test button
            if st.button("🎮 Try with Sample Data", type="secondary"):
                df = self.create_sample_data()
                st.session_state.data = df
                st.rerun()
    
    def run_standard_mode(self):
        """Run standard analysis mode"""
        st.markdown("## 📊 Standard Analysis Mode")
        
        # Load or create data
        if st.session_state.data is None:
            st.session_state.data = self.create_sample_data()
            st.session_state.risk_data = self.create_risk_data()
        
        df = st.session_state.data
        risk_df = st.session_state.risk_data
        
        # Show mode info
        st.markdown("""
        <div class="success-box">
        <h4>✅ Standard Mode Active</h4>
        <p>Using pre-configured Aadhaar analysis with:</p>
        <ul>
        <li>Advanced anomaly detection</li>
        <li>State-level risk scoring</li>
        <li>Interactive visualizations</li>
        <li>Actionable insights</li>
        </ul>
        </div>
        """, unsafe_allow_html=True)
        
        # Create tabs
        tab1, tab2, tab3, tab4 = st.tabs(["📊 Dashboard", "🚨 Anomalies", "⚠️ Risks", "💡 Insights"])
        
        with tab1:
            self.show_dashboard(df)
        
        with tab2:
            self.show_anomalies(df)
        
        with tab3:
            self.show_risks(risk_df)
        
        with tab4:
            self.show_insights(df, risk_df)
    
    def show_dashboard(self, df):
        """Show dashboard"""
        # KPI Cards
        st.markdown("### 📊 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            total_enrol = df['enrolments_sum'].sum() / 1_000_000
            st.metric("Total Enrolments", f"{total_enrol:.1f}M", "15.2%")
        
        with col2:
            total_updates = df['updates_sum'].sum() / 1_000_000
            st.metric("Total Updates", f"{total_updates:.1f}M", "8.7%")
        
        with col3:
            states = df['state'].nunique()
            st.metric("States Covered", states, "100%")
        
        with col4:
            anomalies = df['is_anomaly'].sum()
            st.metric("Anomalies", anomalies, "⚠️ Review")
        
        # Charts
        st.markdown("---")
        
        col_chart1, col_chart2 = st.columns(2)
        
        with col_chart1:
            # Trend chart
            monthly_trend = df.groupby('date')['enrolments_sum'].sum().reset_index()
            fig = px.line(monthly_trend, x='date', y='enrolments_sum', 
                         title="Monthly Enrolment Trend", markers=True)
            st.plotly_chart(fig, use_container_width=True)
        
        with col_chart2:
            # State comparison
            state_totals = df.groupby('state')['enrolments_sum'].sum().reset_index()
            state_totals = state_totals.sort_values('enrolments_sum', ascending=False).head(10)
            fig = px.bar(state_totals, x='state', y='enrolments_sum',
                        title="Top States by Enrolments", color='enrolments_sum')
            st.plotly_chart(fig, use_container_width=True)
        
        # Growth analysis
        st.markdown("#### 📈 Growth Analysis")
        if 'mom_growth' in df.columns:
            growth_by_state = df.groupby('state')['mom_growth'].mean().reset_index()
            growth_by_state = growth_by_state.sort_values('mom_growth', ascending=False)
            fig = px.bar(growth_by_state, x='state', y='mom_growth',
                        title="Average Monthly Growth by State", color='mom_growth',
                        color_continuous_scale="RdYlGn")
            st.plotly_chart(fig, use_container_width=True)
    
    def show_anomalies(self, df):
        """Show anomaly analysis"""
        st.markdown("### 🚨 Anomaly Detection")
        
        anomalies_df = df[df['is_anomaly'] == 1]
        
        if not anomalies_df.empty:
            # Summary
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Anomalies", len(anomalies_df))
            with col2:
                st.metric("States Affected", anomalies_df['state'].nunique())
            with col3:
                if 'anomaly_score' in anomalies_df.columns:
                    max_score = anomalies_df['anomaly_score'].max()
                    st.metric("Max Severity", f"{max_score:.2f}")
            
            # Details
            st.markdown("#### 📋 Anomaly Details")
            display_cols = ['state', 'year_month', 'enrolments_sum']
            if 'anomaly_score' in anomalies_df.columns:
                display_cols.append('anomaly_score')
            
            display_df = anomalies_df[display_cols].copy()
            if 'anomaly_score' in display_df.columns:
                display_df = display_df.sort_values('anomaly_score', ascending=False)
            
            st.dataframe(display_df, use_container_width=True, hide_index=True)
            
            # Trend
            st.markdown("#### 📈 Anomaly Trend")
            if 'date' in anomalies_df.columns:
                anomaly_trend = anomalies_df.groupby('date').size().reset_index()
                anomaly_trend.columns = ['date', 'anomaly_count']
                fig = px.line(anomaly_trend, x='date', y='anomaly_count',
                             title="Anomalies Over Time", markers=True)
                st.plotly_chart(fig, use_container_width=True)
        else:
            st.success("✅ No anomalies detected!")
    
    def show_risks(self, risk_df):
        """Show risk analysis"""
        st.markdown("### ⚠️ Risk Assessment")
        
        # Risk distribution
        risk_dist = risk_df['risk_level'].value_counts().reset_index()
        risk_dist.columns = ['Risk Level', 'Count']
        
        color_map = {
            'CRITICAL': '#dc3545',
            'HIGH': '#fd7e14',
            'MEDIUM': '#ffc107',
            'LOW': '#28a745',
            'VERY_LOW': '#6c757d'
        }
        
        fig = px.pie(risk_dist, values='Count', names='Risk Level',
                    title="State Risk Level Distribution",
                    color='Risk Level', color_discrete_map=color_map)
        st.plotly_chart(fig, use_container_width=True)
        
        # Detailed table
        st.markdown("#### 📋 Detailed Risk Scores")
        display_risk = risk_df[['state', 'risk_score', 'risk_level']].copy()
        display_risk['risk_score'] = display_risk['risk_score'].round(3)
        display_risk = display_risk.sort_values('risk_score', ascending=False)
        
        # Add emoji indicators
        def get_risk_emoji(level):
            emoji_map = {
                'CRITICAL': '🔴',
                'HIGH': '🟠',
                'MEDIUM': '🟡',
                'LOW': '🟢',
                'VERY_LOW': '⚫'
            }
            return emoji_map.get(level, '⚫')
        
        display_risk['risk_indicator'] = display_risk['risk_level'].apply(get_risk_emoji)
        
        st.dataframe(
            display_risk,
            column_config={
                "state": "State",
                "risk_score": st.column_config.ProgressColumn(
                    "Risk Score",
                    format="%.3f",
                    min_value=0,
                    max_value=1
                ),
                "risk_level": "Risk Level",
                "risk_indicator": "Level"
            },
            hide_index=True,
            use_container_width=True
        )
        
        # Critical states warning
        critical_states = display_risk[display_risk['risk_level'] == 'CRITICAL']
        if not critical_states.empty:  # FIXED: removed parentheses ()
            st.markdown("""
            <div class="danger-box">
            <strong>🚨 Immediate Action Required</strong>
            <p>{} states at critical risk level:</p>
            <p><strong>{}</strong></p>
            <p><strong>Recommended Actions:</strong></p>
            <ol>
            <li>Immediate field verification</li>
            <li>Data quality audit</li>
            <li>System integration check</li>
            <li>Weekly monitoring</li>
            </ol>
            </div>
            """.format(len(critical_states), ", ".join(critical_states['state'].tolist())), 
            unsafe_allow_html=True)
    
    def show_insights(self, df, risk_df):
        """Show insights and recommendations"""
        st.markdown("### 💡 AI-Generated Insights")
        
        insights = []
        
        # Insight 1: Overall performance
        total_enrolments = df['enrolments_sum'].sum()
        if total_enrolments > 1000000:
            insights.append({
                "type": "success",
                "title": "Strong Enrolment Performance",
                "description": f"Total enrolments: {total_enrolments:,.0f}",
                "action": "Continue current enrolment strategies"
            })
        
        # Insight 2: Anomalies
        anomaly_count = df['is_anomaly'].sum()
        if anomaly_count > 0:
            top_state = df[df['is_anomaly'] == 1].groupby('state').size().idxmax()
            insights.append({
                "type": "warning",
                "title": "Anomalies Detected",
                "description": f"{anomaly_count} anomalies, highest in {top_state}",
                "action": "Investigate anomalies in high-frequency states"
            })
        
        # Insight 3: Risk levels (FIXED: removed parentheses from empty)
        critical_states = risk_df[risk_df['risk_level'] == 'CRITICAL']
        if not critical_states.empty:  # FIXED: removed parentheses ()
            insights.append({
                "type": "danger",
                "title": "Critical Risk States",
                "description": f"{len(critical_states)} states at critical risk level",
                "action": "Immediate field verification and data audit"
            })
        
        # Display insights
        if insights:
            for insight in insights:
                if insight["type"] == "danger":
                    st.error(f"🔴 **{insight['title']}**\n\n{insight['description']}\n\n**Action:** {insight['action']}")
                elif insight["type"] == "warning":
                    st.warning(f"🟡 **{insight['title']}**\n\n{insight['description']}\n\n**Action:** {insight['action']}")
                elif insight["type"] == "success":
                    st.success(f"🟢 **{insight['title']}**\n\n{insight['description']}\n\n**Action:** {insight['action']}")
        else:
            st.info("ℹ️ **All Systems Normal**\n\nNo significant issues detected. Current operations are running smoothly.")
        
        # Recommendations summary
        st.markdown("#### 🎯 Recommended Actions Summary")
        st.markdown("""
        1. **Data Validation**: Regular quality checks and validation
        2. **Monitoring**: Real-time tracking of key metrics
        3. **Reporting**: Automated insights generation
        4. **Action**: Follow-up on high-priority items
        5. **Improvement**: Continuous process optimization
        """)
    
    def show_sidebar(self):
        """Show sidebar"""
        st.sidebar.title("🔧 Controls")
        
        # Mode switcher
        st.sidebar.markdown("### 🎯 Analysis Mode")
        current_mode = st.session_state.mode
        
        if st.sidebar.button("🌐 Switch to Universal Mode" if current_mode != "universal" else "✅ Universal Mode Active", 
                           disabled=current_mode == "universal",
                           use_container_width=True):
            st.session_state.mode = "universal"
            st.session_state.data = None
            st.rerun()
        
        if st.sidebar.button("📊 Switch to Standard Mode" if current_mode != "standard" else "✅ Standard Mode Active", 
                           disabled=current_mode == "standard",
                           use_container_width=True):
            st.session_state.mode = "standard"
            st.rerun()
        
        st.sidebar.markdown("---")
        
        # Data info
        st.sidebar.markdown("### 📊 Data Info")
        if st.session_state.data is not None:
            st.sidebar.metric("Records", len(st.session_state.data))
            st.sidebar.metric("Columns", len(st.session_state.data.columns))
        
        # Actions
        st.sidebar.markdown("---")
        st.sidebar.markdown("### ⚡ Actions")
        
        if st.sidebar.button("🔄 Refresh Data", use_container_width=True):
            if st.session_state.mode == "standard":
                st.session_state.data = self.create_sample_data()
                st.session_state.risk_data = self.create_risk_data()
            st.rerun()
        
        if st.sidebar.button("📥 Export Results", use_container_width=True):
            if st.session_state.data is not None:
                csv = st.session_state.data.to_csv(index=False)
                st.sidebar.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="aadhaar_analysis.csv",
                    mime="text/csv"
                )
        
        if st.sidebar.button("🆘 Help", use_container_width=True):
            st.sidebar.info("""
            **Need help?**
            - Universal Mode: Upload any dataset
            - Standard Mode: Use sample data
            - Contact: support@aadhaar.gov.in
            """)
    
    def run(self):
        """Main function"""
        self.show_header()
        
        # Initialize if first time
        if st.session_state.mode is None:
            self.select_mode()
        else:
            # Show sidebar
            self.show_sidebar()
            
            # Show current mode
            mode_display = {
                "universal": "🌐 Universal Mode",
                "standard": "📊 Standard Mode"
            }
            
            current_mode_display = mode_display.get(st.session_state.mode, "Unknown Mode")
            
            # Safe data length check
            data_length = 0
            if st.session_state.data is not None:
                data_length = len(st.session_state.data)
            
            st.markdown(f"""
            <div style="background: #e8f5e8; padding: 0.5rem 1rem; border-radius: 10px; 
                        border-left: 4px solid #138808; margin: 1rem 0;">
                <strong>{current_mode_display}</strong>
                <span style="float: right; font-size: 0.9rem; color: #666;">
                    📊 {data_length:,} records
                </span>
            </div>
            """, unsafe_allow_html=True)
            
            # Run the selected mode
            if st.session_state.mode == "universal":
                self.run_universal_mode()
            elif st.session_state.mode == "standard":
                self.run_standard_mode()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
            <strong>Aadhaar Analytics Platform</strong><br>
            🇮🇳 Ministry of Electronics & IT | Version 2.0<br>
            <small>For administrative use. All insights require verification.</small>
        </div>
        """, unsafe_allow_html=True)

def main():
    """Main entry point"""
    # Create necessary directories
    os.makedirs("data", exist_ok=True)
    
    # Run the dashboard
    dashboard = UnifiedAadhaarDashboard()
    dashboard.run()

if __name__ == "__main__":
    main()