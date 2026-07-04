import boto3
from botocore.exceptions import ClientError


class NotificationDispatcher:
    def __init__(self, topic_arn, region_name="eu-west-1"):
        self.topic_arn = topic_arn
        self.client = boto3.client("sns", region_name=region_name)

    def send_low_stock_alert(self, site_id, material_name, current_stock, threshold):
        subject = f"Low stock alert: {material_name}"
        message = (
            f"Site {site_id}: {material_name} stock is {current_stock}, "
            f"below the threshold of {threshold}. Please arrange a reorder."
        )
        return self._publish(subject, message)

    def send_delivery_confirmation(self, site_id, material_name, quantity):
        subject = f"Delivery logged: {material_name}"
        message = f"Site {site_id}: {quantity} units of {material_name} received."
        return self._publish(subject, message)

    def _publish(self, subject, message):
        try:
            response = self.client.publish(
                TopicArn=self.topic_arn,
                Subject=subject,
                Message=message,
            )
            return response.get("MessageId")
        except ClientError as e:
            # In production code you'd log this properly (Section 6 discussion point)
            print(f"SNS publish failed: {e}")
            return None