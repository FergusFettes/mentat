import asyncio
import logging
import signal
from dataclasses import dataclass
from typing import Any, Literal, Set

from .rpc import RpcServer

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger()


# @dataclass
# class Completion:
#     source: Literal["syntax"] | Literal["command"]
#     data: str


# class MentatCompleter:
#     fake_completions = [
#         Completion(source="syntax", data="these"),
#         Completion(source="syntax", data="are"),
#         Completion(source="syntax", data="fake"),
#         Completion(source="syntax", data="completions"),
#         Completion(source="command", data="/help"),
#         Completion(source="command", data="/add"),
#     ]
#
#     def __init__(self):
#         ...
#
#     async def get_completions(self, text: str):
#         completions = []
#         for completion in self.fake_completions:
#             if completion.data.startswith(text.lower()):
#                 completions.append(completion)
#         return completions


class MentatEngine:
    """Manages all processes."""

    def __init__(self, with_rpc: bool = False):
        self.server = RpcServer() if with_rpc else None

        self.conversations = dict()

        self._should_exit = False
        self._force_exit = False
        self._tasks: Set[asyncio.Task] = set()

    ### rpc-exposed methods (terminal client can call these directly)

    async def on_connect(self):
        """Sets up an RPC connection with a client"""
        ...

    async def disconnect(self):
        """Closes an RPC connection with a client"""
        ...

    async def restart(self):
        """Restart the MentatEngine and RPC server"""
        ...

    async def shutdown(self):
        """Shutdown the MentatEngine and RPC server"""
        ...

    # Conversation

    async def create_conversation_message(self):
        ...

    async def get_conversation_cost(self):
        ...

    # Completions

    async def get_conversation_completions(self):
        ...

    # Commands

    async def get_commands(self):
        ...

    async def run_command(self):
        ...

    ### lifecycle methods

    async def heartbeat(self):
        while True:
            logger.info("heartbeat")
            await asyncio.sleep(3)

    def _handle_exit(self):
        if self._should_exit:
            self._force_exit = True
        else:
            self._should_exit = True

    def _init_signal_handlers(self):
        loop = asyncio.get_event_loop()
        loop.add_signal_handler(signal.SIGINT, self._handle_exit)
        loop.add_signal_handler(signal.SIGTERM, self._handle_exit)

    async def _startup(self):
        logger.info("Starting Engine...")
        heahtheck_task = asyncio.create_task(self.heartbeat())
        self._tasks.add(heahtheck_task)

    async def _main_loop(self):
        logger.info("Running Engine...")

        counter = 0
        while not self._should_exit:
            counter += 1
            counter = counter % 86400
            await asyncio.sleep(0.1)

    async def _shutdown(self):
        logger.info("Shutting Engine down...")

        for task in self._tasks:
            task.cancel()
        logger.info("Waiting for Jobs to finish. (CTRL+C to force quit)")
        while not self._force_exit:
            if all([task.cancelled() for task in self._tasks]):
                break
            await asyncio.sleep(0.1)

        if self._force_exit:
            logger.debug("Force exiting.")

        logger.info("Engine has stopped")

    async def _run(self):
        self._init_signal_handlers()
        await self._startup()
        await self._main_loop()
        await self._shutdown()

    def run(self):
        asyncio.run(self._run())


if __name__ == "__main__":
    mentat_engine = MentatEngine()
    mentat_engine.run()
