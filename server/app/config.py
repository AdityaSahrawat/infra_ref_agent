import logging
import os
from google import genai

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
   logging.error("GEMINI_API_KEY not found")
   raise ValueError("GEMINI_API_KEY not found")

GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

# Initialize the client and model globally
client = genai.Client(api_key=api_key)
model = client.models.generate_content
