import os
import asyncio
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
import src.backend.state as state
from src.backend.pipeline_manager import PipelineManager
from src.backend.routes import extract, download, system
from src.backend.websocket_manager import router as ws_router, broadcast_progress, _on_pipeline_progress
from src.logger import get_logger

logger = get_logger("WebAPI")

app = FastAPI(
    title="YTDL — High Quality YouTube Video Downloader API",
    description="Backend API for YTDL web client.",
    version="2.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
async def startup_event():
    logger.info("Initializing download pipeline manager...")
    state.main_loop = asyncio.get_running_loop()
    pm = PipelineManager(
        on_stage_progress=_on_pipeline_progress,
        on_job_status=_on_pipeline_progress
    )
    state.pipeline_manager = pm
    app.state.pipeline_manager = pm
    logger.info("Pipeline manager initialized and attached to state.")

@app.on_event("shutdown")
async def shutdown_event():
    if state.pipeline_manager:
        state.pipeline_manager.shutdown()
        logger.info("Pipeline manager shut down.")

# Mount modular feature routes
app.include_router(extract.router)
app.include_router(download.router)
app.include_router(system.router)
app.include_router(ws_router)

# Mount static web frontend
web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.exists(web_dir):
    app.mount("/", StaticFiles(directory=web_dir, html=True), name="static")
else:
    logger.warning(f"Web directory not found at {web_dir}. UI will not be served.")
