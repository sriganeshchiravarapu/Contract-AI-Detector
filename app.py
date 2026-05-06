import streamlit as st
import requests
import json
from processor import extract_text, analyze_contract

# --- Page Setup ---
st.set_page_config(page_title="ContractGuard AI", page_icon="🛡️", layout="wide")

# --- Custom Aesthetic CSS ---
st.markdown("""
    <style>
        /* Main background and font */
        .main {
            background-color: #f8f9fa;
            font-family: 'Inter', sans-serif;
        }
        
        /* Sidebar styling */
        .css-1d391kg {
            background-color: #ffffff;
        }
        
        /* Metric Card Styling */
        [data-testid="stMetricValue"] {
            font-size: 28px;
            color: #1E3A8A;
        }
        
        /* Custom Button Styling */
        .stButton>button {
            width: 100%;
            border-radius: 8px;
            height: 3em;
            background-color: #2563EB;
            color: white;
            border: none;
            font-weight: bold;
            transition: all 0.3s;
        }
        .stButton>button:hover {
            background-color: #1D4ED8;
            box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
        }
        
        /* Status boxes */
        .stAlert {
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.title("🛡️ ContractGuard AI")
st.caption("Advanced Risk Detection & Automation Suite")
st.divider()

# --- Settings & State ---
api_key = st.secrets.get("GEMINI_API_KEY")
n8n_url = st.secrets.get("N8N_WEBHOOK_URL")

# --- UI Layout: Sidebar & Inputs ---
with st.sidebar:
    st.header("📂 Document Center")
    uploaded_file = st.file_uploader("Upload Legal Document", type=['pdf', 'txt'])
    user_query = st.text_area("Analysis Objectives", "Identify major risks, liability gaps, and unfavorable payment terms.", height=100)
    
    if st.button("🚀 Run AI Analysis"):
        if uploaded_file and api_key:
            with st.spinner("Processing document..."):
                text = extract_text(uploaded_file)
                try:
                    analysis = analyze_contract(text, user_query, api_key)
                    st.session_state['analysis'] = analysis
                    st.session_state['full_text'] = text
                    st.toast("Analysis Successful!", icon="✅")
                except Exception as e:
                    st.error(f"Analysis failed: {e}")
        else:
            st.warning("Please upload a file and check API keys.")

# --- Main Dashboard ---
if 'analysis' in st.session_state:
    res = st.session_state['analysis']
    
    # Top Row Metrics
    m1, m2, m3, m4 = st.columns(4)
    risk = res.get('risk_level', 'Low')
    risk_color = "🔴" if risk == "High" else "🟡" if risk == "Medium" else "🟢"
    
    m1.metric("Risk Profile", f"{risk_color} {risk}")
    m2.metric("Entities", "02")
    m3.metric("Clauses Scanned", "05")
    m4.metric("AI Confidence", "High")

    # Content Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Risk Insights", "📜 Full Text", "🤖 Automation"])

    with tab1:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.subheader("Key Findings")
            # Aesthetic display of clauses
            st.markdown(f"### 🏢 Parties\n**{res.get('party_1')}** vs **{res.get('party_2')}**")
            
            with st.container(border=True):
                st.markdown(f"**💰 Payment Terms:**\n{res.get('payment_terms')}")
            with st.container(border=True):
                st.markdown(f"**🚪 Termination:**\n{res.get('termination_clause')}")
            with st.container(border=True):
                st.markdown(f"**⚖️ Liability:**\n{res.get('liability_clause')}")

        with c2:
            st.subheader("Executive Summary")
            st.info(res.get('risk_summary'))
            
            # Download analysis as JSON
            json_data = json.dumps(res, indent=4)
            st.download_button(
                label="📥 Export Report (JSON)",
                data=json_data,
                file_name="risk_analysis.json",
                mime="application/json"
            )

    with tab2:
        st.subheader("Extracted Raw Content")
        st.text_area("Document Content", st.session_state['full_text'], height=450)

    with tab3:
        st.subheader("Trigger Workflow")
        col_email, col_btn = st.columns([2, 1])
        
        with col_email:
            recipient = st.text_input("Notify Stakeholder (Email)", placeholder="legal@company.com")
        
        with col_btn:
            st.write(" ") # Spacer
            st.write(" ") # Spacer
            if st.button("📤 Send Alert"):
                if n8n_url:
                    payload = {"email": recipient, "analysis": res, "query": user_query}
                    try:
                        resp = requests.post(n8n_url, json=payload)
                        if resp.status_code == 200:
                            st.success("Notification Dispatched")
                        else:
                            st.error(f"Error: {resp.status_code}")
                    except Exception as e:
                        st.error(f"Network error: {e}")
                else:
                    st.warning("n8n Webhook URL not configured.")
else:
    # Empty State
    st.info("👈 Upload a contract in the sidebar to begin AI analysis.")