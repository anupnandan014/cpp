"""
Standalone test script for S3Client.
Run directly: python3 aws_services/s3/test_s3.py
"""

import io
import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from s3_client import S3Client

BUCKET_NAME = "buildstock-receipts-anup"
REGION = "us-east-1"

if __name__ == "__main__":
    client = S3Client(bucket_name=BUCKET_NAME, region_name=REGION)

    test_content = b"This is a test receipt file for BuildStock."
    key = client.upload_file(io.BytesIO(test_content), "test_receipt.txt")

    print("\nFiles currently in bucket (receipts/ prefix):")
    for f in client.list_files():
        print(" -", f)

    if key:
        url = client.get_presigned_url(key)
        print(f"\nPresigned URL (valid 1 hour):\n{url}")
