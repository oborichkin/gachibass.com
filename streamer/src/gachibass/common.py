from dataclasses import dataclass


@dataclass
class IcecastConfig:
    server: str = "localhost"
    port: int = 8000
    username: str = "source"
    password: str = "password"
