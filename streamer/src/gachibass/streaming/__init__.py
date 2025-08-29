from typing import Dict
from .stream import RadioStation


__streams: Dict[str, "RadioStation"] = {}


def is_admin(station_id: str, user_id: int):
    return True


def add_new_station(station_id, station_config):
    pass


def delete_station(station_id):
    pass
