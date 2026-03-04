import uuid
from pathlib import Path
from typing import BinaryIO, Optional

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import settings
from app.core.logging import logger


class StorageError(Exception):
    pass

class StorageUploadError(StorageError):
    pass

class StorageDeleteError(StorageError):
    pass

class StorageNotFoundError(StorageError):
    pass


class BaseStorage:

    def upload(self, file: BinaryIO, destination_path: str, content_type: Optional[str] = None) -> str:
        raise NotImplementedError

    def delete(self, file_path: str) -> bool:
        raise NotImplementedError

    def get_url(self, file_path: str, expiry: int = 3600) -> str:
        raise NotImplementedError

    def exists(self, file_path: str) -> bool:
        raise NotImplementedError

    @staticmethod
    def generate_path(user_id: int, domain: str, filename: str, view: Optional[str] = None) -> str:
        ext = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex[:8]}_{Path(filename).stem}{ext}"
        parts = ["uploads", str(user_id), domain]
        if view:
            parts.append(view)
        parts.append(unique_name)
        return "/".join(parts)


class LocalStorage(BaseStorage):

    def __init__(self, base_path: Optional[str] = None):
        self.base_path = Path(base_path or settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)

    def _get_full_path(self, file_path: str) -> Path:
        return self.base_path / file_path.lstrip("/")

    def upload(self, file: BinaryIO, destination_path: str, content_type: Optional[str] = None) -> str:
        try:
            full_path = self._get_full_path(destination_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, "wb") as f:
                f.write(file.read() if hasattr(file, "read") else file)
            return destination_path
        except Exception as e:
            raise StorageUploadError(f"Failed to upload file: {e}")

    def delete(self, file_path: str) -> bool:
        try:
            full_path = self._get_full_path(file_path)
            if not full_path.exists():
                raise StorageNotFoundError(f"File not found: {file_path}")
            full_path.unlink()
            return True
        except StorageNotFoundError:
            raise
        except Exception as e:
            raise StorageDeleteError(f"Failed to delete file: {e}")

    def get_url(self, file_path: str, expiry: int = 3600) -> str:
        if settings.APP_URL:
            return f"{settings.APP_URL}/media/{file_path}"
        return f"/media/{file_path}"

    def exists(self, file_path: str) -> bool:
        return self._get_full_path(file_path).exists()


class S3Storage(BaseStorage):

    def __init__(self):
        try:
            self.s3_client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
            )
            self.bucket_name = settings.AWS_S3_BUCKET
            self.cloudfront_domain = settings.CLOUDFRONT_DOMAIN
        except Exception as e:
            raise StorageError(f"S3 initialization failed: {e}")

    def upload(self, file: BinaryIO, destination_path: str, content_type: Optional[str] = None) -> str:
        try:
            extra_args: dict = {"ServerSideEncryption": "AES256"}
            if content_type:
                extra_args["ContentType"] = content_type

            if hasattr(file, "read"):
                self.s3_client.upload_fileobj(file, self.bucket_name, destination_path, ExtraArgs=extra_args)
            else:
                self.s3_client.put_object(Bucket=self.bucket_name, Key=destination_path, Body=file, **extra_args)

            return destination_path
        except (ClientError, BotoCoreError) as e:
            raise StorageUploadError(f"Failed to upload to S3: {e}")

    def delete(self, file_path: str) -> bool:
        try:
            if not self.exists(file_path):
                raise StorageNotFoundError(f"File not found in S3: {file_path}")
            self.s3_client.delete_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except StorageNotFoundError:
            raise
        except (ClientError, BotoCoreError) as e:
            raise StorageDeleteError(f"Failed to delete from S3: {e}")

    def get_url(self, file_path: str, expiry: int = 3600) -> str:
        try:
            if self.cloudfront_domain:
                return f"https://{self.cloudfront_domain}/{file_path}"
            return self.s3_client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": file_path},
                ExpiresIn=expiry,
            )
        except (ClientError, BotoCoreError) as e:
            raise StorageError(f"Failed to generate URL: {e}")

    def exists(self, file_path: str) -> bool:
        try:
            self.s3_client.head_object(Bucket=self.bucket_name, Key=file_path)
            return True
        except ClientError:
            return False

    def copy(self, source_path: str, destination_path: str) -> str:
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={"Bucket": self.bucket_name, "Key": source_path},
                Key=destination_path,
                ServerSideEncryption="AES256",
            )
            return destination_path
        except (ClientError, BotoCoreError) as e:
            raise StorageUploadError(f"Failed to copy in S3: {e}")


_storage_instance: Optional[BaseStorage] = None


def get_storage() -> BaseStorage:
    global _storage_instance
    if _storage_instance is None:
        _storage_instance = S3Storage() if settings.use_s3 else LocalStorage()
        logger.info(f"Storage backend: {'S3' if settings.use_s3 else 'local'}")
    return _storage_instance

