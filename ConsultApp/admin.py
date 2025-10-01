from django.contrib import admin
from .models import User, ConsultantProfile, Consultation, Message, Feedback, Report

# Register the custom User model properly
@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'email', 'role', 'is_verified', 'date_joined', 'is_active')
    list_filter = ('role', 'is_verified', 'is_active')
    search_fields = ('username', 'email', 'role')

# Register the rest of your models
@admin.register(ConsultantProfile)
class ConsultantProfileAdmin(admin.ModelAdmin):
    list_display = ('consultant', 'expertise', 'department', 'availability', 'profile_verified')
    list_filter = ('profile_verified', 'department')
    search_fields = ('consultant__username', 'expertise', 'department')

@admin.register(Consultation)
class ConsultationAdmin(admin.ModelAdmin):
    list_display = ('consultation_id', 'student', 'consultant', 'topic', 'status', 'requested_date', 'scheduled_date')
    list_filter = ('status', 'requested_date')
    search_fields = ('student__username', 'consultant__consultant__username', 'topic')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'sender', 'timestamp', 'is_read')
    list_filter = ('is_read', 'timestamp')
    search_fields = ('sender__username', 'consultation__consultation_id', 'message_text')

@admin.register(Feedback)
class FeedbackAdmin(admin.ModelAdmin):
    list_display = ('consultation', 'student', 'rating', 'created_at')
    list_filter = ('rating', 'created_at')
    search_fields = ('student__username', 'consultation__consultation_id')

@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ('report_id', 'reported_user', 'reporter', 'status', 'created_at')
    list_filter = ('status', 'created_at')
    search_fields = ('reported_user__username', 'reporter__username', 'reason')
