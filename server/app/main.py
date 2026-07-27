# app/main.py
from fastapi import FastAPI
from app.services.logger import configure_root_logger, get_logger
from app.api import alerts, incidents, actions  # ensure routers are imported

configure_root_logger()  # set up logging once
logger = get_logger(__name__)


def createAPP() -> FastAPI:
    app = FastAPI(title="AI MAINTAINER AGENT (MVP)")

    app.include_router(alerts.router , prefix="/alerts" , tags=["alerts"])
    app.include_router(actions.router , prefix="/incident" , tags=["action"])
    app.include_router(incidents.router , prefix="/incident" , tags=["incident"])

    @app.get("/health")
    async def health():
        return {"status": "ok"}

    @app.post("/executor/execute")
    async def execute_tool_direct(payload: dict):
        """Directly control Kubernetes without AI involved."""
        from app.executor.executor import execute_action_payload
        return execute_action_payload(payload)

    @app.post("/demo/scenarios")
    async def trigger_demo_scenarios():
        """Run all 3 demo scenarios (High CPU scale, Pod deletion self-healing, Crash remediation)."""
        from app.services.demo_scenarios import run_all_demo_scenarios
        return run_all_demo_scenarios()

    return app


app = createAPP()
logger.info("========FastAPI application started!!========")

