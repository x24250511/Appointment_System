from django.urls import path
from . import views

urlpatterns = [
    # Frontend views
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('', views.appointment_list_view, name='appointment_list'),
    path('create/', views.appointment_create_view, name='appointment_create'),
    path('<uuid:appointment_id>/', views.appointment_detail_view,
         name='appointment_detail_view'),
    path('<uuid:appointment_id>/edit/',
         views.appointment_edit_view, name='appointment_edit'),
    path('<uuid:appointment_id>/delete/',
         views.appointment_delete_view, name='appointment_delete'),
    path('<uuid:appointment_id>/status/', views.appointment_change_status,
         name='appointment_change_status'),

    # API endpoints
    path('api/', views.appointment_list_create,
         name='appointment_list_create_api'),
    path('api/<uuid:pk>/', views.appointment_detail,
         name='appointment_detail_api'),
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]
