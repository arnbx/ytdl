// Shared Application State for YTDL
export const state = {
  currentData: null,
  singleMode: "video_audio",
  playlistBatchMode: "video_audio",
  websocket: null
};

export function setCurrentData(data) {
  state.currentData = data;
}

export function setSingleMode(mode) {
  state.singleMode = mode;
}

export function setPlaylistBatchMode(mode) {
  state.playlistBatchMode = mode;
}

export function setWebSocket(ws) {
  state.websocket = ws;
}
