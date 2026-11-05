#!/bin/sh
# Wrapper so GUIs and lichess-bot can launch the engine as one executable.
DIR="$(cd "$(dirname "$0")" && pwd)"
exec python3 "$DIR/uci.py"
