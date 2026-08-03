import re
from typing import List, Optional, Dict, Any
from src.backend.models import VideoMetadata, PlaylistGroup
from src.logger import get_logger

logger = get_logger("PlaylistGrouper")

def group_playlist_videos(
    videos: List[VideoMetadata],
    target_video_res: str = "(Best Available)",
    target_audio_bitrate: float = -1.0,
    mode: str = "video_audio",
    tiers: Optional[List[Dict[str, Any]]] = None
) -> List[PlaylistGroup]:
    if not videos:
        return []

    groups: List[PlaylistGroup] = []

    if tiers and len(tiers) > 0:
        remaining = list(videos)
        for idx, t in enumerate(tiers):
            if not remaining:
                break
            t_res = t.get("target_res", "(Best Available)")
            t_abr_str = str(t.get("target_abr", "(Best Available)"))
            t_abr = -1.0
            if t_abr_str != "(Best Available)":
                m = re.search(r"(\d+)", t_abr_str)
                if m:
                    t_abr = float(m.group(1))
            
            matching = []
            for v in list(remaining):
                res_match = True
                abr_match = True
                if mode in ("video_audio", "video_only") and t_res != "(Best Available)":
                    res_match = any(vs.resolution == t_res for vs in v.video_streams)
                if mode in ("video_audio", "audio_only") and t_abr > 0:
                    abr_match = any(as_.bitrate and abs(as_.bitrate - t_abr) <= 32 for as_ in v.audio_streams)
                if res_match and abr_match:
                    matching.append(v)
            
            if matching:
                for m_v in matching:
                    remaining.remove(m_v)
                g_name = f"Tier {idx+1}: {t_res} / {t_abr_str} ({len(matching)} videos)"
                groups.append(PlaylistGroup(
                    group_name=g_name,
                    quality_tier=f"Tier {idx+1}",
                    videos=matching,
                    selected_video_format_id="batch_dynamic",
                    selected_audio_format_id="batch_dynamic"
                ))
        if remaining:
            groups.append(PlaylistGroup(
                group_name=f"Fallback Group: Best Available ({len(remaining)} videos)",
                quality_tier="Fallback",
                videos=remaining,
                selected_video_format_id="batch_dynamic",
                selected_audio_format_id="batch_dynamic"
            ))
        logger.debug(f"Grouped {len(videos)} playlist videos into {len(groups)} multi-tier group(s).")
        return groups

    if mode == "audio_only":
        if target_audio_bitrate < 0:
            group = PlaylistGroup(
                group_name=f"All Videos - Best Available Audio (.MP3) ({len(videos)} videos)",
                quality_tier="Audio Only",
                videos=list(videos),
                selected_video_format_id="batch_dynamic",
                selected_audio_format_id="batch_dynamic"
            )
            groups.append(group)
        else:
            matching = []
            fallback = []
            for v in videos:
                has_bitrate = any(as_.bitrate and abs(as_.bitrate - target_audio_bitrate) <= 32 for as_ in v.audio_streams)
                if has_bitrate:
                    matching.append(v)
                else:
                    fallback.append(v)

            if matching:
                g_match = PlaylistGroup(
                    group_name=f"Videos with {int(target_audio_bitrate)} kbps Audio Available ({len(matching)} videos)",
                    quality_tier=f"{int(target_audio_bitrate)} kbps",
                    videos=matching,
                    selected_video_format_id="batch_dynamic",
                    selected_audio_format_id="batch_dynamic"
                )
                groups.append(g_match)

            if fallback:
                g_fall = PlaylistGroup(
                    group_name=f"Videos without {int(target_audio_bitrate)} kbps Audio - Fallback to Best Available ({len(fallback)} videos)",
                    quality_tier="Fallback to Best",
                    videos=fallback,
                    selected_video_format_id="batch_dynamic",
                    selected_audio_format_id="batch_dynamic"
                )
                groups.append(g_fall)

    elif mode == "video_only":
        if target_video_res == "(Best Available)":
            group = PlaylistGroup(
                group_name=f"All Videos - Best Available Video Only (Muted .MP4) ({len(videos)} videos)",
                quality_tier="(Best Available)",
                videos=list(videos),
                selected_video_format_id="batch_dynamic",
                selected_audio_format_id="batch_dynamic"
            )
            groups.append(group)
        else:
            matching = []
            fallback = []
            for v in videos:
                has_res = any(vs.resolution == target_video_res for vs in v.video_streams)
                if has_res:
                    matching.append(v)
                else:
                    fallback.append(v)

            if matching:
                g_match = PlaylistGroup(
                    group_name=f"Videos with {target_video_res} Available - Video Only ({len(matching)} videos)",
                    quality_tier=target_video_res,
                    videos=matching,
                    selected_video_format_id="batch_dynamic",
                    selected_audio_format_id="batch_dynamic"
                )
                groups.append(g_match)

            if fallback:
                g_fall = PlaylistGroup(
                    group_name=f"Videos without {target_video_res} - Fallback to Best Available Video Only ({len(fallback)} videos)",
                    quality_tier="Fallback to Best",
                    videos=fallback,
                    selected_video_format_id="batch_dynamic",
                    selected_audio_format_id="batch_dynamic"
                )
                groups.append(g_fall)

    else:
        if target_video_res == "(Best Available)":
            group = PlaylistGroup(
                group_name=f"All Videos - Best Available Video & Audio (.MP4) ({len(videos)} videos)",
                quality_tier="(Best Available)",
                videos=list(videos),
                selected_video_format_id="batch_dynamic",
                selected_audio_format_id="batch_dynamic"
            )
            groups.append(group)
        else:
            matching = []
            fallback = []
            for v in videos:
                has_res = any(vs.resolution == target_video_res for vs in v.video_streams)
                if has_res:
                    matching.append(v)
                else:
                    fallback.append(v)

            if matching:
                g_match = PlaylistGroup(
                    group_name=f"Videos with {target_video_res} Available ({len(matching)} videos)",
                    quality_tier=target_video_res,
                    videos=matching,
                    selected_video_format_id="batch_dynamic",
                    selected_audio_format_id="batch_dynamic"
                )
                groups.append(g_match)

            if fallback:
                g_fall = PlaylistGroup(
                    group_name=f"Videos without {target_video_res} - Fallback to Best Available ({len(fallback)} videos)",
                    quality_tier="Fallback to Best",
                    videos=fallback,
                    selected_video_format_id="batch_dynamic",
                    selected_audio_format_id="batch_dynamic"
                )
                groups.append(g_fall)

    logger.debug(f"Grouped {len(videos)} playlist videos into {len(groups)} batch group(s) (mode={mode}, target={target_video_res}).")
    return groups
