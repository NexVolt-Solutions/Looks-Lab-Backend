"""
Storage backends for file management (S3 and local filesystem).
"""
import uuid
from datetime import datetime, timezone
from pathlib import Path
from typing import BinaryIO

import boto3
from botocore.exceptions import ClientError, BotoCoreError

from app.core.config import settings
from app.core.logging import logger


# ── Custom Exceptions ─────────────────────────────────────────────

class StorageError(Exception):
    pass


class StorageUploadError(StorageError):
    pass


class StorageDeleteError(StorageError):
    pass


class StorageNotFoundError(StorageError):
    pass


# ── Base Class ────────────────────────────────────────────────────

class BaseStorage:
    """Abstract base class for storage backends."""

    def upload(
        self,
        file: BinaryIO,
        destination_path: str,
        content_type: str | None = None
    ) -> str:
        raise NotImplementedError

    def delete(self, file_path: str) -> bool:
        raise NotImplementedError

    def get_url(self, file_path: str, expiry: int = 3600) -> str:
        raise NotImplementedError

    def exists(self, file_path: str) -> bool:
        raise NotImplementedError

    @staticmethod
    def generate_path(
        user_id: int,
        domain: str,
        filename: str,
        view: str | None = None
    ) -> str:
        """
         Added: Generate unique file path to prevent overwrites.

        Format: uploads/{user_id}/{domain}/{view}/{uuid}_{filename}

        Example:
            uploads/42/facial/front/a1b2c3d4_photo.jpg
        """
        ext = Path(filename).suffix.lower()
        unique_name = f"{uuid.uuid4().hex[:8]}_{Path(filename).stem}{ext}"

        parts = ["uploads", str(user_id), domain]
        if view:
            parts.append(view)
        parts.append(unique_name)

        return "/".join(parts)


# ── Local Storage ─────────────────────────────────────────────────

class LocalStorage(BaseStorage):

    def __init__(self, base_path: str | None = None):
        self.base_path = Path(base_path or settings.LOCAL_STORAGE_PATH)
        self.base_path.mkdir(parents=True, exist_ok=True)
        logger.info(f"LocalStorage initialized at: {self.base_path}")

    def _get_full_path(self, file_path: str) -> Path:
        return self.base_path / file_path.lstrip("/")

    def upload(
        self,
        file: BinaryIO,
        destination_path: str,
        content_type: str | None = None
    ) -> str:
        try:
            full_path = self._get_full_path(destination_path)
            full_path.parent.mkdir(parents=True, exist_ok=True)

            with open(full_path, "wb") as f:
                if hasattr(file, "read"):
                    f.write(file.read())
                else:
                    f.write(file)

            logger.info(f"File uploaded to local storage: {destination_path}")
            return destination_path

        except Exception as e:
            logger.error(f"Local storage upload failed: {str(e)}")
            raise StorageUploadError(f"Failed to upload file: {str(e)}")

    def delete(self, file_path: str) -> bool:
        try:
            full_path = self._get_full_path(file_path)

            if not full_path.exists():
                raise StorageNotFoundError(f"File not found: {file_path}")

            full_path.unlink()
            logger.info(f"File deleted from local storage: {file_path}")
            return True

        except StorageNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Local storage deletion failed: {str(e)}")
            raise StorageDeleteError(f"Failed to delete file: {str(e)}")

    def get_url(self, file_path: str, expiry: int = 3600) -> str:
        """
        Local URLs don't expire — expiry param ignored.
        Returns full URL if APP_URL set, otherwise relative path.
        """
        if settings.APP_URL:
            return f"{settings.APP_URL}/media/{file_path}"
        return f"/media/{file_path}"

    def exists(self, file_path: str) -> bool:
        return self._get_full_path(file_path).exists()

    def copy(self, source_path: str, destination_path: str) -> str:
        """ Added: copy file to new location."""
        import shutil
        try:
            src = self._get_full_path(source_path)
            dst = self._get_full_path(destination_path)

            if not src.exists():
                raise StorageNotFoundError(f"Source not found: {source_path}")

            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)

            logger.info(f"File copied: {source_path} → {destination_path}")
            return destination_path

        except StorageNotFoundError:
            raise
        except Exception as e:
            raise StorageUploadError(f"Failed to copy file: {str(e)}")


# ── S3 Storage ────────────────────────────────────────────────────

