from google import genai

from app.settings import settings

# Configure Gemini
GEMINI_MODEL = settings.gemini_model

# Initialize the client and model globally
client = genai.Client(api_key=settings.gemini_api_key)
model = client.models.generate_content
