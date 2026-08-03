// Playlist UI Handler for YTDL
import { state } from "./state.js";
import { apiDownloadPlaylist, apiFetchQueueState } from "./api.js";
import { refreshPlaylistGroupsPreview } from "./ui_playlist_groups.js";
import { initSelectionChecklist, initPlaylistTiers } from "./ui_playlist_tiers.js";
import { renderQueueDashboard } from "./ui_queue.js";

export { refreshPlaylistGroupsPreview };

export function initPlaylistView(data) {
  document.getElementById("playlist-title").textContent = data.title || "YouTube Playlist";
  document.getElementById("playlist-meta").textContent = `${data.videos.length} videos loaded in playlist`;

  const selectionSection = document.getElementById("playlist-selection-section");
  const batchControls = document.getElementById("playlist-batch-controls");
  const indivControls = document.getElementById("playlist-individual-controls");
  const globalToggle = document.querySelector(".playlist-global-toggle");

  if (data.is_fast_enum) {
    if (selectionSection) selectionSection.classList.remove("hidden");
    if (batchControls) batchControls.classList.add("hidden");
    if (indivControls) indivControls.classList.add("hidden");
    if (globalToggle) globalToggle.classList.add("hidden");
    initSelectionChecklist(data, (fullData) => {
      state.currentData = fullData;
      initPlaylistView(fullData);
    });
    return;
  }

  if (selectionSection) selectionSection.classList.add("hidden");
  if (batchControls) batchControls.classList.remove("hidden");
  if (indivControls) indivControls.classList.add("hidden");
  if (globalToggle) globalToggle.classList.remove("hidden");
  document.getElementById("toggle-batch-mode").checked = true;

  initPlaylistTiers(data);
  refreshPlaylistGroupsPreview();
}

export function updatePlaylistBatchVisibility() {
  refreshPlaylistGroupsPreview();
}

export function renderIndividualCardsGrid() {
  if (!state.currentData || !state.currentData.videos) return;

  const grid = document.getElementById("individual-cards-grid");
  grid.innerHTML = "";

  state.currentData.videos.forEach((v, idx) => {
    const card = document.createElement("div");
    card.className = "video-card-item";

    const header = document.createElement("div");
    header.className = "video-card-header";
    header.innerHTML = `
      <img src="${v.thumbnail_url || ''}" class="video-card-thumb" alt="thumb" />
      <span class="video-card-title">${idx + 1}. ${v.title}</span>
    `;

    const modeRow = document.createElement("div");
    modeRow.className = "control-group";
    modeRow.innerHTML = `
      <label class="control-label" style="font-size: 0.75rem;">Download Mode</label>
      <select id="mode-indiv-${idx}" class="stream-select" style="padding: 8px;">
        <option value="video_audio">Video + Audio (.MP4)</option>
        <option value="video_only">Video Only (Muted)</option>
        <option value="audio_only">Audio Only (.MP3)</option>
      </select>
    `;

    // Fix 5: Stack stream columns vertically inside card so they never overflow
    const streamsRow = document.createElement("div");
    streamsRow.className = "streams-row";

    const vCol = document.createElement("div");
    vCol.className = "stream-col";
    vCol.innerHTML = `<label class="control-label" style="font-size: 0.75rem;">Video Stream</label>`;
    const vSel = document.createElement("select");
    vSel.id = `sel-v-indiv-${idx}`;
    vSel.className = "stream-select";
    vSel.style.padding = "8px";
    v.video_streams.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.display_label;
      opt.textContent = s.display_label;
      vSel.appendChild(opt);
    });
    vCol.appendChild(vSel);

    const aCol = document.createElement("div");
    aCol.className = "stream-col";
    aCol.innerHTML = `<label class="control-label" style="font-size: 0.75rem;">Audio Stream</label>`;
    const aSel = document.createElement("select");
    aSel.id = `sel-a-indiv-${idx}`;
    aSel.className = "stream-select";
    aSel.style.padding = "8px";
    v.audio_streams.forEach(s => {
      const opt = document.createElement("option");
      opt.value = s.display_label;
      opt.textContent = s.display_label;
      aSel.appendChild(opt);
    });
    aCol.appendChild(aSel);

    streamsRow.appendChild(vCol);
    streamsRow.appendChild(aCol);

    modeRow.querySelector("select").addEventListener("change", (e) => {
      const m = e.target.value;
      if (m === "video_audio") {
        vCol.classList.remove("hidden");
        aCol.classList.remove("hidden");
      } else if (m === "video_only") {
        vCol.classList.remove("hidden");
        aCol.classList.add("hidden");
      } else if (m === "audio_only") {
        vCol.classList.add("hidden");
        aCol.classList.remove("hidden");
      }
    });

    card.appendChild(header);
    card.appendChild(modeRow);
    card.appendChild(streamsRow);
    grid.appendChild(card);
  });
}

export async function handlePlaylistDownload(isBatch) {
  let reqBody = {
    is_batch: isBatch,
    target_video_res: "(Best Available)",
    target_audio_bitrate: -1.0,
    tiers: state.playlistTiers,
    mode: state.playlistBatchMode,
    individual_selections: []
  };

  if (isBatch) {
    reqBody.group_selections = [];
    const groupCards = document.querySelectorAll("#groups-preview-container .group-card");
    groupCards.forEach((card, idx) => {
      const gNameEl = card.querySelector(".group-header span:first-child");
      const groupName = gNameEl ? gNameEl.textContent.split(" (")[0].trim() : "";
      const vSel = document.getElementById(`sel-grp-res-${idx}`);
      const aSel = document.getElementById(`sel-grp-abr-${idx}`);

      let grpRes = vSel ? vSel.value : reqBody.target_video_res;
      let grpAbrStr = aSel ? aSel.value : "(Best Available)";
      let grpAbr = -1.0;
      if (grpAbrStr !== "(Best Available)") {
        const m = grpAbrStr.match(/(\d+)/);
        if (m) grpAbr = parseFloat(m[1]);
      }

      reqBody.group_selections.push({
        group_name: groupName,
        target_video_res: grpRes,
        target_audio_bitrate: grpAbr
      });
    });
  } else {
    state.currentData.videos.forEach((v, idx) => {
      const chk = document.getElementById(`chk-indiv-${idx}`);
      const modeSel = document.getElementById(`mode-indiv-${idx}`);
      const vSel = document.getElementById(`sel-v-indiv-${idx}`);
      const aSel = document.getElementById(`sel-a-indiv-${idx}`);

      if (!chk || chk.checked) {
        reqBody.individual_selections.push({
          index: idx,
          enabled: true,
          mode: modeSel.value,
          video_label: vSel.value,
          audio_label: aSel.value
        });
      }
    });
  }

  try {
    await apiDownloadPlaylist(reqBody);
    const qSection = document.getElementById("queue-section");
    qSection.scrollIntoView({ behavior: "smooth" });
    const data = await apiFetchQueueState();
    if (data && data.jobs) {
      renderQueueDashboard(data.jobs);
    }
  } catch (e) {
    console.error("Playlist download dispatch failed:", e);
  }
}
