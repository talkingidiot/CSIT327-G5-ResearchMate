from django.urls import path
from . import views

urlpatterns = [
    # Auth pages
    path('login-register/', views.login_register_view, name='login_register'),   # root shows login/register
    path('login/', views.login_user, name='login_user'),
    path('register/', views.register_user, name='register_user'),

    # Dashboards
    path('dashboard/', views.dashboard_view, name='dashboard'),
    path('admin-dashboard/', views.admin_dashboard_view, name='admin-dashboard'),
    path('consultant-dashboard/', views.consultant_dashboard_view, name='consultant-dashboard'),
    path('student-dashboard/', views.student_dashboard_view, name='student-dashboard'),

    # Consultant specific
    path('consultant-verification/', views.consultant_verification_view, name='consultant_verification'),
    path('consultant-appointments/', views.consultant_appointments_view, name='consultant_appointments'),
    path('consultant-profile/', views.consultant_profile_view, name='consultant_profile'),
    path('consultant-students/', views.consultant_students_view, name='consultant_students'),
       
    # Student specific
    path('bookings/', views.bookings_view, name='bookings'),
    path('student-history/', views.student_history_view, name='student-history'),
    path('student-profile/', views.student_profile_view, name='student-profile'),
        
    # Admin specific
    path('admin-manage-consultants/', views.admin_manage_consultants_view, name='admin-manage-consultatns'),
    path('admin-manage-students/', views.admin_manage_students_view, name='admin-manage-students'),
    path('admin-profile/', views.admin_profile_view, name='admin-profile'),
    path('admin-reports/', views.admin_reports_view, name='admin-reports'),
    

]   
