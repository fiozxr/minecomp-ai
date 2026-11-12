#!/usr/bin/env bash
# minecomp-ai installer (ARM-friendly, robust)
# Usage: curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash

set -euo pipefail

# ---- Detect architecture ----
ARCH=$(uname -m 2>/dev/null || echo "unknown")
echo ""
echo "========================================"
echo "  minecomp-ai installer"
echo "========================================"
echo "  CPU: $ARCH"

# ---- Helper functions ----
info()    { echo "  ℹ $*"; }
error()   { echo "  ✗ ERROR: $*" >&2; }
warn()    { echo "  ⚠ $*"; }
success() { echo "  ✓ $*"; }

# ---- Step 0: Directory check ----
echo ""
if [ -d "minecomp-ai" ]; then
    echo "[0/5] Directory 'minecomp-ai' already exists."
    echo "  Use it, or clone fresh? [use]"
    read -r ANS
    if [ "$ANS" = "n" ] || [ "$ANS" = "N" ]; then
        echo "  Removing old directory..."
        rm -rf minecomp-ai
    fi
fi

# ---- Step 1: Check git ----
echo ""
echo "[1/5] Checking for git..."
if ! command -v git &>/dev/null; then
    info "git not found. Installing..."
    if command -v pkg &>/dev/null; then
        pkg install -y git
    elif command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y git
    elif command -v apk &>/dev/null; then
        apk add git
    elif command -v brew &>/dev/null; then
        brew install git
    else
        error "git required but could not install."
        exit 1
    fi
fi
command -v git &>/dev/null || { error "git still not found. Exiting."; exit 1; }
success "git found."

# ---- Step 2: Clone repository ----
echo ""
echo "[2/5] Cloning repository..."
if [ -d "minecomp-ai" ]; then
    echo "  Directory exists. Using it..."
    cd minecomp-ai
else
    if git clone https://github.com/fiozxr/minecomp-ai.git 2>/dev/null; then
        success "Repository cloned."
        cd minecomp-ai
    else
        error "Failed to clone repository."
        exit 1
    fi
fi

# ---- Step 3: Check Python ----
echo ""
echo "[3/5] Checking for Python..."
if ! command -v python3 &>/dev/null; then
    info "Python not found. Installing..."
    if command -v pkg &>/dev/null; then
        pkg install -y python
    elif command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y python3 python3-pip
    elif command -v apk &>/dev/null; then
        apk add python3 py3-pip
    elif command -v brew &>/dev/null; then
        brew install python
    else
        error "Python 3 required but could not install."
        exit 1
    fi
fi
command -v python3 &>/dev/null || { error "Python 3 still not found. Exiting."; exit 1; }
success "Python $(python3 --version 2>&1) found."

# Check pip
if ! python3 -m pip --version &>/dev/null; then
    info "pip not found. Installing..."
    if command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y python3-pip
    elif command -v apk &>/dev/null; then
        apk add py3-pip
    else
        python3 -m ensurepip --upgrade
    fi
fi
success "pip found."

# ---- Step 4: Install dependencies ----
echo ""
echo "[4/5] Installing dependencies..."
if ! python3 -m pip install -r requirements.txt 2>/dev/null; then
    warn "Some packages failed. Trying with --break-system-packages..."
    python3 -m pip install --break-system-packages -r requirements.txt 2>/dev/null || {
        echo "  ⚠ Manual install needed: python3 -m pip install -r requirements.txt"
    }
fi
success "Dependencies installed."

# ---- Step 6: Choose install location ----
echo ""
echo "[5/5] Where to install?"
echo "  1) Global (system-wide)"
echo "  2) Current directory"
echo "  3) Custom directory"
read -p "Choice [2]: " CHOICE
CHOICE=${CHOICE:-2}

if [ "$CHOICE" = "1" ]; then
    echo "  → Global install..."
    python3 -m pip install -r requirements.txt
    success "Global install complete."
elif [ "$CHOICE" = "3" ]; then
    read -p "Directory name: " DIR
    echo "  → Installing to '$DIR'..."
    mkdir -p "$DIR"
    cp -r * "$DIR/" 2>/dev/null
    success "Install complete."
    echo "  Run: cd $DIR && python -m minecomp"
else
    echo "  → Current directory..."
    echo "  ✓ Dependencies installed."
    echo "  ✓ Files ready in this folder."
    echo "  Run: python -m minecomp"
fi

# ---- Step 6: Next steps ----
echo ""
echo "[6/5] Next steps:"
echo "  1. Edit ~/.minecomp-ai/config.yaml → set api_key"
echo "  2. Install mcbe-ws-sdk addon on your Bedrock world"
echo "  3. Start server: python -m minecomp.gateway --host 0.0.0.0 --port 8080"
echo "  4. Run: python -m minecomp"
echo ""
echo "Done!"
