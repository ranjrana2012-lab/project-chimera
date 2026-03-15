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


@pytest.mark.asyncio
async def test_add_overlays_captions_only():
    """Test overlays with captions only (no logo)"""

    pipeline = VideoPipeline()

    with patch.object(pipeline, '_run_ffmpeg') as mock_run:
        overlays = {"captions": "Test Caption"}
        await pipeline.add_overlays("/tmp/test.mp4", "/tmp/output.mp4", overlays)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]

        # Verify filter_complex is built correctly
        assert "-filter_complex" in call_args
        filter_complex = call_args[call_args.index("-filter_complex") + 1]
        assert "drawtext" in filter_complex
        assert "Test Caption" in filter_complex
        # Should not have logo input
        assert call_args.count("-i") == 1


@pytest.mark.asyncio
async def test_add_overlays_logo_and_captions():
    """Test overlays with both logo and captions"""

    pipeline = VideoPipeline()

    with patch.object(pipeline, '_run_ffmpeg') as mock_run:
        overlays = {
            "logo": "/tmp/logo.png",
            "captions": "Test Caption"
        }
        await pipeline.add_overlays("/tmp/test.mp4", "/tmp/output.mp4", overlays)

        mock_run.assert_called_once()
        call_args = mock_run.call_args[0][0]

        # Should have two inputs (video + logo)
        assert call_args.count("-i") == 2
        assert "/tmp/logo.png" in call_args

        # Verify filter_complex includes both logo overlay and captions
        assert "-filter_complex" in call_args
        filter_complex = call_args[call_args.index("-filter_complex") + 1]
        assert "overlay" in filter_complex
        assert "drawtext" in filter_complex


@pytest.mark.asyncio
async def test_stitch_videos_no_transitions():
    """Test video stitching without transitions"""

    pipeline = VideoPipeline()

    with patch.object(pipeline, '_download_videos') as mock_download:
        with patch.object(pipeline, '_cleanup_files') as mock_cleanup:
            with patch.object(pipeline, '_stitch_simple_concat') as mock_stitch:
                mock_download.return_value = ["/tmp/v1.mp4", "/tmp/v2.mp4"]

                await pipeline.stitch_videos(
                    ["http://example.com/v1.mp4", "http://example.com/v2.mp4"],
                    "/tmp/output.mp4",
                    transitions=False
                )

                mock_stitch.assert_called_once_with(
                    ["/tmp/v1.mp4", "/tmp/v2.mp4"],
                    "/tmp/output.mp4"
                )


@pytest.mark.asyncio
async def test_stitch_videos_with_transitions():
    """Test video stitching with transitions"""

    pipeline = VideoPipeline()

    with patch.object(pipeline, '_download_videos') as mock_download:
        with patch.object(pipeline, '_cleanup_files') as mock_cleanup:
            with patch.object(pipeline, '_stitch_with_xfade') as mock_stitch:
                mock_download.return_value = ["/tmp/v1.mp4", "/tmp/v2.mp4"]

                await pipeline.stitch_videos(
                    ["http://example.com/v1.mp4", "http://example.com/v2.mp4"],
                    "/tmp/output.mp4",
                    transitions=True,
                    transition_duration=1.5
                )

                mock_stitch.assert_called_once_with(
                    ["/tmp/v1.mp4", "/tmp/v2.mp4"],
                    "/tmp/output.mp4",
                    1.5
                )
