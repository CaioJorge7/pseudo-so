#!/bin/sh
# Executa o pseudo-SO em Linux/macOS (ambiente UNIX).
cd "$(dirname "$0")"
if [ "$#" -eq 0 ]; then
    python3 dispatcher.py processes.txt files.txt string.txt
else
    python3 dispatcher.py "$@"
fi
