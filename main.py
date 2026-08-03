import os
import sys
import time
import threading
import uvicorn

# Ensure Linux system site-packages is in sys.path so PyWebView can access system 'gi' (WebKit2GTK)
system_dist_path = "/usr/lib/python3/dist-packages"
if os.path.exists(system_dist_path) and system_dist_path not in sys.path:
    sys.path.append(system_dist_path)

import webview
from src.logger import get_logger
from src.backend.web_api import app

logger = get_logger("Main")

def start_server():
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="warning")

def main():
    logger.info("Starting YTDL YouTube Downloader Suite (Webview Edition)...")
    try:
        # Start uvicorn server in a background daemon thread
        server_thread = threading.Thread(target=start_server, daemon=True)
        server_thread.start()
        
        # Give server a brief moment to bind socket
        time.sleep(1.0)
        
        logger.info("Launching PyWebView native desktop window on http://127.0.0.1:8000")
        window = webview.create_window(
            title="YTDL — High Quality YouTube Video Downloader",
            url="http://127.0.0.1:8000",
            width=1280,
            height=850,
            min_size=(900, 600),
            background_color="#0A0D14"
        )
        try:
            webview.start()
        except Exception as wv_err:
            logger.warning(f"PyWebView could not start native window ({wv_err}). Falling back to system browser...")
            import webbrowser
            webbrowser.open("http://127.0.0.1:8000")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                pass
                
        logger.info("Application closed normally.")
    except Exception as e:
        logger.critical(f"Application encountered a fatal exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
