from django.contrib.auth.models import AbstractUser, BaseUserManager
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

    USERNAME_FIELD = 'email'   # login with email
    REQUIRED_FIELDS = []       # no username required

    objects = UserManager()

    def __str__(self):
        return f"{self.email} ({self.role})"


# Student model
class Student(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    student_year_level = models.IntegerField()
    student_department = models.CharField(max_length=100)
    student_course = models.CharField(max_length=100)
    student_program = models.CharField(max_length=100)

    def __str__(self):
        return f"Student: {self.user.username}"


# Consultant model
class Consultant(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    contact_number = models.CharField(max_length=15)
    expertise = models.CharField(max_length=100)
    workplace = models.CharField(max_length=100)
    is_verified = models.BooleanField(default=False)

    def __str__(self):
        return f"Consultant: {self.user.username}"


# Admin model
class Admin(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, primary_key=True)
    contact_number = models.CharField(max_length=15)

    def __str__(self):
        return f"Admin: {self.user.username}"
