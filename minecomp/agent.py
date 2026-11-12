"""Main agent orchestrator.

Responsibilities:
  * load configuration (API key, model, gateway address)
  * connect to the Bedrock WebSocket gateway
  * run the task loop (chat -> LLM -> action/response)
  * keep the agent alive in the world and react to events
"""

import asyncio
import os
import sys

from . import core
from . import llm as llm_mod
from . import lan
from . import ws_bridge as ws_mod
from . import chat_bridge as chat_mod


class Agent:
    def __init__(self, config: dict):
        self.config = config
        # Fall back to env var for API key
        if self.config.get("api_key") is None:
            self.config["api_key"] = os.environ.get("MINECOMP_API_KEY")
        self.llm = llm_mod.LLM(
            api_key=self.config.get("api_key"),
            model=self.config.get("model", "google/gemini-2.0-flash"),
            base_url=self.config.get("base_url"),
        )
        self.bridge = ws_mod.WsBridge(
            host=config.get("gateway_host", "127.0.0.1"),
            port=config.get("gateway_port", 8080),
        )
        self.task_queue = asyncio.Queue()
        self.chat_bridge = chat_mod.ChatBridge(self, self.llm)
        self.running = False

    async def connect_gateway(self) -> bool:
        try:
            await self.bridge.connect(timeout=10.0)
            return True
        except Exception as e:
            print(f"[!] Gateway connection failed: {e}", file=sys.stderr)
            return False

    async def send_say(self, message: str):
        """Send a /say to the world (broadcast to all players)."""
        return await self.bridge.send_command(f"say {message}")

    async def stop(self):
        self.running = False
        await self.chat_bridge.stop()
        await self.bridge.close()

    # -- internal ---------------------------------------------------------

    def _build_context(self, sender: str, message: str) -> list:
        """Build the prompt context for the LLM."""
        system_prompt = (
            "You are a helpful AI agent inside a Minecraft: Bedrock world called "
            "minecomp-ai. You read player messages and can act by sending slash "
            "commands to the game. Respond with a plain chat message to players, "
            "or a command (starting with /) to act in the world.\n\n"
            "Available actions you can send:\n"
            "  /say <text>     - broadcast a message to all players\n"
            "  /tp @p <x> <y> <z> - teleport to coordinates\n"
            "  /give @p <item> <count> - give items\n"
            "  /time set <day|night|0|1|2|3> - change time\n"
            "  /weather clear|rain|thunder - change weather\n"
            "  /xp <amount> - give experience\n\n"
            "Keep responses short. If you don't know what to do, just reply in "
            "chat. Never send the same command twice in a row."
        )
        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Player {sender} says: {message}"},
        ]

    # -- main loop ------------------------------------------------------

    async def run(self):
        """Full agent lifecycle: connect, start chat bridge, process tasks."""
        self.running = True
        print("[minecomp-ai] Connecting to gateway ...")
        if not await self.connect_gateway():
            print("[!] Could not connect. Exiting.", file=sys.stderr)
            return

        print(f"[minecomp-ai] Connected to gateway at "
              f"{self.bridge.host}:{self.bridge.port}")
        print("[minecomp-ai] Chat bridge active. Type 'quit' to exit.")

        await self.chat_bridge.run()

        # Keep alive until 'quit' is requested
        try:
            while self.running:
                await asyncio.sleep(1)
        finally:
            await self.stop()


def parse_args(argv):
    """Minimal argument parser (no argparse dependency)."""
    config = {
        "api_key": None,
        "model": "google/gemini-2.0-flash",
        "model_name": None,
        "base_url": None,
        "gateway_host": "127.0.0.1",
        "gateway_port": 8080,
        "config_file": None,
        "list_models": False,
    }
    i = 0
    while i < len(argv):
        arg = argv[i]
        if arg == "--config" and i + 1 < len(argv):
            config["config_file"] = argv[i + 1]
            i += 2
        elif arg == "--api-key" and i + 1 < len(argv):
            config["api_key"] = argv[i + 1]
            i += 2
        elif arg == "--base-url" and i + 1 < len(argv):
            config["base_url"] = argv[i + 1]
            i += 2
        elif arg == "--list-models":
            config["list_models"] = True
            i += 1
        elif arg == "--model" and i + 1 < len(argv):
            config["model"] = argv[i + 1]
            i += 2
        elif arg.startswith("--model="):
            config["model"] = arg.split("=", 1)[1]
            i += 1
        elif arg.startswith("--gateway-host="):
            config["gateway_host"] = arg.split("=", 1)[1]
            i += 1
        elif arg == "--gateway-host" and i + 1 < len(argv):
            config["gateway_host"] = argv[i + 1]
            i += 2
        elif arg.startswith("--gateway-port="):
            config["gateway_port"] = int(arg.split("=", 1)[1])
            i += 1
        elif arg == "--gateway-port" and i + 1 < len(argv):
            config["gateway_port"] = int(argv[i + 1])
            i += 2
        else:
            print(f"Unknown argument: {arg}", file=sys.stderr)
            i += 1
    return config

def load_config(config_path: str) -> dict:
    """Load configuration from a YAML file if provided."""
    import yaml

    default = {
        "api_key": None,
        "model": "google/gemini-2.0-flash",
        "model_name": None,
        "base_url": None,
        "gateway_host": "127.0.0.1",
        "gateway_port": 8080,
    }
    if config_path and os.path.exists(config_path):
        with open(config_path) as f:
            loaded = yaml.safe_load(f) or {}
            default.update(loaded)
    return default
