from django.contrib import admin
from .models import Site, Material, Delivery, UsageLog

admin.site.register(Site)
admin.site.register(Material)
admin.site.register(Delivery)
admin.site.register(UsageLog)