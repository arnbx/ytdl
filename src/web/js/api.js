// REST API Client Methods for YTDL

export async function apiExtractUrl(url) {
  const resp = await fetch("/api/extract", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.detail || "Extraction failed.");
  }
  return data;
}

export async function apiAnalyzeSelectedPlaylist(url, selectedIndices) {
  const resp = await fetch("/api/playlist/analyze_selected", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url: url, selected_indices: selectedIndices })
  });
  const data = await resp.json();
  if (!resp.ok) {
    let detail = data.detail || "Selected playlist analysis failed.";
    if (typeof detail === "object") detail = JSON.stringify(detail);
    throw new Error(detail);
  }
  return data;
}

export async function apiGroupPlaylist(tiers, mode) {
  const resp = await fetch("/api/group_playlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      tiers: tiers,
      mode: mode
    })
  });
  const data = await resp.json();
  if (!resp.ok) {
    throw new Error(data.detail || "Playlist grouping failed.");
  }
  return data;
}

export async function apiDownloadSingle(videoIndex, mode, videoLabel, audioLabel) {
  const resp = await fetch("/api/download/single", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      video_index: videoIndex,
      mode: mode,
      video_label: videoLabel,
      audio_label: audioLabel
    })
  });
  if (!resp.ok) {
    const data = await resp.json();
    throw new Error(data.detail || "Single download job failed.");
  }
  return await resp.json();
}

export async function apiDownloadPlaylist(reqBody) {
  const resp = await fetch("/api/download/playlist", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(reqBody)
  });
  if (!resp.ok) {
    const data = await resp.json();
    throw new Error(data.detail || "Playlist download job failed.");
  }
  return await resp.json();
}

export async function apiOpenFolder() {
  const resp = await fetch("/api/open_folder", { method: "POST" });
  return await resp.json();
}

export async function apiOpenUrl(url) {
  const resp = await fetch("/api/open_url", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ url })
  });
  return await resp.json();
}

export async function apiFetchQueueState() {
  const resp = await fetch("/api/queue");
  if (!resp.ok) return { jobs: [] };
  return await resp.json();
}
