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

@app.middleware("http")
async def gui_security_middleware(request, call_next):
    from fastapi.responses import HTMLResponse, JSONResponse
    expected_token = os.environ.get("YTDL_APP_TOKEN")
    if not expected_token:
        # If no token set in environment (e.g. during standalone unit test execution), allow
        return await call_next(request)

    token_param = request.query_params.get("token")
    cookie_token = request.cookies.get("ytdl_token")

    if token_param == expected_token or cookie_token == expected_token:
        response = await call_next(request)
        if token_param == expected_token and cookie_token != expected_token:
            response.set_cookie(
                key="ytdl_token",
                value=expected_token,
                httponly=True,
                samesite="strict"
            )
        return response

    if request.url.path.startswith("/api/") or request.url.path == "/ws":
        return JSONResponse(
            status_code=403,
            content={"detail": "Access Denied: YTDL can only be accessed via the official desktop GUI."}
        )

    return HTMLResponse(
        status_code=403,
        content="""<!DOCTYPE html>
<html>
<head><title>Access Denied — YTDL</title></head>
<body style="background: #0A0D14; color: #fff; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; margin: 0;">
  <div style="text-align: center; max-width: 480px; padding: 40px; border: 1px solid rgba(255,255,255,0.1); border-radius: 16px; background: #131824; box-shadow: 0 20px 50px rgba(0,0,0,0.5);">
    <div style="font-size: 3rem; margin-bottom: 16px;">⛔</div>
    <h1 style="color: #EF4444; font-size: 1.5rem; margin-bottom: 12px; font-weight: 700;">Access Denied</h1>
    <p style="color: #94A3B8; line-height: 1.6; font-size: 0.95rem;">YTDL is a standalone desktop application and cannot be accessed from an external web browser.</p>
    <p style="color: #64748B; font-size: 0.8rem; margin-top: 24px;">Please launch the official YTDL desktop GUI application to use this software.</p>
  </div>
</body>
</html>"""
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
