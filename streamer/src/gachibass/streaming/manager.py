"""Station manager for managing radio stations.

This module provides a centralized interface for managing radio stations,
including CRUD operations and admin authorization checks.
"""

import logging
from typing import Dict, List, Optional

from .stream import RadioStation
from ..settings import Settings, StreamConfig

logger = logging.getLogger(__name__)


class StationManager:
    """Manages radio station instances."""

    def __init__(self, settings: Settings):
        """Initialize the station manager with settings.

        Args:
            settings: Application settings containing stream configs and admins
        """
        self._settings = settings
        self._stations: Dict[str, RadioStation] = {}

    @property
    def admins(self) -> List[int]:
        """Get list of admin user IDs."""
        return self._settings.admins

    def is_admin(self, station_id: str, user_id: int) -> bool:
        """Check if a user is an admin for a station.

        Args:
            station_id: The station identifier
            user_id: Telegram user ID

        Returns:
            True if user is in admins list, False otherwise
        """
        return user_id in self.admins

    def is_global_admin(self, user_id: int) -> bool:
        """Check if a user is a global admin.

        Args:
            user_id: Telegram user ID

        Returns:
            True if user is in admins list, False otherwise
        """
        return user_id in self.admins

    def get_station(self, station_id: str) -> Optional[RadioStation]:
        """Get a station by ID.

        Args:
            station_id: The station identifier

        Returns:
            RadioStation instance or None if not found
        """
        return self._stations.get(station_id)

    def get_all_stations(self) -> Dict[str, RadioStation]:
        """Get all stations.

        Returns:
            Dict mapping station IDs to RadioStation instances
        """
        return self._stations.copy()

    def get_station_names(self) -> List[str]:
        """Get list of all station names.

        Returns:
            List of station IDs
        """
        return list(self._stations.keys())

    def station_exists(self, station_id: str) -> bool:
        """Check if a station exists.

        Args:
            station_id: The station identifier

        Returns:
            True if station exists, False otherwise
        """
        return station_id in self._stations

    def add_station(self, station_id: str, stream_config: StreamConfig) -> RadioStation:
        """Add a new station.

        Args:
            station_id: The station identifier
            stream_config: Stream configuration

        Returns:
            The created RadioStation instance
        """
        if station_id in self._stations:
            raise ValueError(f"Station {station_id} already exists")

        from ..common import IcecastConfig

        icecast_config = IcecastConfig(
            server=self._settings.icecast.server,
            port=self._settings.icecast.port,
            username=self._settings.icecast.username,
            password=self._settings.icecast.password,
        )

        station = RadioStation(
            stream_name=stream_config.name,
            music_directory=stream_config.playlist,
            icecast_config=icecast_config,
            mount=stream_config.mount,
        )

        self._stations[station_id] = station
        logger.info(f"Added station: {station_id}")
        return station

    def remove_station(self, station_id: str) -> bool:
        """Remove a station.

        Args:
            station_id: The station identifier

        Returns:
            True if station was removed, False if not found
        """
        if station_id not in self._stations:
            return False

        station = self._stations.pop(station_id)
        # TODO: Stop the station pipeline
        logger.info(f"Removed station: {station_id}")
        return True

    def start_all(self):
        """Start all stations."""
        for station in self._stations.values():
            station.start()
        logger.info(f"Started {len(self._stations)} stations")

    def initialize_from_config(self):
        """Initialize all stations from config settings."""
        for station_id, stream_config in self._settings.streams.items():
            try:
                self.add_station(station_id, stream_config)
            except Exception as e:
                logger.error(f"Failed to initialize station {station_id}: {e}")
