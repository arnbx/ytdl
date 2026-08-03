import asyncio
from typing import List
from fastapi import APIRouter, WebSocket, WebSocketDisconnect
import src.backend.state as state
from src.logger import get_logger

logger = get_logger("WebSocketManager")
router = APIRouter()

async def broadcast_progress():
    """Broadcasts job status updates to all connected WebSocket clients."""
    if not state.active_websockets or not state.pipeline_manager:
        return
    jobs = [state.job_to_dict(j) for j in state.pipeline_manager.jobs.values()]
    message = {"event": "progress_update", "jobs": jobs}
    disconnected = []
    for ws in state.active_websockets:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in state.active_websockets:
            state.active_websockets.remove(ws)

async def broadcast_extract_progress(message: str, current: int, total: int):
    """Broadcasts live extraction progress to all connected WebSocket clients."""
    payload = {
        "event": "extract_progress",
        "message": message,
        "current": current,
        "total": total
    }
    disconnected = []
    for ws in state.active_websockets:
        try:
            await ws.send_json(payload)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        if ws in state.active_websockets:
            state.active_websockets.remove(ws)

def _on_extract_progress(msg: str, current: int, total: int):
    try:
        loop = state.main_loop
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_extract_progress(msg, current, total), loop)
        else:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(broadcast_extract_progress(msg, current, total), loop)
            except RuntimeError:
                pass
    except Exception as e:
        logger.debug(f"Could not dispatch broadcast_extract_progress: {e}")

def _on_pipeline_progress(*args, **kwargs):
    try:
        loop = state.main_loop
        if loop and loop.is_running():
            asyncio.run_coroutine_threadsafe(broadcast_progress(), loop)
        else:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    asyncio.run_coroutine_threadsafe(broadcast_progress(), loop)
            except RuntimeError:
                pass
    except Exception as e:
        logger.debug(f"Could not dispatch broadcast_progress: {e}")

@router.websocket("/ws/progress")
async def ws_progress(websocket: WebSocket):
    await websocket.accept()
    state.active_websockets.append(websocket)
    try:
        jobs = []
        if state.pipeline_manager:
            jobs = [state.job_to_dict(j) for j in state.pipeline_manager.jobs.values()]
        await websocket.send_json({"event": "progress_update", "jobs": jobs})
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        if websocket in state.active_websockets:
            state.active_websockets.remove(websocket)
    except Exception:
        if websocket in state.active_websockets:
            state.active_websockets.remove(websocket)
