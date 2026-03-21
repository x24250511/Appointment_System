from django.urls import path
from . import views, admin_views

urlpatterns = [
    # User Frontend views
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

    # Admin views
    path('admin-panel/', admin_views.admin_dashboard_view, name='admin_dashboard'),
    path('admin-panel/appointments/',
         admin_views.admin_appointments_view, name='admin_appointments'),
    path('admin-panel/appointments/<uuid:appointment_id>/',
         admin_views.admin_appointment_detail_view, name='admin_appointment_detail'),
    path('admin-panel/appointments/<uuid:appointment_id>/confirm/',
         admin_views.admin_confirm_appointment, name='admin_confirm'),
    path('admin-panel/appointments/<uuid:appointment_id>/complete/',
         admin_views.admin_complete_appointment, name='admin_complete'),
    path('admin-panel/appointments/<uuid:appointment_id>/cancel/',
         admin_views.admin_cancel_appointment, name='admin_cancel'),

    # AJAX endpoints
    path('api/get-slots/', views.get_available_slots_ajax,
         name='get_available_slots_ajax'),

    # API endpoints
    path('api/', views.appointment_list_create,
         name='appointment_list_create_api'),
    path('api/<uuid:pk>/', views.appointment_detail,
         name='appointment_detail_api'),
    path('api/dashboard/stats/', views.dashboard_stats, name='dashboard_stats'),
]
