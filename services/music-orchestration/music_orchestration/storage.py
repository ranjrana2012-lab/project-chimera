from datetime import timedelta
from typing import Any
from minio import Minio
from minio.helpers import ObjectWriteResult


class MinIOStorage:
    """MinIO/S3 storage for audio files"""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        bucket: str = "chimeramusic",
        client: Minio | None = None
    ):
        self.client = client or Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=False
        )
        self.bucket = bucket
        if client is None:
            self._ensure_bucket_exists()

    def _ensure_bucket_exists(self):
        """Create bucket if it doesn't exist"""
        if not self.client.bucket_exists(self.bucket):
            self.client.make_bucket(self.bucket)
            # Create folder structure
            self._create_folders()

    def _create_folders(self):
        """Create initial folder structure"""
        folders = ["marketing/social", "marketing/promotional",
                   "show/underscore", "show/transitions", "show/approved",
                   "previews"]
        for folder in folders:
            self.client.put_object(
                self.bucket,
                f"{folder}/.keep",
                data=b"",
                length=0
            )

    async def upload_audio(
        self,
        key: str,
        audio_data: bytes,
        metadata: dict[str, str] | None = None
    ) -> str:
        """Upload audio file and return path"""
        from io import BytesIO

        data = BytesIO(audio_data)
        length = len(audio_data)

        result: ObjectWriteResult = self.client.put_object(
            self.bucket,
            key,
            data=data,
            length=length,
            metadata=metadata or {}
        )

        return result.object_name

    async def get_presigned_url(
        self,
        key: str,
        expires: timedelta = timedelta(hours=1)
    ) -> str:
        """Generate presigned URL for download"""
        return self.client.presigned_get_object(
            self.bucket,
            key,
            expires=expires
        )

    async def delete_audio(self, key: str) -> None:
        """Delete audio file"""
        self.client.remove_object(self.bucket, key)

    def get_key_for_use_case(
        self,
        use_case: str,
        music_id: str,
        format: str = "mp3"
    ) -> str:
        """Generate storage key based on use case"""
        if use_case == "marketing":
            return f"marketing/social/{music_id}.{format}"
        return f"show/underscore/{music_id}.{format}"
