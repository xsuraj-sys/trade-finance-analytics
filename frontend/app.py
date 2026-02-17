
import streamlit as st
import pandas as pd
import requests
import plotly.express as px
import plotly.graph_objects as go
import os

# Configuration
API_URL = os.getenv("API_URL", "http://127.0.0.1:8000")
# Adjust path to respect running from frontend/ directory
DATA_DIR = os.path.join(os.path.dirname(__file__), "..", "processed_data")

st.set_page_config(
    page_title="Trade Finance Analytics",
    page_icon="💸",
    layout="wide",
)

@st.cache_data
def load_data():
    invoices = pd.read_csv(os.path.join(DATA_DIR, "invoices_scored.csv"))
    invoices.rename(columns={
        'id': 'Invoice ID',
        'importer_country': 'Country',
        'invoice_amount': 'Amount',
        'risk_score': 'Risk Score',
        'avg_delay_raw': 'Avg Days Late'
    }, inplace=True)
    
    exporters = pd.read_csv(os.path.join(DATA_DIR, "exporters_scored.csv"))
    return invoices, exporters

st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Dashboard Overview", "Exporter Analysis", "AI Risk Predictor"])

try:
    invoices_df, exporters_df = load_data()
except FileNotFoundError:
    st.error("Data not found. Please ensure the ETL pipeline has run.")
    st.stop()

# --- Page: Dashboard Overview ---
if page == "Dashboard Overview":
    st.title("💸 Trade Finance Risk Dashboard")
    st.markdown("### Real-time Portfolio Health & Global Exposure")
    
    col1, col2, col3, col4 = st.columns(4)
    total_exposure = invoices_df['Amount'].sum()
    avg_risk = invoices_df['Risk Score'].mean()
    high_risk_count = len(invoices_df[invoices_df['risk_category'] == 'High'])
    avg_delay = invoices_df['Avg Days Late'].mean()
    
    col1.metric("Total Exposure", f"${total_exposure:,.0f}", delta="Active deals")
    col2.metric("Portfolio Avg Delay", f"{avg_delay:.1f} Days", delta="-2.1 Days (MoM)", delta_color="inverse")
    col3.metric("High Risk Invoices", f"{high_risk_count}", delta=f"{high_risk_count/len(invoices_df):.1%}", delta_color="inverse")
    col4.metric("Avg Risk Score", f"{avg_risk:.1f}/100", delta_color="inverse")

    st.markdown("---")

    st.subheader("🚩 Critical Watchlist: High Risk Invoices")
    
    # Adding Decision Recommendation to Table
    def get_action_label(score):
        prob = score / 100.0
        if prob > 0.7: return "Reject / Review"
        elif prob >= 0.4: return "Safeguards"
        return "Approve"

    high_risk_inv = invoices_df[invoices_df['risk_category'] == 'High'][['invoice_id', 'exporter_id', 'Country', 'Amount', 'Risk Score', 'risk_explanation']].copy()
    high_risk_inv['Recommended Action'] = high_risk_inv['Risk Score'].apply(get_action_label)
    
    st.dataframe(
        high_risk_inv.style.background_gradient(subset=['Risk Score'], cmap='Reds'),
        use_container_width=True
    )
    
    col_chart1, col_chart2 = st.columns(2)
    with col_chart1:
        st.write("**Risk Exposure by Country**")
        country_risk = invoices_df.groupby('Country')[['Risk Score', 'Amount']].mean().reset_index()
        fig_map = px.choropleth(country_risk, locations="Country", locationmode="country names",
                                color="Risk Score", hover_name="Country",
                                color_continuous_scale="Reds", title="Global Risk Heatmap")
        st.plotly_chart(fig_map, use_container_width=True)

    with col_chart2:
        st.write("**Risk Category Distribution**")
        risk_dist = invoices_df['risk_category'].value_counts()
        fig_pie = px.pie(values=risk_dist.values, names=risk_dist.index, 
                         color=risk_dist.index,
                         color_discrete_map={'High': 'red', 'Medium': 'orange', 'Low': 'green'},
                         title="Portfolio Breakdown")
        st.plotly_chart(fig_pie, use_container_width=True)

