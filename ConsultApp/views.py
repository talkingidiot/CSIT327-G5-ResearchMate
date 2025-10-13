from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib.auth.hashers import make_password
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from .models import User, Student, Consultant, Admin

User = get_user_model()

# 🔹 Auth Pages
def login_register_view(request):
    """Render combined login/register page."""
    return render(request, "ConsultApp/login-register.html")

# ========== REGISTER VIEW ==========
@csrf_exempt
def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        # Check email uniqueness
        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "ConsultApp/login-register.html", {
                "show_signup": True,
                "form_source": "register",
            })

        # Check name uniqueness
        name_parts = full_name.strip().split(" ", 1)
        first_name = name_parts[0]
        last_name = name_parts[1] if len(name_parts) > 1 else ""

        if User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists():
            messages.error(request, "A user with that name already exists.")
            return render(request, "ConsultApp/login-register.html", {
                "show_signup": True,
                "form_source": "register",
            })

        # Create user
        user = User.objects.create_user(
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            role=role
        )

        if role == "student":
            Student.objects.create(
                user=user,
                student_year_level=request.POST.get("student_year_level") or 1,
                student_department=request.POST.get("student_department") or "",
                student_course=request.POST.get("student_course") or "",
                student_program=request.POST.get("student_program") or ""
            )
        elif role == "consultant":
            Consultant.objects.create(
                user=user,
                contact_number=request.POST.get("contact_number") or "",
                expertise=request.POST.get("expertise") or "",
                workplace=request.POST.get("workplace") or "",
                is_verified=False
            )
        elif role == "admin":
            user.is_staff = True
            user.is_superuser = True
            user.save()
            Admin.objects.create(
                user=user,
                contact_number=request.POST.get("contact_number_admin") or ""
            )

        messages.success(request, f"Account created successfully as {role.title()}!")
        return redirect("login")
    
    return render(request, "ConsultApp/login-register.html")


# ========== LOGIN VIEW ==========
@csrf_exempt
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        user = authenticate(request, email=email, password=password)

        if user is not None:
            login(request, user)
            # Redirect based on role
            if user.role == "student":
                return redirect("student_dashboard")
            elif user.role == "consultant":
                return redirect("consultant_dashboard")
            elif user.role == "admin":
                return redirect("admin_dashboard")

            else:
                messages.error(request, "Invalid role assigned.")
        else:
            messages.error(request, "Invalid email or password.")

    return render(request, "ConsultApp/login-register.html")


# ========== LOGOUT VIEW ==========
@login_required
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.")
    return redirect("login")

# 🔹 Consultant Views
@login_required
def consultant_dashboard(request):
    return render(request, "ConsultApp/consultant-dashboard.html")

@login_required
def consultant_appointments_view(request):
    return render(request, "ConsultApp/consultant-appointments.html")

@login_required
def consultant_profile_view(request):
    return render(request, "ConsultApp/consultant-profile.html")

@login_required
def consultant_students_view(request):
    return render(request, "ConsultApp/consultant-students.html")

@login_required
def consultant_verification_view(request):
    return render(request, "ConsultApp/consultant-verification.html")

# 🔹 Student Views
@login_required
def student_dashboard(request):
    return render(request, "ConsultApp/student-dashboard.html")

@login_required
def student_profile_view(request):
    return render(request, "ConsultApp/student-profile.html")

@login_required
def student_history_view(request):
    return render(request, "ConsultApp/student-history.html")

@login_required
def bookings_view(request):
    return render(request, "ConsultApp/bookings.html")

# 🔹 Admin Views
def is_admin(user):
    return user.is_superuser or getattr(user, "user_type", "") == "Admin"

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    return render(request, "ConsultApp/admin-dashboard.html")

@login_required
@user_passes_test(is_admin)
def admin_students_view(request):
    return render(request, "ConsultApp/admin-students.html")

@login_required
@user_passes_test(is_admin)
def admin_consultants_view(request):
    return render(request, "ConsultApp/admin-consultants.html")

@login_required
@user_passes_test(is_admin)
def admin_reports_view(request):
    return render(request, "ConsultApp/admin-reports.html")

@login_required
@user_passes_test(is_admin)
def admin_profile_view(request):
    return render(request, "ConsultApp/admin-profile.html")