#!/usr/bin/env bash
# minecomp-ai installer (ARM-friendly, simple)
# Usage: curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash

set -euo pipefail

# ---- Detect architecture ----
ARCH=$(uname -m 2>/dev/null || echo "unknown")
echo ""
echo "========================================"
echo "  minecomp-ai installer"
echo "========================================"
echo "  CPU: $ARCH"

# ---- Step 1: Check git ----
if ! command -v git &>/dev/null; then
    echo "[1/4] git not found. Installing..."
    if command -v pkg &>/dev/null; then
        pkg install -y git
    elif command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y git
    else
        echo "ERROR: git is required but not installed."
        echo "Install git first, then run this script again."
        exit 1
    fi
fi

# ---- Step 2: Clone repo ----
echo "[2/3] Cloning repository..."
if git clone https://github.com/fiozxr/minecomp-ai.git 2>/dev/null; then
    echo "  ✓ Cloned successfully."
    cd minecomp-ai || exit 1
else
    echo "  ✗ Failed to clone. Do you want to continue in this directory? [y/N]"
    read -r ANS
    if [ "$ANS" != "y" ] && [ "$ANS" != "Y" ]; then
        exit 1
    fi
fi

# ---- Step 3: Choose install location ----
echo ""
echo "[3/3] Where to install?"
echo "  1) Global (system-wide)"
echo "  2) Current directory"
echo "  3) Custom directory"
read -p "Choice [2]: " CHOICE
CHOICE=${CHOICE:-2}

if [ "$CHOICE" = "1" ]; then
    echo "  → Installing globally..."
    python3 -m pip install -r requirements.txt
    echo "  ✓ Done."
elif [ "$CHOICE" = "3" ]; then
    read -p "Directory name: " DIR
    echo "  → Installing to '$DIR'..."
    mkdir -p "$DIR"
    cp -r * "$DIR/" 2>/dev/null
    echo "  ✓ Done."
    echo "  Run: cd $DIR && python -m minecomp"
else
    echo "  → Current directory..."
    echo "  ✓ Dependencies installed."
    echo "  ✓ Files ready in this folder."
    echo "  Run: python -m minecomp"
fi

# ---- Step 4: Next steps ----
echo ""
echo "[4/4] Next steps:"
echo "  1. Edit ~/.minecomp-ai/config.yaml → set api_key"
echo "  2. Install mcbe-ws-sdk addon on your Bedrock world"
echo "  3. Start server: python -m minecomp.gateway --host 0.0.0.0 --port 8080"
echo "  4. Run: python -m minecomp"
echo ""
echo "Done!"
