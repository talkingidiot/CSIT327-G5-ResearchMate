from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db import models

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    username = None  
    email = models.EmailField(unique=True)
    ROLE_CHOICES = [
        ('student', 'Student'),
        ('consultant', 'Consultant'),
        ('admin', 'Admin'),
    ]
    role = models.CharField(max_length=20, choices=ROLE_CHOICES)

    USERNAME_FIELD = 'email'   
    REQUIRED_FIELDS = []      

    objects = UserManager()

    def __str__(self):
        return f"{self.get_full_name()} ({self.role})"
    
# Consultant model
class Consultant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    contact_number = models.CharField(max_length=15)
    expertise = models.CharField(max_length=100)
    workplace = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Consultant: {self.user.get_full_name()}"

# Student model
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_year_level = models.IntegerField(default=0)
    student_department = models.CharField(max_length=100)
    student_course = models.CharField(max_length=100)
    student_program = models.CharField(max_length=100)
    assigned_consultant = models.ForeignKey(
        Consultant, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    sessions_completed = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Student: {self.user.get_full_name()}"

# Admin model
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"Admin: {self.user.get_full_name()}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="consultant_appointments")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="student_appointments")
    topic = models.CharField(max_length=100)
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending') 

    def __str__(self):
        return f"{self.student.get_full_name()} — {self.topic}"


class Verification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20, blank=True)
    expertise = models.CharField(max_length=200)
    workplace = models.CharField(max_length=200, blank=True)
    qualification = models.TextField(blank=True)
    proof_document = models.FileField(upload_to='verification_docs/', blank=True, null=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.consultant.get_full_name()} - {self.status.capitalize()}"

class Market(models.Model):
    consultant = models.ForeignKey(
        Consultant, on_delete=models.CASCADE, related_name="market_listings"
    )
    expertise = models.CharField(max_length=200)
    profession = models.CharField(max_length=100)
    available_from = models.TimeField()
    available_to = models.TimeField(null=True, blank=True)
    rate_per_hour = models.PositiveIntegerField(help_text="Rate in PHP per hour")
    meeting_place = models.CharField(max_length=200, help_text="e.g. Online, CIT Campus, Coffee Shop")
    description = models.TextField(blank=True, help_text="Optional: short service description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.consultant.user.get_full_name()} — {self.profession} ({self.expertise})"
