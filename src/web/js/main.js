// Main Coordinator for YTDL Web Client Application v2.0
import { state, setSingleMode, setPlaylistBatchMode } from "./state.js";
import { apiOpenFolder, apiFetchQueueState } from "./api.js";
import { initWebSocket } from "./websocket.js";
import { handleExtract, updateSingleStreamDropdownVisibility, handleSingleDownload } from "./ui_extract.js";
import { updatePlaylistBatchVisibility, refreshPlaylistGroupsPreview, renderIndividualCardsGrid, handlePlaylistDownload } from "./ui_playlist.js";
import { renderQueueDashboard } from "./ui_queue.js";

document.addEventListener("DOMContentLoaded", () => {
  initEventListeners();
  initWebSocket();
  loadInitialQueue();
});

function initEventListeners() {
  // Extract Button
  document.getElementById("btn-extract").addEventListener("click", handleExtract);
  document.getElementById("input-url").addEventListener("keypress", (e) => {
    if (e.key === "Enter") handleExtract();
  });

  // Open Folder
  document.getElementById("btn-open-folder").addEventListener("click", async () => {
    try {
      await apiOpenFolder();
    } catch (e) {
      console.error("Failed to open folder:", e);
    }
  });

  // Single Video Mode Pills
  const singlePills = document.querySelectorAll("#single-mode-pills .mode-pill");
  singlePills.forEach(pill => {
    pill.addEventListener("click", () => {
      singlePills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      setSingleMode(pill.dataset.mode);
      updateSingleStreamDropdownVisibility();
    });
  });

  // Single Download CTA
  document.getElementById("btn-single-download").addEventListener("click", handleSingleDownload);

  // Playlist Mode Pills
  const plPills = document.querySelectorAll("#playlist-mode-pills .mode-pill");
  plPills.forEach(pill => {
    pill.addEventListener("click", () => {
      plPills.forEach(p => p.classList.remove("active"));
      pill.classList.add("active");
      setPlaylistBatchMode(pill.dataset.mode);
      updatePlaylistBatchVisibility();
      refreshPlaylistGroupsPreview();
    });
  });

  // Playlist Global Toggle (Batch vs Individual)
  document.getElementById("toggle-batch-mode").addEventListener("change", (e) => {
    const isBatch = e.target.checked;
    document.getElementById("playlist-batch-controls").classList.toggle("hidden", !isBatch);
    document.getElementById("playlist-individual-controls").classList.toggle("hidden", isBatch);
    if (isBatch) {
      refreshPlaylistGroupsPreview();
    } else {
      renderIndividualCardsGrid();
    }
  });

  // Playlist CTAs
  document.getElementById("btn-playlist-batch-download").addEventListener("click", () => handlePlaylistDownload(true));
  document.getElementById("btn-playlist-indiv-download").addEventListener("click", () => handlePlaylistDownload(false));
}

async function loadInitialQueue() {
  try {
    const data = await apiFetchQueueState();
    if (data.jobs) {
      renderQueueDashboard(data.jobs);
    }
  } catch (e) {
    console.error("Failed to load initial queue state:", e);
  }
}
