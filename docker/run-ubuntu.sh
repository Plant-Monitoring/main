#!/usr/bin/env bash
# One-command launch for Ubuntu/Linux. Run from the repository root.
set -e

# Allow local Docker containers to use the X11 display
xhost +local:docker

docker compose -f docker/docker-compose.ubuntu.yml up --build

# When you stop (Ctrl+C), optionally revoke X11 access again:
# xhost -local:docker