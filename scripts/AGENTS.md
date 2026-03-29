# Scripts - Agent Reference

## Overview

Start and stop scripts for running the app locally via Docker Compose. Covers Mac, Linux, and Windows.

## Scripts

| File | Platform | Action |
|------|----------|--------|
| `start.sh` | Mac / Linux | `docker compose up --build -d` |
| `start.bat` | Windows | `docker compose up --build -d` |
| `stop.sh` | Mac / Linux | `docker compose down` |
| `stop.bat` | Windows | `docker compose down` |

## Usage

**Mac / Linux:**
```bash
chmod +x scripts/start.sh scripts/stop.sh
./scripts/start.sh   # builds image and starts container
./scripts/stop.sh    # stops and removes container
```

**Windows:**
```bat
scripts\start.bat
scripts\stop.bat
```

After starting, the app is available at `http://localhost:8000`.
