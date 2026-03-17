# app/main.py
from fastapi import FastAPI
from app.services.logger import configure_root_logger, get_logger
from app.api import alerts, incidents, actions  # ensure routers are imported

configure_root_logger()  # set up logging once
logger = get_logger(__name__)


def createAPP() -> FastAPI:
    app = FastAPI(title="AI MAINTAINER AGENT (MVP)")

    app.include_router(alerts.router , prefix="/alerts" , tags=["alerts"])
    app.include_router(incidents.router , prefix="/incident" , tags=["incident"])
    app.include_router(actions.router , prefix="/incident" , tags=["action"])

    @app.get("/health")
    async def health():
        return {"status" : "ok"}
    
    return app


app = createAPP()
logger.info("========FastAPI application started!!========")

