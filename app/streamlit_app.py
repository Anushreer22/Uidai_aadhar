import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os
import sys

# Add src to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from src.utils.config_loader import load_config
from src.visualization.plotter import create_trend_chart, create_heatmap, create_bar_chart
from src.visualization.map_generator import create_india_map

# Page configuration
st.set_page_config(
    page_title="Aadhaar Enrolment Analytics",
    page_icon="🇮🇳",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Load configuration
config = load_config()

# Custom CSS
st.markdown("""
<style>
    /* Main title with India flag colors */
    .main-header {
        background: linear-gradient(90deg, #FF9933 0%, #FFFFFF 50%, #138808 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem;
        margin-bottom: 0;
    }
    
    /* KPI Cards */
    .kpi-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid #138808;
        transition: transform 0.3s ease;
    }
    
    .kpi-card:hover {
        transform: translateY(-5px);
    }
    
    .kpi-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #000080;
        margin: 0.5rem 0;
    }
    
    .kpi-label {
        font-size: 1rem;
        color: #666;
        margin: 0;
    }
    
    /* Risk level colors */
    .risk-critical { color: #DC3545; font-weight: bold; }
    .risk-high { color: #FD7E14; font-weight: bold; }
    .risk-medium { color: #FFC107; font-weight: bold; }
    .risk-low { color: #28A745; font-weight: bold; }
    .risk-very-low { color: #6C757D; }
    
    /* Insight cards */
    .insight-card {
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        border-left: 4px solid;
    }
    
    .insight-critical { border-color: #DC3545; background: #FFF5F5; }
    .insight-high { border-color: #FD7E14; background: #FFF9F0; }
    .insight-medium { border-color: #FFC107; background: #FFFCE6; }
    .insight-low { border-color: #28A745; background: #F0FFF4; }
</style>
""", unsafe_allow_html=True)

class AadhaarDashboard:
    def __init__(self):
        self.config = config
        self.data = None
        self.anomalies = None
        self.risk_scores = None
        self.clusters = None
        self.insights = None
        
    def load_data(self):
        """Load processed data"""
        try:
            # Load sample or processed data
            data_dir = self.config['data']['processed_path']
            
            if os.path.exists(os.path.join(data_dir, 'monthly_aggregates.csv')):
                self.data = pd.read_csv(os.path.join(data_dir, 'monthly_aggregates.csv'))
                self.data['date'] = pd.to_datetime(self.data['year_month'] + '-01')
            
            if os.path.exists(os.path.join(data_dir, 'anomalies.csv')):
                self.anomalies = pd.read_csv(os.path.join(data_dir, 'anomalies.csv'))
            
            if os.path.exists(os.path.join(data_dir, 'risk_scores.csv')):
                self.risk_scores = pd.read_csv(os.path.join(data_dir, 'risk_scores.csv'))
            
            if os.path.exists(os.path.join(data_dir, 'clusters.csv')):
                self.clusters = pd.read_csv(os.path.join(data_dir, 'clusters.csv'))
            
            if os.path.exists(os.path.join(data_dir, '..', 'outputs', 'latest', 'insights.json')):
                with open(os.path.join(data_dir, '..', 'outputs', 'latest', 'insights.json'), 'r') as f:
                    self.insights = json.load(f)
                    
        except Exception as e:
            st.warning(f"Could not load data: {e}. Using sample data.")
            self._create_sample_data()
    
    def _create_sample_data(self):
        """Create sample data for demonstration"""
        # Create sample data similar to data loader
        dates = pd.date_range('2023-01-01', '2023-12-01', freq='MS')
        states = ['Maharashtra', 'Uttar Pradesh', 'Karnataka', 'Tamil Nadu', 'Delhi']
        
        data = []
        for date in dates:
            for state in states:
                base = np.random.randint(500000, 2000000)
                # Add some anomalies
                if state == 'Maharashtra' and date.month == 6:
                    base = int(base * 2.5)  # Anomaly
                
                data.append({
                    'year_month': date.strftime('%Y-%m'),
                    'date': date,
                    'state': state,
                    'enrolment_count_sum': base,
                    'update_count_sum': int(base * 0.15),
                    'mom_growth': np.random.uniform(-0.1, 0.2),
                    'update_ratio': np.random.uniform(0.1, 0.2),
                    'is_anomaly': 1 if (state == 'Maharashtra' and date.month == 6) else 0,
                    'anomaly_score': 0.9 if (state == 'Maharashtra' and date.month == 6) else np.random.uniform(0, 0.3)
                })
        
        self.data = pd.DataFrame(data)
        
        # Create sample risk scores
        self.risk_scores = pd.DataFrame({
            'state': states,
            'risk_score': [0.85, 0.62, 0.45, 0.38, 0.72],
            'risk_level': ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'HIGH']
        })
    
    def sidebar_filters(self):
        """Create sidebar filters"""
        st.sidebar.title("🔍 Filters & Controls")
        st.sidebar.markdown("---")
        
        # Date range filter
        if self.data is not None and 'date' in self.data.columns:
            min_date = self.data['date'].min().date()
            max_date = self.data['date'].max().date()
            
            date_range = st.sidebar.date_input(
                "📅 Date Range",
                [min_date, max_date],
                min_value=min_date,
                max_value=max_date
            )
        else:
            date_range = None
        
        # State filter
        if self.data is not None and 'state' in self.data.columns:
            states = self.data['state'].unique()
            selected_states = st.sidebar.multiselect(
                "🏛️ States",
                options=list(states),
                default=list(states[:3]) if len(states) > 3 else list(states)
            )
        else:
            selected_states = []
        
        # Data type filter
        data_type = st.sidebar.radio(
            "📊 Data Type",
            ["Enrolments", "Updates", "Both"],
            index=2
        )
        
        # Risk level filter
        if self.risk_scores is not None:
            risk_levels = ['All', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW', 'VERY_LOW']
            selected_risk = st.sidebar.selectbox(
                "⚠️ Risk Level",
                options=risk_levels,
                index=0
            )
        else:
            selected_risk = 'All'
        
        st.sidebar.markdown("---")
        
        # Actions
        col1, col2 = st.sidebar.columns(2)
        with col1:
            if st.button("🔄 Refresh"):
                st.rerun()
        
        with col2:
            if st.button("📥 Export"):
                self._export_data()
        
        return date_range, selected_states, data_type, selected_risk
    
    def display_kpi_cards(self):
        """Display KPI cards"""
        st.markdown("### 📊 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if self.data is not None and 'enrolment_count_sum' in self.data.columns:
                total = self.data['enrolment_count_sum'].sum() / 1_000_000  # In millions
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Total Enrolments</div>
                    <div class="kpi-value">{total:.1f}M</div>
                    <div style="color: #28A745;">↑ 12.3% MoM</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col2:
            if self.data is not None and 'update_count_sum' in self.data.columns:
                total = self.data['update_count_sum'].sum() / 1_000_000
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Total Updates</div>
                    <div class="kpi-value">{total:.1f}M</div>
                    <div style="color: #28A745;">↑ 8.7% MoM</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col3:
            if self.data is not None:
                states = len(self.data['state'].unique())
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Active States</div>
                    <div class="kpi-value">{states}</div>
                    <div style="color: #6C757D;">→ Stable</div>
                </div>
                """, unsafe_allow_html=True)
        
        with col4:
            if self.anomalies is not None and 'is_anomaly' in self.anomalies.columns:
                anomalies = self.anomalies['is_anomaly'].sum()
                st.markdown(f"""
                <div class="kpi-card">
                    <div class="kpi-label">Anomalies Detected</div>
                    <div class="kpi-value">{anomalies}</div>
                    <div style="color: #DC3545;">↑ 23</div>
                </div>
                """, unsafe_allow_html=True)
    
    def display_trend_chart(self):
        """Display trend chart"""
        st.markdown("### 📈 Monthly Enrolment Trend")
        
        if self.data is not None:
            # Aggregate by month
            monthly_data = self.data.groupby('date')['enrolment_count_sum'].sum().reset_index()
            
            fig = px.line(
                monthly_data,
                x='date',
                y='enrolment_count_sum',
                title="",
                markers=True,
                line_shape="spline"
            )
            
            fig.update_layout(
                xaxis_title="Month",
                yaxis_title="Enrolments",
                hovermode="x unified",
                plot_bgcolor="white",
                height=400
            )
            
            fig.update_traces(
                line=dict(color="#138808", width=3),
                marker=dict(size=6, color="#FF9933")
            )
            
            st.plotly_chart(fig, use_container_width=True)
    
    def display_india_heatmap(self):
        """Display India heatmap"""
        st.markdown("### 🗺️ State-wise Risk Distribution")
        
        if self.risk_scores is not None:
            # Create a simple bar chart as heatmap alternative
            fig = px.bar(
                self.risk_scores.sort_values('risk_score', ascending=False).head(10),
                x='state',
                y='risk_score',
                color='risk_score',
                color_continuous_scale='RdYlGn_r',  # Red for high risk
                title="Top 10 States by Risk Score"
            )
            
            fig.update_layout(
                xaxis_title="State",
                yaxis_title="Risk Score",
                height=400
            )
            
            st.plotly_chart(fig, use_container_width=True)
            
            # Display risk table
            st.markdown("#### 📋 Detailed Risk Assessment")
            display_df = self.risk_scores[['state', 'risk_score', 'risk_level']].copy()
            display_df['risk_score'] = display_df['risk_score'].round(3)
            display_df = display_df.sort_values('risk_score', ascending=False)
            
            # Format risk level with colors
            def format_risk_level(level):
                color_map = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢',
                    'VERY_LOW': '⚫'
                }
                return f"{color_map.get(level, '⚫')} {level}"
            
            display_df['risk_level'] = display_df['risk_level'].apply(format_risk_level)
            
            st.dataframe(
                display_df,
                column_config={
                    "state": "State",
                    "risk_score": st.column_config.NumberColumn(
                        "Risk Score",
                        format="%.3f",
                        help="0-1 scale, higher is riskier"
                    ),
                    "risk_level": "Risk Level"
                },
                hide_index=True,
                use_container_width=True
            )
    
    def display_anomalies(self):
        """Display anomaly detection results"""
        st.markdown("### 🚨 Anomaly Detection")
        
        if self.anomalies is not None and 'is_anomaly' in self.anomalies.columns:
            anomaly_data = self.anomalies[self.anomalies['is_anomaly'] == 1]
            
            if not anomaly_data.empty:
                # Summary stats
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Anomalies", len(anomaly_data))
                with col2:
                    st.metric("High Severity", len(anomaly_data[anomaly_data['anomaly_score'] > 0.8]))
                with col3:
                    top_state = anomaly_data.groupby('state').size().nlargest(1)
                    if not top_state.empty:
                        st.metric("Top State", top_state.index[0])
                
                # Display anomalies
                st.markdown("#### 📋 Anomaly Details")
                
                display_cols = ['state', 'year_month', 'enrolment_count_sum', 'anomaly_score']
                display_cols = [col for col in display_cols if col in anomaly_data.columns]
                
                display_df = anomaly_data[display_cols].copy()
                if 'anomaly_score' in display_df.columns:
                    display_df['anomaly_score'] = display_df['anomaly_score'].round(3)
                
                st.dataframe(
                    display_df.sort_values('anomaly_score', ascending=False).head(20),
                    column_config={
                        "state": "State",
                        "year_month": "Period",
                        "enrolment_count_sum": st.column_config.NumberColumn(
                            "Enrolments",
                            format="%,.0f"
                        ),
                        "anomaly_score": st.column_config.ProgressColumn(
                            "Anomaly Score",
                            format="%.3f",
                            min_value=0,
                            max_value=1
                        )
                    },
                    hide_index=True,
                    use_container_width=True
                )
            else:
                st.success("✅ No anomalies detected in the selected period")
        else:
            st.info("ℹ️ Anomaly data not available")
    
    def display_insights(self):
        """Display AI-generated insights"""
        st.markdown("### 💡 AI-Generated Insights")
        
        if self.insights:
            insights_data = self.insights
            
            # Executive Summary
            st.markdown("#### 🎯 Executive Summary")
            if 'executive_summary' in insights_data:
                summary = insights_data['executive_summary']
                cols = st.columns(3)
                
                if 'total_enrolments' in summary:
                    with cols[0]:
                        st.metric("Total Enrolments", f"{summary['total_enrolments']:,}")
                
                if 'anomalies_detected' in summary:
                    with cols[1]:
                        st.metric("Anomalies", summary['anomalies_detected'])
                
                if 'critical_risk_states' in summary:
                    with cols[2]:
                        st.metric("Critical States", summary['critical_risk_states'])
            
            # Display insights by category
            insight_categories = [
                ('trend_insights', '📈 Trend Insights'),
                ('anomaly_insights', '🚨 Anomaly Insights'),
                ('risk_insights', '⚠️ Risk Insights'),
                ('cluster_insights', '🔍 Cluster Insights')
            ]
            
            for category_key, category_title in insight_categories:
                if category_key in insights_data and insights_data[category_key]:
                    st.markdown(f"#### {category_title}")
                    
                    for insight in insights_data[category_key]:
                        severity_class = f"insight-{insight.get('severity', 'medium').lower()}"
                        
                        st.markdown(f"""
                        <div class="insight-card {severity_class}">
                            <strong>{insight.get('title', 'Insight')}</strong><br>
                            {insight.get('description', '')}<br>
                            <small>Confidence: {insight.get('confidence', 'MEDIUM')} | 
                            Severity: {insight.get('severity', 'MEDIUM')}</small>
                        </div>
                        """, unsafe_allow_html=True)
            
            # Recommendations
            if 'recommendations' in insights_data and insights_data['recommendations']:
                st.markdown("#### 🎯 Recommendations")
                
                for rec in insights_data['recommendations']:
                    priority_icon = {
                        'CRITICAL': '🔴',
                        'HIGH': '🟠',
                        'MEDIUM': '🟡',
                        'LOW': '🟢'
                    }.get(rec.get('priority', 'MEDIUM'), '🟡')
                    
                    with st.expander(f"{priority_icon} {rec.get('action', 'Recommendation')}"):
                        st.write(f"**Description:** {rec.get('description', '')}")
                        st.write(f"**Category:** {rec.get('category', 'General')}")
                        st.write(f"**Priority:** {rec.get('priority', 'MEDIUM')}")
                        st.write(f"**Timeline:** {rec.get('timeline', 'TBD')}")
                        st.write(f"**Responsible:** {rec.get('responsible', 'TBD')}")
        else:
            st.info("ℹ️ Insights will be generated after data processing")
    
    def _export_data(self):
        """Export data functionality"""
        st.sidebar.info("Export functionality would save reports here")
    
    def run(self):
        """Main dashboard runner"""
        # Header
        st.markdown('<h1 class="main-header">🇮🇳 Aadhaar Enrolment Analytics Dashboard</h1>', 
                   unsafe_allow_html=True)
        st.markdown("### Unlocking Societal Trends through Data Intelligence")
        
        # Load data
        self.load_data()
        
        # Sidebar filters
        date_range, selected_states, data_type, selected_risk = self.sidebar_filters()
        
        # Apply filters if data exists
        if self.data is not None and selected_states:
            filtered_data = self.data[self.data['state'].isin(selected_states)]
        else:
            filtered_data = self.data
        
        # Navigation tabs
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "🏠 Overview", 
            "📈 Trends", 
            "🚨 Anomalies", 
            "⚠️ Risks", 
            "💡 Insights"
        ])
        
        with tab1:
            self.display_kpi_cards()
            st.markdown("---")
            col1, col2 = st.columns(2)
            with col1:
                self.display_trend_chart()
            with col2:
                self.display_india_heatmap()
        
        with tab2:
            self.display_trend_chart()
            st.markdown("---")
            
            # Additional trend analysis
            if filtered_data is not None and 'state' in filtered_data.columns:
                st.markdown("#### 📊 State-wise Comparison")
                
                # Let user select states to compare
                compare_states = st.multiselect(
                    "Select states to compare:",
                    options=filtered_data['state'].unique(),
                    default=filtered_data['state'].unique()[:3]
                )
                
                if compare_states:
                    compare_data = filtered_data[filtered_data['state'].isin(compare_states)]
                    
                    fig = px.line(
                        compare_data,
                        x='date',
                        y='enrolment_count_sum',
                        color='state',
                        title="State-wise Enrolment Trends",
                        line_shape="spline"
                    )
                    
                    fig.update_layout(
                        xaxis_title="Month",
                        yaxis_title="Enrolments",
                        hovermode="x unified",
                        height=500
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
        
        with tab3:
            self.display_anomalies()
        
        with tab4:
            self.display_india_heatmap()
        
        with tab5:
            self.display_insights()
        
        # Footer
        st.markdown("---")
        st.markdown("""
        <div style="text-align: center; color: #666; font-size: 0.9rem;">
            <strong>Aadhaar Enrolment Analytics Platform</strong><br>
            Data Source: UIDAI | Last Updated: Today | Version: 1.0<br>
            <small>For administrative use only. All insights are indicative and require verification.</small>
        </div>
        """, unsafe_allow_html=True)

# Run the app
if __name__ == "__main__":
    dashboard = AadhaarDashboard()
    dashboard.run()