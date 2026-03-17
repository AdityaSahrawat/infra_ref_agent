import os

from dotenv import load_dotenv
from pydantic import BaseModel, Field


# Load environment variables from .env as early as possible.
# This keeps `uvicorn app.main:app` working without needing `export`.
load_dotenv()


class Settings(BaseModel):
    database_url: str = Field(..., min_length=1, description="SQLAlchemy database URL")
    gemini_api_key: str = Field(..., min_length=1, description="Google AI Studio API key")
    gemini_model: str = Field(
        default="gemini-2.0-flash",
        description="Model name for google-genai (Google AI API)",
    )

    @classmethod
    def from_env(cls) -> "Settings":
        database_url = os.getenv("DATABASE_URL")
        gemini_api_key = os.getenv("GEMINI_API_KEY")
        gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.0-flash")

        return cls(
            database_url=database_url or "",
            gemini_api_key=gemini_api_key or "",
            gemini_model=gemini_model,
        )


settings = Settings.from_env()
