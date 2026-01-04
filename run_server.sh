#!/bin/bash
# freee MCP Server Launcher with logging

# Change to the freee-mcp directory
cd "$(dirname "$0")" || exit 1

LOG_FILE="/tmp/freee-mcp-$(date +%Y%m%d-%H%M%S).log"

{
    echo "=== freee MCP Server Start ===" >&2
    echo "Time: $(date)" >&2
    echo "Script location: $(dirname "$0")" >&2
    echo "Working directory: $(pwd)" >&2
    echo "Python: $(/Users/ksato/workspace/.venv/bin/python --version)" >&2
    echo "Environment variables:" >&2
    env | grep FREEE_ >&2
    echo "Checking server.py exists:" >&2
    ls -la src/server.py >&2
    echo "===========================" >&2

    exec /Users/ksato/workspace/.venv/bin/python src/server.py
} 2>>"$LOG_FILE"
