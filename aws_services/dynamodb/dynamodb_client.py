"""
DynamoDBClient: standalone boto3 wrapper for the Materials and
Deliveries tables used by BuildStock.
"""

import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError


class DynamoDBClient:
    def __init__(self, materials_table, deliveries_table, region_name="us-east-1"):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.materials_table = self.dynamodb.Table(materials_table)
        self.deliveries_table = self.dynamodb.Table(deliveries_table)

    def put_material(self, site_id, material_id, name, unit, current_stock, threshold):
        item = {
            "site_id": str(site_id),
            "material_id": str(material_id),
            "name": name,
            "unit": unit,
            "current_stock": current_stock,
            "threshold": threshold,
            "last_updated": datetime.utcnow().isoformat(),
        }
        try:
            self.materials_table.put_item(Item=item)
            print(f"Put material: {item}")
            return item
        except ClientError as e:
            print(f"DynamoDB put_item failed: {e}")
            return None

    def get_material(self, site_id, material_id):
        try:
            response = self.materials_table.get_item(
                Key={"site_id": str(site_id), "material_id": str(material_id)}
            )
            return response.get("Item")
        except ClientError as e:
            print(f"DynamoDB get_item failed: {e}")
            return None

    def update_stock(self, site_id, material_id, new_stock):
        try:
            self.materials_table.update_item(
                Key={"site_id": str(site_id), "material_id": str(material_id)},
                UpdateExpression="SET current_stock = :s, last_updated = :t",
                ExpressionAttributeValues={
                    ":s": new_stock,
                    ":t": datetime.utcnow().isoformat(),
                },
            )
            print(f"Updated stock for {material_id} to {new_stock}")
            return True
        except ClientError as e:
            print(f"DynamoDB update_item failed: {e}")
            return False

    def log_delivery(self, site_id, material_id, quantity, receipt_s3_key=""):
        delivery_id = str(uuid.uuid4())
        try:
            self.deliveries_table.put_item(Item={
                "site_id": str(site_id),
                "delivery_id": delivery_id,
                "material_id": str(material_id),
                "quantity": quantity,
                "date": datetime.utcnow().isoformat(),
                "receipt_s3_key": receipt_s3_key,
            })
            print(f"Logged delivery {delivery_id} for {material_id}")
            return delivery_id
        except ClientError as e:
            print(f"DynamoDB delivery log failed: {e}")
            return None

    def query_materials_for_site(self, site_id):
        try:
            response = self.materials_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("site_id").eq(str(site_id))
            )
            return response.get("Items", [])
        except ClientError as e:
            print(f"DynamoDB query failed: {e}")
            return []
