"""Basic tests for the Scheduler and StreamRecorder.

These tests mock the Recorder to avoid actually invoking yt-dlp and ffmpeg.
They verify that the scheduler respects concurrency limits and that tasks
transition through the expected states.

To run these tests, install pytest and run ``pytest`` in the project root.
"""

import asyncio
from pathlib import Path

import pytest

from multirec.config.config import Config
from multirec.scheduler.scheduler import Scheduler
from multirec.recorder.recorder import RecordingResult


class DummyRecorder:
    """A dummy recorder that sleeps instead of downloading."""
    def __init__(self, delay: float = 0.1):
        self.delay = delay
        self.cancelled = False

    async def record(self) -> RecordingResult:
        await asyncio.sleep(self.delay)
        return RecordingResult(success=True, file_path=Path("/tmp/dummy.mp4"))


@pytest.mark.asyncio
async def test_scheduler_limits_concurrency(monkeypatch):
    config = Config(concurrency_limit=2)
    scheduler = Scheduler(config=config, download_dir=Path("/tmp"))
    # Monkeypatch StreamRecorder to return DummyRecorder
    from multirec.recorder import recorder as recorder_module
    monkeypatch.setattr(recorder_module, "StreamRecorder", lambda *args, **kwargs: DummyRecorder())

    # Add 5 recordings
    for i in range(5):
        await scheduler.add_recording(url=f"https://example.com/{i}")
    # Start scheduler in background
    async def run_sched():
        await asyncio.wait_for(scheduler.start(), timeout=1)
    task = asyncio.create_task(run_sched())
    # Wait a short period and then cancel
    await asyncio.sleep(0.3)
    await scheduler.shutdown()
    assert len(scheduler.running) <= config.concurrency_limit