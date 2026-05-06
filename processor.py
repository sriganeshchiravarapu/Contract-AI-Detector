import google.generativeai as genai
import streamlit as st
import json
import re
from PyPDF2 import PdfReader

# 1. Initialize Gemma 4 31B
# Ensure your Streamlit secrets has GEMINI_API_KEY
api_key = st.secrets.get("GEMINI_API_KEY")
genai.configure(api_key=api_key)

# The production identifier for Gemma 4 31B
MODEL_NAME = 'models/gemma-4-31b-it'
model = genai.GenerativeModel(MODEL_NAME)

def extract_text(uploaded_file):
    """Extracts text from PDF or TXT files."""
    if uploaded_file.type == "application/pdf":
        reader = PdfReader(uploaded_file)
        text = ""
        for page in reader.pages:
            text += page.extract_text()
        return text
    else:
        return str(uploaded_file.read(), "utf-8")

def analyze_contract(text, user_query, api_key):
    """
    Uses Gemma 4 31B to perform a deep legal analysis.
    Returns a structured dictionary for the dashboard.
    """
    
    # SYSTEM PROMPT: Forces Gemma to output clean JSON
    system_instruction = (
        "You are a Senior Legal AI. Analyze the contract text and output ONLY a valid JSON object. "
        "Do not include conversational filler, markdown code blocks (like ```json), or notes. "
        "The JSON must have these exact keys: "
        "'risk_level' (High/Medium/Low), 'party_1', 'party_2', 'payment_terms', "
        "'termination_clause', 'liability_clause', 'risk_summary', 'entity_count', 'clauses_found'."
    )

    prompt = f"{system_instruction}\n\nUser Analysis Goal: {user_query}\n\nContract Text:\n{text[:10000]}" # Limit to 10k chars for speed

    try:
        response = model.generate_content(prompt)
        
        # Clean the response string in case Gemma adds markdown backticks
        clean_json = response.text.replace('```json', '').replace('```', '').strip()
        
        # Parse into a Python dictionary
        analysis_dict = json.loads(clean_json)
        return analysis_dict
        
    except json.JSONDecodeError:
        # Fallback if the AI fails to output valid JSON
        return {
            "risk_level": "Error",
            "risk_summary": "Gemma failed to generate a structured JSON report. Please try again.",
            "party_1": "Unknown", "party_2": "Unknown",
            "payment_terms": "Error", "termination_clause": "Error", "liability_clause": "Error"
        }
    except Exception as e:
        raise Exception(f"Gemma 4 Error: {str(e)}")
