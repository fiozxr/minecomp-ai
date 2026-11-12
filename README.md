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
