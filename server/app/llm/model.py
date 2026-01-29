import os
import json
import google.generativeai as genai

# 1️⃣ Configure Gemini once
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel("gemini-1.5-flash")




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
        response = model.generate_content(prompt)
        text = response.text.strip()

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
