"""
Gemini_Engine/gemini_client.py
==============================
Handles all communication with Google's Gemini API.
"""

import os
from pathlib import Path
from dotenv import load_dotenv

try:
    import google.generativeai as genai
except ImportError:
    print("ERROR: Install google-generativeai driver → pip install google-generativeai")
    raise

# Load environment variables (such as GEMINI_API_KEY)
# Using parent.parent since it resides in backend/Gemini_Engine/
load_dotenv(Path(__file__).parent.parent / ".env")

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "")

if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)
else:
    # If the user runs with process env directly or hasn't supplied it
    print("[Gemini Client] Warning: GEMINI_API_KEY environment variable not found.")

def generate_report(prompt: str) -> str:
    """
    Sends the compiled investigation prompt to Gemini 1.5 Flash
    and returns the markdown investigation report.
    """
    if not os.getenv("GEMINI_API_KEY"):
        # Let's see if we can get it from the environment directly if load_dotenv didn't have it
        key = os.getenv("GEMINI_API_KEY", "")
        if not key:
            raise ValueError(
                "GEMINI_API_KEY environment variable is not configured. "
                "Please configure GEMINI_API_KEY in backend/.env"
            )
        genai.configure(api_key=key)

    # We use gemini-1.5-flash as the standard, robust model for general text and reasoning tasks
    model = genai.GenerativeModel("gemini-2.5-flash")
    
    print("[Gemini Client] Querying Gemini model...")
    response = model.generate_content(prompt)
    
    return response.text
