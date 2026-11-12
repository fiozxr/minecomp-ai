# minecomp-ai — AI Minecraft Bedrock Agent

A terminal-driven AI agent that joins a Minecraft: Bedrock LAN world and
executes tasks given via chat, using any OpenAI-compatible API.

## Quick Start (copy-paste ready)

### 1. Run the installer
```bash
curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash
```

The installer will:
- Check and install `git` / `python3` / `pip` if missing
- Ask where to install (global or current directory)
- Ask which provider you use (OpenRouter, OpenAI, NVIDIA, Together AI,
  Groq, DeepSeek, Mistral, Ollama, or a custom endpoint)
- Ask for your API key
- Fetch the live model list from your provider and let you pick a model
- Install dependencies and write `~/.minecomp-ai/config.yaml`

### 2. Set up the Minecraft server side
On your Bedrock server:
1. Install the **mcbe-ws-sdk** addon in the world
2. Start the WebSocket gateway:
   ```bash
   python -m minecomp.gateway --host 0.0.0.0 --port 8080
   ```
3. In the Minecraft world (cheats ON), run:
   ```
   /wsserver <server-ip>:8080
   ```

### 3. Run the agent
```bash
python -m minecomp
```

### 4. Chat with your agent
Players in your LAN world type messages. The AI agent reads them
and responds or executes commands (teleport, give items, change weather, etc.).


## Custom Provider Setup

The agent supports any OpenAI-compatible API. The installer asks which provider
you use, fetches the live model list from it, and lets you pick a model — or
enter any model name manually.

### Supported providers

| Provider | base_url |
|----------|----------|
| OpenRouter | `https://openrouter.ai/api/v1` |
| OpenAI | `https://api.openai.com/v1` |
| NVIDIA | `https://integrate.api.nvidia.com/v1` |
| Together AI | `https://api.together.xyz/v1` |
| Groq | `https://api.groq.com/openai/v1` |
| DeepSeek | `https://api.deepseek.com/v1` |
| Mistral | `https://api.mistral.ai/v1` |
| Ollama (local) | `http://localhost:11434/v1` |
| Any other OpenAI-compatible endpoint | custom base URL |

### Setup

1. **Run the installer** — it asks for your provider, API key, and model:

   ```bash
   curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash
   ```

2. **Or configure manually** — edit `~/.minecomp-ai/config.yaml`:

   ```yaml
   api_key: "your-api-key-here"
   base_url: "https://openrouter.ai/api/v1"
   model: "google/gemini-2.0-flash"
   ```

3. **Run the agent**:

   ```bash
   python -m minecomp
   ```

### List Available Models

To see what models your provider offers:

```bash
python -m minecomp --list-models
```

This will fetch the available models from your API provider and display them.

### Use a Specific Model

You can select a model by:
- Using the `--model` CLI flag: `python -m minecomp --model google/gemini-2.0-flash`
- Or editing `~/.minecomp-ai/config.yaml`

## Configuration

The installer writes `~/.minecomp-ai/config.yaml` for you. To change
providers or models later, edit that file or re-run the installer.

```yaml
api_key: "your-api-key-here"
base_url: "https://openrouter.ai/api/v1"
model: "google/gemini-2.0-flash"
gateway_host: "127.0.0.1"
gateway_port: 8080
```

| Key | Description | Default |
|-----|-------------|---------|
| `api_key` | API key for your provider | — |
| `base_url` | OpenAI-compatible API base URL | `https://openrouter.ai/api/v1` |
| `model` | Model ID from your provider | `google/gemini-2.0-flash` |
| `gateway_host` | WebSocket gateway host | `127.0.0.1` |
| `gateway_port` | WebSocket gateway port | `8080` |

## Architecture

```
Minecraft: Bedrock World (cheats ON)
   |  /wsserver <host>:8080
   v
WebSocket Gateway (minecomp.gateway)
   |
   v
minecomp-ai Agent (terminal UI)
   |  LLM via OpenRouter / NVIDIA / any OpenAI-compatible API
   v
Player chat -> LLM -> /say or /command -> game
```

## Behavior

- **LAN discovery**: UDP broadcast on port 4242; the agent lists all
  minecomp-ai servers found on the local network
- **World selection**: Terminal UI lets you pick a world to join
- **Task processing**: Players type messages -> LLM decides whether to
  reply in chat or execute a slash command
- **Supported actions**: /say, /tp, /give, /time set, /weather, /xp

## Requirements

- Python 3.11+
- Minecraft: Bedrock Edition with cheats enabled
- mcbe-ws-sdk addon on the server
- WebSocket gateway on the server
- OpenAI-compatible API key (OpenRouter, NVIDIA, etc.)

## License

MIT


## Command-Line Reference

The `minecomp` entry point accepts the following command-line arguments:

| Flag | Description |
|------|-------------|
| `--model <name>` | Select the AI model (any model ID from your provider) |
| `--model=<name>` | Same as above, alternative syntax |
| `--base-url <url>` | OpenAI-compatible API base URL (e.g., `https://openrouter.ai/api/v1`) |
| `--api-key <key>` | API key for the LLM provider |
| `--list-models` | Fetch and list available models, then exit |
| `--config <path>` | Path to a YAML config file (default: `~/.minecomp-ai/config.yaml`) |
| `--gateway-host <host>` | WebSocket gateway host (default: `127.0.0.1`) |
| `--gateway-port <port>` | WebSocket gateway port (default: `8080`) |

