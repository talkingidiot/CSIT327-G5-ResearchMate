import json
from pyexpat.errors import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, get_user_model
from django.contrib.auth.hashers import make_password
from .models import ConsultantProfile

User = get_user_model()

# 🔹 Auth Pages
def login_register_view(request):
    """Render combined login/register page."""
    return render(request, "ConsultApp/login-register.html")


@csrf_exempt
def register_user(request):
    """Handle user registration (AJAX POST)."""
    if request.method == "POST":
        try:
            data = json.loads(request.body)

            first_name = data.get("first_name")
            last_name = data.get("last_name")
            username = data.get("username")
            email = data.get("email")
            password = data.get("password")
            role = data.get("role")
            workplace = data.get("workplace", "")

            # Create user
            user = User(
                first_name=first_name,
                last_name=last_name,
                username=username,
                email=email,
                role=role,
                is_verified=True,
                password=make_password(password),
            )

            # Grant admin privileges
            if role == "admin":
                user.is_staff = True
                user.is_superuser = True

            user.save()

            # Extra profile for consultants
            if role == "consultant":
                ConsultantProfile.objects.create(
                    consultant=user,
                    department=workplace,
                    expertise="",
                    availability="",
                )

            return JsonResponse({"message": "Registration successful!"}, status=201)

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)

    return JsonResponse({"error": "Invalid request method"}, status=400)

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            return JsonResponse({"error": "Invalid email or password"}, status=400)

        user = authenticate(username=user_obj.username, password=password)
        if user:
            login(request, user)
            role = getattr(user, "role", "student")
            return redirect(f"{role}_dashboard")
        else:
            return JsonResponse({"error": "Invalid email or password"}, status=400)

    return render(request, "ConsultApp/login-register.html")

# 🔹 Dashboards
def admin_dashboard_view(request):
    return render(request, "ConsultApp/admin-dashboard.html")


def student_dashboard_view(request):
    return render(request, "ConsultApp/student-dashboard.html")


def consultant_dashboard_view(request):
    return render(request, "ConsultApp/consultant-dashboard.html")


# 🔹 Consultant Verification
def consultant_verification_view(request):
    return render(request, "ConsultApp/consultant-verification.html")
