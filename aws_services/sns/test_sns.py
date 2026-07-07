"""
Standalone test script for SNSClient.
Run directly: python3 aws_services/sns/test_sns.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from sns_client import SNSClient

TOPIC_ARN = "arn:aws:sns:us-east-1:431225169372:buildstock-low-stock-alerts"
REGION = "us-east-1"

if __name__ == "__main__":
    client = SNSClient(topic_arn=TOPIC_ARN, region_name=REGION)
    client.publish_low_stock_alert(
        site_id="demo-site",
        material_name="Steel rebar",
        current_stock=2,
        threshold=5,
    )
