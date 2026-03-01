from unittest.mock import Mock, patch

import pytest

from music_orchestration.storage import MinIOStorage


@pytest.mark.asyncio
async def test_upload_audio():
    minio_mock = Mock()
    result_mock = Mock()
    result_mock.object_name = "test/audio.mp3"
    minio_mock.put_object = Mock(return_value=result_mock)

    with patch.object(MinIOStorage, "_ensure_bucket_exists"):
        storage = MinIOStorage(client=minio_mock)

    result = await storage.upload_audio(
        key="test/audio.mp3",
        audio_data=b"fake audio",
        metadata={"duration": "30"}
    )

    assert result == "test/audio.mp3"
    minio_mock.put_object.assert_called_once()


@pytest.mark.asyncio
async def test_generate_presigned_url():
    minio_mock = Mock()
    minio_mock.presigned_get_object = Mock(return_value="https://minio/audio.mp3")
    minio_mock.bucket_exists = Mock(return_value=True)

    with patch.object(MinIOStorage, "_ensure_bucket_exists"):
        storage = MinIOStorage(client=minio_mock)

    url = await storage.get_presigned_url("test/audio.mp3")

    assert url == "https://minio/audio.mp3"
