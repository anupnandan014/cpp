from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.landing, name='landing'),
    path('login/', auth_views.LoginView.as_view(template_name='inventory/login.html', redirect_authenticated_user=True), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('activity/', views.activity, name='activity'),
    path('sites/', views.home, name='home'),
    path('sites/add/', views.add_site, name='add_site'),
    path('sites/<str:site_id>/', views.site_detail, name='site_detail'),
    path('sites/<str:site_id>/materials/add/', views.add_material, name='add_material'),
    path('sites/<str:site_id>/materials/<str:material_id>/delivery/', views.log_delivery, name='log_delivery'),
    path('sites/<str:site_id>/materials/<str:material_id>/usage/', views.log_usage, name='log_usage'),
]
