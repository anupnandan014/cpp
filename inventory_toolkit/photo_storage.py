"""
PhotoStorage: wraps boto3 S3 upload logic for delivery receipt photos.
Keeps S3 SDK detail out of Django views.
"""

import uuid

import boto3
from botocore.exceptions import ClientError


class PhotoStorage:
    def __init__(self, bucket_name, region_name="us-east-1"):
        self.bucket_name = bucket_name
        self.client = boto3.client("s3", region_name=region_name)

    def upload_receipt_photo(self, file_obj, original_filename):
        """
        Uploads an in-memory file object to S3 under a unique key.
        Returns the S3 object key on success, or None on failure.
        """
        extension = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "jpg"
        key = f"receipts/{uuid.uuid4()}.{extension}"

        try:
            self.client.upload_fileobj(file_obj, self.bucket_name, key)
            return key
        except ClientError as e:
            print(f"S3 upload failed: {e}")
            return None

    def get_photo_url(self, key, expires_in=3600):
        """Generate a temporary signed URL so the photo can be viewed/downloaded."""
        try:
            url = self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
            return url
        except ClientError as e:
            print(f"S3 presigned URL generation failed: {e}")
            return None
