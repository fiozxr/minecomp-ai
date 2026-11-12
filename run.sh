#!/usr/bin/env bash
# minecomp-ai — one script to install, configure, and run the agent.
# Usage:
#   curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/run.sh | bash
#   bash run.sh              # setup (if needed) then run
#   bash run.sh --install    # only setup / re-configure, don't run
#   bash run.sh --run        # only run (assume already configured)

set -euo pipefail

# Interactive prompts must work even when the script is piped via curl.
{ exec < /dev/tty; } 2>/dev/null || true

prompt() {
    local val=""
    read -r -p "$1 " val || true
    printf '%s' "$val"
}

CONFIG_DIR="$HOME/.minecomp-ai"
CONFIG_FILE="$CONFIG_DIR/config.yaml"
REPO="https://github.com/fiozxr/minecomp-ai.git"
APP_DIR="$HOME/.local/share/minecomp-ai"
DO_INSTALL=0
DO_RUN=1

for arg in "$@"; do
    case "$arg" in
        --install) DO_INSTALL=1; DO_RUN=0 ;;
        --run) DO_RUN=1 ;;
    esac
done

echo "========================================"
echo "  minecomp-ai"
echo "========================================"

# ---------------------------------------------------------------------------
# Preflight
# ---------------------------------------------------------------------------
echo ""
echo "Checking resources..."

if ! command -v git >/dev/null 2>&1; then
    echo "  git not found. Installing..."
    if command -v pkg >/dev/null 2>&1; then pkg install -y git
    elif command -v apt-get >/dev/null 2>&1; then apt-get update && apt-get install -y git
    elif command -v apk >/dev/null 2>&1; then apk add git
    elif command -v brew >/dev/null 2>&1; then brew install git
    else echo "ERROR: git required but could not be installed."; exit 1; fi
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "  python3 not found. Installing..."
    if command -v pkg >/dev/null 2>&1; then pkg install -y python
    elif command -v apt-get >/dev/null 2>&1; then apt-get update && apt-get install -y python3 python3-pip
    elif command -v apk >/dev/null 2>&1; then apk add python3 py3-pip
    elif command -v brew >/dev/null 2>&1; then brew install python
    else echo "ERROR: python3 required but could not be installed."; exit 1; fi
fi

if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "  pip not found. Installing..."
    if command -v apt-get >/dev/null 2>&1; then apt-get update && apt-get install -y python3-pip
    elif command -v apk >/dev/null 2>&1; then apk add py3-pip
    else python3 -m ensurepip --upgrade || true; fi
fi

echo "  All resources OK."

# ---------------------------------------------------------------------------
# Install if missing (or --install requested)
# ---------------------------------------------------------------------------
needs_install=0
if [ ! -d "$APP_DIR" ]; then
    needs_install=1
fi

if [ "$DO_INSTALL" = "1" ] || [ "$needs_install" = "1" ]; then
    echo ""
    echo "Installing minecomp-ai ..."

    if [ ! -d "$APP_DIR" ]; then
        mkdir -p "$HOME/.local/share"
        git clone "$REPO" "$APP_DIR" || { echo "ERROR: failed to clone."; exit 1; }
    fi

    cd "$APP_DIR"
    python3 -m pip install -r requirements.txt >/dev/null 2>&1 \
        || python3 -m pip install --break-system-packages -r requirements.txt >/dev/null 2>&1 \
        || { echo "ERROR: dependency install failed."; echo "  Run manually: python3 -m pip install -r requirements.txt"; exit 1; }

    echo "  Dependencies installed."

    # Launcher on PATH
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/minecomp" <<'L'
#!/usr/bin/env bash
exec bash "$HOME/.local/share/minecomp-ai/run.sh" --run "$@"
L
    chmod +x "$HOME/.local/bin/minecomp"
    echo "  Launcher created: ~/.local/bin/minecomp"
fi

