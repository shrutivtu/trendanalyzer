import os
from dotenv import load_dotenv
import google.generativeai as genai

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Gemini API key missing in .env")
else:
    genai.configure(api_key=GEMINI_API_KEY)


def gemini_pro(prompt, model="gemini-1.5-pro-latest"):
    """
    Calls Gemini 1.5 Pro (correct model name for generateContent).
    """
    try:
        mdl = genai.GenerativeModel(model)
        response = mdl.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"Gemini error: {e}"
