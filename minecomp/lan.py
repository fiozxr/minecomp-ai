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

    def __eq__(self, other):
        if not isinstance(other, ServerAnnounce):
            return NotImplemented
        return (self.ip, self.world, self.players, self.port) == (
            other.ip, other.world, other.players, other.port,
        )

    def __hash__(self):
        return hash((self.ip, self.world, self.players, self.port))

    def __repr__(self):
        return f"ServerAnnounce(ip={self.ip}, world={self.world}, players={self.players})"


class LanDiscovery:
    def __init__(self, port: int = DISCOVERY_PORT):
        self.port = port
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self.sock.settimeout(0.5)
        self.servers = []
        self._running = False

    def _send_broadcast(self):
        payload = f"{BANNER}|{os.uname().nodename}|{os.getlogin()}"
        for target in (BROADCAST_ADDR, "192.168.1.255", "192.168.0.255"):
            try:
                self.sock.sendto(payload.encode(), (target, self.port))
            except OSError:
                continue

    def _handle_datagram(self, data, addr):
        try:
            text = data.decode("utf-8", errors="ignore").strip()
        except Exception:
            return
        if text.startswith(BANNER):
            try:
                announce = ServerAnnounce.parse(text[len(BANNER) + 1:])
                announce.ip = addr[0]
                if announce not in self.servers:
                    self.servers.append(announce)
            except ValueError:
                pass

    def _receive_loop(self, stop_event):
        """Blocking socket loop, meant to run in a thread/executor."""
        while not stop_event.is_set():
            try:
                data, addr = self.sock.recvfrom(4096)
            except socket.timeout:
                continue
            except socket.error:
                break
            self._handle_datagram(data, addr)

    def _continuous_loop(self, interval, stop_event):
        """Broadcast periodically while receiving, until stop_event is set."""
        import time
        while not stop_event.is_set():
            self._send_broadcast()
            deadline = time.time() + interval
            while time.time() < deadline and not stop_event.is_set():
                try:
                    data, addr = self.sock.recvfrom(4096)
                except socket.timeout:
                    continue
                except socket.error:
                    break
                self._handle_datagram(data, addr)

    async def discover(self, timeout: float = 3.0):
        """Return a list of announced servers on the LAN (one scan)."""
        self.sock.bind(("0.0.0.0", 0))
        self.servers = []
        stop_event = asyncio.Event()
        loop = asyncio.get_event_loop()
        loop.call_soon(self._send_broadcast)
        future = loop.run_in_executor(None, self._receive_loop, stop_event)

        await asyncio.sleep(timeout)
        stop_event.set()
        await future
        return self.servers

    async def discover_continuous(self, interval: float = 3.0):
        """Keep scanning the LAN until `stop()` is called.

        This returns immediately; the scan runs in the background. Read
        ``self.servers`` at any time to see what has been found so far, and
        call :meth:`stop` when done.
        """
        self.sock.bind(("0.0.0.0", 0))
        self.servers = []
        self._running = True
        self._stop_event = asyncio.Event()

        loop = asyncio.get_event_loop()
        self._executor_future = loop.run_in_executor(
            None, self._continuous_loop, interval, self._stop_event
        )
        return self.servers

    def stop(self):
        """Stop a running continuous discovery."""
        self._running = False
        if getattr(self, "_stop_event", None):
            self._stop_event.set()

    def clear(self):
        self.servers = []
