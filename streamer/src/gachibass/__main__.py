"""Main entry point for the Gachibass streamer application."""

import logging

from .api import run_api

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)

if __name__ == "__main__":
    run_api()
