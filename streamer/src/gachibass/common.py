"""Common types and configurations used across modules."""

from pydantic import BaseModel


class IcecastConfig(BaseModel):
    """Icecast server configuration."""

    server: str = "localhost"
    port: int = 8000
    username: str = "source"
    password: str = "password"