### CLI Examples

```bash
# List available models
python -m minecomp --list-models --api-key YOUR_KEY --base-url https://openrouter.ai/api/v1

# Run with a specific model and provider
python -m minecomp --model YOUR_MODEL --api-key YOUR_KEY --base-url https://your-provider.com/v1

# Run with default config
python -m minecomp
```

## Issues & Support

### Reporting Bugs

If you encounter a bug, please open an issue on GitHub with:
- Your operating system and Python version (`python --version`)
- The command you ran
- The full error message (copy-paste, not screenshots)
- Any relevant output from `--list-models`

### Getting Help

- Check the [Examples](#examples) section first — your use case may already be covered
- Search existing GitHub issues before opening a new one
- Provide reproducible steps and any logs from the terminal

## Contributing

We welcome contributions! Here's how to get started:

### Development Setup

```bash
# Clone the repository
git clone https://github.com/fiozxr/minecomp-ai.git
cd minecomp-ai

# Run the installer (or install manually)
curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash

# Activate your virtual environment
source venv/bin/activate

# Run tests (if available)
python -m minecomp --list-models --api-key YOUR_KEY --base-url https://openrouter.ai/api/v1
```

### How to Contribute

1. **Fork** the repository
2. **Create a branch** for your feature or bugfix
3. **Test your changes** locally (run `python -m minecomp --list-models`)
4. **Commit** with clear, descriptive messages
5. **Open a pull request** with:
   - A summary of the change
   - Testing steps you performed
   - Screenshots or logs (if applicable)
   - Any breaking changes (if applicable)

### Areas for Contribution

- **LLM providers** — add support for new OpenAI-compatible APIs
- **Minecraft gameplay** — add more slash commands (`/say`, `/tp`, `/give`, etc.)
- **UI** — improve the terminal interface and world selection
- **Documentation** — translations, examples, troubleshooting guides
- **Performance** — optimize LLM calls, reduce latency

## Troubleshooting & Diagnostics

### Common Issues

#### No servers found on the network

- Ensure your Bedrock server is running
- Check that UDP broadcast is allowed on port 4242 (firewall settings)
- Try `python -m minecomp.lan` directly to debug discovery

#### API key rejected

- Verify your API key is correct and active
- Check the base URL is correct (common mistake: missing `/v1` suffix)
- Ensure the model name is supported by your provider (run `--list-models` to see)

#### Gateway connection failed

- Start the WebSocket gateway on the server:
  ```bash
  python -m minecomp.gateway --host 0.0.0.0 --port 8080
  ```
- In Minecraft, run `/wsserver <server-ip>:8080` (cheats ON)
- Verify the IP address matches your server's LAN IP

### Diagnostics

Run these commands to diagnose issues:

```bash
# Check Python version
python --version

# List available models
python -m minecomp --list-models --api-key YOUR_KEY --base-url https://openrouter.ai/api/v1

# Test LLM connectivity
python -c "from minecomp.llm import LLM; import asyncio; llm = LLM(model='YOUR_MODEL', base_url='https://your-provider.com/v1', api_key='YOUR_KEY'); print(asyncio.run(llm.list_models()))"

# Check config file
cat ~/.minecomp-ai/config.yaml
```

## Examples

### Example 1: Run with OpenRouter

```bash
python -m minecomp --api-key sk-... --base-url https://openrouter.ai/api/v1 --model google/gemini-2.0-flash
```

### Example 2: Run with NVIDIA

```bash
python -m minecomp --api-key nvapi-... --base-url https://integrate.api.nvidia.com/v1 --model nvidia/llama-3.3-70b-instruct
```

### Example 3: Run with any other OpenAI-compatible provider

```bash
python -m minecomp --api-key YOUR_KEY --base-url https://your-provider.com/v1 --model YOUR_MODEL
```

## Project Structure

```
minecomp-ai/
├── setup.sh                    # One-click installer
├── README.md                   # This file
├── requirements.txt            # Python dependencies
├── minecomp/
│   ├── __init__.py            # Version: 0.2.1
│   ├── __main__.py            # Entry point (python -m minecomp)
│   ├── agent.py               # Core orchestrator
│   ├── llm.py                 # LLM client (OpenAI-compatible)
│   ├── lan.py                 # LAN discovery (UDP broadcast)
│   ├── ws_bridge.py           # WebSocket bridge for Minecraft
│   ├── chat_bridge.py         # Chat bridge between players and AI
│   ├── gateway.py             # WebSocket gateway (server-side)
│   └── ui.py                  # Terminal user interface
└── minecomp-ai/               # User config directory (~/.minecomp-ai)
    └── config.yaml             # Your configuration (created by setup.sh)
```

## Roadmap

- [ ] Add more Minecraft slash commands (`/effect`, `/scoreboard`, etc.)
- [ ] Support for voice chat and TTS
- [ ] Web-based UI option
- [ ] Cloud deployment guides (Docker, VPS)
- [ ] Multi-agent coordination

## License

MIT
