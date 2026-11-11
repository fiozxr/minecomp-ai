"""Terminal user interface.

The UI walks the user through:
  1. Configuration (API key, model, gateway address)
  2. LAN server discovery
  3. World selection
  4. Confirmation of the agent launch
"""

from __future__ import annotations

import asyncio
import os
import sys

from . import agent as agent_mod
from . import lan

CONFIG_DIR = os.path.expanduser("~/.minecomp-ai")
CONFIG_FILE = os.path.join(CONFIG_DIR, "config.yaml")


def _prompt(text: str, default: str = "") -> str:
    """Simple prompt with a default value."""
    suffix = f" [{default}]" if default else ""
    try:
        val = input(f"{text}{suffix}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return val if val else default


def _prompt_password(text: str, default: str = "") -> str:
    """Prompt but hide input."""
    import getpass
    try:
        val = getpass.getpass(f"{text}: ").strip()
    except (EOFError, KeyboardInterrupt):
        print()
        sys.exit(0)
    return val if val else default


def _select_world(servers: list) -> dict:
    """Present a numbered list of discovered servers and return the choice."""
    if not servers:
        print("[!] No servers found on the LAN.")
        sys.exit(1)

    print("\n[ Available Minecraft worlds ]")
    for i, s in enumerate(servers, 1):
        print(f"  [{i}]  {s.world}  ({s.players} player(s), {s.ip})")

    while True:
        try:
            choice = input("\nSelect world [1]: ").strip()
            idx = int(choice) - 1
            if 0 <= idx < len(servers):
                return servers[idx].to_json()
        except (ValueError, EOFError, KeyboardInterrupt):
            pass
        print("Invalid selection. Try again.")


def _load_or_configure() -> dict:
    """Check for an existing config; if missing, guide the user through setup."""
    os.makedirs(CONFIG_DIR, exist_ok=True)

    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE) as f:
            import yaml
            return yaml.safe_load(f) or {}

    print("=" * 40)
    print("  minecomp-ai first-run setup")
    print("=" * 40)
    print("\nThis program controls an AI agent in a Minecraft: Bedrock world.")
    print("The agent connects to a WebSocket gateway on your Bedrock server.")
    print("Default gateway address: 127.0.0.1:8080 (run the gateway on the server)")
    print("=" * 40)

    cfg = {}
    cfg["api_key"] = _prompt_password("  OpenAI-compatible API key")
    cfg["model"] = _prompt("  Model name", "google/gemini-2.0-flash")
    cfg["base_url"] = _prompt(
        "  API base URL (OpenRouter default)",
        "https://openrouter.ai/api/v1",
    )
    cfg["gateway_host"] = _prompt("  Gateway host", "127.0.0.1")
    cfg["gateway_port"] = _prompt("  Gateway port", "8080")

    with open(CONFIG_FILE, "w") as f:
        import yaml
        yaml.safe_dump(cfg, f, default_flow_style=False)

    print(f"\n  Config saved to {CONFIG_FILE}")
    return cfg


async def run_ui() -> None:
    """Entry point for the interactive UI."""
    print("=" * 40)
    print("  minecomp-ai")
    print("  AI Minecraft Bedrock Agent")
    print("=" * 40)

    # 1. Load / configure
    config = _load_or_configure()

    # 2. LAN discover
    print("\n[ Discovering Minecraft worlds on LAN ... ]")
    disc = lan.LanDiscovery()
    servers = await disc.discover(timeout=3.0)
    if not servers:
        print("[!] No servers discovered. Is a minecomp-ai server running?")
        sys.exit(1)

    # 3. Select world
    world = _select_world(servers)

    # 4. Confirm launch
    print("\n" + "=" * 40)
    print("  Launching agent ...")
    print(f"  World:  {world['world']}")
    print(f"  Model:  {config['model']}")
    print(f"  Server: {world['ip']}:{world['port']}")
    print("=" * 40)

    a = agent_mod.Agent(config)
    await a.run()


def main():
    """CLI entry point."""
    config = agent_mod.parse_args(sys.argv[1:])
    cfg_path = config.pop("config_file", None)
    if cfg_path:
        config = agent_mod.load_config(cfg_path)

    # Merge CLI overrides
    if config.get("api_key"):
        config["api_key"] = config.pop("api_key")
    if config.get("model"):
        config["model"] = config.pop("model")

    asyncio.run(run_ui())


if __name__ == "__main__":
    main()
