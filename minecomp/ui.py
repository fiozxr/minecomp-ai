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


def list_available_models(config_path: str = None):
    """Fetch available models from the configured API provider.

    Returns a list of (model_name, description) tuples.
    """
    import os

    config = {}
    if config_path and os.path.exists(config_path):
        import yaml
        with open(config_path) as f:
            config = yaml.safe_load(f) or {}

    api_key = config.get("api_key") or os.environ.get("MINECOMP_API_KEY")
    base_url = config.get("base_url") or os.environ.get("MINECOMP_BASE_URL", "https://openrouter.ai/api/v1")

    if not api_key:
        print("[!] No API key found. Set MINECOMP_API_KEY env var or use --api-key.")
        return []

    from .llm import LLM
    llm = LLM(api_key=api_key, base_url=base_url)

    models = asyncio.run(llm.list_models())
    if not models:
        # Fallback: return default model
        return [("google/gemini-2.0-flash", "Default model (OpenRouter)")]

    # Return as (name, description) tuples
    return [(m, "Run model") for m in models]


def _select_world(servers: list, allow_empty: bool = False) -> dict:
    """Present a numbered list of discovered servers and return the choice.

    If `allow_empty` is True and there are no servers yet, return None so the
    caller can keep waiting instead of exiting.
    """
    if not servers:
        if allow_empty:
            return None
        print("[!] No servers found on the LAN.")
        sys.exit(1)

    print("\n[ Available Minecraft worlds ]")
    for i, s in enumerate(servers, 1):
        print(f"  [{i}]  {s.world}  ({s.players} player(s), {s.ip})")

    while True:
        try:
            choice = input("\nSelect world [1]: ").strip()
            if not choice:
                return None
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

    # 2. Discover LAN worlds continuously until one is selected
    print("\n[ Searching for Minecraft worlds on LAN ... (Ctrl+C to stop) ]")
    disc = lan.LanDiscovery()
    try:
        await disc.discover_continuous(interval=3.0)
    except Exception as e:
        print(f"[!] Discovery error: {e}")
        sys.exit(1)

    try:
        # Keep waiting until the user picks a world; re-print the list as
        # new servers appear.
        seen = set()
        while True:
            if not disc.servers:
                print("  No servers yet — still searching...")
            else:
                for s in disc.servers:
                    key = (s.ip, s.world)
                    if key not in seen:
                        print(f"  [New] {s.world} ({s.players} player(s), {s.ip})")
                        seen.add(key)

            world = _select_world(disc.servers, allow_empty=True)
            if world is not None:
                break
            await asyncio.sleep(2)
    finally:
        disc.stop()

    # 3. Confirm launch
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
    cli = agent_mod.parse_args(sys.argv[1:])
    cfg_path = cli.pop("config_file", None)

    # Base config: explicit --config file, else the default user config file
    if cfg_path:
        config = agent_mod.load_config(cfg_path)
    elif os.path.exists(CONFIG_FILE):
        config = agent_mod.load_config(CONFIG_FILE)
    else:
        config = {}

    # CLI flags override values from the config file
    if cli.get("api_key"):
        config["api_key"] = cli["api_key"]
    if cli.get("model") and cli["model"] != "google/gemini-2.0-flash":
        config["model"] = cli["model"]
    if cli.get("base_url"):
        config["base_url"] = cli["base_url"]
    if cli.get("gateway_host") and cli["gateway_host"] != "127.0.0.1":
        config["gateway_host"] = cli["gateway_host"]
    if cli.get("gateway_port") and cli["gateway_port"] != 8080:
        config["gateway_port"] = cli["gateway_port"]

    if cli.get("list_models"):
        # List models and exit
        from . import llm as llm_mod

        # Determine base_url
        base_url = config.get("base_url") or os.environ.get("MINECOMP_BASE_URL", "https://openrouter.ai/api/v1")
        api_key = config.get("api_key") or os.environ.get("MINECOMP_API_KEY")

        if not api_key:
            print("[!] No API key found. Use --api-key, set MINECOMP_API_KEY, or run setup.sh.")
            sys.exit(1)

        llm = llm_mod.LLM(api_key=api_key, base_url=base_url)
        models = asyncio.run(llm.list_models())

        if models:
            print("Available models:")
            for i, model_name in enumerate(models, 1):
                print(f"  [{i}] {model_name}")
        else:
            print("No models found. Check your API key and base_url.")
            sys.exit(1)
        return

    asyncio.run(run_ui())


if __name__ == "__main__":
    main()
