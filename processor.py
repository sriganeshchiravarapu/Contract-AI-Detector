import google.generativeai as genai
import streamlit as st
import json
import time
from pypdf import PdfReader

# --- 1. Configuration & Model Setup ---
# Use the official Gemma 4 identifier released April 2026
MODEL_ID = 'models/gemma-4-31b-it'
api_key = st.secrets.get("GEMINI_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel(MODEL_ID)
else:
    st.error("API Key missing. Please check Streamlit Secrets.")

def extract_text(uploaded_file):
    """
    Handles PDF and TXT extraction. 
    Optimized for pypdf 4.0+ (2026 standard).
    """
    try:
        if uploaded_file.type == "application/pdf":
            reader = PdfReader(uploaded_file)
            # Extracting first 15 pages to stay within token performance limits
            text = "\n".join([page.extract_text() for page in reader.pages[:15] if page.extract_text()])
            return text
        else:
            return str(uploaded_file.read(), "utf-8")
    except Exception as e:
        raise Exception(f"Extraction Error: {str(e)}")

def analyze_contract(text, user_query, api_key):
    """
    Orchestrates the Gemma 4 31B analysis.
    Forces strict JSON output to prevent dashboard 'Error' states.
    """
    
    # This 'Machine Role' prevents Gemma from adding conversational filler
    system_prompt = (
        "ROLE: Mandatory JSON Generator.\n"
        "TASK: Analyze legal text and return ONLY raw JSON.\n"
        "FORBIDDEN: Markdown fences (```), intro text, or concluding remarks.\n"
        "SCHEMA: {\n"
        "  'risk_level': 'High' | 'Medium' | 'Low',\n"
        "  'party_1': 'string', 'party_2': 'string',\n"
        "  'payment_terms': 'string', 'termination_clause': 'string',\n"
        "  'liability_clause': 'string', 'risk_summary': 'string',\n"
        "  'entity_count': 'string', 'clauses_found': 'string'\n"
        "}"
    )

    # Gemma 4 handles up to 256K, but we use a 12K snippet for rapid UI response
    input_content = f"{system_prompt}\n\nGOAL: {user_query}\n\nTEXT:\n{text[:12000]}"

    max_retries = 2
    for attempt in range(max_retries):
        try:
            response = model.generate_content(input_content)
            raw_output = response.text.strip()

            # Sanitization: Strip any accidental markdown blocks
            if "{" in raw_output:
                # Find the first { and last } to isolate the JSON
                start = raw_output.find("{")
                end = raw_output.rfind("}") + 1
                json_str = raw_output[start:end]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON detected in response")

        except (json.JSONDecodeError, ValueError) as e:
            if attempt < max_retries - 1:
                time.sleep(2) # Brief pause before retry
                continue
            # Safe Fallback to keep the Dashboard functional
            return {
                "risk_level": "Medium",
                "risk_summary": "Gemma produced an unstructured report. Check 'Full Text' tab.",
                "party_1": "Unknown", "party_2": "Unknown",
                "payment_terms": "Analysis incomplete",
                "termination_clause": "Analysis incomplete",
                "liability_clause": "Analysis incomplete",
                "entity_count": "N/A", "clauses_found": "N/A"
            }
