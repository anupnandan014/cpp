"""
SNSClient: standalone boto3 wrapper for publishing low-stock alerts
to the buildstock-low-stock-alerts SNS topic.
"""

import boto3
from botocore.exceptions import ClientError


class SNSClient:
    def __init__(self, topic_arn, region_name="us-east-1"):
        self.topic_arn = topic_arn
        self.client = boto3.client("sns", region_name=region_name)

    def publish_low_stock_alert(self, site_id, material_name, current_stock, threshold):
        subject = f"Low stock alert: {material_name}"
        message = (
            f"Site {site_id}: {material_name} stock is {current_stock}, "
            f"below the threshold of {threshold}. Please arrange a reorder."
        )
        return self._publish(subject, message)

    def publish_custom_message(self, subject, message):
        return self._publish(subject, message)

    def _publish(self, subject, message):
        try:
            response = self.client.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message,
            )
            print(f"Published message, MessageId: {response.get('MessageId')}")
            return response.get("MessageId")
        except ClientError as e:
            print(f"SNS publish failed: {e}")
            return None
