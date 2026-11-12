# minecomp-ai — AI Minecraft Bedrock Agent

A terminal-driven AI agent that joins a Minecraft: Bedrock LAN world and
executes tasks given via chat, using any OpenAI-compatible API.

## Quick Start (copy-paste ready)

### 1. Install dependencies
```bash
curl -sSL https://github.com/fiozxr/minecomp-ai/raw/main/setup.sh | bash
```

That's it. The installer will:
- Check Python and install dependencies
- Create ~/.minecomp-ai/config.yaml from the example
- Guide you through first-run setup

### 2. Configure your API key
```bash
nano ~/.minecomp-ai/config.yaml
```
Set your `api_key` (OpenRouter, NVIDIA, or any OpenAI-compatible endpoint).

### 3. Set up the Minecraft server side
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

### 4. Run the agent
```bash
python -m minecomp
```

### 5. Chat with your agent
Players in your LAN world type messages. The AI agent reads them
and responds or executes commands (teleport, give items, change weather, etc.).


## Custom Provider Setup

The agent supports any OpenAI-compatible API (OpenRouter, NVIDIA, local models, etc.).

### Setup

1. **Get your API key** from your provider.

2. **Set the base URL** for your provider. Common examples:

   | Provider | base_url |
   |----------|----------|
   | OpenRouter | `https://openrouter.ai/api/v1` |
   | NVIDIA | `https://integrate.api.nvidia.com/v1` |
   | Local (Ollama, LM Studio) | `http://localhost:1234/v1` |

3. **Update `~/.minecomp-ai/config.yaml`**:

   ```yaml
   api_key: "your-api-key-here"
   base_url: "https://openrouter.ai/api/v1"
   model: "google/gemini-2.0-flash"
   ```

4. **Run the agent**:

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

### Example: Using NVIDIA

```bash
pip install openai
python -m minecomp --api-key YOUR_NVIDIA_KEY --base-url https://integrate.api.nvidia.com/v1 --model nvidia/llama-3.3-70b-instruct
```

## Configuration

See `config.yaml.example` for all available options.

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


## Using a Custom Provider (Step-by-Step)

### 1. Configure your API key and base URL

Edit `~/.minecomp-ai/config.yaml`:

```yaml
api_key: "your-api-key"
base_url: "https://openrouter.ai/api/v1"  # or your custom endpoint
model: "google/gemini-2.0-flash"
```

### 2. List available models

```bash
python -m minecomp --list-models --api-key YOUR_KEY --base-url https://openrouter.ai/api/v1
```

The program will fetch the available models and display them:

```
Available models:
  [1] google/gemini-2.0-flash
  [2] google/gemini-2.0-flash-lite
  [3] openai/gpt-4o-mini
  [4] openai/gpt-4o
```

### 3. Select a model

Use the `--model` flag or edit the config:

```bash
python -m minecomp --model google/gemini-2.0-flash
```

### Examples

**OpenRouter:**
```bash
python -m minecomp --api-key sk-... --base-url https://openrouter.ai/api/v1 --model google/gemini-2.0-flash
```

**NVIDIA:**
```bash
python -m minecomp --api-key nvapi-... --base-url https://integrate.api.nvidia.com/v1 --model nvidia/llama-3.3-70b-instruct
```

**Local model (Ollama/LM Studio):**
```bash
python -m minecomp --api-key local --base-url http://localhost:1234/v1 --model llama-3.3-70b-instruct
```

## Configuration Reference

See `config.yaml.example` for all available options.

## Requirements

- Python 3.11+
- Minecraft: Bedrock Edition with cheats enabled
- mcbe-ws-sdk addon on the server
- WebSocket gateway on the server
- OpenAI-compatible API key (OpenRouter, NVIDIA, etc.)

## License

MIT
