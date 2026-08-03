import asyncio
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import src.backend.state as state
from src.backend.models import VideoMetadata
from src.backend.extractor import (
    ExtractorThread,
    get_available_resolutions,
    get_available_audio_bitrates,
    group_playlist_videos,
)
from src.backend.websocket_manager import _on_extract_progress
from src.logger import get_logger

logger = get_logger("ExtractRoute")
router = APIRouter()

class ExtractRequest(BaseModel):
    url: str

class AnalyzeSelectedRequest(BaseModel):
    url: str
    selected_indices: List[int]

class GroupRequest(BaseModel):
    target_video_res: str = "(Best Available)"
    target_audio_bitrate: float = -1.0
    mode: str = "video_audio"
    tiers: Optional[List[Dict[str, Any]]] = None

@router.post("/api/extract")
async def extract_url(req: ExtractRequest, request: Request):
    url = req.url.strip()
    if not url:
        raise HTTPException(status_code=400, detail="URL is required.")

    loop = asyncio.get_event_loop()
    future = loop.create_future()

    def on_success(videos: List[VideoMetadata], is_pl: bool, title: str):
        loop.call_soon_threadsafe(future.set_result, {
            "success": True,
            "title": title,
            "is_playlist": is_pl,
            "videos": videos
        })

    def on_error(err_msg: str):
        loop.call_soon_threadsafe(future.set_exception, HTTPException(status_code=400, detail=err_msg))

    extractor = ExtractorThread(url=url, on_success=on_success, on_error=on_error, on_progress=_on_extract_progress)
    extractor.start()

    try:
        result = await future
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    videos = result["videos"]
    state.current_videos = videos
    request.app.state.current_videos = videos
    state.current_playlist_title = result["title"]
    request.app.state.current_playlist_title = result["title"]

    avail_res = get_available_resolutions(videos)
    avail_audio = get_available_audio_bitrates(videos)

    return {
        "success": True,
        "url": url,
        "playlist_url": url,
        "title": result["title"],
        "is_playlist": result["is_playlist"],
        "is_fast_enum": result["is_playlist"] and len(videos) > 1,
        "videos": [state.video_to_dict(v, i) for i, v in enumerate(videos)],
        "available_resolutions": avail_res,
        "available_audio_bitrates": avail_audio
    }

@router.post("/api/playlist/analyze_selected")
async def analyze_selected_playlist(req: AnalyzeSelectedRequest, request: Request):
    videos = state.get_current_videos(request.app.state)
    if not videos:
        raise HTTPException(status_code=400, detail="No playlist videos loaded.")
    
    selected_videos = [v for idx, v in enumerate(videos) if idx in req.selected_indices]
    if not selected_videos:
        raise HTTPException(status_code=400, detail="No valid videos selected.")
    
    import yt_dlp
    from src.backend.ffmpeg_locator import get_ffmpeg_path
    from src.backend.extractor.stream_parser import extract_video_metadata
    
    full_opts = {
        'quiet': True,
        'no_warnings': True,
        'extract_flat': False,
        'ignoreerrors': True,
        'extractor_args': {'youtube': {'player_client': ['default', 'web']}},
        'ffmpeg_location': get_ffmpeg_path(),
    }
    total_sel = len(selected_videos)
    with yt_dlp.YoutubeDL(full_opts) as ydl_full:
        for idx, v in enumerate(selected_videos):
            pct = int(((idx + 1) / total_sel) * 100)
            _on_extract_progress(f"Analyzed {idx + 1}/{total_sel} videos ({pct}%)", idx + 1, total_sel)
            if not v.video_streams and not v.audio_streams and v.url:
                try:
                    full_entry = ydl_full.extract_info(v.url, download=False)
                    if full_entry:
                        vm = extract_video_metadata(full_entry)
                        v.video_streams = vm.video_streams
                        v.audio_streams = vm.audio_streams
                        v.best_video = vm.best_video
                        v.best_audio = vm.best_audio
                        if vm.duration:
                            v.duration = vm.duration
                        if vm.thumbnail_url:
                            v.thumbnail_url = vm.thumbnail_url
                except Exception as e:
                    logger.warning(f"Error analyzing selected stream '{v.title}': {e}")
    
    state.current_videos = selected_videos
    request.app.state.current_videos = selected_videos

    avail_res = get_available_resolutions(selected_videos)
    avail_audio = get_available_audio_bitrates(selected_videos)

    return {
        "success": True,
        "title": state.current_playlist_title,
        "is_playlist": True,
        "is_fast_enum": False,
        "videos": [state.video_to_dict(v, i) for i, v in enumerate(selected_videos)],
        "available_resolutions": avail_res,
        "available_audio_bitrates": avail_audio
    }

@router.post("/api/group_playlist")
async def api_group_playlist(req: GroupRequest, request: Request):
    videos = state.get_current_videos(request.app.state)
    if not videos:
        return {"groups": []}

    groups = group_playlist_videos(
        videos=videos,
        target_video_res=req.target_video_res,
        target_audio_bitrate=req.target_audio_bitrate,
        mode=req.mode,
        tiers=req.tiers
    )

    group_dicts = []
    for g in groups:
        group_dicts.append({
            "group_name": g.group_name,
            "quality_tier": g.quality_tier,
            "videos": [state.video_to_dict(v, i) for i, v in enumerate(g.videos)]
        })

    return {"groups": group_dicts}