# --- Page: Exporter Analysis ---
elif page == "Exporter Analysis":
    st.title("🏭 Exporter Reliability Analysis")
    selected_industry = st.selectbox("Filter by Industry", ["All"] + list(exporters_df['industry'].unique()))
    
    filtered_exporters = exporters_df
    if selected_industry != "All":
        filtered_exporters = exporters_df[exporters_df['industry'] == selected_industry]
        
    col1, col2 = st.columns([2, 1])
    with col1:
        st.subheader("Performance Matrix: Default Rate vs. Payment Delay")
        fig_scatter = px.scatter(
            filtered_exporters, 
            x="avg_payment_delay", 
            y="default_rate", 
            size="total_invoices", 
            color="industry",
            hover_name="exporter_id",
            title="Exporter Risk Landscape (Size = Volume)",
            labels={"avg_payment_delay": "Avg Payment Delay (Days)", "default_rate": "Default Rate (%)"}
        )
        fig_scatter.add_vline(x=30, line_dash="dash", line_color="orange", annotation_text="Delay Threshold")
        fig_scatter.add_hline(y=0.10, line_dash="dash", line_color="red", annotation_text="High Default Risk")
        st.plotly_chart(fig_scatter, use_container_width=True)

    with col2:
        st.subheader("Top Riskiest Exporters")
        riskiest = filtered_exporters.sort_values(by="default_rate", ascending=False).head(10)
        st.dataframe(riskiest[['exporter_id', 'default_rate', 'avg_payment_delay']], hide_index=True)

# --- Page: AI Predictor ---
elif page == "AI Risk Predictor":
    st.title("🤖 AI-Powered Deal Assessment")
    st.markdown("Use this tool to predict the **probability of payment delay** for a *new* invoice before financing.")
    
    with st.form("prediction_form"):
        col1, col2 = st.columns(2)
        with col1:
            amount = st.number_input("Invoice Amount ($)", min_value=1000, value=50000)
            exporter_age = st.slider("Exporter Company Age (Years)", 1, 100, 10)
            risk_score = st.slider("Current Risk Score (0-100)", 0, 100, 50)
        with col2:
            importer_country = st.selectbox("Importer Country", invoices_df['Country'].unique())
            industry = st.selectbox("Industry", exporters_df['industry'].unique())
            exporter_country = st.selectbox("Exporter Country", exporters_df['country'].unique())
            
        submitted = st.form_submit_button("Analyze Deal Risk")
        
        if submitted:
            payload = {
                "invoice_amount": amount,
                "risk_score": float(risk_score),
                "company_age": int(exporter_age),
                "importer_country": importer_country,
                "industry": industry,
                "exporter_country": exporter_country
            }
            
            try:
                with st.spinner("Consulting AI Model..."):
                    response = requests.post(f"{API_URL}/api/v1/predict/delay", json=payload)
                    
                if response.status_code == 200:
                    result = response.json()
                    prob = result['probability_of_delay']
                    rec = result.get('recommendation', {})
                    
                    st.success("Analysis Complete")
                    
                    # --- Prediction Results ---
                    # Top Section: Recommendation
                    st.divider()
                    st.subheader("📝 Analyst Recommendation")
                    
                    if rec.get('code') == 'RED':
                        st.error(f"**ACTION: {rec.get('action')}**")
                    elif rec.get('code') == 'AMBER':
                        st.warning(f"**ACTION: {rec.get('action')}**")
                    else:
                        st.success(f"**ACTION: {rec.get('action')}**")
                        
                    st.info(f"**Reasoning:** {rec.get('details')}")
                    st.caption(f"Business Impact: {rec.get('impact')}")
                    
                    st.divider()
                    
                    # Bottom Section: Metrics
                    res_col1, res_col2 = st.columns(2)
                    with res_col1:
                        st.metric("Probability of Delay", f"{prob:.1%}")
                        
                        # Gauge Chart
                        fig_gauge = go.Figure(go.Indicator(
                            mode = "gauge+number",
                            value = prob * 100,
                            domain = {'x': [0, 1], 'y': [0, 1]},
                            title = {'text': "Risk Probability"},
                            gauge = {
                                'axis': {'range': [None, 100]},
                                'bar': {'color': "black"},
                                'steps': [
                                    {'range': [0, 40], 'color': "lightgreen"},
                                    {'range': [40, 70], 'color': "orange"},
                                    {'range': [70, 100], 'color': "red"}
                                ],
                                'threshold': {
                                    'line': {'color': "red", 'width': 4},
                                    'thickness': 0.75,
                                    'value': prob * 100}}))
                        st.plotly_chart(fig_gauge, use_container_width=True)
                        
                    with res_col2:
                         st.write(f"**Input Summary:**")
                         st.json(result['input_summary'])

                else:
                    st.error(f"Error from API: {response.text}")
                    
            except requests.exceptions.ConnectionError:
                st.error("Cannot connect to backend server. Is FastAPI running on port 8000?")
