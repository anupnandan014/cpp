"""
S3Client: standalone boto3 wrapper for uploading and retrieving
delivery receipt photos from the buildstock-receipts bucket.
"""

import uuid
import boto3
from botocore.exceptions import ClientError


class S3Client:
    def __init__(self, bucket_name, region_name="us-east-1"):
        self.bucket_name = bucket_name
        self.client = boto3.client("s3", region_name=region_name)

    def upload_file(self, file_obj, original_filename, prefix="receipts"):
        extension = original_filename.rsplit(".", 1)[-1] if "." in original_filename else "jpg"
        key = f"{prefix}/{uuid.uuid4()}.{extension}"
        try:
            self.client.upload_fileobj(file_obj, self.bucket_name, key)
            print(f"Uploaded to s3://{self.bucket_name}/{key}")
            return key
        except ClientError as e:
            print(f"S3 upload failed: {e}")
            return None

    def list_files(self, prefix="receipts/"):
        try:
            response = self.client.list_objects_v2(Bucket=self.bucket_name, Prefix=prefix)
            return [obj["Key"] for obj in response.get("Contents", [])]
        except ClientError as e:
            print(f"S3 list failed: {e}")
            return []

    def get_presigned_url(self, key, expires_in=3600):
        try:
            return self.client.generate_presigned_url(
                "get_object",
                Params={"Bucket": self.bucket_name, "Key": key},
                ExpiresIn=expires_in,
            )
        except ClientError as e:
            print(f"Presigned URL generation failed: {e}")
            return None

    def delete_file(self, key):
        try:
            self.client.delete_object(Bucket=self.bucket_name, Key=key)
            print(f"Deleted s3://{self.bucket_name}/{key}")
            return True
        except ClientError as e:
            print(f"S3 delete failed: {e}")
            return False
