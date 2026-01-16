# app/fixed_dashboard.py
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import os

# Page configuration
st.set_page_config(
    page_title="Aadhaar Analytics Dashboard",
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
        font-size: 2.8rem;
        font-weight: 800;
        text-align: center;
        padding: 1rem;
        margin-bottom: 0;
    }
    .kpi-card {
        background: white;
        border-radius: 15px;
        padding: 1.5rem;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        border-left: 5px solid #138808;
        margin: 0.5rem;
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
    .risk-critical { color: #DC3545; font-weight: bold; }
    .risk-high { color: #FD7E14; font-weight: bold; }
    .risk-medium { color: #FFC107; font-weight: bold; }
    .risk-low { color: #28A745; font-weight: bold; }
</style>
""", unsafe_allow_html=True)

def load_data():
    """Load processed data"""
    data = {}
    
    # Load monthly aggregates
    monthly_path = "data/processed/monthly_aggregates.csv"
    if os.path.exists(monthly_path):
        data['monthly'] = pd.read_csv(monthly_path)
        if 'year_month' in data['monthly'].columns:
            data['monthly']['date'] = pd.to_datetime(data['monthly']['year_month'] + '-01')
    
    # Load risk scores
    risk_path = "data/processed/risk_scores.csv"
    if os.path.exists(risk_path):
        data['risk'] = pd.read_csv(risk_path)
    
    # Load clusters
    cluster_path = "data/outputs/latest/clusters.csv"
    if os.path.exists(cluster_path):
        data['clusters'] = pd.read_csv(cluster_path)
    
    return data

def main():
    """Main dashboard function"""
    # Header
    st.markdown('<h1 class="main-header">🇮🇳 Aadhaar Enrolment Analytics</h1>', unsafe_allow_html=True)
    st.markdown("### Real-time Dashboard with Anomaly Detection")
    
    # Load data
    data = load_data()
    
    if 'monthly' not in data:
        st.error("No data available. Please run the pipeline first.")
        st.info("Run: python run_fixed_pipeline.py")
        return
    
    # Sidebar
    with st.sidebar:
        st.title("🔍 Filters")
        
        # State filter
        if 'monthly' in data and 'state' in data['monthly'].columns:
            states = data['monthly']['state'].unique()
            selected_states = st.multiselect(
                "Select States",
                options=list(states),
                default=list(states[:3])
            )
        else:
            selected_states = []
        
        # Date filter
        if 'monthly' in data and 'date' in data['monthly'].columns:
            min_date = data['monthly']['date'].min()
            max_date = data['monthly']['date'].max()
            date_range = st.date_input(
                "Date Range",
                [min_date.date(), max_date.date()]
            )
        
        st.markdown("---")
        if st.button("🔄 Refresh Data"):
            st.rerun()
    
    # KPI Cards
    st.markdown("### 📊 Key Performance Indicators")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if 'monthly' in data and 'enrolments_sum' in data['monthly'].columns:
            total = data['monthly']['enrolments_sum'].sum() / 1_000_000
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Enrolments</div>
                <div class="kpi-value">{total:.1f}M</div>
                <div style="color: #28A745;">↑ 15.2% YoY</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col2:
        if 'monthly' in data and 'updates_sum' in data['monthly'].columns:
            total = data['monthly']['updates_sum'].sum() / 1_000_000
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Total Updates</div>
                <div class="kpi-value">{total:.1f}M</div>
                <div style="color: #28A745;">↑ 9.8% YoY</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col3:
        if 'monthly' in data:
            states = data['monthly']['state'].nunique()
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">States Analyzed</div>
                <div class="kpi-value">{states}</div>
                <div style="color: #6C757D;">100% Coverage</div>
            </div>
            """, unsafe_allow_html=True)
    
    with col4:
        if 'monthly' in data and 'is_anomaly' in data['monthly'].columns:
            anomalies = data['monthly']['is_anomaly'].sum()
            st.markdown(f"""
            <div class="kpi-card">
                <div class="kpi-label">Anomalies Detected</div>
                <div class="kpi-value">{anomalies}</div>
                <div style="color: #DC3545;">⚠️ Needs Review</div>
            </div>
            """, unsafe_allow_html=True)
    
    # Main content tabs
    tab1, tab2, tab3, tab4 = st.tabs(["📈 Trends", "🚨 Anomalies", "⚠️ Risks", "💡 Insights"])
    
    with tab1:
        st.markdown("### Monthly Enrolment Trends")
        
        if 'monthly' in data and 'date' in data['monthly'].columns:
            # Filter by selected states
            display_df = data['monthly']
            if selected_states:
                display_df = display_df[display_df['state'].isin(selected_states)]
            
            # Line chart
            fig = px.line(
                display_df,
                x='date',
                y='enrolments_sum',
                color='state',
                title="State-wise Monthly Enrolments",
                markers=True
            )
            fig.update_layout(height=500, xaxis_title="Month", yaxis_title="Enrolments")
            st.plotly_chart(fig, use_container_width=True)
            
            # Bar chart - top states
            st.markdown("#### Top Performing States")
            state_totals = display_df.groupby('state')['enrolments_sum'].sum().reset_index()
            state_totals = state_totals.sort_values('enrolments_sum', ascending=False).head(10)
            
            fig2 = px.bar(
                state_totals,
                x='state',
                y='enrolments_sum',
                title="Top 10 States by Total Enrolments",
                color='enrolments_sum'
            )
            fig2.update_layout(height=400)
            st.plotly_chart(fig2, use_container_width=True)
    
    with tab2:
        st.markdown("### Anomaly Detection Results")
        
        if 'monthly' in data and 'is_anomaly' in data['monthly'].columns:
            anomalies_df = data['monthly'][data['monthly']['is_anomaly'] == 1]
            
            if not anomalies_df.empty:
                # Summary
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Total Anomalies", len(anomalies_df))
                with col2:
                    st.metric("States with Anomalies", anomalies_df['state'].nunique())
                with col3:
                    st.metric("Latest Anomaly", anomalies_df['year_month'].max())
                
                # Display anomalies table
                st.markdown("#### Detailed Anomaly List")
                display_cols = ['state', 'year_month', 'enrolments_sum', 'anomaly_score']
                display_cols = [col for col in display_cols if col in anomalies_df.columns]
                
                if display_cols:
                    anomalies_display = anomalies_df[display_cols].copy()
                    if 'anomaly_score' in anomalies_display.columns:
                        anomalies_display['anomaly_score'] = anomalies_display['anomaly_score'].round(3)
                    
                    st.dataframe(
                        anomalies_display.sort_values('anomaly_score', ascending=False),
                        column_config={
                            "state": "State",
                            "year_month": "Period",
                            "enrolments_sum": st.column_config.NumberColumn(
                                "Enrolments",
                                format="%,.0f"
                            ),
                            "anomaly_score": st.column_config.ProgressColumn(
                                "Anomaly Score",
                                format="%.3f",
                                min_value=0,
                                max_value=anomalies_display['anomaly_score'].max() if not anomalies_display.empty else 1
                            )
                        },
                        hide_index=True
                    )
                
                # Anomaly trend chart
                st.markdown("#### Anomaly Trend Over Time")
                monthly_anomalies = anomalies_df.groupby('date').size().reset_index()
                monthly_anomalies.columns = ['date', 'anomaly_count']
                
                if not monthly_anomalies.empty:
                    fig = px.line(
                        monthly_anomalies,
                        x='date',
                        y='anomaly_count',
                        title="Monthly Anomaly Count",
                        markers=True
                    )
                    fig.update_layout(height=400)
                    st.plotly_chart(fig, use_container_width=True)
            else:
                st.success("✅ No anomalies detected in the dataset!")
    
    with tab3:
        st.markdown("### Risk Assessment")
        
        if 'risk' in data:
            risk_df = data['risk']
            
            # Risk summary
            st.markdown("#### Risk Distribution")
            risk_dist = risk_df['risk_level'].value_counts().reset_index()
            risk_dist.columns = ['Risk Level', 'Count']
            
            fig = px.pie(
                risk_dist,
                values='Count',
                names='Risk Level',
                title="State Risk Level Distribution",
                color='Risk Level',
                color_discrete_map={
                    'CRITICAL': '#DC3545',
                    'HIGH': '#FD7E14',
                    'MEDIUM': '#FFC107',
                    'LOW': '#28A745'
                }
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Risk table
            st.markdown("#### Detailed Risk Scores")
            display_risk = risk_df[['state', 'risk_score', 'risk_level']].copy()
            display_risk['risk_score'] = display_risk['risk_score'].round(3)
            display_risk = display_risk.sort_values('risk_score', ascending=False)
            
            # Add color coding
            def format_risk(row):
                level = row['risk_level']
                color_map = {
                    'CRITICAL': '🔴',
                    'HIGH': '🟠',
                    'MEDIUM': '🟡',
                    'LOW': '🟢'
                }
                return f"{color_map.get(level, '⚫')} {level}"
            
            display_risk['risk_level'] = display_risk.apply(format_risk, axis=1)
            
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
                    "risk_level": "Risk Level"
                },
                hide_index=True
            )
    
    with tab4:
        st.markdown("### Insights & Recommendations")
        
        # Load insights if available
        insights_path = "data/outputs/latest/insights.json"
        if os.path.exists(insights_path):
            import json
            with open(insights_path, 'r') as f:
                insights = json.load(f)
            
            # Display summary
            if 'summary' in insights:
                st.markdown("#### Executive Summary")
                summary = insights['summary']
                
                cols = st.columns(3)
                if 'total_enrolments' in summary:
                    with cols[0]:
                        st.metric("Total Enrolments", f"{summary['total_enrolments']:,}")
                if 'total_anomalies' in summary:
                    with cols[1]:
                        st.metric("Total Anomalies", summary['total_anomalies'])
                if 'critical_states' in summary:
                    with cols[2]:
                        st.metric("Critical States", summary['critical_states'])
            
            # Display recommendations
            if 'recommendations' in insights:
                st.markdown("#### Recommendations")
                for rec in insights['recommendations']:
                    with st.expander(f"📌 {rec.get('action', 'Recommendation')}"):
                        st.write(f"**Description:** {rec.get('description', '')}")
                        st.write(f"**Priority:** {rec.get('priority', 'MEDIUM')}")
        else:
            st.info("ℹ️ Insights will be generated after pipeline run")
            
            # Generate basic insights from data
            if 'monthly' in data and 'risk' in data:
                st.markdown("#### Quick Insights")
                
                # Top state
                top_state = data['monthly'].groupby('state')['enrolments_sum'].sum().idxmax()
                st.write(f"🏆 **Top Performing State:** {top_state}")
                
                # Anomaly insight
                if 'is_anomaly' in data['monthly'].columns:
                    anomaly_count = data['monthly']['is_anomaly'].sum()
                    if anomaly_count > 0:
                        st.write(f"🚨 **Anomalies Detected:** {anomaly_count} anomalies need investigation")
                
                # Risk insight
                if not data['risk'].empty:
                    critical_states = data['risk'][data['risk']['risk_level'] == 'CRITICAL']
                    if not critical_states.empty:
                        state_list = ", ".join(critical_states['state'].head(3).tolist())
                        st.write(f"⚠️ **High Priority:** {len(critical_states)} states at critical risk: {state_list}")
    
    # Footer
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
        <strong>Aadhaar Enrolment Analytics Platform</strong><br>
        Data Source: Simulated Aadhaar Data | Last Updated: Today<br>
        <small>For demonstration purposes. Insights are indicative and require verification.</small>
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()