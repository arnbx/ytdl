// Quality Preference Tiers & Selection Checklist Handler
import { state } from "./state.js";
import { apiAnalyzeSelectedPlaylist } from "./api.js";
import { refreshPlaylistGroupsPreview } from "./ui_playlist_groups.js";

export function initSelectionChecklist(data, onAnalyzedCallback) {
  const grid = document.getElementById("playlist-selection-grid");
  if (!grid) return;
  grid.innerHTML = "";

  (data.videos || []).forEach((v, idx) => {
    const card = document.createElement("div");
    card.className = "selection-item-card";
    card.innerHTML = `
      <input type="checkbox" id="chk-sel-${idx}" class="custom-checkbox" data-idx="${idx}" checked />
      <img src="${v.thumbnail_url || ''}" style="width: 64px; height: 36px; object-fit: cover; border-radius: 4px; flex-shrink: 0;" alt="thumb" />
      <div class="selection-item-info">
        <span class="selection-item-title">${idx + 1}. ${v.title}</span>
        <span class="selection-item-duration">${(v.duration_string && v.duration_string !== 'N/A') ? v.duration_string : ''}</span>
      </div>
    `;
    card.addEventListener("click", (e) => {
      if (e.target.tagName !== "INPUT") {
        const chk = card.querySelector("input[type='checkbox']");
        if (chk) chk.checked = !chk.checked;
      }
    });
    grid.appendChild(card);
  });

  const getCheckboxes = () => Array.from(grid.querySelectorAll("input[type='checkbox']"));
  const btnSelectAll = document.getElementById("btn-select-all");
  const btnDeselectAll = document.getElementById("btn-deselect-all");
  const btnInvertSelect = document.getElementById("btn-invert-select");

  if (btnSelectAll) btnSelectAll.onclick = () => getCheckboxes().forEach(c => c.checked = true);
  if (btnDeselectAll) btnDeselectAll.onclick = () => getCheckboxes().forEach(c => c.checked = false);
  if (btnInvertSelect) btnInvertSelect.onclick = () => getCheckboxes().forEach(c => c.checked = !c.checked);

  const btnAnalyze = document.getElementById("btn-analyze-selected");
  if (btnAnalyze) {
    btnAnalyze.onclick = async () => {
      const selectedIndices = getCheckboxes().filter(c => c.checked).map(c => parseInt(c.getAttribute("data-idx")));
      if (selectedIndices.length === 0) {
        alert("Please select at least one video to analyze.");
        return;
      }
      const progressWrap = document.getElementById("playlist-analyze-progress-wrapper");
      const progressFill = document.getElementById("playlist-analyze-progress-fill");
      const progressText = document.getElementById("playlist-analyze-progress-text");
      if (progressWrap) progressWrap.classList.remove("hidden");
      if (progressFill) progressFill.style.width = "0%";
      if (progressText) progressText.textContent = `Analyzing ${selectedIndices.length} videos...`;

      try {
        const targetUrl = state.currentData.url || state.currentData.playlist_url || "";
        const fullData = await apiAnalyzeSelectedPlaylist(targetUrl, selectedIndices);
        if (progressFill) progressFill.style.width = "100%";
        if (progressText) progressText.textContent = "Analysis complete!";
        setTimeout(() => {
          if (progressWrap) progressWrap.classList.add("hidden");
          onAnalyzedCallback(fullData);
        }, 500);
      } catch (err) {
        let msg = err.message || String(err);
        if (msg === "[object Object]") msg = JSON.stringify(err);
        if (progressText) progressText.textContent = `Error: ${msg}`;
      }
    };
  }
}

export function initPlaylistTiers(data) {
  state.playlistTiers = [{ target_res: "(Best Available)", target_abr: "(Best Available)" }];
  refreshPlaylistGroupsPreview();
}

export function renderTiersList(data) {
  // Standalone quality preference tiers replaced by inline controls in Group Cards
}
