$ErrorActionPreference = "Stop"

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Host "Python not found"
    exit 1
}

pip install -r requirements.txt
New-Item -ItemType Directory -Path "dist" -Force | Out-Null

pyinstaller --onefile --noconsole --distpath dist svchost.py
pyinstaller --onefile --distpath dist server.py

Write-Host "Build complete. Binaries in dist/"