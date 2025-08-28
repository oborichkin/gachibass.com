import os
import yaml
import logging
import argparse
from typing import Dict
from contextlib import asynccontextmanager

import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter

from gachibass.bot import get_bot
from gachibass.common import IcecastConfig
from gachibass.stream import RadioStation, streams

load_dotenv()


parser = argparse.ArgumentParser()
parser.add_argument("--config", default="config.yml")
args = parser.parse_args()


bot = get_bot(os.environ["BOT_TOKEN"])


with open(args.config, "r") as f:
    config = yaml.load(f, Loader=yaml.Loader)

    icecast_config = IcecastConfig(**config["icecast"])

    for name, stream_config in config["streams"].items():
        streams[name] = RadioStation(
            stream_config["name"],
            stream_config["playlist"],
            icecast_config,
            stream_config["mount"],
            stream_config["admins"],
            daemon=True,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    await bot.initialize()
    await bot.start()
    await bot.updater.start_polling()
    yield
    await bot.updater.stop()
    await bot.stop()
    await bot.shutdown()



for name, stream in streams.items():
    stream.start()

router = APIRouter(prefix="/api")
api = FastAPI(lifespan=lifespan)

@router.get("/")
def root():
    return [
        {
            "name": stream.stream_name,
            "mount": stream.mount,
        } for stream in streams.values()
    ]

api.include_router(router)
uvicorn.run(api, host="0.0.0.0", port=5000)
