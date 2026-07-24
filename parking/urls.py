from django.urls import path
from . import views

urlpatterns = [
    path('', views.index_view, name='index'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('worker/entry/', views.worker_entry_view, name='worker_entry'),
    path('worker/exit/', views.worker_exit_view, name='worker_exit'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    
    # REST API endpoints
    path('api/worker/checkin/', views.api_worker_checkin, name='api_worker_checkin'),
    path('api/worker/checkout/', views.api_worker_checkout, name='api_worker_checkout'),
    path('api/slots/', views.api_slots, name='api_slots'),
    path('api/slots/<slug:slug>/', views.api_slots, name='api_slots_slug'),
]
