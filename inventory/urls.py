from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('sites/add/', views.add_site, name='add_site'),
    path('sites/<int:site_id>/', views.site_detail, name='site_detail'),
    path('sites/<int:site_id>/materials/add/', views.add_material, name='add_material'),
    path('materials/<int:material_id>/delivery/', views.log_delivery, name='log_delivery'),
    path('materials/<int:material_id>/usage/', views.log_usage, name='log_usage'),
]