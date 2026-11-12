#!/usr/bin/env bash
# minecomp-ai setup installer
# Usage: curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash

set -euo pipefail

echo "========================================"
echo "  minecomp-ai setup installer"
echo "========================================"

echo "[1/5] Checking Python ..."
if ! command -v python3 &>/dev/null; then
  echo "ERROR: python3 is not installed."
  exit 1
fi
PY_VER=$(python3 --version 2>&1)
echo "  Found: $PY_VER"

if [ -f requirements.txt ]; then
  echo "[2/5] Installing dependencies ..."
  python3 -m pip install --upgrade pip
  python3 -m pip install -r requirements.txt
  echo "  Done."
fi

if [ -f config.yaml.example ]; then
  if [ ! -f ~/.minecomp-ai/config.yaml ]; then
    echo "  Creating ~/.minecomp-ai/config.yaml from example ..."
    cp config.yaml.example ~/.minecomp-ai/config.yaml
    echo "  Open ~/.minecomp-ai/config.yaml and fill in your api_key."
  else
    echo "  Existing config found at ~/.minecomp-ai/config.yaml"
  fi
fi

echo "[3/5] Git setup ..."
if [ -d .git ]; then
  echo "  Already a git repo."
else
  echo "  Initializing git repo ..."
  git init
  git add -A
  git commit -m "Initial commit: minecomp-ai"
  echo "  Committed."
fi

echo "[4/5] Next steps ..."
echo ""
echo "  Configuration:"
echo "    Edit ~/.minecomp-ai/config.yaml and set your api_key."
echo ""
echo "  Minecraft side:"
echo "    1. Install mcbe-ws-sdk addon on your Bedrock world"
echo "    2. Start a Bedrock server with WebSocket enabled"
echo "    3. Run:  python -m minecomp.gateway --host 0.0.0.0 --port 8080"
echo ""
echo "  Agent side:"
echo "    python -m minecomp"
echo ""
echo "  Enjoy!"
exit 0
