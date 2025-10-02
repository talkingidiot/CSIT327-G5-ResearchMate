from django.urls import path
from . import views

urlpatterns = [
    # Auth pages
    path('login-register/', views.login_register_view, name='login_register'),   # root shows login/register
    path('login/', views.login_user, name='login_user'),
    path('register/', views.register_user, name='register_user'),

    # Dashboards
    # path('admin-dashboard/', views.admin_dashboard_view, name='admin_dashboard'),
    # path('student-dashboard/', views.student_dashboard_view, name='student_dashboard'),
    # path('consultant-dashboard/', views.consultant_dashboard_view, name='consultant_dashboard'),
    path('dashboard/', views.dashboard_view, name='dashboard'),

    # Consultant specific
    path('consultant-verification/', views.consultant_verification_view, name='consultant_verification'),
]
