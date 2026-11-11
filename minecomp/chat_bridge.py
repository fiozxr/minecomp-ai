"""Chat bridge: relays messages between LAN players and the AI agent.

Every message a player types in the Minecraft world is forwarded to the
AI agent, which decides whether to answer in chat or execute a game
command. The agent's responses are sent back to players via /say.
"""

import asyncio

from . import core


class ChatBridge:
    def __init__(self, agent, llm):
        self.agent = agent
        self.llm = llm
        self._running = False
        self._task = None

    async def queue_message(self, sender: str, message: str):
        """Called when a player sends a chat message in-game."""
        if self._running:
            self.agent.task_queue.put_nowait({"sender": sender, "message": message})

    async def run(self):
        """Listen for queued tasks and process them with the LLM."""
        self._running = True
        self._task = asyncio.create_task(self._loop())

    async def stop(self):
        self._running = False
        if self._task:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass

    async def _loop(self):
        while self._running:
            try:
                item = await asyncio.wait_for(
                    self.agent.task_queue.get(), timeout=1.0
                )
            except asyncio.TimeoutError:
                continue

            sender = item["sender"]
            message = item["message"]

            # Build the conversation context for the LLM
            response = await self._think(sender, message)

            # If the LLM returned a chat response, send it to the game
            if response and not response.startswith("/"):
                await self.agent.send_say(f"[{sender}] {message}")
                await self.agent.send_say(f"Minecomp-AI: {response}")
            # If it's a command, execute it (skipping the leading /)
            elif response and response.startswith("/"):
                await self.agent.bridge.send_command(response[1:])

    async def _think(self, sender: str, message: str) -> str:
        """Ask the LLM what to do with this player message."""
        context = self.agent._build_context(sender, message)
        return await self.llm.complete(
            context, temperature=0.5, max_tokens=300
        )


__all__ = ["ChatBridge"]
