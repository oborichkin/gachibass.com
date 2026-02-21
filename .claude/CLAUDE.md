# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Gachibass is a Telegram-based radio streaming platform with a Fallout Pip-Boy themed interface. Users can listen to music streams through a Telegram Mini App, and admins can manage streams and upload music via Telegram bot commands.

## Architecture

The system consists of three main components:

### 1. Frontend (`web/`)
- **TypeScript** Telegram Mini App with Pip-Boy themed UI
- Uses `telegram-web-app` SDK
- Compiles to `web/dist/` via TypeScript
- Served by Caddy at the root path

### 2. Streamer Backend (`streamer/`)
- **Python 3.12** application using FastAPI and python-telegram-bot
- **GStreamer** for audio streaming (encodes to MP3 and sends to Icecast)
- Manages multiple radio stations with playlists
- Telegram bot integration for admin commands:
  - `/list` - List available streams
  - `/select <name>` - Select current station for admin operations
  - Send audio files to add to playlist
- REST API at port 5000 (proxied through Caddy at `/api/`)

### 3. Infrastructure
- **Icecast** (`docker/icecast/`) - Radio streaming server on port 8000
- **Caddy** (`docker/caddy/`) - Reverse proxy and static file server

## Commands

### Development
```bash
# Build frontend TypeScript (from web/ directory)
cd web
pnpm tsc --outDir dist src/main.ts

# Or use the Makefile
make dist/main.js  # Builds single file (pattern: dist/*.js: src/*.ts)

# Run streamer locally (requires Python 3.12 and GStreamer)
cd streamer
uv sync  # Install dependencies
uv run python -m gachibass --config config.yml

# Run all services (from root)
docker compose up --build
```

### Configuration
- `streamer/config.yml` - Stream configuration (Icecast connection, streams, admins)
- Environment variables for `docker-compose.yml`:
  - `ICECAST_*` - Icecast server settings
  - `STREAMER_BOT_TOKEN` - Required Telegram bot token

### Stream Configuration Structure
```yaml
icecast:
  server: icecast
  port: 8000
  password: password
  username: source

admins:
  - 123456789  # Telegram user IDs

streams:
  main:
    name: Main Music Stream
    mount: /main
    playlist: /music/main/
```

## Key Implementation Details

### GStreamer Pipeline
The streaming pipeline in `streamer/src/gachibass/streaming/stream.py`:
```
filesrc → decodebin → audioconvert → audioresample → volume → lamemp3enc → shout2send
```
- Runs in separate threads with GLib main loop
- Auto-advances playlist on EOS/error
- Supports MP3, WAV, OGG, FLAC, M4A, AAC files

### API Routing (Caddy)
- `/` → Static files from `web/dist/`
- `/radio/*` → Icecast proxy
- `/api/*` → Streamer FastAPI backend

### TODO/Incomplete Features
- `streamer/src/gachibass/playlist/__init__.py` - Playlist class is a stub (next, shuffle, etc. not implemented)
- `streamer/src/gachibass/streaming/__init__.py` - `is_admin()` always returns True, station management functions are stubs
- Stream initialization is referenced in `api/__init__.py` but the `streams` dict import is incomplete
