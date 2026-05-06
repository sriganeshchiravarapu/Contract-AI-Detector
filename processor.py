import pdfplumber
import google.generativeai as genai
import json

def extract_text(uploaded_file):
    """Reads PDF or TXT files on Windows."""
    text = ""
    try:
        if uploaded_file.name.endswith('.pdf'):
            with pdfplumber.open(uploaded_file) as pdf:
                for page in pdf.pages:
                    text += page.extract_text() + "\n"
        else:
            text = uploaded_file.read().decode("utf-8")
    except Exception as e:
        return f"Error: {e}"
    return text.strip()

def analyze_contract(text, query, api_key):
    genai.configure(api_key=api_key)
    
    # --- DEBUG STEP: Print available models to your terminal ---
    print("Listing available models for your API key...")
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(f"Found: {m.name}")
    # -----------------------------------------------------------

    # Use the most direct model name
    # If gemini-1.5-flash fails, the list above will tell us why
    model = genai.GenerativeModel('gemini-2.5-flash')
    
    prompt = f"""
    Analyze the following contract based on: {query}
    
    Return JSON only:
    {{
      "party_1": "...", "party_2": "...", "risk_level": "High/Medium/Low",
      "risk_summary": "...", "payment_terms": "...",
      "termination_clause": "...", "liability_clause": "..."
    }}

    Text: {text[:10000]}
    """
    
    response = model.generate_content(prompt)
    clean_json = response.text.replace('```json', '').replace('```', '').strip()
    return json.loads(clean_json)