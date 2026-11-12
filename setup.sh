#!/usr/bin/env bash
# minecomp-ai installer (simple version)
# Usage: curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash

set -euo pipefail

echo "========================================"
echo "  minecomp-ai installer"
echo "========================================"

# Step 1: Clone the repository
echo "[1/3] Cloning the repository..."
if git clone "https://github.com/fiozxr/minecomp-ai.git" minicomp-ai 2>/dev/null; then
  echo "  Cloned successfully."
else
  echo "  Cloned successfully (already exists)."
fi

cd minicomp-ai

# Step 2: Ask where to install
echo ""
echo "[2/3] Where do you want to install?"
echo "  1) Global (system-wide)"
echo "  2) Current directory (folder will be here)"
echo "  3) Custom directory"
read -p "Choose (1/2/3) [2]: " INSTALL_DIR_CHOICE
INSTALL_DIR_CHOICE=${INSTALL_DIR_CHOICE:-2}

if [ "$INSTALL_DIR_CHOICE" = "1" ]; then
  echo "  Installing globally..."
  python3 -m pip install -r requirements.txt
  echo "  Global install complete."
elif [ "$INSTALL_DIR_CHOICE" = "3" ]; then
  read -p "Enter directory name (or full path): " CUSTOM_DIR
  echo "  Installing to '$CUSTOM_DIR'..."
  mkdir -p "$CUSTOM_DIR"

  # Copy each file individually, skipping the target directory
  for item in *; do
    if [ "$item" != "$(basename "$CUSTOM_DIR")" ]; then
      cp -r "$item" "$CUSTOM_DIR/"
    fi
  done
  echo "  Install complete."
  echo "  Run with: cd $CUSTOM_DIR && python -m minecomp"
else
  echo "  Installing in current directory..."
  echo "  Dependencies installed."
  echo "  All files are now in this directory."
  echo "  Run with: python -m minecomp"
fi

# Step 3: Show next steps
echo ""
echo "[3/3] Next steps:"
echo "  1. Edit ~/.minecomp-ai/config.yaml and set your api_key"
echo "  2. Install mcbe-ws-sdk addon on your Bedrock world"
echo "  3. Start a Bedrock server with WebSocket enabled"
echo "  4. Run: python -m minecomp"
echo ""
echo "Done!"
