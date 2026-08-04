# YTDL By Arnab Bose

<div align="center">

**A Modern, High-Performance Native Desktop YouTube Video & Playlist Downloader Suite**

[![GitHub](https://img.shields.io/badge/GitHub-developer--arnab--bose-24292e?style=for-the-badge&logo=github)](https://github.com/developer-arnab-bose/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110%2B-009688?style=for-the-badge&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com/)
[![PyWebView](https://img.shields.io/badge/PyWebView-5.0%2B-4B8BBE?style=for-the-badge)](https://pywebview.flowrl.com/)

</div>

---

## 🌟 Overview

**YTDL By Arnab Bose** is a state-of-the-art desktop YouTube downloader built with a high-performance **Python/FastAPI** backend and a sleek, responsive **glassmorphic vanilla HTML/CSS/JS** user interface rendered in a native desktop window via **PyWebView**.

Designed for speed, reliability, and precision, YTDL handles everything from individual 8K Dolby Vision videos to 100+ video educational playlists with granular control over formats, resolutions, and stream multiplexing.

---

## ✨ Key Features

- **🚀 Modular 4-Stage Download Pipeline**:
  - **Stage 1 (Video Download)**: High-speed extraction of dedicated high-resolution video streams using `yt-dlp`.
  - **Stage 2 (Audio Download)**: Concurrent or sequential download of the highest-bitrate audio streams.
  - **Stage 3 (Muxing & Merging)**: Zero-loss stream multiplexing via bundled static **FFmpeg** (`imageio-ffmpeg`), requiring no system-level FFmpeg installation.
  - **Stage 4 (Conversion & Finalization)**: Seamless container formatting into MP4, MP3, MKV, or audio-only formats.
- **📑 Comprehensive Playlist & Batch Analysis**:
  - Paste any playlist or channel URL to inspect full video lists asynchronously.
  - **Live Progress Visualization**: Real-time progress bar smoothly tracks playlist metadata extraction from `0%` to `100%`.
  - **Multi-Tier Resolution Selection**: Download entire playlists in uniform resolutions (4K 2160p, 1080p, 720p, Audio Only, or Best Available) or customize individual videos within a playlist.
- **⚡ Real-Time WebSocket Telemetry**:
  - Instantaneous updates for download speed, ETA, percentage complete, active queue counters, and stage status badges without polling overhead.
- **🔒 Secure Native Desktop Execution**:
  - Binds dynamically to an unused random loopback port (`127.0.0.1`) secured by a 128-bit cryptographic session token (`YTDL_APP_TOKEN`).
  - Restricts access strictly to the native PyWebView application window—external web browsers are denied access.
- **🧹 Automatic FIFO Log Manager**:
  - Built-in `FIFOFileHandler` automatically monitors `logs/ytdl.log` and caps file size at **512 KB**.
  - When logs exceed the threshold, older entries are safely pruned from the beginning of the file while retaining the most recent activity, preventing unbounded disk growth.

---

## 🛠️ Technology Stack

- **Backend**: Python 3.10+, FastAPI, Uvicorn, yt-dlp, imageio-ffmpeg
- **GUI Engine**: PyWebView (WebKit2GTK on Linux, WebView2 on Windows, Cocoa on macOS)
- **Frontend**: Vanilla HTML5, Modern CSS3 (Glassmorphism & HSL Dark Mode), ES6+ JavaScript, WebSockets
- **Packaging**: PyInstaller (`ytdl.spec`)

---

## 🚀 Getting Started

### 📦 1. Standard Installation (Recommended for Most Users)

For a seamless, ready-to-use experience without installing Python or any system dependencies, download the pre-compiled native desktop application for your operating system directly from **[GitHub Releases](https://github.com/developer-arnab-bose/YtDownloader/releases)**:

| Platform | Format | Instructions |
| :--- | :--- | :--- |
| **Windows** | Portable Executable / Installer (`.exe`) | Download `YTDL-Windows.exe`, double-click to launch the native desktop app. |
| **macOS** | Application Bundle (`.app` / `.dmg`) | Download `YTDL-macOS.dmg`, drag to **Applications**, and launch. |
| **Linux** | Standalone Binary / AppImage | Download `YTDL-Linux`, grant execution permissions (`chmod +x YTDL-Linux`), and run. |

---

### 💻 2. Advanced Installation (For Developers & Running from Source)

If you prefer to run YTDL directly from the Python source code or contribute to development, follow the steps below:

#### Prerequisites
- **Python 3.10** or higher (Windows, macOS, or Linux)
- System libraries for PyWebView (required **only on Linux/Debian/Ubuntu**):
  ```bash
  sudo apt update && sudo apt install -y python3-gi python3-gi-cairo gir1.2-gtk-3.0 gir1.2-webkit2-4.1
  ```

#### Setup & Execution
1. **Clone the repository**:
   ```bash
   git clone https://github.com/developer-arnab-bose/YtDownloader.git
   cd YtDownloader
   ```

2. **Create and activate a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install --upgrade pip
   pip install -r requirements.txt
   ```

4. **Launch the application**:
   ```bash
   python main.py
   ```
   The application will initialize its internal backend server, generate a secure session token, and open the YTDL native desktop window.

---


## 📁 Project Structure

```text
YtDownloader/
├── main.py                          # Application entrypoint & PyWebView desktop window launcher
├── requirements.txt                 # Project dependencies
├── ytdl.spec                        # PyInstaller standalone packaging specification
├── logs/
│   └── ytdl.log                     # Auto-managed rolling FIFO log file (capped at 512 KB)
├── downloads/                       # Default download directory for finished media & temp builds
├── src/
│   ├── logger.py                    # Custom FIFO log manager & formatting utilities
│   ├── backend/
│   │   ├── web_api.py               # FastAPI application, CORS, and startup hooks
│   │   ├── state.py                 # Thread-safe global download & queue state management
│   │   ├── websocket_manager.py     # Real-time WebSocket broadcasting for UI progress
│   │   ├── ffmpeg_locator.py        # Static FFmpeg binary resolution (imageio-ffmpeg)
│   │   ├── extractor/               # YouTube URL parsing & playlist metadata extraction
│   │   ├── pipeline/                # Modular 4-stage download & conversion workers
│   │   └── routes/                  # REST endpoints (/api/extract, /api/download, /api/queue, etc.)
│   └── web/
│       ├── index.html               # Main glassmorphic desktop interface
│       ├── css/
│       │   └── index.css            # Custom design system & animations
│       └── js/                      # UI modules (WebSockets, Queue Dashboard, Playlist Tiers)
└── test/                            # Comprehensive unit & integration test suite
```

---

## 🧪 Running Automated Tests

YTDL includes a comprehensive automated test suite covering HTML/DOM validation, REST API endpoints, playlist grouping logic, FIFO log truncation, and pipeline stages.

To run all unit tests:

```bash
./venv/bin/python3 -m unittest discover -s test -v
```

---

## 📦 Standalone Packaging

To build a standalone redistributable executable using **PyInstaller**:

```bash
./venv/bin/pyinstaller ytdl.spec
```

The compiled application bundle will be output to the `dist/` directory.

---

## 📜 License & Attribution

- **Author**: Arnab Bose  
- **GitHub**: [https://github.com/developer-arnab-bose/](https://github.com/developer-arnab-bose/)
- **License**: **Proprietary No-Modification Attribution License** — See the [LICENSE](file:///home/arnab/Desktop/Developer/YtDownloader/LICENSE) file for full legal terms.

### Key Licensing Permissions & Prohibitions:
- **✅ Permitted (Commercial & Private Use)**: Anyone may install, run, and use the unmodified software for both private/personal and commercial/internal business purposes.
- **🙏 Mandatory Attribution**: Any use of the software must give prominent credit and attribution to **Arnab Bose** and retain all existing author credits and GitHub links.
- **🚫 Prohibited**:
  - **No Modification**: Modifying, adapting, translating, reverse-engineering, or creating derivative works is strictly prohibited.
  - **No Distribution**: Redistributing, selling, sublicensing, or making the software available as a public SaaS/hosted service is prohibited without express written authorization.
  - **No Patent Use**: Using the software or its architecture to file, claim, or assert patent rights is strictly prohibited.

