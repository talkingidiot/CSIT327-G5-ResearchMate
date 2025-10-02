from pyexpat.errors import messages
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
    if request.method == "POST":
        first_name = request.POST.get("first_name")
        last_name = request.POST.get("last_name")
        username = request.POST.get("username")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")
        workplace = request.POST.get("workplace", "")

        try:
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

            # Admin privileges if role is admin
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

            messages.success(request, "Registration successful! Please log in.")
            return redirect("login_user")

        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
            return redirect("register_user")

    return render(request, "ConsultApp/login-register.html")

@csrf_exempt
def login_user(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            messages.error(request, "Invalid email or password")
            return redirect("login_user")  # reload form with error

        user = authenticate(username=user_obj.username, password=password)
        return redirect(f"dashboard")

    return render(request, "ConsultApp/login-register.html")


# # 🔹 Dashboards
# def admin_dashboard_view(request):
#     return render(request, "ConsultApp/admin-dashboard.html")


# def student_dashboard_view(request):
#     return render(request, "ConsultApp/student-dashboard.html")


# def consultant_dashboard_view(request):
#     return render(request, "ConsultApp/consultant-dashboard.html")


# 🔹 Consultant Verification
def consultant_verification_view(request):
    return render(request, "ConsultApp/consultant-verification.html")

def dashboard_view(request):
    return render(request, "ConsultApp/dashboard.html")