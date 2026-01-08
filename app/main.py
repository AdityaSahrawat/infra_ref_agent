# app/main.py
from fastapi import FastAPI
from app.services.logger import configure_root_logger, get_logger
from app.api import alerts, incidents  # ensure routers are imported

configure_root_logger()  # set up logging once
logger = get_logger(__name__)

app = FastAPI(title="AI Maintainer Agent (MVP)")

# include routers
app.include_router(alerts.router, prefix="", tags=["alerts"])
app.include_router(incidents.router, prefix="", tags=["incidents"])

@app.get("/health")
async def health():
    return {"status": "ok"}
