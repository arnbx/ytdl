import os
import sys
import subprocess
from fastapi import APIRouter
from src.backend.pipeline_manager import get_target_directory
from src.logger import get_logger

logger = get_logger("SystemRoute")
router = APIRouter()

@router.post("/api/open_folder")
async def open_folder():
    folder = get_target_directory(None)
    os.makedirs(folder, exist_ok=True)
    try:
        if sys.platform == "win32":
            os.startfile(folder)
        elif sys.platform == "darwin":
            subprocess.run(["open", folder], check=False)
        else:
            subprocess.run(["xdg-open", folder], check=False)
        return {"success": True, "path": folder}
    except Exception as e:
        logger.error(f"Error opening folder {folder}: {e}")
        return {"success": False, "error": str(e)}
