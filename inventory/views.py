import io
import json
from django.conf import settings
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib import messages
from django.http import Http404
from inventory_toolkit.material_repository import MaterialRepository
from inventory_toolkit.notification_dispatcher import NotificationDispatcher
from inventory_toolkit.photo_storage import PhotoStorage


def get_repository():
    return MaterialRepository(
        materials_table_name=settings.DYNAMODB_MATERIALS_TABLE,
        deliveries_table_name=settings.DYNAMODB_DELIVERIES_TABLE,
        sites_table_name=settings.DYNAMODB_SITES_TABLE,
        usage_logs_table_name=settings.DYNAMODB_USAGE_LOGS_TABLE,
        region_name=settings.AWS_REGION,
    )


def landing(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
    return render(request, 'inventory/landing.html')


@login_required
def dashboard(request):
    repo = get_repository()
    sites = {s['site_id']: s for s in repo.list_sites()}
    all_materials = repo.list_all_materials()

    rows = []
    low_stock_count = 0
    for m in all_materials:
        current_stock = int(m.get('current_stock', 0))
        threshold = int(m.get('threshold', 0))
        is_low = current_stock < threshold
        if is_low:
            low_stock_count += 1

        site = sites.get(m['site_id'], {'name': 'Unknown site'})

        rows.append({
            'material': m,
            'site_name': site.get('name', 'Unknown site'),
            'current_stock': current_stock,
            'threshold': threshold,
            'is_low': is_low,
        })

    rows.sort(key=lambda r: r['is_low'], reverse=True)

    stats = {
        'total_sites': len(sites),
        'total_materials': len(rows),
        'low_stock_count': low_stock_count,
        'total_deliveries': len(repo.list_recent_deliveries(limit=1000)),
    }

    top_rows = sorted(rows, key=lambda r: r['current_stock'], reverse=True)[:5]
    chart_labels = [r['material']['name'] for r in top_rows]
    chart_values = [r['current_stock'] for r in top_rows]
    ok_count = len(rows) - low_stock_count

    return render(request, 'inventory/dashboard.html', {
        'rows': rows,
        'stats': stats,
        'is_admin': request.user.is_staff,
        'chart_labels_json': json.dumps(chart_labels),
        'chart_values_json': json.dumps(chart_values),
        'low_stock_count': low_stock_count,
        'ok_stock_count': ok_count,
    })


@login_required
def activity(request):
    repo = get_repository()
    sites = {s['site_id']: s for s in repo.list_sites()}
    materials_by_key = {}
    for m in repo.list_all_materials():
        materials_by_key[(m['site_id'], m['material_id'])] = m

    events = []
    for d in repo.list_recent_deliveries(limit=20):
        material = materials_by_key.get((d['site_id'], d['material_id']), {})
        site = sites.get(d['site_id'], {})
        events.append({
            'type': 'delivery',
            'material_name': material.get('name', 'Unknown material'),
            'unit': material.get('unit', ''),
            'site_name': site.get('name', 'Unknown site'),
            'quantity': d['quantity'],
            'date': d['date'],
        })
    for u in repo.list_recent_usage(limit=20):
        material = materials_by_key.get((u['site_id'], u['material_id']), {})
        site = sites.get(u['site_id'], {})
        events.append({
            'type': 'usage',
            'material_name': material.get('name', 'Unknown material'),
            'unit': material.get('unit', ''),
            'site_name': site.get('name', 'Unknown site'),
            'quantity': u['quantity'],
            'date': u['date'],
        })

    events.sort(key=lambda e: e['date'], reverse=True)
    events = events[:30]

    return render(request, 'inventory/activity.html', {
        'events': events,
        'is_admin': request.user.is_staff,
    })


@login_required
def home(request):
    repo = get_repository()
    sites = repo.list_sites()
    for site in sites:
        materials = repo.list_materials_for_site(site['site_id'])
        for m in materials:
            m['current_stock'] = int(m.get('current_stock', 0))
            m['threshold'] = int(m.get('threshold', 0))
            m['is_low'] = m['current_stock'] < m['threshold']
        site['materials'] = materials
        site['material_count'] = len(materials)
    return render(request, 'inventory/home.html', {'sites': sites, 'is_admin': request.user.is_staff})


@staff_member_required
def add_site(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        location = request.POST.get('location')
        repo = get_repository()
        repo.create_site(name=name, location=location)
        messages.success(request, f'Site "{name}" created.')
    return redirect('home')


@login_required
def site_detail(request, site_id):
    repo = get_repository()
    site = repo.get_site(site_id)
    if site is None:
        raise Http404("Site not found")

    materials = repo.list_materials_for_site(site_id)
    material_stock = {}
    for m in materials:
        material_stock[m['material_id']] = {
            'current_stock': int(m.get('current_stock', 0)),
            'threshold': int(m.get('threshold', 0)),
        }

    return render(request, 'inventory/site_detail.html', {
        'site': site,
        'materials': materials,
        'material_stock': material_stock,
        'is_admin': request.user.is_staff,
    })


@staff_member_required
def add_material(request, site_id):
    repo = get_repository()
    site = repo.get_site(site_id)
    if site is None:
        raise Http404("Site not found")

    if request.method == 'POST':
        name = request.POST.get('name')
        unit = request.POST.get('unit')
        threshold = int(request.POST.get('threshold', 10))

        import uuid
        material_id = str(uuid.uuid4())
        repo.create_material(
            site_id=site_id,
            material_id=material_id,
            name=name,
            unit=unit,
            threshold=threshold,
        )
        messages.success(request, f'Material "{name}" added to {site["name"]}.')

    return redirect('site_detail', site_id=site_id)


@login_required
def log_delivery(request, site_id, material_id):
    repo = get_repository()
    material = repo.get_material(site_id, material_id)
    if material is None:
        raise Http404("Material not found")

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))
        photo = request.FILES.get('receipt_photo')

        receipt_s3_key = None
        if photo:
            photo_bytes = photo.read()
            storage = PhotoStorage(bucket_name=settings.S3_BUCKET_NAME, region_name=settings.AWS_REGION)
            receipt_s3_key = storage.upload_receipt_photo(io.BytesIO(photo_bytes), photo.name)

        updated_item, below_threshold = repo.record_delivery(
            site_id=site_id,
            material_id=material_id,
            quantity=quantity,
            receipt_s3_key=receipt_s3_key,
        )

        if below_threshold:
            dispatcher = NotificationDispatcher(
                topic_arn=settings.SNS_LOW_STOCK_TOPIC_ARN,
                region_name=settings.AWS_REGION,
            )
            dispatcher.send_low_stock_alert(
                site_id=site_id,
                material_name=material['name'],
                current_stock=updated_item['current_stock'],
                threshold=updated_item['threshold'],
            )

        new_stock = updated_item['current_stock'] if updated_item else material.get('current_stock', 0)
        messages.success(
            request,
            f"{quantity} {material['unit']} of {material['name']} added. New stock: {new_stock}."
        )
        if below_threshold:
            messages.warning(
                request,
                f"{material['name']} is still below its reorder threshold. A low-stock alert has been sent."
            )

    return redirect('site_detail', site_id=site_id)


@login_required
def log_usage(request, site_id, material_id):
    repo = get_repository()
    material = repo.get_material(site_id, material_id)
    if material is None:
        raise Http404("Material not found")

    if request.method == 'POST':
        quantity = int(request.POST.get('quantity'))

        updated_item, below_threshold = repo.record_usage(
            site_id=site_id,
            material_id=material_id,
            quantity=quantity,
        )

        if below_threshold:
            dispatcher = NotificationDispatcher(
                topic_arn=settings.SNS_LOW_STOCK_TOPIC_ARN,
                region_name=settings.AWS_REGION,
            )
            dispatcher.send_low_stock_alert(
                site_id=site_id,
                material_name=material['name'],
                current_stock=updated_item['current_stock'],
                threshold=updated_item['threshold'],
            )

        new_stock = updated_item['current_stock'] if updated_item else material.get('current_stock', 0)
        messages.success(
            request,
            f"{quantity} {material['unit']} of {material['name']} used. Remaining stock: {new_stock}."
        )
        if below_threshold:
            messages.warning(
                request,
                f"Low stock! {material['name']} needs reordering. An alert has been sent."
            )

    return redirect('site_detail', site_id=site_id)
