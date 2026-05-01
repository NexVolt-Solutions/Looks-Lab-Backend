import uuid
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
        _storage_instance = S3Storage()
        logger.info("Storage backend: S3")
    return _storage_instance

