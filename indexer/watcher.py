import logging
import os
import time
from pathlib import Path
from threading import Timer

import ingest
from dotenv import load_dotenv
from watchdog.events import FileSystemEventHandler
from watchdog.observers import Observer


class DebouncedHandler(FileSystemEventHandler):
    def __init__(self, delay: float):
        self.delay = delay
        self._timer: Timer | None = None

    def on_any_event(self, event):  # type: ignore[override]
        if self._timer:
            self._timer.cancel()
        self._timer = Timer(self.delay, self.run_ingest)
        self._timer.start()

    @staticmethod
    def run_ingest() -> None:
        logging.info("Changes detected. Running ingest.")
        ingest.main()


def main() -> None:
    load_dotenv()
    docs_dir = Path(os.environ.get("DOCS_DIR", "docs"))
    debounce = float(os.environ.get("DEBOUNCE_SECONDS", "1.0"))
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s"
    )
    ingest.main()
    handler = DebouncedHandler(debounce)
    observer = Observer()
    observer.schedule(handler, str(docs_dir), recursive=True)
    observer.start()
    logging.info("Watching %s for changes", docs_dir)
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


if __name__ == "__main__":
    main()
