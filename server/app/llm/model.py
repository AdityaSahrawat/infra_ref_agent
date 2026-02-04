import json
import re
from app.config import model

def analyze_incident_with_llm(incident: dict) -> dict:
    """
    Pure function:
    incident data -> structured LLM advice

    NEVER:
    - write to DB
    - create actions
    - change system state
    """

    prompt = f"""
        You are an expert Site Reliability Engineer.

        Analyze the following incident and respond ONLY with valid JSON
        having exactly these keys:
        - root_cause (string or null)
        - recommended_action (string or null)
        - confidence (number between 0 and 1)

        Incident data:
        {json.dumps(incident, indent=2)}

        Rules:
        - Do not include explanations
        - Do not include markdown
        - Do not include extra keys
        """

    try:
        response = model(
            model="gemini-1.5-flash",
            contents=prompt
        )
        text = response.text.strip()

        # Clean markdown code blocks if present
        if text.startswith("```"):
            # Remove opening ```json or just ```
            text = re.sub(r"^```[a-zA-Z]*\n", "", text)
            # Remove closing ```
            text = re.sub(r"\n```$", "", text)
            text = text.strip()

        result = json.loads(text)

        # Defensive normalization
        return {
            "root_cause": result.get("root_cause"),
            "recommended_action": result.get("recommended_action"),
            "confidence": float(result.get("confidence", 0.0)),
        }

    except Exception as e:
        # HARD GUARANTEE: never break the system
        return {
            "root_cause": "LLM analysis failed",
            "recommended_action": None,
            "confidence": 0.0,
        }
