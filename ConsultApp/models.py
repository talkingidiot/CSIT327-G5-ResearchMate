from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.conf import settings
from django.db import models
from django.core.validators import RegexValidator, MinValueValidator, MaxValueValidator
from .storage_backends import VerificationStorage

# Validator for names (letters, spaces, hyphens only)
name_validator = RegexValidator(
    regex=r'^[a-zA-Z\s\-]+$',
    message='Only letters, spaces, and hyphens are allowed.'
)

# Validator for contact numbers (digits, spaces, hyphens, parentheses, plus sign)
phone_validator = RegexValidator(
    regex=r'^[\d\s\-\(\)\+]+$',
    message='Only numbers, spaces, hyphens, parentheses, and plus signs are allowed.'
)

list_string_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9\s\-,]+$', 
    message='Only letters, numbers, spaces, hyphens, and commas are allowed.'
)

# Validator for alphanumeric with spaces (no special chars except spaces and hyphens)
alphanumeric_validator = RegexValidator(
    regex=r'^[a-zA-Z0-9\s\-]+$',
    message='Only letters, numbers, spaces, and hyphens are allowed.'
)

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
    email = models.EmailField(unique=True, max_length=255)
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
    contact_number = models.CharField(max_length=20, validators=[phone_validator])
    expertise = models.CharField(max_length=1000, validators=[list_string_validator], blank=True)
    workplace = models.CharField(max_length=150, validators=[alphanumeric_validator])
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Consultant: {self.user.get_full_name()}"

# Student model
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_year_level = models.IntegerField(default=0)
    student_department = models.CharField(max_length=100, validators=[alphanumeric_validator])
    student_course = models.CharField(max_length=100, validators=[alphanumeric_validator])
    student_program = models.CharField(max_length=150, validators=[alphanumeric_validator])
    assigned_consultant = models.ForeignKey(
        Consultant, on_delete=models.SET_NULL, null=True, blank=True, related_name="students"
    )
    sessions_completed = models.PositiveIntegerField(default=0)

    def __str__(self):
        return f"Student: {self.user.get_full_name()}"

# Admin model
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    contact_number = models.CharField(max_length=20, validators=[phone_validator])

    def __str__(self):
        return f"Admin: {self.user.get_full_name()}"

class Appointment(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
        ('pending_student_review', 'Pending Student Review'),
        ('disputed', 'Disputed'),
    ]

    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE, related_name="consultant_appointments")
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name="student_appointments")
    topic = models.CharField(max_length=100, validators=[alphanumeric_validator])
    date = models.DateField()
    time = models.TimeField()
    duration_minutes = models.IntegerField(default=60)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='pending')
    research_title = models.CharField(max_length=200, validators=[alphanumeric_validator], blank=True)
    
    consultant_marked_as = models.CharField(
        max_length=20, 
        choices=[('completed', 'Completed'), ('not_completed', 'Not Completed')],
        null=True,
        blank=True,
        help_text="Consultant's assessment of meeting status"
    )
    student_dispute_remark = models.TextField(
        blank=True,
        null=True,
        help_text="Student's explanation if disputing the meeting status"
    )
    disputed_at = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.student.user.get_full_name()} — {self.topic}"


class Feedback(models.Model):
    appointment = models.OneToOneField(
        Appointment, 
        on_delete=models.CASCADE, 
        related_name='feedback'
    )
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    consultant = models.ForeignKey(Consultant, on_delete=models.CASCADE)
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        help_text="Rating from 1 to 5 stars"
    )
    comment = models.TextField(blank=True, help_text="Optional feedback comment")
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Feedback by {self.student.user.get_full_name()} - {self.rating} stars"
    
    class Meta:
        ordering = ['-created_at']


class Verification(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ]

    consultant = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    contact_number = models.CharField(max_length=20, validators=[phone_validator], blank=True)
    expertise = models.CharField(max_length=200, validators=[alphanumeric_validator])
    workplace = models.CharField(max_length=200, validators=[alphanumeric_validator], blank=True)
    qualification = models.TextField(blank=True)
    bio = models.TextField(blank=True, null=True)
    valid_id = models.FileField(
        upload_to='verification_docs/', storage=VerificationStorage(), blank=True, null=True
    )
    license = models.FileField(
        upload_to='verification_docs/', storage=VerificationStorage(), blank=True, null=True
    )
    profile_photo = models.FileField(
        upload_to='verification_docs/', storage=VerificationStorage(), blank=True, null=True
    )
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return f"{self.consultant.get_full_name()} - {self.status.capitalize()}"

class Market(models.Model):
    DAYS_CHOICES = [
        ('monday', 'Monday'),
        ('tuesday', 'Tuesday'),
        ('wednesday', 'Wednesday'),
        ('thursday', 'Thursday'),
        ('friday', 'Friday'),
        ('saturday', 'Saturday'),
        ('sunday', 'Sunday'),
    ]
    
    consultant = models.ForeignKey(
        Consultant, on_delete=models.CASCADE, related_name="market_listings"
    )
    expertise = models.CharField(max_length=200, validators=[alphanumeric_validator])
    profession = models.CharField(max_length=100, validators=[alphanumeric_validator])
    available_from = models.TimeField()
    available_to = models.TimeField(null=True, blank=True)
    available_days = models.CharField(
        max_length=200, 
        help_text="Comma-separated days (e.g., 'monday,wednesday,friday')",
        blank=True
    )
    rate_per_hour = models.PositiveIntegerField(help_text="Rate in PHP per hour")
    meeting_place = models.CharField(max_length=200, validators=[alphanumeric_validator], help_text="e.g. Online, CIT Campus, Coffee Shop")
    description = models.TextField(blank=True, help_text="Optional: short service description")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.consultant.user.get_full_name()} — {self.profession} ({self.expertise})"
    
    def get_available_days_list(self):
        if self.available_days:
            return [day.strip() for day in self.available_days.split(',')]
        return []
    
    def is_available_on_day(self, day_name):
        return day_name.lower() in self.get_available_days_list()