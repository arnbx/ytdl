import os
import sys
import time
import socket
import secrets
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

def get_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]

def start_server(port: int):
    uvicorn.run(app, host="127.0.0.1", port=port, log_level="warning")

def main():
    logger.info("Starting YTDL YouTube Downloader Suite (Webview Edition)...")
    try:
        # Generate secret session token to restrict access strictly to the native GUI window
        app_token = secrets.token_hex(16)
        os.environ["YTDL_APP_TOKEN"] = app_token

        # Bind to a dynamic random unused port on localhost (no hardcoded port 8000)
        port = get_free_port()

        # Start uvicorn server in a background daemon thread
        server_thread = threading.Thread(target=start_server, args=(port,), daemon=True)
        server_thread.start()
        
        # Give server a brief moment to bind socket
        time.sleep(1.0)
        
        gui_url = f"http://127.0.0.1:{port}/?token={app_token}"
        logger.info(f"Launching PyWebView native desktop window on internal port {port}")
        window = webview.create_window(
            title="YTDL — High Quality YouTube Video Downloader",
            url=gui_url,
            width=1280,
            height=850,
            min_size=(900, 600),
            background_color="#0A0D14"
        )
        try:
            webview.start()
        except Exception as wv_err:
            logger.critical(f"PyWebView could not start native window ({wv_err}). Exiting.")
            sys.exit(1)
                
        logger.info("Application closed normally.")
    except Exception as e:
        logger.critical(f"Application encountered a fatal exception: {e}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
