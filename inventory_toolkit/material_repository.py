"""
MaterialRepository: wraps boto3 DynamoDB calls for the Materials and
Deliveries tables. Keeps all AWS SDK detail out of Django views, and
uses StockManager internally to apply business rules before persisting.
"""

import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from .stock_manager import StockManager


class MaterialRepository:
    def __init__(self, materials_table_name, deliveries_table_name, region_name="us-east-1"):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.materials_table = self.dynamodb.Table(materials_table_name)
        self.deliveries_table = self.dynamodb.Table(deliveries_table_name)

    def create_material(self, site_id, material_id, name, unit, threshold):
        """Create a new material record with zero starting stock."""
        item = {
            "site_id": str(site_id),
            "material_id": str(material_id),
            "name": name,
            "unit": unit,
            "current_stock": 0,
            "threshold": threshold,
            "last_updated": datetime.utcnow().isoformat(),
        }
        try:
            self.materials_table.put_item(Item=item)
            return item
        except ClientError as e:
            print(f"DynamoDB put_item failed: {e}")
            return None

    def get_material(self, site_id, material_id):
        """Fetch a single material record."""
        try:
            response = self.materials_table.get_item(
                Key={"site_id": str(site_id), "material_id": str(material_id)}
            )
            return response.get("Item")
        except ClientError as e:
            print(f"DynamoDB get_item failed: {e}")
            return None

    def list_materials_for_site(self, site_id):
        """List all materials tracked for a given site."""
        try:
            response = self.materials_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("site_id").eq(str(site_id))
            )
            return response.get("Items", [])
        except ClientError as e:
            print(f"DynamoDB query failed: {e}")
            return []

    def record_delivery(self, site_id, material_id, quantity, receipt_s3_key=None):
        """
        Record a delivery: increases stock via StockManager, persists the
        updated material record, and logs the delivery itself.
        Returns (updated_material_item, is_below_threshold).
        """
        item = self.get_material(site_id, material_id)
        if item is None:
            return None, False

        stock = StockManager.from_dynamo_item(item)
        stock.add_stock(quantity)

        self.materials_table.update_item(
            Key={"site_id": str(site_id), "material_id": str(material_id)},
            UpdateExpression="SET current_stock = :s, last_updated = :t",
            ExpressionAttributeValues={
                ":s": stock.current_stock,
                ":t": stock.last_updated,
            },
        )

        delivery_id = str(uuid.uuid4())
        self.deliveries_table.put_item(Item={
            "site_id": str(site_id),
            "delivery_id": delivery_id,
            "material_id": str(material_id),
            "quantity": quantity,
            "date": datetime.utcnow().isoformat(),
            "receipt_s3_key": receipt_s3_key or "",
        })

        return stock.to_dict(), stock.is_below_threshold()

    def record_usage(self, site_id, material_id, quantity):
        """
        Record usage: decreases stock via StockManager, persists the
        updated material record. Returns (updated_material_item, is_below_threshold).
        """
        item = self.get_material(site_id, material_id)
        if item is None:
            return None, False

        stock = StockManager.from_dynamo_item(item)
        stock.deduct_stock(quantity)

        self.materials_table.update_item(
            Key={"site_id": str(site_id), "material_id": str(material_id)},
            UpdateExpression="SET current_stock = :s, last_updated = :t",
            ExpressionAttributeValues={
                ":s": stock.current_stock,
                ":t": stock.last_updated,
            },
        )

        return stock.to_dict(), stock.is_below_threshold()
