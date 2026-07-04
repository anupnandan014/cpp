"""
StockManager: core class for tracking material stock levels at a
construction site. Encapsulates the business rules for adding stock
(deliveries) and deducting stock (usage), keeping this logic out of
Django views entirely.
"""

from datetime import datetime


class StockManager:
    """
    Represents the stock state of a single material at a single site.
    Wraps the increment/decrement logic and threshold checking so this
    logic can be reused across Django views and Lambda functions.
    """

    def __init__(self, site_id, material_id, current_stock, threshold, unit="units"):
        self.site_id = site_id
        self.material_id = material_id
        self.current_stock = current_stock
        self.threshold = threshold
        self.unit = unit
        self.last_updated = datetime.utcnow().isoformat()

    def add_stock(self, quantity):
        """Record a delivery: increase stock and update timestamp."""
        if quantity <= 0:
            raise ValueError("Delivery quantity must be positive")
        self.current_stock += quantity
        self.last_updated = datetime.utcnow().isoformat()
        return self.current_stock

    def deduct_stock(self, quantity):
        """Record usage/consumption: decrease stock, never below zero."""
        if quantity <= 0:
            raise ValueError("Usage quantity must be positive")
        self.current_stock = max(0, self.current_stock - quantity)
        self.last_updated = datetime.utcnow().isoformat()
        return self.current_stock

    def is_below_threshold(self):
        """Return True if stock has fallen below the reorder threshold."""
        return self.current_stock < self.threshold

    def to_dict(self):
        """Serialize to a plain dict, ready for a DynamoDB put_item call."""
        return {
            "site_id": self.site_id,
            "material_id": self.material_id,
            "current_stock": self.current_stock,
            "threshold": self.threshold,
            "unit": self.unit,
            "last_updated": self.last_updated,
        }

    @classmethod
    def from_dynamo_item(cls, item):
        """Rebuild a StockManager instance from a DynamoDB item dict."""
        return cls(
            site_id=item["site_id"],
            material_id=item["material_id"],
            current_stock=int(item["current_stock"]),
            threshold=int(item["threshold"]),
            unit=item.get("unit", "units"),
        )
