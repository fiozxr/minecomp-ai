"""LAN-based Minecraft server discovery.

The agent broadcasts a UDP discovery packet on the local network; any
running Minecraft: Bedrock server (with minecomp-ai announce enabled)
responds with its world list. This lets the agent present a list of
available worlds for the user to choose from.
"""

import asyncio
import os
import socket

DISCOVERY_PORT = 4242
BROADCAST_ADDR = "255.255.255.255"
BANNER = "MINECOMP_DISCOVER"


class ServerAnnounce:
    """Metadata announced by a minecomp-ai-backed server."""

    def __init__(self, ip: str, world: str, players: int, port: int = 19132):
        self.ip = ip
        self.world = world
        self.players = players
        self.port = port

    @classmethod
    def parse(cls, data: str):
        parts = data.split("|")
        if len(parts) < 3:
            raise ValueError(f"Invalid announce: {data!r}")
        ip = parts[0]
        world = parts[1]
        players = int(parts[2])
        return cls(ip=ip, world=world, players=players)

    def to_json(self):
        return {"ip": self.ip, "world": self.world, "players": self.players, "port": self.port}

    def __repr__(self):
        return f"ServerAnnounce(ip={self.ip}, world={self.world}, players={self.players})"


class LanDiscovery:
    def __init__(self, port: int = DISCOVERY_PORT):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(0.5)

    def _send_broadcast(self):
        payload = f"{BANNER}|{os.uname().nodename}|{os.getlogin()}"
        for target in (BROADCAST_ADDR, "192.168.1.255", "192.168.0.255"):
            try:
                self.sock.sendto(payload.encode(), (target, self.port))
            except OSError:
                continue

    async def discover(self, timeout: float = 3.0):
        """Return a list of announced servers on the LAN."""
        self.sock.bind(("0.0.0.0", 0))
        self.servers = []

        loop = asyncio.get_event_loop()
        loop.call_soon(self._send_broadcast)
        future = loop.run_in_executor(None, self._receive_loop, timeout)

        await future
        return self.servers

    def _receive_loop(self, timeout):
        import time
        deadline = time.time() + timeout
        self.servers = []
        while time.time() < deadline:
            try:
                data, addr = self.sock.recvfrom(4096)
            except socket.error:
                break
            try:
                text = data.decode("utf-8", errors="ignore").strip()
            except Exception:
                continue
            if text.startswith(BANNER):
                try:
                    announce = ServerAnnounce.parse(text[len(BANNER) + 1:])
                    announce.ip = addr[0]
                    if announce not in self.servers:
                        self.servers.append(announce)
                except ValueError:
                    continue
        return self.servers

    def clear(self):
        self.servers = []
