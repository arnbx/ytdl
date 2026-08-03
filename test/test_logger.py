import os
import tempfile
import unittest
import logging
from src.logger import FIFOFileHandler


class TestFIFOFileHandler(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, "test_fifo.log")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_fifo_file_handler_truncates_from_beginning(self):
        # Set a very small max_bytes (100 bytes) to trigger truncation quickly
        handler = FIFOFileHandler(
            self.log_file, max_bytes=100, keep_ratio=0.5, mode="a", encoding="utf-8"
        )
        logger = logging.getLogger("test_fifo_logger")
        logger.setLevel(logging.DEBUG)
        logger.addHandler(handler)

        try:
            logger.info("LINE_ONE_LONG_MESSAGE_11111111111111111111111")
            logger.info("LINE_TWO_LONG_MESSAGE_22222222222222222222222")
            logger.info("LINE_THREE_LONG_MESSAGE_3333333333333333333")
            logger.info("LINE_FOUR_LATEST_44444444444444444444444444")
            handler.flush()

            with open(self.log_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Verify that early lines were truncated from the beginning and latest line is present
            self.assertNotIn("LINE_ONE", content)
            self.assertIn("LINE_FOUR_LATEST", content)
            self.assertLessEqual(os.path.getsize(self.log_file), 100)
        finally:
            logger.removeHandler(handler)
            handler.close()


if __name__ == "__main__":
    unittest.main()
