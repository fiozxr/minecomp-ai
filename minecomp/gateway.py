"""minicomp-ai WebSocket gateway — runs on the Minecraft: Bedrock server.

This is a standalone gateway that bridges the Minecraft world to an
AI agent over WebSocket. It:

  1. Listens for WebSocket connections (agents connect here).
  2. Negotiates the MCBEWS/2 protocol.
  3. Can forward commands to the game and relay chat/events back.

To run on your server:
    python -m minecomp.gateway --host 0.0.0.0 --port 8080

In the Minecraft world (with mcbe-ws-sdk addon installed and cheats
enabled), run:  /wsserver <server-ip>:8080
"""

from __future__ import annotations

import asyncio
import json
import uuid
import argparse
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("minecomp-gateway")

# V2 protocol magic
PROTOCOL_VERSION = "MCBEWS/2"
BANNER = "MINECOMP_GATEWAY"


class Gateway:
    def __init__(self, host: str = "0.0.0.0", port: int = 8080):
        self.host = host
        self.port = port
        self.clients = set()

    async def start(self):
        from websockets.server import serve

        async def handler(websocket):
            await self._handle_client(websocket)

        self.server = await serve(handler, self.host, self.port)
        logger.info(f"Gateway listening on ws://{self.host}:{self.port}")
        await self.server.serve_forever()

    async def _handle_client(self, websocket):
        self.clients.add(websocket)
        client_id = str(uuid.uuid4())
        logger.info(f"Client connected: {client_id}")

        try:
            await self._negotiate(websocket, client_id)
            async for raw in websocket:
                await self._dispatch(raw, websocket, client_id)
        except (asyncio.CancelledError, ConnectionResetError):
            pass
        except Exception as e:
            logger.warning(f"Client {client_id} error: {e}")
        finally:
            self.clients.discard(websocket)
            logger.info(f"Client disconnected: {client_id}")

    async def _negotiate(self, websocket, client_id):
        """Wait for the client's connection request with capabilities."""
        req_id = str(uuid.uuid4())
        try:
            raw = await asyncio.wait_for(websocket.recv(), timeout=5.0)
        except asyncio.TimeoutError:
            await websocket.send(json.dumps({
                "protocol": PROTOCOL_VERSION,
                "messagePurpose": "connectionRejected",
                "messageType": "connectionRejected",
                "requestId": req_id,
                "body": {"reason": "No connection request received"},
            }))
            return

        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            await websocket.send(json.dumps({
                "protocol": PROTOCOL_VERSION,
                "messagePurpose": "connectionRejected",
                "messageType": "connectionRejected",
                "requestId": req_id,
                "body": {"reason": "Invalid JSON"},
            }))
            return

        if data.get("messagePurpose") != "connectionRequest":
            await websocket.send(json.dumps({
                "protocol": PROTOCOL_VERSION,
                "messagePurpose": "connectionRejected",
                "messageType": "connectionRejected",
                "requestId": req_id,
                "body": {"reason": "Not a connection request"},
            }))
            return

        # Accept the connection
        await websocket.send(json.dumps({
            "protocol": PROTOCOL_VERSION,
            "messagePurpose": "connectionAccepted",
            "messageType": "connectionAccepted",
            "requestId": req_id,
            "body": {
                "clientId": client_id,
                "serverMetadata": {"name": "minecomp-ai gateway"},
            },
        }))

    async def _dispatch(self, raw, websocket, client_id):
        try:
            data = json.loads(raw)
        except json.JSONDecodeError:
            return

        mtype = data.get("messageType")
        purpose = data.get("messagePurpose")

        if purpose == "commandRequest":
            await self._handle_command(data, websocket, client_id)
        elif mtype == "chatMessage":
            # Forward to connected clients as a chat message
            await self._broadcast(json.dumps({
                "protocol": PROTOCOL_VERSION,
                "messagePurpose": "chatMessage",
                "messageType": "chatMessage",
                "requestId": str(uuid.uuid4()),
                "body": {
                    "sender": data.get("body", {}).get("sender", "unknown"),
                    "message": data.get("body", {}).get("message", ""),
                },
            }))
        elif mtype == "event":
            # Broadcast game events to all connected clients
            await self._broadcast(json.dumps({
                "protocol": PROTOCOL_VERSION,
                "messagePurpose": "event",
                "messageType": "event",
                "requestId": str(uuid.uuid4()),
                "body": data.get("body", {}),
            }))

    async def _handle_command(self, data, websocket, client_id):
        """Handle a command request from the agent."""
        request_id = data.get("requestId")
        command = data.get("body", {}).get("command", "")

        logger.info(f"Command from {client_id}: {command}")

        # Simulate command execution (in production, this would send the
        # command to the game via the mcbe-ws-sdk addon)
        success = False
        if command.startswith("say "):
            # Broadcast to all connected clients as a chat message
            message = command[4:]
            await self._broadcast(json.dumps({
                "protocol": PROTOCOL_VERSION,
                "messagePurpose": "chatMessage",
                "messageType": "chatMessage",
                "requestId": request_id,
                "body": {"sender": "minecomp-ai", "message": message},
            }))
            success = True
        elif command in ("", "/"):
            success = True
        else:
            logger.warning(f"Unknown command: {command}")

        await websocket.send(json.dumps({
            "protocol": PROTOCOL_VERSION,
            "messagePurpose": "commandResponse",
            "messageType": "commandResponse",
            "requestId": request_id,
            "body": {"success": success},
        }))

    async def _broadcast(self, message: str):
        """Send a message to all connected clients."""
        dead = set()
        for ws in self.clients:
            try:
                await ws.send(message)
            except Exception:
                dead.add(ws)
        for ws in dead:
            self.clients.discard(ws)

    async def stop(self):
        if self.server:
            self.server.close()
            await self.server.wait_closed()


def main():
    parser = argparse.ArgumentParser(description="minecomp-ai WebSocket gateway")
    parser.add_argument("--host", default="0.0.0.0", help="Bind address")
    parser.add_argument("--port", type=int, default=8080, help="Bind port")
    args = parser.parse_args()

    gw = Gateway(host=args.host, port=args.port)
    asyncio.run(gw.start())


if __name__ == "__main__":
    main()
