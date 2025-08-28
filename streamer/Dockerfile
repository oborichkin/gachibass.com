FROM python:3.12-slim-trixie
COPY --from=ghcr.io/astral-sh/uv:0.8.13 /uv /uvx /bin/

RUN apt-get update
RUN apt-get install -y --no-install-recommends libcairo2-dev
RUN apt-get install -y --no-install-recommends gcc
RUN apt-get install -y --no-install-recommends libgirepository-2.0
RUN apt-get install -y --no-install-recommends gstreamer-1.0
RUN apt-get install -y --no-install-recommends gstreamer1.0-plugins-good

WORKDIR /app
ADD uv.lock pyproject.toml config.yml .
ADD src /app/src
RUN uv sync --locked

ENTRYPOINT [ "uv", "run", "python", "-m", "gachibass" ]
