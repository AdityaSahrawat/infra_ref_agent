"""
End-to-End integration test for Alert ingestion -> LLM Tool Call -> Kubernetes Execution -> DB Persistence.
"""

from unittest.mock import patch
from app.agents.agent import handle_alert
from app.database.engine import SessionLocal
from app.database.models import Action, Incident


def test_agent_auto_execution_flow():
    """Test critical alert triggering auto-executed Kubernetes scaling action."""
    mock_llm_response = {
        "tool": "scale_deployment",
        "args": {"deployment": "auth-api", "replicas": 3},
        "confidence": 0.92,
        "root_cause": "High CPU utilization detected",
        "recommended_action": "Scale auth-api deployment to 3 replicas",
    }

    mock_context = {
        "similar_incidents": [],
        "service_history": [],
        "alert_history": [],
    }

    with patch("app.agents.agent.analyze_incident_with_llm", return_value=mock_llm_response), \
         patch("app.agents.agent.get_embedding", return_value=[0.1] * 768), \
         patch("app.agents.agent.retrieve_context", return_value=mock_context):

        alert_payload = {
            "status": "firing",
            "labels": {
                "alertname": "HighCPUUsage",
                "severity": "critical",
                "service": "auth-api",
                "instance": "auth-api-7b89f4c5d-x9z1a",
            },
            "annotations": {
                "summary": "CPU usage exceeded 90% threshold for 5m",
            },
            "startsAt": "2026-07-27T08:00:00Z",
        }

        handle_alert(alert_payload)

        # Query database to verify Incident & Action status
        db = SessionLocal()
        try:
            incident = (
                db.query(Incident)
                .filter(Incident.alert_name == "HighCPUUsage")
                .order_by(Incident.created_at.desc())
                .first()
            )
            assert incident is not None
            assert incident.root_cause == "High CPU utilization detected"
            assert incident.llm_confidence == 0.92
            assert incident.status == "resolved"

            actions = db.query(Action).filter(Action.incident_id == incident.id).all()
            assert len(actions) == 1
            action = actions[0]
            assert action.status == "executed"
            assert action.action_type == "scale_deployment"
            assert action.action_payload["tool"] == "scale_deployment"
            assert action.action_payload["result"]["replicas"] == 3
            assert action.executed_at is not None
        finally:
            db.close()
