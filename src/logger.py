import os
import sys
import logging

class FIFOFileHandler(logging.FileHandler):
    """
    A file handler that prevents the log file from growing indefinitely.
    When the file size exceeds `max_bytes`, older log entries from the beginning
    are discarded while preserving the most recent log entries.
    """
    def __init__(self, filename, max_bytes=512 * 1024, keep_ratio=0.6, mode="a", encoding="utf-8", delay=False):
        self.max_bytes = max_bytes
        self.keep_ratio = keep_ratio
        self._prune_file(filename)
        super().__init__(filename, mode=mode, encoding=encoding, delay=delay)

    def _prune_file(self, filename):
        try:
            if not os.path.exists(filename):
                return
            file_size = os.path.getsize(filename)
            if file_size <= self.max_bytes:
                return
            keep_size = int(self.max_bytes * self.keep_ratio)
            with open(filename, "rb") as f:
                if file_size > keep_size:
                    f.seek(-keep_size, os.SEEK_END)
                    f.readline()  # discard partial first line to start cleanly at a newline
                data = f.read()
            with open(filename, "wb") as f:
                f.write(data)
        except Exception:
            pass

    def emit(self, record):
        super().emit(record)
        self.truncate_if_needed(record)

    def truncate_if_needed(self, record=None):
        try:
            if self.stream is None:
                return
            self.stream.flush()
            if os.path.getsize(self.baseFilename) > self.max_bytes:
                try:
                    self.stream.close()
                    self.stream = None
                    self._prune_file(self.baseFilename)
                    self.stream = self._open()
                except Exception:
                    pass
        except Exception:
            if record:
                self.handleError(record)

def get_logger(name: str = "YTDL") -> logging.Logger:
    logger = logging.getLogger(name)
    if logger.handlers:
        return logger

    logger.setLevel(logging.DEBUG)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s.%(funcName)s:%(lineno)d] - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Do not create logs directory or store log files when running as a packaged app
    if not getattr(sys, "frozen", False):
        # Ensure ./logs directory exists
        logs_dir = os.path.abspath("logs")
        os.makedirs(logs_dir, exist_ok=True)
        log_file = os.path.join(logs_dir, "ytdl.log")

        # File Handler with FIFO Log Manager (keeps size capped under max_bytes)
        fh = FIFOFileHandler(log_file, max_bytes=512 * 1024, keep_ratio=0.6, mode="a", encoding="utf-8")
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)

    # Console Handler
    ch = logging.StreamHandler()
    ch.setLevel(logging.INFO)
    ch.setFormatter(formatter)
    logger.addHandler(ch)

    return logger

