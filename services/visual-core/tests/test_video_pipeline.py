"""Tests for video pipeline"""

import pytest
import os
from video_pipeline import VideoPipeline
from unittest.mock import AsyncMock, patch, MagicMock


@pytest.mark.asyncio
async def test_download_videos():
    """Test video downloading"""

    pipeline = VideoPipeline()

    with patch("httpx.AsyncClient.get") as mock_get:
        mock_response = AsyncMock()
        mock_response.raise_for_status = AsyncMock()
        mock_response.content = b"fake video content"

        mock_get.return_value = mock_response

        urls = ["http://example.com/video1.mp4"]
        paths = await pipeline._download_videos(urls)

        assert len(paths) == 1
        assert paths[0].endswith(".mp4")


@pytest.mark.asyncio
async def test_create_concat_file():
    """Test concat file creation"""

    pipeline = VideoPipeline()
    test_paths = ["/tmp/video1.mp4", "/tmp/video2.mp4"]

    concat_file = await pipeline._create_concat_file(test_paths)

    assert concat_file.endswith(".txt")

    # Read and verify content
    with open(concat_file, "r") as f:
        content = f.read()
        assert "file '/tmp/video1.mp4'" in content
        assert "file '/tmp/video2.mp4'" in content

    # Cleanup
    os.unlink(concat_file)


@pytest.mark.asyncio
async def test_cleanup_files():
    """Test temporary file cleanup"""

    pipeline = VideoPipeline()

    # Create temporary files
    import tempfile
    temp_files = []
    for _ in range(2):
        with tempfile.NamedTemporaryFile(delete=False) as f:
            temp_files.append(f.name)

    # Verify files exist
    for path in temp_files:
        assert os.path.exists(path)

    # Cleanup
    await pipeline._cleanup_files(temp_files)

    # Verify files are deleted
    for path in temp_files:
        assert not os.path.exists(path)


@pytest.mark.asyncio
async def test_cleanup_files_handles_missing_files():
    """Test cleanup handles missing files gracefully"""

    pipeline = VideoPipeline()

    # Try to cleanup non-existent files - should not raise
    await pipeline._cleanup_files(["/tmp/nonexistent1.mp4", "/tmp/nonexistent2.mp4"])


@pytest.mark.asyncio
async def test_generate_thumbnail_default_output():
    """Test thumbnail generation with default output path"""

    pipeline = VideoPipeline()

    with patch.object(pipeline, '_run_ffmpeg') as mock_run:
        await pipeline.generate_thumbnail("/tmp/test.mp4")

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "-ss" in call_args
        assert "-i" in call_args
        assert "/tmp/test_thumb.jpg" in call_args


@pytest.mark.asyncio
async def test_generate_thumbnail_custom_output():
    """Test thumbnail generation with custom output path"""

    pipeline = VideoPipeline()

    with patch.object(pipeline, '_run_ffmpeg') as mock_run:
        await pipeline.generate_thumbnail(
            "/tmp/test.mp4",
            output_path="/custom/thumb.jpg"
        )

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]
        assert "/custom/thumb.jpg" in call_args
