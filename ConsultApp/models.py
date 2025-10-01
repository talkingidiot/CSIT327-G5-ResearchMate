from django.db import models
from django.contrib.auth.models import AbstractUser  
from django.conf import settings

# Create your models here.
class User(AbstractUser):
    Role_Choices = [
        ('student', 'Student'), 
        ('consultant', 'Consultant'),
        ('admin', 'Admin'),
        ]

    role = models.CharField(max_length=20, choices=Role_Choices)
    is_verified = models.BooleanField(default=False)
    date_joined = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.username} ({self.role})"
    
class ConsultantProfile(models.Model):
    """
    Extended profile for users with the 'consultant' role.
    Stores expertise, department, and availability details.
    """
    consultant = models.OneToOneField(
        settings.AUTH_USER_MODEL, 
        on_delete=models.CASCADE,
        related_name='consultant_profile'
    )

    expertise = models.CharField(max_length=255)  # e.g. "Data Analysis, Statistics"
    department = models.CharField(max_length=100)  # e.g. "Computer Science"
    availability = models.TextField()  # e.g. "MWF 1:00 PM - 5:00 PM"
    bio = models.TextField(blank=True, null=True)
    credentials = models.TextField(blank=True, null=True)  # e.g. resume link, LinkedIn
    profile_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Consultant Profile: {self.consultant.username}"

class Consultation(models.Model):
    """
    A consultation request between a student and a consultant.
    """

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('completed', 'Completed'),
    ]

    consultation_id = models.AutoField(primary_key=True)
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='student_consultations'
    )
    consultant = models.ForeignKey(
        ConsultantProfile,
        on_delete=models.CASCADE,
        related_name='consultations'
    )
    topic = models.CharField(max_length=255)
    notes = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    requested_date = models.DateTimeField(auto_now_add=True)
    scheduled_date = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"Consultation #{self.consultation_id} - {self.student.username} → {self.consultant.consultant.username}"

class Message(models.Model):
    """
    Simple messaging system between student and consultant.
    """

    consultation = models.ForeignKey(
        Consultation,
        on_delete=models.CASCADE,
        related_name='messages'
    )
    sender = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )
    message_text = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Message from {self.sender.username} in Consultation #{self.consultation.consultation_id}"

class Feedback(models.Model):
    """
    Feedback from students after consultation is completed.
    """

    consultation = models.OneToOneField(
        Consultation,
        on_delete=models.CASCADE,
        related_name='feedback'
    )
    student = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feedbacks'
    )
    rating = models.PositiveSmallIntegerField()  # 1-5 stars
    comment = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Feedback by {self.student.username} on Consultation #{self.consultation.consultation_id}"

class Report(models.Model):
    """
    Reports submitted by users (students or consultants) to flag issues.
    """

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('reviewed', 'Reviewed'),
        ('resolved', 'Resolved'),
    ]

    report_id = models.AutoField(primary_key=True)
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_against'
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='reports_made'
    )
    reason = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Report #{self.report_id} - {self.reported_user.username} ({self.status})"