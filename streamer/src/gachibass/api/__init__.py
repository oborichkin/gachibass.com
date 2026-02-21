"""FastAPI REST API for Gachibass.

This module provides the REST API that serves the frontend and
orchestrates the bot and streaming functionality.
"""

import logging
import os

from contextlib import asynccontextmanager
from fastapi import FastAPI, APIRouter
import uvicorn

from ..bot import get_bot
from ..streaming import StationManager
from ..settings import get_settings

logger = logging.getLogger(__name__)


# Global instances
station_manager: StationManager | None = None
bot = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage application lifespan - initialize bot and streams."""
    global station_manager, bot

    # Load settings and initialize station manager
    settings = get_settings()
    station_manager = StationManager(settings)
    station_manager.initialize_from_config()

    # Start all streaming stations
    station_manager.start_all()

    # Initialize and start the bot
    bot_token = os.getenv("STREAMER_BOT_TOKEN")
    if not bot_token:
        raise RuntimeError("STREAMER_BOT_TOKEN environment variable not set")

    bot = get_bot(bot_token, station_manager)
    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()

    logger.info("Application started successfully")

    yield

    # Cleanup
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()
    logger.info("Application shutdown complete")


# Create FastAPI app
router = APIRouter(prefix="/api")
api = FastAPI(lifespan=lifespan)


@router.get("/")
def list_streams():
    """List all available radio streams."""
    if not station_manager:
        return []

    stations = station_manager.get_all_stations()
    return [
        {
            "name": station.stream_name,
            "mount": station.mount,
        }
        for station in stations.values()
    ]


api.include_router(router)


def run_api():
    """Run the API server."""
    uvicorn.run(api, host="0.0.0.0", port=5000)


if __name__ == "__main__":
    run_api()
