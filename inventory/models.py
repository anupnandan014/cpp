from django.db import models


class Site(models.Model):
    """A construction site/project."""
    name = models.CharField(max_length=200)
    location = models.CharField(max_length=200, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Material(models.Model):
    """A material tracked at a specific site, with a reorder threshold."""
    site = models.ForeignKey(Site, on_delete=models.CASCADE, related_name="materials")
    name = models.CharField(max_length=200)
    unit = models.CharField(max_length=50, default="units")
    current_stock = models.IntegerField(default=0)
    threshold = models.IntegerField(default=10)

    def __str__(self):
        return f"{self.name} ({self.site.name})"


class Delivery(models.Model):
    """A logged delivery of a material to a site."""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="deliveries")
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    receipt_photo = models.ImageField(upload_to="receipts/", blank=True, null=True)
    logged_by = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return f"{self.quantity} {self.material.unit} of {self.material.name}"


class UsageLog(models.Model):
    """A logged consumption/usage of a material at a site."""
    material = models.ForeignKey(Material, on_delete=models.CASCADE, related_name="usage_logs")
    quantity = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.quantity} {self.material.unit} used"