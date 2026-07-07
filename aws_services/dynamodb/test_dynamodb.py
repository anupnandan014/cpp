"""
Standalone test script for DynamoDBClient.
Run directly: python3 aws_services/dynamodb/test_dynamodb.py
"""

import sys
import os

sys.path.insert(0, os.path.dirname(__file__))
from dynamodb_client import DynamoDBClient

REGION = "us-east-1"

if __name__ == "__main__":
    client = DynamoDBClient("Materials", "Deliveries", region_name=REGION)

    client.put_material(
        site_id="demo-site", material_id="steel-1",
        name="Steel rebar", unit="tonnes", current_stock=10, threshold=3
    )

    item = client.get_material("demo-site", "steel-1")
    print("\nFetched item:", item)

    client.update_stock("demo-site", "steel-1", new_stock=2)
    updated = client.get_material("demo-site", "steel-1")
    print("\nAfter stock update:", updated)

    client.log_delivery("demo-site", "steel-1", quantity=5, receipt_s3_key="receipts/test.jpg")

    print("\nAll materials for demo-site:")
    for m in client.query_materials_for_site("demo-site"):
        print(" -", m)
