import logging
import os
import google.generativeai as genai

# Configure Gemini
api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
   logging.error("GEMINI_API_KEY not found")
   raise ValueError("GEMINI_API_KEY not found")

genai.configure(api_key=api_key)

# Initialize the model globally
model = genai.GenerativeModel("gemini-1.5-flash")
