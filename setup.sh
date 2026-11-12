#!/usr/bin/env bash
# minecomp-ai installer (interactive, ARM-friendly)
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
    echo "[0/6] Directory 'minecomp-ai' already exists."
    echo "  Use it, or clone fresh? [use]"
    read -r ANS
    if [ "$ANS" = "n" ] || [ "$ANS" = "N" ]; then
        echo "  Removing old directory..."
        rm -rf minecomp-ai
    fi
fi

# ---- Step 1: Check and install git ----
echo ""
echo "[1/6] Checking for git..."
if ! command -v git &>/dev/null; then
    info "git is not installed. Installing..."
    if command -v pkg &>/dev/null; then
        pkg install -y git
    elif command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y git
    elif command -v apk &>/dev/null; then
        apk add git
    elif command -v brew &>/dev/null; then
        brew install git
    else
        error "git is required but could not be installed."
        exit 1
    fi
fi
command -v git &>/dev/null || { error "git still not found. Exiting."; exit 1; }
success "git found."

# ---- Step 2: Clone repository ----
echo ""
echo "[2/6] Cloning repository..."
if [ -d "minecomp-ai" ]; then
    echo "  Using existing directory..."
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

# ---- Step 3: Check and install Python ----
echo ""
echo "[3/6] Checking for Python..."
if ! command -v python3 &>/dev/null; then
    info "Python is not installed. Installing..."
    if command -v pkg &>/dev/null; then
        pkg install -y python
    elif command -v apt-get &>/dev/null; then
        apt-get update && apt-get install -y python3 python3-pip
    elif command -v apk &>/dev/null; then
        apk add python3 py3-pip
    elif command -v brew &>/dev/null; then
        brew install python
    else
        error "Python 3 required but could not be installed."
        exit 1
    fi
fi
command -v python3 &>/dev/null || { error "Python 3 still not found. Exiting."; exit 1; }
success "Python $(python3 --version 2>&1) found."

# Check pip
if ! python3 -m pip --version &>/dev/null; then
    info "pip is not installed. Installing..."
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
echo "[4/6] Installing dependencies..."
if ! python3 -m pip install -r requirements.txt 2>/dev/null; then
    warn "Some packages failed. Trying with --break-system-packages..."
    python3 -m pip install --break-system-packages -r requirements.txt 2>/dev/null || {
        echo "  ⚠ Manual install needed: python3 -m pip install -r requirements.txt"
    }
fi
success "Dependencies installed."

# ---- Step 5: Choose install location ----
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

# ---- Step 6: Configure API key and settings ----
echo ""
echo "[6/6] Let's configure your API key and settings."
echo ""
read -p "  Enter your API key: " API_KEY
echo ""
echo ""
echo "  What model would you like to use?"
echo "  1) mercury-2"
echo "  2) mercury-2.5"
echo "  3) mercury-3"
echo "  4) mercury-decide"
echo "  5) Custom model name"
read -p "  Choice [1]: " MODEL_CHOICE
MODELS=("mercury-2" "mercury-2.5" "mercury-3" "mercury-decide")
if [ "$MODEL_CHOICE" = "5" ]; then
    read -p "  Enter model name: " CUSTOM_MODEL
    MODEL=${CUSTOM_MODEL:-mercury-3}
else
    MODEL=${MODELS[$((MODEL_CHOICE-1))]}
fi

echo ""
echo "  What is your base URL?"
echo "  1) OpenRouter (https://openrouter.ai/api/v1)"
echo "  2) Inception Labs (https://api.inceptionlabs.ai/v1)"
echo "  3) NVIDIA (https://integrate.api.nvidia.com/v1)"
echo "  4) Custom URL"
read -p "  Choice [2]: " BASE_URL_CHOICE
case "$BASE_URL_CHOICE" in
    1) BASE_URL="https://openrouter.ai/api/v1" ;;
    2) BASE_URL="https://api.inceptionlabs.ai/v1" ;;
    3) BASE_URL="https://integrate.api.nvidia.com/v1" ;;
    4) read -p "  Enter base URL: " BASE_URL ;;
    *) BASE_URL="https://api.inceptionlabs.ai/v1" ;;
esac

# ---- Create config file ----
echo ""
echo "[6/6] Creating configuration file..."

# Create config directory
mkdir -p ~/.minecomp-ai

# Create config.yaml
cat > ~/.minecomp-ai/config.yaml << YAMLEOF
# minecomp-ai configuration
api_key: "$API_KEY"
base_url: "$BASE_URL"
model: "$MODEL"
gateway_host: "127.0.0.1"
gateway_port: 8080
YAMLEOF

success "Configuration file created at ~/.minecomp-ai/config.yaml"
echo "  API Key: ${API_KEY:0:8}..."
echo "  Model: $MODEL"
echo "  Base URL: $BASE_URL"

# ---- Step 7: Next steps ----
echo ""
echo "[7/5] Next steps:"
echo "  1. Your agent is ready!"
echo "  2. Start the WebSocket gateway on your Bedrock server:"
echo "     python -m minecomp.gateway --host 0.0.0.0 --port 8080"
echo "  3. Run the agent:"
echo "     python -m minecomp"
echo ""
echo "Done!"
