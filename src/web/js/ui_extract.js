// Extraction UI & Single Video View for YTDL
import { state, setCurrentData } from "./state.js";
import { apiExtractUrl, apiDownloadSingle, apiFetchQueueState } from "./api.js";
import { initPlaylistView } from "./ui_playlist.js";
import { renderQueueDashboard } from "./ui_queue.js";

export async function handleExtract() {
  const urlInput = document.getElementById("input-url");
  const url = urlInput.value.trim();
  const errorBox = document.getElementById("extract-error");
  const spinner = document.getElementById("extract-spinner");
  const label = document.getElementById("extract-label");
  const btn = document.getElementById("btn-extract");

  if (!url) return;

  errorBox.classList.add("hidden");
  errorBox.textContent = "";
  spinner.classList.remove("hidden");
  label.textContent = "Analyzing...";
  btn.disabled = true;

  try {
    const data = await apiExtractUrl(url);
    setCurrentData(data);
    renderMediaContent(data);
  } catch (err) {
    errorBox.textContent = err.message || "An unexpected error occurred during extraction.";
    errorBox.classList.remove("hidden");
  } finally {
    spinner.classList.add("hidden");
    label.textContent = "Analyze Stream";
    btn.disabled = false;
  }
}

export function renderMediaContent(data) {
  const contentSection = document.getElementById("content-section");
  const singleContainer = document.getElementById("single-video-container");
  const playlistContainer = document.getElementById("playlist-container");

  contentSection.classList.remove("hidden");

  if (!data.is_playlist && data.videos && data.videos.length === 1) {
    // SINGLE VIDEO VIEW
    singleContainer.classList.remove("hidden");
    playlistContainer.classList.add("hidden");

    const v = data.videos[0];
    document.getElementById("single-thumb").src = v.thumbnail_url || "";
    document.getElementById("single-duration").textContent = v.formatted_duration || "00:00";
    document.getElementById("single-title").textContent = v.title || "Unknown Title";

    populateSelect("select-single-video", v.video_streams);
    populateSelect("select-single-audio", v.audio_streams);

    updateSingleStreamDropdownVisibility();
  } else {
    // PLAYLIST VIEW
    singleContainer.classList.add("hidden");
    playlistContainer.classList.remove("hidden");
    initPlaylistView(data);
  }

  contentSection.scrollIntoView({ behavior: "smooth" });
}

export function populateSelect(selectId, streams) {
  const sel = document.getElementById(selectId);
  sel.innerHTML = "";
  if (!streams || streams.length === 0) {
    const opt = document.createElement("option");
    opt.value = "";
    opt.textContent = "No streams available";
    sel.appendChild(opt);
    return;
  }
  streams.forEach((s) => {
    const opt = document.createElement("option");
    opt.value = s.display_label;
    opt.textContent = s.display_label;
    sel.appendChild(opt);
  });
}

export function updateSingleStreamDropdownVisibility() {
  const colVideo = document.getElementById("col-single-video-stream");
  const colAudio = document.getElementById("col-single-audio-stream");

  if (state.singleMode === "video_audio") {
    colVideo.classList.remove("hidden");
    colAudio.classList.remove("hidden");
  } else if (state.singleMode === "video_only") {
    colVideo.classList.remove("hidden");
    colAudio.classList.add("hidden");
  } else if (state.singleMode === "audio_only") {
    colVideo.classList.add("hidden");
    colAudio.classList.remove("hidden");
  }
}

export async function handleSingleDownload() {
  const vLabel = document.getElementById("select-single-video").value;
  const aLabel = document.getElementById("select-single-audio").value;

  try {
    await apiDownloadSingle(0, state.singleMode, vLabel, aLabel);
    const qSection = document.getElementById("queue-section");
    qSection.scrollIntoView({ behavior: "smooth" });
    const data = await apiFetchQueueState();
    if (data && data.jobs) {
      renderQueueDashboard(data.jobs);
    }
  } catch (e) {
    console.error("Single download dispatch failed:", e);
  }
}