# ---------------------------------------------------------------------------
# Configuration (ask only if not present or --install)
# ---------------------------------------------------------------------------
if [ "$DO_INSTALL" = "1" ] || [ ! -f "$CONFIG_FILE" ]; then
    echo ""
    echo "Configuration"

    # Provider
    echo "Which provider do you want to use?"
    echo "  1) OpenRouter     (https://openrouter.ai/api/v1)"
    echo "  2) OpenAI         (https://api.openai.com/v1)"
    echo "  3) NVIDIA         (https://integrate.api.nvidia.com/v1)"
    echo "  4) Together AI    (https://api.together.xyz/v1)"
    echo "  5) Groq           (https://api.groq.com/openai/v1)"
    echo "  6) DeepSeek       (https://api.deepseek.com/v1)"
    echo "  7) Mistral        (https://api.mistral.ai/v1)"
    echo "  8) Ollama (local) (http://localhost:11434/v1)"
    echo "  9) Custom provider (enter your own base URL)"
    PROVIDER_CHOICE=$(prompt "Choice [3]: ")
    PROVIDER_CHOICE=${PROVIDER_CHOICE:-3}

    case "$PROVIDER_CHOICE" in
        1) BASE_URL="https://openrouter.ai/api/v1" ;;
        2) BASE_URL="https://api.openai.com/v1" ;;
        3) BASE_URL="https://integrate.api.nvidia.com/v1" ;;
        4) BASE_URL="https://api.together.xyz/v1" ;;
        5) BASE_URL="https://api.groq.com/openai/v1" ;;
        6) BASE_URL="https://api.deepseek.com/v1" ;;
        7) BASE_URL="https://api.mistral.ai/v1" ;;
        8) BASE_URL="http://localhost:11434/v1" ;;
        9) BASE_URL=$(prompt "Enter provider base URL:") ;;
        *) BASE_URL="https://integrate.api.nvidia.com/v1" ;;
    esac

    API_KEY=$(prompt "Enter your API key:")
    while [ -z "$API_KEY" ]; do
        API_KEY=$(prompt "API key cannot be empty. Enter your API key:")
    done

    # Fetch models live
    echo ""
    echo "Fetching available models from $BASE_URL ..."
    MODEL_LIST=$(python3 - "$BASE_URL" "$API_KEY" <<'PY' 2>/dev/null
import json, sys, urllib.request
base_url = sys.argv[1].rstrip("/")
api_key = sys.argv[2]
req = urllib.request.Request(base_url + "/models", headers={"Authorization": "Bearer " + api_key})
with urllib.request.urlopen(req, timeout=30) as r:
    payload = json.load(r)
seen = set()
for item in payload.get("data", []):
    mid = item.get("id")
    if mid and mid not in seen:
        seen.add(mid); print(mid)
for item in payload.get("models", []):
    mid = item.get("name") or item.get("id")
    if mid and mid not in seen:
        seen.add(mid); print(mid)
PY
) || MODEL_LIST=""

    MODEL=""
    if [ -n "$MODEL_LIST" ]; then
        echo "Select a model:"
        declare -a MODELS=()
        TOTAL=0
        while IFS= read -r MID; do
            TOTAL=$((TOTAL + 1))
            MODELS[$TOTAL]="$MID"
        done <<< "$MODEL_LIST"
        MAX_SHOW=50
        SHOW=$TOTAL
        if [ "$SHOW" -gt "$MAX_SHOW" ]; then SHOW=$MAX_SHOW; fi
        for i in $(seq 1 "$SHOW"); do echo "  $i) ${MODELS[$i]}"; done
        if [ "$TOTAL" -gt "$SHOW" ]; then echo "  ... and $((TOTAL - SHOW)) more (choose 0 for manual)"; fi
        echo "  0) Enter model name manually"
        echo ""
        MODEL_CHOICE=$(prompt "Choice [1]: ")
        MODEL_CHOICE=${MODEL_CHOICE:-1}
        if [ "$MODEL_CHOICE" = "0" ]; then
            MODEL=$(prompt "Model name:")
        elif [ "$MODEL_CHOICE" -ge 1 ] 2>/dev/null && [ "$MODEL_CHOICE" -le "$SHOW" ] 2>/dev/null; then
            MODEL="${MODELS[$MODEL_CHOICE]}"
        fi
    fi
    if [ -z "$MODEL" ]; then
        MODEL=$(prompt "Enter model name manually:")
    fi
    if [ -z "$MODEL" ]; then
        echo "ERROR: model is required."
        exit 1
    fi

    mkdir -p "$CONFIG_DIR"
    cat > "$CONFIG_FILE" <<YAMLEOF
api_key: "$API_KEY"
base_url: "$BASE_URL"
model: "$MODEL"
gateway_host: "127.0.0.1"
gateway_port: 8080
YAMLEOF
    echo ""
    echo "  Config written to $CONFIG_FILE"
fi

# ---------------------------------------------------------------------------
# Run
# ---------------------------------------------------------------------------
if [ "$DO_RUN" = "1" ]; then
    cd "$APP_DIR"
    echo ""
    echo "Starting agent (continuous LAN discovery)..."
    exec python3 -m minecomp
fi
