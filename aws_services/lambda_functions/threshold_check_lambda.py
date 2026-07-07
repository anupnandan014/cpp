"""
threshold_check_lambda.py

AWS Lambda function triggered by a DynamoDB Stream on the Materials table.
Whenever a material's stock is updated, this checks if it has dropped
below its threshold, and if so, publishes an alert to the SNS topic.

Deploy this as the handler for a Lambda function named
'buildstock-threshold-check', with a DynamoDB Streams trigger
attached to the Materials table.
"""

import os
import boto3

SNS_TOPIC_ARN = os.environ.get("SNS_TOPIC_ARN", "arn:aws:sns:us-east-1:431225169372:buildstock-low-stock-alerts")
REGION = os.environ.get("AWS_REGION", "us-east-1")

sns_client = boto3.client("sns", region_name=REGION)


def lambda_handler(event, context):
    processed = 0

    for record in event.get("Records", []):
        if record.get("eventName") not in ("INSERT", "MODIFY"):
            continue

        new_image = record.get("dynamodb", {}).get("NewImage")
        if not new_image:
            continue

        try:
            site_id = new_image["site_id"]["S"]
            material_id = new_image["material_id"]["S"]
            name = new_image.get("name", {}).get("S", material_id)
            current_stock = int(new_image["current_stock"]["N"])
            threshold = int(new_image["threshold"]["N"])
        except (KeyError, ValueError) as e:
            print(f"Skipping malformed record: {e}")
            continue

        if current_stock < threshold:
            message = (
                f"Site {site_id}: {name} stock is {current_stock}, "
                f"below the threshold of {threshold}. Please arrange a reorder."
            )
            sns_client.publish(
                TopicArn=SNS_TOPIC_ARN,
                Subject=f"Low stock alert: {name}",
                Message=message,
            )
            print(f"Alert published for {name} at site {site_id}")
            processed += 1

    return {"statusCode": 200, "processedAlerts": processed}
