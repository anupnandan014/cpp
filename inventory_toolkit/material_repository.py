"""
InventoryRepository: single point of access to all BuildStock business
data stored in DynamoDB — sites, materials, deliveries, and usage logs.
Uses StockManager internally to apply business rules before persisting.
"""

import uuid
from datetime import datetime

import boto3
from botocore.exceptions import ClientError

from .stock_manager import StockManager


class MaterialRepository:
    def __init__(self, materials_table_name, deliveries_table_name,
                 sites_table_name=None, usage_logs_table_name=None,
                 region_name="us-east-1"):
        self.dynamodb = boto3.resource("dynamodb", region_name=region_name)
        self.materials_table = self.dynamodb.Table(materials_table_name)
        self.deliveries_table = self.dynamodb.Table(deliveries_table_name)
        self.sites_table = self.dynamodb.Table(sites_table_name) if sites_table_name else None
        self.usage_logs_table = self.dynamodb.Table(usage_logs_table_name) if usage_logs_table_name else None

    # ---------------- Sites ----------------

    def create_site(self, name, location=""):
        site_id = str(uuid.uuid4())
        item = {
            "site_id": site_id,
            "name": name,
            "location": location,
            "created_at": datetime.utcnow().isoformat(),
        }
        try:
            self.sites_table.put_item(Item=item)
            return item
        except ClientError as e:
            print(f"DynamoDB create_site failed: {e}")
            return None

    def get_site(self, site_id):
        try:
            response = self.sites_table.get_item(Key={"site_id": str(site_id)})
            return response.get("Item")
        except ClientError as e:
            print(f"DynamoDB get_site failed: {e}")
            return None

    def list_sites(self):
        try:
            response = self.sites_table.scan()
            items = response.get("Items", [])
            items.sort(key=lambda s: s.get("created_at", ""))
            return items
        except ClientError as e:
            print(f"DynamoDB list_sites failed: {e}")
            return []

    # ---------------- Materials ----------------

    def create_material(self, site_id, material_id, name, unit, threshold):
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
        try:
            response = self.materials_table.get_item(
                Key={"site_id": str(site_id), "material_id": str(material_id)}
            )
            return response.get("Item")
        except ClientError as e:
            print(f"DynamoDB get_item failed: {e}")
            return None

    def list_materials_for_site(self, site_id):
        try:
            response = self.materials_table.query(
                KeyConditionExpression=boto3.dynamodb.conditions.Key("site_id").eq(str(site_id))
            )
            return response.get("Items", [])
        except ClientError as e:
            print(f"DynamoDB query failed: {e}")
            return []

    def list_all_materials(self):
        """Scan every material across every site (used by the dashboard)."""
        try:
            response = self.materials_table.scan()
            return response.get("Items", [])
        except ClientError as e:
            print(f"DynamoDB scan failed: {e}")
            return []

    # ---------------- Deliveries ----------------

    def record_delivery(self, site_id, material_id, quantity, receipt_s3_key=None):
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

    def list_recent_deliveries(self, limit=20):
        try:
            response = self.deliveries_table.scan()
            items = response.get("Items", [])
            items.sort(key=lambda d: d.get("date", ""), reverse=True)
            return items[:limit]
        except ClientError as e:
            print(f"DynamoDB list_recent_deliveries failed: {e}")
            return []

    # ---------------- Usage ----------------

    def record_usage(self, site_id, material_id, quantity):
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

        usage_id = str(uuid.uuid4())
        if self.usage_logs_table:
            self.usage_logs_table.put_item(Item={
                "site_id": str(site_id),
                "usage_id": usage_id,
                "material_id": str(material_id),
                "quantity": quantity,
                "date": datetime.utcnow().isoformat(),
            })

        return stock.to_dict(), stock.is_below_threshold()

    def list_recent_usage(self, limit=20):
        try:
            response = self.usage_logs_table.scan()
            items = response.get("Items", [])
            items.sort(key=lambda u: u.get("date", ""), reverse=True)
            return items[:limit]
        except ClientError as e:
            print(f"DynamoDB list_recent_usage failed: {e}")
            return []
