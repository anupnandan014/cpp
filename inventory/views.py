from django.conf import settings
from django.shortcuts import render, redirect, get_object_or_404
from .models import Site, Material, Delivery, UsageLog
from inventory_toolkit.material_repository import MaterialRepository
from inventory_toolkit.notification_dispatcher import NotificationDispatcher


def get_repository():
    return MaterialRepository(
        materials_table_name=settings.DYNAMODB_MATERIALS_TABLE,
        deliveries_table_name=settings.DYNAMODB_DELIVERIES_TABLE,
        region_name=settings.AWS_REGION,
    )


def home(request):
    sites = Site.objects.all()
    return render(request, 'inventory/home.html', {'sites': sites})


def add_site(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        Site.objects.create(name=name, location=location)
        return redirect('home')
    return render(request, 'inventory/add_site.html')


def site_detail(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    materials = site.materials.all()

    repo = get_repository()
    material_stock = {}
    for material in materials:
        item = repo.get_material(site_id=site.id, material_id=material.id)
        if item:
            material_stock[material.id] = {
                'current_stock': int(item['current_stock']),
                'threshold': int(item['threshold']),
            }
        else:
            material_stock[material.id] = {
                'current_stock': 0,
                'threshold': material.threshold,
            }

    return render(request, 'inventory/site_detail.html', {
        'site': site,
        'materials': materials,
        'material_stock': material_stock,
    })


def add_material(request, site_id):
    site = get_object_or_404(Site, id=site_id)
    if request.method == 'POST':
        name = request.POST.get('name')
        unit = request.POST.get('unit')
        threshold = int(request.POST.get('threshold', 10))

        material = Material.objects.create(
            site=site, name=name, unit=unit,
            current_stock=0, threshold=threshold
        )

        # Create the corresponding record in DynamoDB
        repo = get_repository()
        repo.create_material(
            site_id=site.id,
            material_id=material.id,
            name=name,
            unit=unit,
            threshold=threshold,
        )

        return redirect('site_detail', site_id=site.id)
    return render(request, 'inventory/add_material.html', {'site': site})


def log_delivery(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        photo = request.FILES.get('receipt_photo')

        receipt_s3_key = None
        # S3 upload will be added in the next step

        repo = get_repository()
        updated_item, below_threshold = repo.record_delivery(
            site_id=material.site.id,
            material_id=material.id,
            quantity=quantity,
            receipt_s3_key=receipt_s3_key,
        )

        Delivery.objects.create(material=material, quantity=quantity, receipt_photo=photo)

        if below_threshold:
            dispatcher = NotificationDispatcher(
                topic_arn=settings.SNS_LOW_STOCK_TOPIC_ARN,
                region_name=settings.AWS_REGION,
            )
            dispatcher.send_low_stock_alert(
                site_id=material.site.id,
                material_name=material.name,
                current_stock=updated_item['current_stock'],
                threshold=updated_item['threshold'],
            )

        return render(request, 'inventory/delivery_logged.html', {
            'material': material,
            'quantity': quantity,
            'current_stock': updated_item['current_stock'] if updated_item else material.current_stock,
            'below_threshold': below_threshold,
        })
    return render(request, 'inventory/log_delivery.html', {'material': material})


def log_usage(request, material_id):
    material = get_object_or_404(Material, id=material_id)
    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))

        repo = get_repository()
        updated_item, below_threshold = repo.record_usage(
            site_id=material.site.id,
            material_id=material.id,
            quantity=quantity,
        )

        UsageLog.objects.create(material=material, quantity=quantity)

        if below_threshold:
            dispatcher = NotificationDispatcher(
                topic_arn=settings.SNS_LOW_STOCK_TOPIC_ARN,
                region_name=settings.AWS_REGION,
            )
            dispatcher.send_low_stock_alert(
                site_id=material.site.id,
                material_name=material.name,
                current_stock=updated_item['current_stock'],
                threshold=updated_item['threshold'],
            )

        return render(request, 'inventory/usage_logged.html', {
            'material': material,
            'quantity': quantity,
            'current_stock': updated_item['current_stock'] if updated_item else material.current_stock,
            'below_threshold': below_threshold,
        })
    return render(request, 'inventory/log_usage.html', {'material': material})
