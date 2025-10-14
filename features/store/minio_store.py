"""MinIO-based object storage for large files and tiles."""
import io
import os
from datetime import timedelta
from typing import BinaryIO, Optional

import numpy as np
from loguru import logger
from minio import Minio
from minio.error import S3Error


class MinIOStore:
    """MinIO object store for large files, tiles, and model artifacts."""

    def __init__(
        self,
        endpoint: str = "localhost:9000",
        access_key: str = "minioadmin",
        secret_key: str = "minioadmin",
        secure: bool = False,
        bucket_name: str = "ucip-data",
    ):
        """Initialize MinIO store.
        
        Args:
            endpoint: MinIO endpoint
            access_key: Access key
            secret_key: Secret key
            secure: Use HTTPS
            bucket_name: Default bucket name
        """
        self.client = Minio(
            endpoint,
            access_key=access_key,
            secret_key=secret_key,
            secure=secure
        )
        self.bucket_name = bucket_name
        
        try:
            # Create bucket if it doesn't exist
            if not self.client.bucket_exists(bucket_name):
                self.client.make_bucket(bucket_name)
                logger.info(f"Created bucket: {bucket_name}")
            else:
                logger.info(f"Connected to MinIO bucket: {bucket_name}")
        except S3Error as e:
            logger.error(f"MinIO error: {e}")

    def upload_file(
        self,
        object_name: str,
        file_path: str,
        content_type: str = "application/octet-stream",
        bucket: Optional[str] = None,
    ) -> bool:
        """Upload a file to MinIO.
        
        Args:
            object_name: Object name in bucket
            file_path: Local file path
            content_type: MIME type
            bucket: Optional bucket name (uses default if not specified)
            
        Returns:
            True if successful
        """
        bucket = bucket or self.bucket_name
        
        try:
            self.client.fput_object(
                bucket,
                object_name,
                file_path,
                content_type=content_type
            )
            logger.info(f"Uploaded {file_path} to {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading file: {e}")
            return False

    def upload_bytes(
        self,
        object_name: str,
        data: bytes,
        content_type: str = "application/octet-stream",
        bucket: Optional[str] = None,
    ) -> bool:
        """Upload bytes to MinIO.
        
        Args:
            object_name: Object name in bucket
            data: Bytes to upload
            content_type: MIME type
            bucket: Optional bucket name
            
        Returns:
            True if successful
        """
        bucket = bucket or self.bucket_name
        
        try:
            data_stream = io.BytesIO(data)
            self.client.put_object(
                bucket,
                object_name,
                data_stream,
                length=len(data),
                content_type=content_type
            )
            logger.info(f"Uploaded {len(data)} bytes to {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error uploading bytes: {e}")
            return False

    def upload_numpy(
        self,
        object_name: str,
        array: np.ndarray,
        bucket: Optional[str] = None,
    ) -> bool:
        """Upload a numpy array to MinIO.
        
        Args:
            object_name: Object name in bucket (will add .npy extension)
            array: Numpy array
            bucket: Optional bucket name
            
        Returns:
            True if successful
        """
        if not object_name.endswith('.npy'):
            object_name += '.npy'
        
        try:
            # Serialize numpy array
            buffer = io.BytesIO()
            np.save(buffer, array)
            buffer.seek(0)
            
            return self.upload_bytes(
                object_name,
                buffer.getvalue(),
                content_type="application/octet-stream",
                bucket=bucket
            )
        except Exception as e:
            logger.error(f"Error uploading numpy array: {e}")
            return False

    def download_file(
        self,
        object_name: str,
        file_path: str,
        bucket: Optional[str] = None,
    ) -> bool:
        """Download a file from MinIO.
        
        Args:
            object_name: Object name in bucket
            file_path: Local file path to save to
            bucket: Optional bucket name
            
        Returns:
            True if successful
        """
        bucket = bucket or self.bucket_name
        
        try:
            self.client.fget_object(bucket, object_name, file_path)
            logger.info(f"Downloaded {bucket}/{object_name} to {file_path}")
            return True
        except S3Error as e:
            logger.error(f"Error downloading file: {e}")
            return False

    def download_bytes(
        self,
        object_name: str,
        bucket: Optional[str] = None,
    ) -> Optional[bytes]:
        """Download bytes from MinIO.
        
        Args:
            object_name: Object name in bucket
            bucket: Optional bucket name
            
        Returns:
            Bytes data or None if error
        """
        bucket = bucket or self.bucket_name
        
        try:
            response = self.client.get_object(bucket, object_name)
            data = response.read()
            response.close()
            response.release_conn()
            logger.info(f"Downloaded {len(data)} bytes from {bucket}/{object_name}")
            return data
        except S3Error as e:
            logger.error(f"Error downloading bytes: {e}")
            return None

    def download_numpy(
        self,
        object_name: str,
        bucket: Optional[str] = None,
    ) -> Optional[np.ndarray]:
        """Download a numpy array from MinIO.
        
        Args:
            object_name: Object name in bucket
            bucket: Optional bucket name
            
        Returns:
            Numpy array or None if error
        """
        if not object_name.endswith('.npy'):
            object_name += '.npy'
        
        try:
            data = self.download_bytes(object_name, bucket)
            if data:
                buffer = io.BytesIO(data)
                array = np.load(buffer)
                return array
            return None
        except Exception as e:
            logger.error(f"Error downloading numpy array: {e}")
            return None

    def list_objects(
        self,
        prefix: str = "",
        bucket: Optional[str] = None,
    ) -> list:
        """List objects in bucket.
        
        Args:
            prefix: Object name prefix filter
            bucket: Optional bucket name
            
        Returns:
            List of object names
        """
        bucket = bucket or self.bucket_name
        
        try:
            objects = self.client.list_objects(bucket, prefix=prefix, recursive=True)
            object_names = [obj.object_name for obj in objects]
            logger.info(f"Found {len(object_names)} objects with prefix '{prefix}'")
            return object_names
        except S3Error as e:
            logger.error(f"Error listing objects: {e}")
            return []

    def delete_object(
        self,
        object_name: str,
        bucket: Optional[str] = None,
    ) -> bool:
        """Delete an object from MinIO.
        
        Args:
            object_name: Object name in bucket
            bucket: Optional bucket name
            
        Returns:
            True if successful
        """
        bucket = bucket or self.bucket_name
        
        try:
            self.client.remove_object(bucket, object_name)
            logger.info(f"Deleted {bucket}/{object_name}")
            return True
        except S3Error as e:
            logger.error(f"Error deleting object: {e}")
            return False

    def get_presigned_url(
        self,
        object_name: str,
        expires: timedelta = timedelta(hours=1),
        bucket: Optional[str] = None,
    ) -> Optional[str]:
        """Get a presigned URL for an object.
        
        Args:
            object_name: Object name in bucket
            expires: URL expiration time
            bucket: Optional bucket name
            
        Returns:
            Presigned URL or None if error
        """
        bucket = bucket or self.bucket_name
        
        try:
            url = self.client.presigned_get_object(bucket, object_name, expires=expires)
            logger.info(f"Generated presigned URL for {bucket}/{object_name}")
            return url
        except S3Error as e:
            logger.error(f"Error generating presigned URL: {e}")
            return None


def main():
    """Example usage."""
    store = MinIOStore()
    
    # Upload a numpy array
    array = np.random.rand(100, 100)
    store.upload_numpy("test/embeddings", array)
    
    # Download the array
    downloaded = store.download_numpy("test/embeddings")
    if downloaded is not None:
        logger.info(f"Downloaded array shape: {downloaded.shape}")
    
    # List objects
    objects = store.list_objects(prefix="test/")
    logger.info(f"Objects: {objects}")
    
    # Get presigned URL
    url = store.get_presigned_url("test/embeddings.npy")
    if url:
        logger.info(f"Presigned URL: {url[:100]}...")


if __name__ == "__main__":
    main()