class S3Storage(BaseStorage):

    def __init__(self):
        try:
            self.s3_client = boto3.client(
                "s3",
                region_name=settings.AWS_REGION,
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY
            )
            self.bucket_name = settings.AWS_S3_BUCKET
            self.public_bucket = settings.AWS_S3_PUBLIC_BUCKET
            self.cloudfront_domain = settings.CLOUDFRONT_DOMAIN

            logger.info(f"S3Storage initialized for bucket: {self.bucket_name}")

        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {str(e)}")
            raise StorageError(f"S3 initialization failed: {str(e)}")

    def upload(
        self,
        file: BinaryIO,
        destination_path: str,
        content_type: str | None = None
    ) -> str:
        try:
            extra_args: dict = {
                "ServerSideEncryption": "AES256"    # Always encrypt at rest
            }
            if content_type:
                extra_args["ContentType"] = content_type

            if hasattr(file, "read"):
                self.s3_client.upload_fileobj(
                    file,
                    self.bucket_name,
                    destination_path,
                    ExtraArgs=extra_args
                )
            else:
                self.s3_client.put_object(
                    Bucket=self.bucket_name,
                    Key=destination_path,
                    Body=file,
                    **extra_args
                )

            logger.info(
                f"File uploaded to S3: "
                f"s3://{self.bucket_name}/{destination_path}"
            )
            return destination_path

        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 upload failed: {str(e)}")
            raise StorageUploadError(f"Failed to upload to S3: {str(e)}")
        except Exception as e:
            logger.error(f"Unexpected error during S3 upload: {str(e)}")
            raise StorageUploadError(f"Upload failed: {str(e)}")

    def delete(self, file_path: str) -> bool:
        try:

            if not self.exists(file_path):
                raise StorageNotFoundError(
                    f"File not found in S3: {file_path}"
                )

            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            logger.info(
                f"File deleted from S3: "
                f"s3://{self.bucket_name}/{file_path}"
            )
            return True

        except StorageNotFoundError:
            raise
        except (ClientError, BotoCoreError) as e:
            logger.error(f"S3 deletion failed: {str(e)}")
            raise StorageDeleteError(f"Failed to delete from S3: {str(e)}")

    def get_url(self, file_path: str, expiry: int = 3600) -> str:
        try:
            # Use CloudFront if configured
            if self.cloudfront_domain:
                return f"https://{self.cloudfront_domain}/{file_path}"

            # Generate pre-signed URL
            url = self.s3_client.generate_presigned_url(
                "get_object",
                Params={
                    "Bucket": self.bucket_name,
                    "Key": file_path
                },
                ExpiresIn=expiry
            )
            return url

        except (ClientError, BotoCoreError) as e:
            logger.error(f"Failed to generate presigned URL: {str(e)}")
            raise StorageError(f"Failed to generate URL: {str(e)}")

    def exists(self, file_path: str) -> bool:
        try:
            self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=file_path
            )
            return True
        except ClientError:
            return False

    def copy(self, source_path: str, destination_path: str) -> str:
        """ Added: server-side S3 copy — no download/upload needed."""
        try:
            self.s3_client.copy_object(
                Bucket=self.bucket_name,
                CopySource={
                    "Bucket": self.bucket_name,
                    "Key": source_path
                },
                Key=destination_path,
                ServerSideEncryption="AES256"
            )
            logger.info(f"S3 file copied: {source_path} → {destination_path}")
            return destination_path

        except (ClientError, BotoCoreError) as e:
            raise StorageUploadError(f"Failed to copy in S3: {str(e)}")


# ── Singleton Factory ─────────────────────────────────────────────

_storage_instance: BaseStorage | None = None


def get_storage() -> BaseStorage:
    """
     Fixed: Singleton pattern — creates instance once and reuses.
    Prevents creating new S3 clients on every call.
    """
    global _storage_instance

    if _storage_instance is None:
        if settings.use_s3:
            logger.info("Using S3 storage backend")
            _storage_instance = S3Storage()
        else:
            logger.info("Using local storage backend")
            _storage_instance = LocalStorage()

    return _storage_instance


# ── Module-level accessor ─────────────────────────────────────────
#  Fixed: use property-style access instead of eager instantiation
# Call get_storage() when needed rather than at import time

def get_storage_backend() -> BaseStorage:
    """Alias for get_storage() — use this in services."""
    return get_storage()

