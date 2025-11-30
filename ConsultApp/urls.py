from django.urls import path
from . import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('home/', views.home_view, name='home'),

    # Auth
    path('register/', views.register_view, name='register'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path("forgot-password/", views.forgot_password_view, name="forgot_password"),
    path("reset-password/<uidb64>/<token>/", views.reset_password_view, name="reset_password"),
    
    # Dashboards
    path('student-dashboard/', views.student_dashboard, name='student_dashboard'),
    path('consultant-dashboard/', views.consultant_dashboard, name='consultant_dashboard'),
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),

    # Consultant
    path('consultant-verification/', views.consultant_verification_view, name='consultant_verification'),
    path('consultant-appointments/', views.consultant_appointments_view, name='consultant_appointments'),
    path('consultant-profile/', views.consultant_profile_view, name='consultant_profile'),
    path('consultant-students/', views.consultant_students_view, name='consultant_students'),
    path('consultant-market/', views.consultant_market, name='consultant_market'),
    path('consultant-market/', views.consultant_market, name='edit_market_listing'),
    path('consultant-history/', views.consultant_history_view, name='consultant_history'),
    path('appointment/update/<int:appointment_id>/', views.update_appointment_status, name='update_appointment_status'),
    path('market/toggle/<int:market_id>/', views.toggle_market_status, name='toggle_market_status'),

    # Student
    path('student-appointments/', views.student_appointments_view, name='student_appointments'),
    path('student-history/', views.student_history_view, name='student_history'),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('student-profile/', views.student_profile_view, name='student_profile'),
    path('book-appointment/', views.book_appointment, name='book_appointment'),
    path('book-appointment/<int:consultant_id>/', views.book_appointment, name='book_appointment_with_consultant'),
    path("appointments/cancel/<int:appointment_id>/", views.cancel_appointment, name="cancel_appointment"),
    path('submit-feedback/', views.submit_feedback, name='submit_feedback'),
    path('consultant-details/<int:consultant_user_id>/', views.consultant_details, name='consultant_details'),

    # Admin
    path('admin-consultants/', views.admin_consultants_view, name='admin_consultants'),
    path('admin-students/', views.admin_students_view, name='admin_students'),
    path('admin-profile/', views.admin_profile_view, name='admin_profile'),
    path('admin-reports/', views.admin_reports_view, name='admin_reports'),
    path('admin-student-details/<int:student_id>/', views.student_profile_admin_view, name='student_profile_view'),
    path('admin-sync-sessions/', views.sync_sessions_completed, name='sync_sessions_completed'),
    path('admin-consultant-details/<int:consultant_id>/', views.consultant_profile_admin_view, name='consultant_profile_view'),

    # Verification (Admin Actions)
    path("approve-consultant/<int:verification_id>/", views.approve_consultant, name="approve_consultant"),
    path("reject-consultant/<int:verification_id>/", views.reject_consultant, name="reject_consultant"),
    path("verification-details/<int:verification_id>/", views.verification_details, name="verification_details"),
]

# Allow access to uploaded media files (images, docs, etc.)
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)