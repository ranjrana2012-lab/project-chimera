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
        """Stitch multiple videos together with optional transitions"""

        # Download videos locally
        local_paths = await self._download_videos(video_urls)

        if len(local_paths) == 1:
            # Single video, just copy it
            import shutil
            shutil.copy(local_paths[0], output_path)
            await self._cleanup_files(local_paths)
            return output_path

        if transitions and len(local_paths) > 1:
            # Use xfade filter for crossfade transitions
            await self._stitch_with_xfade(local_paths, output_path, transition_duration)
        else:
            # Simple concatenation without transitions
            await self._stitch_simple_concat(local_paths, output_path)

        # Cleanup
        await self._cleanup_files(local_paths)

        return output_path

    async def _stitch_simple_concat(self, local_paths: List[str], output_path: str) -> None:
        """Stitch videos using simple concatenation"""
        concat_file = await self._create_concat_file(local_paths)

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

        await self._run_ffmpeg(cmd)
        await self._cleanup_files([concat_file])

    async def _stitch_with_xfade(
        self,
        local_paths: List[str],
        output_path: str,
        transition_duration: float
    ) -> None:
        """Stitch videos with crossfade transitions using xfade filter"""
        # For simplicity, use the first video's properties
        # Build xfade filter chain
        filter_complex = []
        inputs = []

        # Add all video inputs
        for i, path in enumerate(local_paths):
            inputs.extend(["-i", path])

        # Build xfade filter chain for crossfading
        # For N videos, we need N-1 transitions
        filter_parts = []
        for i in range(len(local_paths) - 1):
            if i == 0:
                # First transition
                filter_parts.append(
                    f"[0:v][1:v]xfade=transition=fade:duration={transition_duration}:offset=0[v1]"
                )
            else:
                # Subsequent transitions
                filter_parts.append(
                    f"[v{i}][{i+1}:v]xfade=transition=fade:duration={transition_duration}:offset=0[v{i+1}]"
                )

        filter_complex = ";".join(filter_parts)

        cmd = [
            self.ffmpeg_path,
        ] + inputs + [
            "-filter_complex", filter_complex,
            "-map", f"[v{len(local_paths)-1}]",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-pix_fmt", "yuv420p",
            "-c:a", "aac",
            "-b:a", "192k",
            "-movflags", "+faststart",
            output_path
        ]

        await self._run_ffmpeg(cmd)

    async def add_overlays(
        self,
        video_path: str,
        output_path: str,
        overlays: Dict[str, Any]
    ) -> str:
        """Add overlays to video (logos, captions, etc.)"""

        filter_complex = []
        input_streams = "[0:v]"

        # Logo overlay
        if overlays.get("logo"):
            filter_complex.append(
                f"[1:v]scale=100:-1[logo];{input_streams}[logo]overlay=10:10[video]"
            )
            input_streams = "[video]"
        elif overlays.get("captions"):
            # No logo, start with video stream for captions
            filter_complex.append(f"{input_streams}[video]")
            input_streams = "[video]"

        # Captions
        if overlays.get("captions"):
            caption_text = overlays["captions"]
            filter_complex.append(
                f"{input_streams}drawtext=text='{caption_text}':"
                f"fontsize=24:fontcolor=white:x=(w-tw)/2:y=h-50:text_align=center"
            )

        # Build command
        cmd = [self.ffmpeg_path, "-i", video_path]

        # Add logo input if provided
        if overlays.get("logo"):
            cmd.extend(["-i", overlays["logo"]])

        # Only add filter_complex if we have overlays
        if filter_complex:
            cmd.extend([
                "-filter_complex", ";".join(filter_complex),
                "-c:a", "copy",
                output_path
            ])
        else:
            # No overlays, just copy
            cmd.extend([
                "-c", "copy",
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

                # Save to temp file using aiofiles
                temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp4")
                temp_path = temp_file.name
                temp_file.close()

                async with aiofiles.open(temp_path, "wb") as f:
                    await f.write(response.content)

                paths.append(temp_path)

        return paths

    async def _create_concat_file(self, paths: List[str]) -> str:
        """Create FFmpeg concat file"""

        concat_file = tempfile.NamedTemporaryFile(
            mode="w",
            delete=False,
            suffix=".txt"
        )
        concat_path = concat_file.name
        concat_file.close()

        # Write using aiofiles
        async with aiofiles.open(concat_path, "w") as f:
            for path in paths:
                await f.write(f"file '{path}'\n")

        return concat_path

    async def _cleanup_files(self, paths: List[str]) -> None:
        """Clean up temporary files"""
        for path in paths:
            try:
                os.unlink(path)
            except OSError:
                pass
