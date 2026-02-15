#!/usr/bin/env bash
# Expose local Team Brain server via ngrok for Poke connection.
# Start the server first: python src/server.py
# Then run: ./ngrok.sh  (or: ngrok http 8000)

PORT="${PORT:-8000}"
echo "Exposing http://localhost:$PORT (add /mcp for Poke MCP URL)"
exec ngrok http "$PORT"
