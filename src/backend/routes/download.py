from typing import List, Optional
from fastapi import APIRouter, HTTPException, Request
from pydantic import BaseModel
import src.backend.state as state
from src.backend.models import DownloadJob
from src.backend.extractor import group_playlist_videos
from src.logger import get_logger

logger = get_logger("DownloadRoute")
router = APIRouter()

class SingleDownloadRequest(BaseModel):
    video_index: int = 0
    mode: str = "video_audio"
    video_label: Optional[str] = None
    audio_label: Optional[str] = None

def get_pipeline_manager(req_app_state=None):
    if req_app_state and hasattr(req_app_state, "pipeline_manager") and req_app_state.pipeline_manager:
        return req_app_state.pipeline_manager
    return state.pipeline_manager

@router.post("/api/download/single")
async def download_single(req: SingleDownloadRequest, request: Request):
    videos = state.get_current_videos(request.app.state)
    if req.video_index < 0 or req.video_index >= len(videos):
        raise HTTPException(status_code=400, detail="Invalid video index.")

    v = videos[req.video_index]
    v_stream = next((s for s in v.video_streams if s.display_label == req.video_label), v.best_video)
    a_stream = next((s for s in v.audio_streams if s.display_label == req.audio_label), v.best_audio)

    job = DownloadJob(
        video=v,
        playlist_name=state.current_playlist_title,
        selected_video_stream=v_stream,
        selected_audio_stream=a_stream,
        download_mode=req.mode
    )
    pm = get_pipeline_manager(request.app.state)
    if not pm:
        raise HTTPException(status_code=500, detail="Pipeline manager is not initialized.")
    pm.add_job(job)
    return {"success": True, "job_id": job.job_id}

class IndividualItem(BaseModel):
    index: int
    enabled: bool = True
    mode: str = "video_audio"
    video_label: Optional[str] = None
    audio_label: Optional[str] = None

class GroupSelectionItem(BaseModel):
    group_name: str
    target_video_res: str = "(Best Available)"
    target_audio_bitrate: float = -1.0

class PlaylistDownloadRequest(BaseModel):
    is_batch: bool = True
    target_video_res: str = "(Best Available)"
    target_audio_bitrate: float = -1.0
    mode: str = "video_audio"
    individual_selections: List[IndividualItem] = []
    group_selections: List[GroupSelectionItem] = []

@router.post("/api/download/playlist")
async def download_playlist(req: PlaylistDownloadRequest, request: Request):
    videos = state.get_current_videos(request.app.state)
    if not videos:
        raise HTTPException(status_code=400, detail="No playlist videos loaded.")

    pm = get_pipeline_manager(request.app.state)
    if not pm:
        raise HTTPException(status_code=500, detail="Pipeline manager is not initialized.")

    added_ids = []

    if req.is_batch:
        groups = group_playlist_videos(videos, req.target_video_res, req.target_audio_bitrate, mode=req.mode)
        for i, grp in enumerate(groups):
            grp_target_res = req.target_video_res
            grp_target_abr = req.target_audio_bitrate
            if i < len(req.group_selections):
                sel = req.group_selections[i]
                grp_target_res = sel.target_video_res
                grp_target_abr = sel.target_audio_bitrate

            for v in grp.videos:
                v_stream = None
                if req.mode != "audio_only":
                    if grp_target_res != "(Best Available)":
                        for vs in v.video_streams:
                            if vs.resolution == grp_target_res:
                                v_stream = vs
                                break
                    if not v_stream:
                        v_stream = v.best_video

                a_stream = None
                if req.mode != "video_only":
                    if grp_target_abr >= 0:
                        for as_ in v.audio_streams:
                            if as_.bitrate and abs(as_.bitrate - grp_target_abr) <= 32:
                                a_stream = as_
                                break
                    if not a_stream:
                        a_stream = v.best_audio

                job = DownloadJob(
                    video=v,
                    playlist_name=state.current_playlist_title,
                    selected_video_stream=v_stream,
                    selected_audio_stream=a_stream,
                    download_mode=req.mode
                )
                pm.add_job(job)
                added_ids.append(job.job_id)
    else:
        for item in req.individual_selections:
            if not item.enabled:
                continue
            if item.index < 0 or item.index >= len(videos):
                continue
            v = videos[item.index]
            v_stream = next((s for s in v.video_streams if s.display_label == item.video_label), v.best_video)
            a_stream = next((s for s in v.audio_streams if s.display_label == item.audio_label), v.best_audio)

            job = DownloadJob(
                video=v,
                playlist_name=state.current_playlist_title,
                selected_video_stream=v_stream,
                selected_audio_stream=a_stream,
                download_mode=item.mode
            )
            pm.add_job(job)
            added_ids.append(job.job_id)

    return {"success": True, "added_jobs": len(added_ids), "job_ids": added_ids}

@router.get("/api/queue")
async def get_queue(request: Request):
    pm = get_pipeline_manager(request.app.state)
    if not pm:
        return {"jobs": []}
    jobs = [state.job_to_dict(j) for j in pm.jobs.values()]
    return {"jobs": jobs}
