"""Scheduler for managing multiple recording tasks.

The scheduler maintains a queue of requested recordings and ensures that no
more than ``concurrency_limit`` tasks run simultaneously.  Each task is
represented by a coroutine returned from ``StreamRecorder.record``.  When
a task finishes, the scheduler starts the next pending task from the queue.

This module provides a ``Scheduler`` class with methods to add new
recordings, start all pending tasks and gracefully cancel running tasks.
"""

import asyncio
from dataclasses import dataclass
from typing import Dict, Optional

from ..config.config import Config
from ..recorder import recorder as recorder_module


@dataclass
class RecordingTask:
    url: str
    quality: str = "best"
    recorder: Optional[recorder_module.StreamRecorder] = None
    future: Optional[asyncio.Task] = None
    result: Optional[recorder_module.RecordingResult] = None


class Scheduler:
    def __init__(self, config: Config, download_dir):
        self.config = config
        self.download_dir = download_dir
        self.queue: asyncio.Queue[RecordingTask] = asyncio.Queue()
        self.running: Dict[asyncio.Task, RecordingTask] = {}
        self._cancelled = False
        self._loop = asyncio.get_event_loop()

    async def add_recording(self, url: str, quality: str = "best") -> None:
        task = RecordingTask(url=url, quality=quality)
        await self.queue.put(task)

    async def _run_recorder(self, task: RecordingTask) -> recorder_module.RecordingResult:
        """Instantiate and run a ``StreamRecorder`` for the given task.

        The recorder class is retrieved from ``recorder_module`` at runtime so
        it can be monkeypatched in tests without needing to modify this
        scheduler module.  This indirection avoids importing the class at module
        import time which would otherwise freeze the reference.
        """

        recorder = recorder_module.StreamRecorder(
            channel_url=task.url,
            output_dir=self.download_dir,
            segment_duration=self.config.segment_duration_min,
            quality=task.quality,
        )
        task.recorder = recorder
        result = await recorder.record()
        return result

    async def _worker_loop(self) -> None:
        while not self._cancelled:
            # Limit concurrency
            while len(self.running) >= self.config.concurrency_limit:
                done, _ = await asyncio.wait(
                    self.running.keys(), return_when=asyncio.FIRST_COMPLETED
                )
                for d in done:
                    rec_task = self.running.pop(d)
                    rec_task.result = d.result()
            # Get next task
            try:
                next_task = await asyncio.wait_for(self.queue.get(), timeout=0.5)
            except asyncio.TimeoutError:
                # Nothing in queue at the moment
                continue
            coro = self._run_recorder(next_task)
            fut = asyncio.create_task(coro)
            self.running[fut] = next_task
        # Cancel running tasks on shutdown
        for fut, rec_task in self.running.items():
            if rec_task.recorder:
                rec_task.recorder.cancel()
            fut.cancel()
        await asyncio.gather(*self.running.keys(), return_exceptions=True)

    async def start(self) -> None:
        self._cancelled = False
        await self._worker_loop()

    async def shutdown(self) -> None:
        """Request shutdown of all workers and stop scheduling new tasks."""
        self._cancelled = True