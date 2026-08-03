from typing import List, Dict, Any, Optional
from src.backend.models import StreamInfo, VideoMetadata
from src.logger import get_logger

logger = get_logger("StreamParser")

def parse_format_item(f: Dict[str, Any]) -> Optional[StreamInfo]:
    format_id = str(f.get("format_id", ""))
    ext = str(f.get("ext", ""))
    vcodec = str(f.get("vcodec", "none"))
    acodec = str(f.get("acodec", "none"))
    height = f.get("height")
    fps = f.get("fps") or 0.0
    filesize = f.get("filesize") or f.get("filesize_approx") or 0
    tbr = f.get("tbr") or 0.0
    abr = f.get("abr") or 0.0

    if format_id.startswith("sb") or ext in ("mhtml", "jpg", "png", "webp"):
        return None

    if vcodec != "none" and vcodec:
        res_label = f"{height}p" if height else "Video"
        if height and height >= 2160:
            res_label = f"4K ({height}p)"
        elif height and height >= 1440:
            res_label = f"2K ({height}p)"
        elif height and height == 1080:
            res_label = f"FHD (1080p)"
        elif height and height == 720:
            res_label = f"HD (720p)"

        score = (height or 0) * 1000 + (tbr or 0)
        if ext == "mp4" or "avc" in vcodec.lower() or "h264" in vcodec.lower():
            score += 500
        return StreamInfo(
            format_id=format_id,
            ext=ext,
            resolution=res_label,
            fps=fps,
            vcodec=vcodec,
            acodec=acodec,
            filesize=filesize,
            bitrate=tbr,
            quality_score=score,
            stream_type="video"
        )
    elif acodec != "none" and acodec and (vcodec == "none" or not vcodec):
        score = (abr or tbr or 0)
        res_label = f"{int(score)} kbps" if score > 0 else "Audio"
        return StreamInfo(
            format_id=format_id,
            ext=ext,
            resolution=res_label,
            fps=0.0,
            vcodec="none",
            acodec=acodec,
            filesize=filesize,
            bitrate=score,
            quality_score=score,
            stream_type="audio"
        )
    return None

def extract_video_metadata(info_dict: Dict[str, Any]) -> VideoMetadata:
    url = info_dict.get("webpage_url") or info_dict.get("original_url", "")
    title = info_dict.get("title", "Untitled Video")
    duration = info_dict.get("duration", 0) or 0
    thumbnail_url = info_dict.get("thumbnail", "")

    formats = info_dict.get("formats", [])
    video_streams: List[StreamInfo] = []
    audio_streams: List[StreamInfo] = []

    seen_v_ids = set()
    seen_a_ids = set()

    for f in formats:
        s = parse_format_item(f)
        if not s:
            continue
        if s.stream_type == "video":
            if s.format_id not in seen_v_ids:
                seen_v_ids.add(s.format_id)
                video_streams.append(s)
        elif s.stream_type == "audio":
            if s.format_id not in seen_a_ids:
                seen_a_ids.add(s.format_id)
                audio_streams.append(s)

    video_streams.sort(key=lambda x: x.quality_score, reverse=True)
    audio_streams.sort(key=lambda x: x.quality_score, reverse=True)

    best_v = video_streams[0] if video_streams else None
    best_a = audio_streams[0] if audio_streams else None

    logger.debug(f"Extracted metadata for '{title}' -> {len(video_streams)} video formats, {len(audio_streams)} audio formats.")

    return VideoMetadata(
        url=url,
        title=title,
        duration=duration,
        thumbnail_url=thumbnail_url,
        video_streams=video_streams,
        audio_streams=audio_streams,
        best_video=best_v,
        best_audio=best_a
    )

def get_available_resolutions(videos: List[VideoMetadata]) -> List[str]:
    res_order = ["4K (2160p)", "2K (1440p)", "FHD (1080p)", "HD (720p)", "480p", "360p", "240p", "144p"]
    found = set()
    for v in videos:
        for vs in v.video_streams:
            if vs.resolution:
                found.add(vs.resolution)
    ordered = [r for r in res_order if r in found]
    if not ordered:
        ordered = ["HD (720p)"]
    return ["(Best Available)"] + ordered

def get_available_audio_bitrates(videos: List[VideoMetadata]) -> List[str]:
    bitrate_order = [320, 256, 192, 160, 128, 96, 64]
    found = set()
    for v in videos:
        for as_ in v.audio_streams:
            if as_.bitrate:
                for b in bitrate_order:
                    if abs(as_.bitrate - b) <= 24:
                        found.add(b)
                        break
    ordered = sorted(list(found), reverse=True)
    if not ordered:
        ordered = [128]
    return ["(Best Available)"] + [f"{b} kbps" for b in ordered]
