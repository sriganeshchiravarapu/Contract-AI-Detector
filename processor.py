import google.generativeai as genai
import streamlit as st
import time

# 1. Configuration
# It is best practice to pull the key from st.secrets for deployment
api_key = st.secrets["GEMINI_API_KEY"]
genai.configure(api_key=api_key)

# 2. Initialize Gemma 4 31B
# This model has a higher quota than the experimental 2.5 series
MODEL_NAME = 'gemma-4-31b-it'
model = genai.GenerativeModel(MODEL_NAME)

def process_contract(text):
    """
    Analyzes legal text for risks using Gemma 4.
    Includes a retry mechanism for rate-limit stability.
    """
    prompt = f"""
    You are a professional legal risk assessor. 
    Analyze the following contract text for:
    1. High-risk clauses (Liability, Termination, Payments).
    2. Missing protections.
    3. Potential financial gaps.

    Provide a clear, structured summary of findings.
    
    CONTRACT TEXT:
    {text}
    """

    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            return response.text
        except Exception as e:
            if "429" in str(e) and attempt < max_retries - 1:
                # Wait 5 seconds before retrying if rate limited
                time.sleep(5)
                continue
            return f"Analysis Error: {str(e)}"

def extract_entities(text):
    """
    Helper function to get structured data for your dashboard's JSON view.
    """
    prompt = f"Extract the 'Effective Date', 'Parties Involved', and 'Contract Value' from this text as JSON: {text}"
    try:
        response = model.generate_content(prompt)
        return response.text
    except:
        return "{'error': 'Entity extraction failed'}"
