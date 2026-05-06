import streamlit as st
import requests
import json
from processor import extract_text, analyze_contract

# --- Page Setup ---
st.set_page_config(page_title="ContractGuard AI | Gemma 4", page_icon="🛡️", layout="wide")

# --- Custom Aesthetic CSS ---
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; font-family: 'Inter', sans-serif; }
        [data-testid="stMetricValue"] { font-size: 28px; color: #1E3A8A; }
        .stButton>button {
            width: 100%; border-radius: 8px; height: 3em;
            background-color: #2563EB; color: white; font-weight: bold;
        }
        .stButton>button:hover { background-color: #1D4ED8; }
    </style>
    """, unsafe_allow_html=True)

# --- Header Section ---
st.title("🛡️ ContractGuard AI")
st.caption("Powered by Gemma 4 31B | Advanced Legal Orchestration")
st.divider()

# --- Settings & State ---
# Using get to avoid crashes if keys are missing in secrets
api_key = st.secrets.get("GEMINI_API_KEY")
n8n_url = st.secrets.get("N8N_WEBHOOK_URL")

# --- UI Layout: Sidebar & Inputs ---
with st.sidebar:
    st.header("📂 Document Center")
    uploaded_file = st.file_uploader("Upload Legal Document", type=['pdf', 'txt'])
    user_query = st.text_area("Analysis Objectives", 
                             "Identify major risks, liability gaps, and unfavorable payment terms.", 
                             height=100)
    
    if st.button("🚀 Run Gemma Analysis"):
        if uploaded_file and api_key:
            with st.spinner("Gemma 4 is processing document..."):
                try:
                    text = extract_text(uploaded_file)
                    # analyze_contract now uses Gemma 4 31B logic
                    analysis = analyze_contract(text, user_query, api_key)
                    
                    # Store in session state
                    st.session_state['analysis'] = analysis
                    st.session_state['full_text'] = text
                    st.toast("Gemma Analysis Successful!", icon="✅")
                except Exception as e:
                    st.error(f"Gemma failed to analyze: {e}")
        else:
            st.warning("Please upload a file and check API keys.")

# --- Main Dashboard ---
if 'analysis' in st.session_state:
    # Ensure the analysis is treated as a dictionary (Gemma 4 returns structured JSON)
    res = st.session_state['analysis']
    if isinstance(res, str):
        try:
            res = json.loads(res)
        except:
            st.error("Gemma returned unstructured data. Check processor.py prompt.")
            st.stop()
    
    # Top Row Metrics
    m1, m2, m3, m4 = st.columns(4)
    risk = res.get('risk_level', 'Low')
    risk_color = "🔴" if risk == "High" else "🟡" if risk == "Medium" else "🟢"
    
    m1.metric("Risk Profile", f"{risk_color} {risk}")
    m2.metric("Entities", res.get('entity_count', '02'))
    m3.metric("Clauses Scanned", res.get('clauses_found', '05'))
    m4.metric("Gemma Confidence", "High")

    # Content Tabs
    tab1, tab2, tab3 = st.tabs(["📊 Risk Insights", "📜 Full Text", "🤖 Automation"])

    with tab1:
        c1, c2 = st.columns([1.5, 1])
        with c1:
            st.subheader("Key Findings")
            st.markdown(f"### 🏢 Parties\n**{res.get('party_1', 'N/A')}** vs **{res.get('party_2', 'N/A')}**")
            
            with st.container(border=True):
                st.markdown(f"**💰 Payment Terms:**\n{res.get('payment_terms', 'Not found')}")
            with st.container(border=True):
                st.markdown(f"**🚪 Termination:**\n{res.get('termination_clause', 'Not found')}")
            with st.container(border=True):
                st.markdown(f"**⚖️ Liability:**\n{res.get('liability_clause', 'Not found')}")

        with c2:
            st.subheader("Executive Summary")
            st.info(res.get('risk_summary', 'No summary generated.'))
            
            # Export Report
            json_data = json.dumps(res, indent=4)
            st.download_button(
                label="📥 Export Gemma Report (JSON)",
                data=json_data,
                file_name="gemma_risk_report.json",
                mime="application/json"
            )

    with tab2:
        st.subheader("Extracted Raw Content")
        st.text_area("Document Content", st.session_state['full_text'], height=450)

    with tab3:
        st.subheader("Trigger Automation")
        st.write("Send this Gemma 4 analysis to stakeholders via n8n.")
        
        recipient = st.text_input("Notify Stakeholder (Email)", placeholder="legal@company.com")
        
        if st.button("📤 Send Alert"):
            if n8n_url and recipient:
                # Payload format optimized for your single-agent n8n workflow
                payload = {
                    "recipient": recipient, 
                    "analysis": res, 
                    "status": "HIGH RISK ALERT" if risk == "High" else "REVIEW COMPLETE"
                }
                try:
                    resp = requests.post(n8n_url, json=payload)
                    if resp.status_code == 200:
                        st.success("Notification Dispatched via n8n")
                    else:
                        st.error(f"n8n Error: {resp.status_code}")
                except Exception as e:
                    st.error(f"Network error: {e}")
            else:
                st.warning("Ensure Email and n8n URL are ready.")
else:
    st.info("👈 Upload a contract and click 'Run Gemma Analysis' to begin.")
