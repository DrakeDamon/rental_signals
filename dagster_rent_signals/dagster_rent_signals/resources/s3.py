"""S3 resource for uploading ingestion data to AWS S3."""

import os
from pathlib import Path
from typing import Optional
import boto3
from botocore.exceptions import ClientError
from dagster import ConfigurableResource, get_dagster_logger


class S3Resource(ConfigurableResource):
    """Resource for uploading files to S3 with proper partitioning."""
    
    bucket_name: str
    aws_profile: Optional[str] = None
    aws_region: str = "us-east-1"
    
    def get_client(self):
        """Create and return S3 client with proper configuration."""
        session_kwargs = {}
        if self.aws_profile:
            session_kwargs["profile_name"] = self.aws_profile
        
        session = boto3.Session(**session_kwargs)
        return session.client("s3", region_name=self.aws_region)
    
    def upload_file(
        self,
        local_path: Path,
        s3_key: str,
        extra_args: Optional[dict] = None
    ) -> str:
        """
        Upload a file to S3.
        
        Args:
            local_path: Local file path to upload
            s3_key: S3 object key (path within bucket)
            extra_args: Optional extra arguments for S3 upload
            
        Returns:
            S3 URI of uploaded file
        """
        logger = get_dagster_logger()
        
        if not local_path.exists():
            raise FileNotFoundError(f"Local file not found: {local_path}")
        
        client = self.get_client()
        
        try:
            logger.info(f"Uploading {local_path} to s3://{self.bucket_name}/{s3_key}")
            client.upload_file(
                str(local_path),
                self.bucket_name,
                s3_key,
                ExtraArgs=extra_args or {}
            )
            s3_uri = f"s3://{self.bucket_name}/{s3_key}"
            logger.info(f"Upload successful: {s3_uri}")
            return s3_uri
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            raise
    
    def upload_directory(
        self,
        local_dir: Path,
        s3_prefix: str,
        file_pattern: str = "*"
    ) -> list[str]:
        """
        Upload all files matching pattern from a directory to S3.
        
        Args:
            local_dir: Local directory to upload from
            s3_prefix: S3 key prefix (directory path in bucket)
            file_pattern: Glob pattern for files to upload
            
        Returns:
            List of S3 URIs for uploaded files
        """
        logger = get_dagster_logger()
        
        if not local_dir.exists():
            raise FileNotFoundError(f"Local directory not found: {local_dir}")
        
        uploaded_uris = []
        files = list(local_dir.glob(file_pattern))
        
        if not files:
            logger.warning(f"No files found matching pattern '{file_pattern}' in {local_dir}")
            return uploaded_uris
        
        logger.info(f"Found {len(files)} file(s) to upload from {local_dir}")
        
        for file_path in files:
            if file_path.is_file():
                # Preserve relative path structure
                rel_path = file_path.relative_to(local_dir)
                s3_key = f"{s3_prefix}/{rel_path}".replace("\\", "/")
                uri = self.upload_file(file_path, s3_key)
                uploaded_uris.append(uri)
        
        return uploaded_uris
    
    def upload_partitioned_data(
        self,
        source: str,
        layer: str,
        date: str,
        local_path: Path
    ) -> str:
        """
        Upload data with standard partitioned structure.
        
        Standard S3 structure: {source}/{layer}/date={YYYY-MM}/filename
        
        Args:
            source: Data source name (e.g., 'zillow', 'aptlist', 'fred')
            layer: Data layer ('bronze' or 'silver')
            date: Date partition (YYYY-MM format)
            local_path: Local file to upload
            
        Returns:
            S3 URI of uploaded file
        """
        filename = local_path.name
        s3_key = f"{source}/{layer}/date={date}/{filename}"
        return self.upload_file(local_path, s3_key)

