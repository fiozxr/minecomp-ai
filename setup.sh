#!/usr/bin/env bash
# minecomp-ai installer
# Usage: curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash

set -euo pipefail

# Read a line from the terminal (not stdin) so the script works even when
# invoked via `curl -sSL ... | bash`.
# If we have a controlling terminal, read prompts from it rather than from the
# curl pipe (so `curl -sSL ... | bash` still prompts interactively).
{ exec < /dev/tty; } 2>/dev/null || true

prompt() {
    local val=""
    read -r -p "$1 " val || true
    printf '%s' "$val"
}

echo "========================================"
echo "  minecomp-ai installer"
echo "========================================"

# ---------------------------------------------------------------------------
# Preflight: check resources (git, python3, pip, GitHub)
# ---------------------------------------------------------------------------
echo ""
echo "Checking resources..."

if ! command -v git >/dev/null 2>&1; then
    echo "  git not found. Installing..."
    if command -v pkg >/dev/null 2>&1; then
        pkg install -y git
    elif command -v apt-get >/dev/null 2>&1; then
        apt-get update && apt-get install -y git
    elif command -v apk >/dev/null 2>&1; then
        apk add git
    elif command -v brew >/dev/null 2>&1; then
        brew install git
    else
        echo "ERROR: git is required but could not be installed."
        exit 1
    fi
fi

if ! command -v python3 >/dev/null 2>&1; then
    echo "  python3 not found. Installing..."
    if command -v pkg >/dev/null 2>&1; then
        pkg install -y python
    elif command -v apt-get >/dev/null 2>&1; then
        apt-get update && apt-get install -y python3 python3-pip
    elif command -v apk >/dev/null 2>&1; then
        apk add python3 py3-pip
    elif command -v brew >/dev/null 2>&1; then
        brew install python
    else
        echo "ERROR: python3 is required but could not be installed."
        exit 1
    fi
fi

if ! python3 -m pip --version >/dev/null 2>&1; then
    echo "  pip not found. Installing..."
    if command -v apt-get >/dev/null 2>&1; then
        apt-get update && apt-get install -y python3-pip
    elif command -v apk >/dev/null 2>&1; then
        apk add py3-pip
    else
        python3 -m ensurepip --upgrade || true
    fi
fi

if ! git ls-remote https://github.com/fiozxr/minecomp-ai.git >/dev/null 2>&1; then
    echo "ERROR: cannot reach GitHub (github.com/fiozxr/minecomp-ai)."
    echo "       Check your internet connection and try again."
    exit 1
fi

echo "  All resources OK."

# ---------------------------------------------------------------------------
# Question 1: where to install
# ---------------------------------------------------------------------------
echo ""
echo "Where do you want to install?"
echo "  1) Global (system-wide)"
echo "  2) Current directory"
echo "  3) Exit"
INSTALL_CHOICE=$(prompt "Choice [1]: ")
INSTALL_CHOICE=${INSTALL_CHOICE:-1}

if [ "$INSTALL_CHOICE" = "3" ]; then
    echo "Exiting."
    exit 0
fi

# ---------------------------------------------------------------------------
# Question 2: which provider
# ---------------------------------------------------------------------------
echo ""
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
PROVIDER_CHOICE=$(prompt "Choice [1]: ")
PROVIDER_CHOICE=${PROVIDER_CHOICE:-1}

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
    *) BASE_URL="https://openrouter.ai/api/v1" ;;
esac

if [ -z "$BASE_URL" ]; then
    echo "ERROR: provider base URL is required."
    exit 1
fi

# ---------------------------------------------------------------------------
# Question 3: API key
# ---------------------------------------------------------------------------
echo ""
API_KEY=$(prompt "Enter your API key:")

if [ -z "$API_KEY" ]; then
    echo "ERROR: API key is required."
    exit 1
fi

# ---------------------------------------------------------------------------
# Fetch models from the provider
# ---------------------------------------------------------------------------
echo ""
echo "Fetching available models from $BASE_URL ..."

MODEL_LIST=$(python3 - "$BASE_URL" "$API_KEY" <<'PY' 2>/dev/null
import json
import sys
import urllib.request

base_url = sys.argv[1].rstrip("/")
api_key = sys.argv[2]

request = urllib.request.Request(
    base_url + "/models",
    headers={"Authorization": "Bearer " + api_key},
)
with urllib.request.urlopen(request, timeout=30) as response:
    payload = json.load(response)

seen = set()

# OpenAI-style: {"data": [{"id": ...}]}
for item in payload.get("data", []):
    model_id = item.get("id")
    if model_id and model_id not in seen:
        seen.add(model_id)
        print(model_id)

# Ollama-style: {"models": [{"name": ...}]}
for item in payload.get("models", []):
    model_id = item.get("name") or item.get("id")
    if model_id and model_id not in seen:
        seen.add(model_id)
        print(model_id)
PY
) || MODEL_LIST=""

