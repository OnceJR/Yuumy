"""Stream recording management.

This module defines a ``StreamRecorder`` class responsible for downloading
streams using yt-dlp and remuxing/transcoding them with ffmpeg.  Each
``StreamRecorder`` instance runs in its own worker and communicates
progress back to the scheduler via callbacks.

The current implementation provides a starting point: it spawns the
yt-dlp process, writes output to a temporary file and then remuxes it to
MP4 when the download completes.  Error handling and retry logic should
be extended as per the specification.
"""

from __future__ import annotations

import asyncio
import datetime as dt
import shutil
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional


@dataclass
class RecordingResult:
    """Represents the result of a recording session."""
    success: bool
    file_path: Optional[Path] = None
    error: Optional[str] = None
    start_time: dt.datetime = field(default_factory=dt.datetime.utcnow)
    end_time: Optional[dt.datetime] = None


class StreamRecorder:
    """Records a single stream using yt-dlp and ffmpeg."""

    def __init__(
        self,
        channel_url: str,
        output_dir: Path,
        segment_duration: int,
        quality: str = "best",
        on_update: Optional[Callable[[str], None]] = None,
    ) -> None:
        self.channel_url = channel_url
        self.output_dir = output_dir
        self.segment_duration = segment_duration
        self.quality = quality
        self.on_update = on_update
        self._cancel_event = asyncio.Event()

    def cancel(self) -> None:
        """Requests cancellation of the recording."""
        self._cancel_event.set()

    async def record(self) -> RecordingResult:
        """Executes the recording asynchronously."""
        start_time = dt.datetime.utcnow()
        temp_dir = Path(tempfile.mkdtemp(prefix="multirec_"))
        temp_file = temp_dir / "download.ts"
        output_file = self.output_dir / f"{start_time:%Y%m%dT%H%M%S}.mp4"

        # Build the yt-dlp command for HLS download
        yt_cmd = [
            "yt-dlp",
            self.channel_url,
            "-N",
            "8",
            "-f",
            f"{self.quality}",
            "--downloader",
            "ffmpeg",
            "--hls-use-mpegts",
            "-o",
            str(temp_file),
        ]

        # Spawn yt-dlp process
        process = await asyncio.create_subprocess_exec(
            *yt_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )

        try:
            # Read lines asynchronously and optionally notify
            while True:
                if self._cancel_event.is_set():
                    process.terminate()
                    await process.wait()
                    return RecordingResult(success=False, error="Cancelled", start_time=start_time)
                line = await process.stdout.readline()
                if not line:
                    break
                if self.on_update:
                    self.on_update(line.decode(errors="ignore").strip())
            rc = await process.wait()
            if rc != 0:
                return RecordingResult(success=False, error=f"yt-dlp exited with {rc}", start_time=start_time)
        except Exception as e:
            process.terminate()
            await process.wait()
            return RecordingResult(success=False, error=str(e), start_time=start_time)

        # Once download is complete, remux using ffmpeg
        ff_cmd = [
            "ffmpeg",
            "-y",
            "-i",
            str(temp_file),
            "-c",
            "copy",
            "-movflags",
            "+faststart",
            str(output_file),
        ]
        remux_proc = await asyncio.create_subprocess_exec(
            *ff_cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        await remux_proc.communicate()
        rc2 = remux_proc.returncode
        if rc2 != 0:
            return RecordingResult(success=False, error=f"ffmpeg exited with {rc2}", start_time=start_time)

        # Clean up temporary file
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass

        return RecordingResult(success=True, file_path=output_file, start_time=start_time, end_time=dt.datetime.utcnow())