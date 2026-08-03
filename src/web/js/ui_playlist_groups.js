import { state } from "./state.js";
import { apiGroupPlaylist } from "./api.js";

export function getGroupAvailableResolutions(videos) {
  const set = new Set();
  videos.forEach(v => {
    if (v.video_streams) {
      v.video_streams.forEach(s => {
        if (s.resolution && s.resolution !== "N/A") {
          set.add(s.resolution);
        }
      });
    }
  });
  const resOrder = ["8K", "4K", "1440p", "1080p", "720p", "480p", "360p", "240p", "144p"];
  const sorted = Array.from(set).sort((a, b) => {
    const idxA = resOrder.findIndex(r => a.includes(r));
    const idxB = resOrder.findIndex(r => b.includes(r));
    return (idxA === -1 ? 999 : idxA) - (idxB === -1 ? 999 : idxB);
  });
  return ["(Best Available)"].concat(sorted);
}

export function getGroupAvailableAudioBitrates(videos) {
  const set = new Set();
  videos.forEach(v => {
    if (v.audio_streams) {
      v.audio_streams.forEach(s => {
        if (s.bitrate && s.bitrate > 0) {
          set.add(`${Math.round(s.bitrate)} kbps`);
        }
      });
    }
  });
  const sorted = Array.from(set).sort((a, b) => parseInt(b) - parseInt(a));
  return ["(Best Available)"].concat(sorted);
}

export async function refreshPlaylistGroupsPreview() {
  if (!state.currentData || !state.currentData.videos) return;

  const tiers = state.playlistTiers || [{ target_res: "(Best Available)", target_abr: "(Best Available)" }];
  const targetRes = tiers[0] ? tiers[0].target_res : "(Best Available)";
  const targetAbrStr = tiers[0] ? tiers[0].target_abr : "(Best Available)";

  const container = document.getElementById("groups-preview-container");
  container.innerHTML = `<p style="color: var(--text-secondary); font-size: 0.9rem;">Calculating logical groups...</p>`;

  try {
    const data = await apiGroupPlaylist(tiers, state.playlistBatchMode);
    container.innerHTML = "";

    if (!data.groups || data.groups.length === 0) {
      container.innerHTML = `<p style="color: var(--text-muted);">No grouping available.</p>`;
      return;
    }

    data.groups.forEach((grp, idx) => {
      const card = document.createElement("div");
      card.className = "group-card";
      
      const header = document.createElement("div");
      header.className = "group-header";
      header.innerHTML = `
        <span>${grp.group_name} (${grp.videos.length} videos)</span>
        <span class="group-tier-badge">${grp.quality_tier || "Standard"}</span>
      `;

      const controlsRow = document.createElement("div");
      controlsRow.className = "streams-row";
      controlsRow.style.marginTop = "10px";
      controlsRow.style.marginBottom = "8px";
      controlsRow.style.gap = "12px";

      const resList = getGroupAvailableResolutions(grp.videos);
      const abrList = getGroupAvailableAudioBitrates(grp.videos);

      const tierRes = (tiers[idx] && tiers[idx].target_res) ? tiers[idx].target_res : "(Best Available)";
      const tierAbr = (tiers[idx] && tiers[idx].target_abr) ? tiers[idx].target_abr : "(Best Available)";

      let defaultRes = tierRes;
      if (grp.group_name.includes("Fallback") || !resList.includes(tierRes)) {
        defaultRes = "(Best Available)";
      }

      const vCol = document.createElement("div");
      vCol.className = "stream-col";
      vCol.innerHTML = `<label class="control-label" style="font-size: 0.75rem;">Target Video Resolution</label>`;
      const vSel = document.createElement("select");
      vSel.id = `sel-grp-res-${idx}`;
      vSel.className = "stream-select";
      vSel.style.padding = "8px";
      resList.forEach(item => {
        const opt = document.createElement("option");
        opt.value = item;
        opt.textContent = item;
        if (item === defaultRes) opt.selected = true;
        vSel.appendChild(opt);
      });
      vCol.appendChild(vSel);

      const aCol = document.createElement("div");
      aCol.className = "stream-col";
      aCol.innerHTML = `<label class="control-label" style="font-size: 0.75rem;">Target Audio Quality</label>`;
      const aSel = document.createElement("select");
      aSel.id = `sel-grp-abr-${idx}`;
      aSel.className = "stream-select";
      aSel.style.padding = "8px";
      abrList.forEach(item => {
        const opt = document.createElement("option");
        opt.value = item;
        opt.textContent = item;
        if (item === tierAbr) opt.selected = true;
        aSel.appendChild(opt);
      });
      aCol.appendChild(aSel);

      const handleTierChange = () => {
        if (!state.playlistTiers[idx]) {
          state.playlistTiers[idx] = { target_res: "(Best Available)", target_abr: "(Best Available)" };
        }
        state.playlistTiers[idx].target_res = vSel.value;
        state.playlistTiers[idx].target_abr = aSel.value;

        if (vSel.value === "(Best Available)" && aSel.value === "(Best Available)") {
          state.playlistTiers = state.playlistTiers.slice(0, idx + 1);
        } else if (idx === state.playlistTiers.length - 1) {
          state.playlistTiers.push({ target_res: "(Best Available)", target_abr: "(Best Available)" });
        }
        refreshPlaylistGroupsPreview();
      };

      vSel.addEventListener("change", handleTierChange);
      aSel.addEventListener("change", handleTierChange);

      if (state.playlistBatchMode === "video_audio") {
        controlsRow.appendChild(vCol);
        controlsRow.appendChild(aCol);
      } else if (state.playlistBatchMode === "video_only") {
        controlsRow.appendChild(vCol);
      } else if (state.playlistBatchMode === "audio_only") {
        controlsRow.appendChild(aCol);
      }

      const sampleTitles = grp.videos.slice(0, 4).map(v => `&bull; ${v.title}`).join("<br/>");
      const moreCount = grp.videos.length > 4 ? `<br/><em>...and ${grp.videos.length - 4} more videos</em>` : "";
      
      const preview = document.createElement("div");
      preview.className = "group-video-preview";
      preview.innerHTML = sampleTitles + moreCount;

      card.appendChild(header);
      card.appendChild(controlsRow);
      card.appendChild(preview);
      container.appendChild(card);
    });

  } catch (e) {
    console.error("Error refreshing playlist groups:", e);
    container.innerHTML = `<p style="color: #FCA5A5;">Error computing playlist groups.</p>`;
  }
}