# ---------------------------------------------------------------------------
# Question 4: select a model
# ---------------------------------------------------------------------------
echo ""
MODEL=""

if [ -n "$MODEL_LIST" ]; then
    echo "Select a model:"
    declare -a MODELS=()
    TOTAL=0
    while IFS= read -r MODEL_ID; do
        TOTAL=$((TOTAL + 1))
        MODELS[$TOTAL]="$MODEL_ID"
    done <<< "$MODEL_LIST"

    MAX_SHOW=50
    SHOW=$TOTAL
    if [ "$SHOW" -gt "$MAX_SHOW" ]; then
        SHOW=$MAX_SHOW
    fi

    for i in $(seq 1 "$SHOW"); do
        echo "  $i) ${MODELS[$i]}"
    done
    if [ "$TOTAL" -gt "$SHOW" ]; then
        echo "  ... and $((TOTAL - SHOW)) more (choose 0 to enter a model name manually)"
    fi
    echo "  0) Enter model name manually"
    echo ""

    MODEL_CHOICE=$(prompt "Choice [1]: ")
    MODEL_CHOICE=${MODEL_CHOICE:-1}

    if [ "$MODEL_CHOICE" = "0" ]; then
        MODEL=$(prompt "Model name:")
    elif [ "$MODEL_CHOICE" -ge 1 ] 2>/dev/null && [ "$MODEL_CHOICE" -le "$SHOW" ] 2>/dev/null; then
        MODEL="${MODELS[$MODEL_CHOICE]}"
    else
        echo "  Invalid choice."
    fi
fi

if [ -z "$MODEL" ]; then
    MODEL=$(prompt "Enter model name manually:")
fi

if [ -z "$MODEL" ]; then
    echo "ERROR: model is required."
    exit 1
fi

# ---------------------------------------------------------------------------
# Install
# ---------------------------------------------------------------------------
echo ""
echo "Installing minecomp-ai..."

if [ "$INSTALL_CHOICE" = "1" ]; then
    APP_DIR="$HOME/.local/share/minecomp-ai"
else
    APP_DIR="$PWD/minecomp-ai"
fi

if [ ! -d "$APP_DIR" ]; then
    git clone https://github.com/fiozxr/minecomp-ai.git "$APP_DIR" || {
        echo "ERROR: failed to clone the repository."
        exit 1
    }
fi
cd "$APP_DIR"

echo "  Installing dependencies..."
python3 -m pip install -r requirements.txt >/dev/null 2>&1 \
    || python3 -m pip install --break-system-packages -r requirements.txt >/dev/null 2>&1 \
    || {
        echo "ERROR: failed to install dependencies."
        echo "       Run manually: python3 -m pip install -r requirements.txt"
        exit 1
    }
echo "  Dependencies installed."

if [ "$INSTALL_CHOICE" = "1" ]; then
    mkdir -p "$HOME/.local/bin"
    cat > "$HOME/.local/bin/minecomp" <<'LAUNCHER'
#!/usr/bin/env bash
cd "$HOME/.local/share/minecomp-ai" && python3 -m minecomp "$@"
LAUNCHER
    chmod +x "$HOME/.local/bin/minecomp"
    echo "  Launcher created: ~/.local/bin/minecomp"
    case ":$PATH:" in
        *":$HOME/.local/bin:"*) ;;
        *) echo "  Note: add ~/.local/bin to your PATH to run 'minecomp' anywhere." ;;
    esac
fi

# ---------------------------------------------------------------------------
# Write configuration
# ---------------------------------------------------------------------------
mkdir -p "$HOME/.minecomp-ai"

cat > "$HOME/.minecomp-ai/config.yaml" <<YAMLEOF
# minecomp-ai configuration (created by setup.sh)
api_key: "$API_KEY"
base_url: "$BASE_URL"
model: "$MODEL"
gateway_host: "127.0.0.1"
gateway_port: 8080
YAMLEOF

# ---------------------------------------------------------------------------
# Done
# ---------------------------------------------------------------------------
echo ""
echo "========================================"
echo "  Installation complete!"
echo "========================================"
echo ""
echo "  Provider: $BASE_URL"
echo "  Model:    $MODEL"
echo "  Config:   ~/.minecomp-ai/config.yaml"
echo ""
echo "Next steps:"
echo "  1. Start the gateway: python3 -m minecomp.gateway --host 0.0.0.0 --port 8080"
echo "  2. Run the agent:     python3 -m minecomp"
echo ""
echo "Done!"
