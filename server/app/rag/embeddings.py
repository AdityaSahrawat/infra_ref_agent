from google import genai
from google.genai import types
from app.settings import settings

client = genai.Client(api_key=settings.gemini_api_key)

EMBEDDING_MODEL = settings.gemini_embedding_model


def build_query_text(
    alert_name: str,
    service: str | None,
    severity: str,
    metrics_summary: str | None = None,
) -> str:
    return f"""
Alert Name: {alert_name}
Service: {service or "unknown"}
Severity: {severity}
Metrics Summary: {metrics_summary or ""}
""".strip()


def build_incident_text(incident) -> str:
    return f"""
Alert Name: {incident.alert_name}
Service: {incident.service or "unknown"}
Severity: {incident.severity}

Root Cause:
{incident.root_cause or ""}

Recommended Action:
{incident.recommended_action or ""}

Metrics Summary:
{incident.metrics_summary or ""}
""".strip()


def get_embedding(text: str) -> list[float]:
    response = client.models.embed_content(
        model=EMBEDDING_MODEL,
        contents=text,
        config=types.EmbedContentConfig(output_dimensionality=768),
    )

    return response.embeddings[0].values