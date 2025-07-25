#!/bin/bash
# Simple runner script for RAG_07 CLI
# Usage: ./run.sh <command> [args...]

cd "$(dirname "$0")"
export PYTHONPATH="$(pwd)"
exec .venv/bin/python src/cli.py "$@"
