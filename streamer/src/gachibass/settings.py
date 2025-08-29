import yaml
from argparse import ArgumentParser
from pydantic import BaseModel
from typing import List, Dict

__settings = None

parser = ArgumentParser()
parser.add_argument("--config", default="config.yml")
args = parser.parse_args()


class IcecastConfig(BaseModel):
    server: str = "localhost"
    port: int = 8000
    username: str = "source"
    password: str = "password"


class StreamConfig(BaseModel):
    name: str
    mount: str
    playlist: str


class Settings(BaseModel):
    icecast: IcecastConfig
    admins: List[int]
    streams: Dict[str, StreamConfig]


def get_settings():
    global __settings
    if not __settings:
        with open(args.config, "r") as f:
            config = yaml.load(f, Loader=yaml.Loader)
            __settings = Settings(**config)
    return __settings
