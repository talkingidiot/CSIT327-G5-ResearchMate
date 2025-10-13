from django.urls import path
from . import views

urlpatterns = [
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),

    # Dashboards (placeholder for now)
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('consultant-dashboard/', views.consultant_dashboard, name='consultant_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Consultant specific
    path('consultant-verification/', views.consultant_verification_view, name='consultant_verification'),
    path('consultant-appointments/', views.consultant_appointments_view, name='consultant_appointments'),
    path('consultant-profile/', views.consultant_profile_view, name='consultant_profile'),
    path('consultant-students/', views.consultant_students_view, name='consultant_students'),
       
    # Student specific
    path('bookings/', views.bookings_view, name='bookings'),
    path('student-history/', views.student_history_view, name='student_history'),
    path('student-profile/', views.student_profile_view, name='student_profile'),
        
    # Admin specific
    path('admin-consultants/', views.admin_consultants_view, name='admin_consultants'),
    path('admin-students/', views.admin_students_view, name='admin_students'),
    path('admin-profile/', views.admin_profile_view, name='admin_profile'),
    path('admin-reports/', views.admin_reports_view, name='admin_reports'),
]   
