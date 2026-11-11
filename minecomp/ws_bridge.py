"""WebSocket bridge to a Minecraft: Bedrock server via a WebSocket gateway.

Minecraft: Bedrock Edition does not ship an official RCON-like API.
The de-facto approach is the Bedrock WebSocket protocol (MCBEWS/2) used
by the `mcbe-ws-sdk` gateway. This module connects to that gateway and
exposes:

  * send_command()      -> execute a /command in the game
  * listen_chat()       -> async iterator of chat messages from players
  * listen_events()     -> async iterator of game events (entity spawn, etc.)

The agent uses this bridge to act in the world and to receive tasks from
players over LAN chat.
"""

import asyncio
import json
import uuid

PROTOCOL_VERSION = "MCBEWS/2"

# Capability names the agent advertises
AGENT_CAPABILITIES = [
    "minecomp.ai/command:execute",
    "minecomp.ai/chat:receive",
    "minecomp.ai/chat:send",
]


class WsBridge:
    """Async WebSocket connection to a Bedrock WebSocket gateway."""

    def __init__(self, host: str, port: int = 8080):
        self.host = host
        self.port = port
        self.ws = None
        self._closing = False
        self._chat_queue: asyncio.Queue = asyncio.Queue()
        self._msg_queue: asyncio.Queue = asyncio.Queue()

        # Callbacks
        self.on_chat = lambda _: None      # noqa: E731
        self.on_event = lambda _: None    # noqa: E731

    async def connect(self, timeout: float = 10.0) -> bool:
        """Connect to the gateway and complete protocol negotiation."""
        import websockets

        self._closing = False
        self.ws = await asyncio.wait_for(
            websockets.connect(
                f"ws://{self.host}:{self.port}", open_timeout=timeout
            ),
            timeout=timeout,
        )
        await self._negotiate()
        # Start listener in the background
        asyncio.create_task(self._listen())
        return True

    async def close(self):
        self._closing = True
        if self.ws:
            await self.ws.close()

    # -- internal ---------------------------------------------------------

    async def _negotiate(self):
        """Send our capabilities and wait for a connection-accepted response."""
        req_id = str(uuid.uuid4())
        await self.ws.send(json.dumps({
            "protocol": PROTOCOL_VERSION,
            "messagePurpose": "connectionRequest",
            "messageType": "connectionRequest",
            "requestId": req_id,
            "body": {
                "capabilities": AGENT_CAPABILITIES,
                "clientMetadata": {"name": "minecomp-ai"},
            },
        }))

        # Wait for connectionAccepted
        while True:
            raw = await self.ws.recv()
            data = json.loads(raw)
            if (data.get("messagePurpose") == "connectionAccepted"
                    and data.get("requestId") == req_id):
                return
            # If it's a failure, raise
            if data.get("messagePurpose") == "connectionRejected":
                raise RuntimeError(f"Gateway rejected connection: {data.get('body', {})}")

    async def _listen(self):
        """Background loop reading messages from the gateway."""
        assert self.ws is not None
        async for raw in self.ws:
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                continue

            mtype = data.get("messageType")
            purpose = data.get("messagePurpose")

            if mtype == "chatMessage":
                body = data.get("body", {})
                self._chat_queue.put_nowait((
                    body.get("sender", "unknown"),
                    body.get("message", ""),
                ))
            elif mtype == "event":
                self._msg_queue.put_nowait(("event", data.get("body", {})))
            elif mtype == "commandResult":
                self._msg_queue.put_nowait(("command_result", data.get("body", {})))

    # -- public API -------------------------------------------------------

    async def send_command(self, command: str, timeout: float = 5.0):
        """Send a slash command to the game. Returns True if executed."""
        if self.ws is None:
            raise RuntimeError("Not connected to gateway")
        request_id = str(uuid.uuid4())
        await self.ws.send(json.dumps({
            "protocol": PROTOCOL_VERSION,
            "messagePurpose": "commandRequest",
            "messageType": "commandRequest",
            "requestId": request_id,
            "body": {"command": command},
        }))

        # Wait for the matching commandResponse (simplified polling)
        deadline = asyncio.get_event_loop().time() + timeout
        while asyncio.get_event_loop().time() < deadline:
            try:
                raw = await asyncio.wait_for(self.ws.recv(), timeout=0.5)
            except asyncio.TimeoutError:
                continue
            data = json.loads(raw)
            if (data.get("messagePurpose") == "commandResponse"
                    and data.get("requestId") == request_id):
                return data.get("body", {}).get("success", False)
        return False

    async def listen_chat(self):
        """Async iterator over (sender, message) tuples from LAN players."""
        while not self._closing:
            try:
                sender, message = await asyncio.wait_for(
                    self._chat_queue.get(), timeout=1.0
                )
                yield sender, message
            except asyncio.TimeoutError:
                continue

    async def listen_events(self):
        """Async iterator over game event dicts."""
        while not self._closing:
            try:
                kind, payload = await asyncio.wait_for(
                    self._msg_queue.get(), timeout=1.0
                )
                if kind == "event":
                    yield payload
            except asyncio.TimeoutError:
                continue

    @property
    def is_connected(self) -> bool:
        return self.ws is not None
