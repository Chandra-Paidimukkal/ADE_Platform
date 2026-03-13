"""Task Queue - Simple async background job queue."""

import asyncio
from utils.logger import get_logger

logger = get_logger(__name__)


class SimpleTaskQueue:
    """Lightweight async task queue for background processing."""

    def __init__(self):
        self._running = False
        self._task_count = 0

    async def start(self):
        self._running = True
        logger.info("Task queue started")

    async def stop(self):
        self._running = False
        logger.info("Task queue stopped")

    async def status(self) -> dict:
        return {"running": self._running, "active_tasks": self._task_count}


task_queue = SimpleTaskQueue()
