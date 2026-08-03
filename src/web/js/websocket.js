// WebSocket Real-time Progress Client for YTDL
import { state, setWebSocket } from "./state.js";
import { renderQueueDashboard } from "./ui_queue.js";

export function initWebSocket() {
  const protocol = window.location.protocol === "https:" ? "wss:" : "ws:";
  const wsUrl = `${protocol}//${window.location.host}/ws/progress`;

  const ws = new WebSocket(wsUrl);
  setWebSocket(ws);

  ws.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      if (data.event === "progress_update" && Array.isArray(data.jobs)) {
        renderQueueDashboard(data.jobs);
      } else if (data.event === "extract_progress") {
        const label = document.getElementById("extract-label");
        if (label) {
          label.textContent = data.message || "Analyzing...";
        }
        const plWrap = document.getElementById("playlist-analyze-progress-wrapper");
        const plFill = document.getElementById("playlist-analyze-progress-fill");
        const plText = document.getElementById("playlist-analyze-progress-text");
        if (plWrap && !plWrap.classList.contains("hidden")) {
          if (data.total > 0) {
            const pct = Math.round((data.current / data.total) * 100);
            if (plFill) plFill.style.width = pct + "%";
            if (plText) plText.textContent = data.message || `Analyzed ${data.current}/${data.total} (${pct}%)`;
          }
        }
      }
    } catch (e) {
      console.error("Error parsing WS message:", e);
    }
  };

  ws.onclose = () => {
    setTimeout(initWebSocket, 2000);
  };
}
