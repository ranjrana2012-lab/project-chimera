"""Video processing pipeline with FFmpeg on ARM64"""

import asyncio
import subprocess
import os
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Optional
import httpx
import aiofiles


class VideoPipeline:
    """Video processing pipeline using FFmpeg"""

    def __init__(self, ffmpeg_path: str = "ffmpeg"):
        self.ffmpeg_path = ffmpeg_path

    async def stitch_videos(
        self,
        video_urls: List[str],
        output_path: str,
        transitions: bool = True,
        transition_duration: float = 1.0
    ) -> str:
        """Stitch multiple videos together"""

        # Download videos locally
        local_paths = await self._download_videos(video_urls)

        # Create concat file
        concat_file = await self._create_concat_file(local_paths)

        # Build FFmpeg command
        cmd = [
            self.ffmpeg_path,
            "-f", "concat",
            "-safe", "0",
            "-i", concat_file,
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]

        # Execute
        await self._run_ffmpeg(cmd)

        # Cleanup
        await self._cleanup_files(local_paths + [concat_file])

        return output_path

    async def add_overlays(
        self,
        video_path: str,
        output_path: str,
        overlays: Dict[str, Any]
    ) -> str:
        """Add overlays to video (logos, captions, etc.)"""

        filter_complex = []

        # Logo overlay
        if overlays.get("logo"):
            filter_complex.append(
                f"[1:v]scale=100:-1[logo];[0:v][logo]overlay=10:10[video]"
            )

        # Captions
        if overlays.get("captions"):
            caption_text = overlays["captions"]
            filter_complex.append(
                f"[video]drawtext=text='{caption_text}':"
                f"fontsize=24:fontcolor=white:x=(w-tw)/2:y=h-50:text_align=center"
            )

        # Build command
        cmd = [self.ffmpeg_path, "-i", video_path]

        # Add logo input if provided
        if overlays.get("logo"):
            cmd.extend(["-i", overlays["logo"]])

        cmd.extend([
            "-filter_complex", ",".join(filter_complex),
            "-c:a", "copy",
            output_path
        ])

        await self._run_ffmpeg(cmd)
        return output_path

    async def generate_thumbnail(
        self,
        video_path: str,
        timestamp: float = 1.0,
        output_path: Optional[str] = None
    ) -> str:
        """Generate thumbnail from video"""

        if output_path is None:
            output_path = video_path.replace(".mp4", "_thumb.jpg")

        cmd = [
            self.ffmpeg_path,
            "-ss", str(timestamp),
            "-i", video_path,
            "-vframes", "1",
            "-vf", "scale=320:-1",
            "-q:v", "2",
            output_path
        ]

        await self._run_ffmpeg(cmd)
        return output_path

    async def _run_ffmpeg(self, cmd: List[str]) -> None:
        """Execute FFmpeg command asynchronously"""
        proc = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )

        stdout, stderr = await proc.communicate()

        if proc.returncode != 0:
            raise RuntimeError(f"FFmpeg failed: {stderr.decode()}")

    async def _download_videos(self, urls: List[str]) -> List[str]:
        """Download videos from URLs to local temp storage"""

        paths = []
        async with httpx.AsyncClient() as client:
            for url in urls:
                response = await client.get(url)
                response.raise_for_status()

                # Save to temp file
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as f:
                    f.write(response.content)
                    f.flush()
                    paths.append(f.name)

        return paths

    async def _create_concat_file(self, paths: List[str]) -> str:
        """Create FFmpeg concat file"""

        concat_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".txt"
        )

        for path in paths:
            concat_file.write(f"file '{path}'\n")

        concat_file.close()
        return concat_file.name

    async def _cleanup_files(self, paths: List[str]) -> None:
        """Clean up temporary files"""
        for path in paths:
            try:
                os.unlink(path)
            except OSError:
                pass
