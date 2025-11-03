from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime
from .models import User, Student, Consultant, Admin, Appointment, Verification, Market

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings


User = get_user_model()

def home_view(request):
    return render(request, "ConsultApp/landing-page.html")

# 🔹 Auth Pages
def login_register_view(request):
    return render(request, "ConsultApp/login-register.html")

# 🔹 Register View
@csrf_exempt
def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email")
        password = request.POST.get("password")
        role = request.POST.get("role")

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email is already registered.")
            return render(request, "ConsultApp/login-register.html", {
                "show_signup": True,
                "form_source": "register",
            })

        name_parts = full_name.split()
        if len(name_parts) == 1:
            first_name = name_parts[0].title()
            last_name = ""
        else:
            first_name = " ".join(name_parts[:-1]).title()
            last_name = name_parts[-1].title()

        if not full_name or not email or not password or not role:
            messages.error(request, "All fields are required.")
            return render(request, "ConsultApp/login-register.html", {
                "show_signup": True,
                "form_source": "register",
            })

        if User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists():
            messages.error(request, "A user with that name already exists.")
            return render(request, "ConsultApp/login-register.html", {
                "show_signup": True,
                "form_source": "register",
            })

        if not (email.endswith("@cit.edu") or email.endswith("@gmail.com")):
            messages.error(request, "Please use your institutional email address.")
            return render(request, "ConsultApp/login-register.html", {
                "show_signup": True,
                "form_source": "register",
            })

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.")
            return render(request, "ConsultApp/login-register.html", {
                "show_signup": True,
                "form_source": "register",
            })

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
                student_year_level=request.POST.get("student_year_level") or 0,
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

        messages.success(request, f"Account created successfully as {role.title()}!", extra_tags="login")
        response = redirect("login")
        response["Clear-SessionStorage"] = "true"
        return response

    return render(request, "ConsultApp/login-register.html")


# 🔹 Login View
@csrf_exempt
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        password = request.POST.get("password")

        if not email or not password:
            messages.error(request, "Please fill in both email and password.", extra_tags="login")
            return render(request, "ConsultApp/login-register.html")

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, "Invalid credentials. Please try again or register your account.", extra_tags="login")
            return render(request, "ConsultApp/login-register.html")

        if user is not None:
            login(request, user)
            if user.role == "student":
                return redirect("student_dashboard")
            elif user.role == "consultant":
                return redirect("consultant_dashboard")
            elif user.role == "admin":
                return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid credentials. Please try again or register your account.", extra_tags="login")

    return render(request, "ConsultApp/login-register.html", {"form_source":"login"})

# 🔹 Logout View
def logout_view(request):
    logout(request)
    messages.success(request, "You have been logged out successfully.", extra_tags="login")
    return redirect("login")

# 🔹 Consultant Views
@login_required
def consultant_dashboard(request):
    consultant_user = request.user
    consultant = Consultant.objects.filter(user=consultant_user).first()

    pending_verification = Verification.objects.filter(
        consultant=consultant_user,
        status='pending'
    ).exists()

    approved_verification = Verification.objects.filter(
        consultant=consultant_user,
        status='approved'
    ).order_by('-reviewed_at').first()

    rejected_verification = None
    # Only show rejected if there’s no pending or approved one
    if not pending_verification and not approved_verification:
        rejected_verification = Verification.objects.filter(
            consultant=consultant_user,
            status='rejected'
        ).order_by('-reviewed_at').first()

    total_students = Student.objects.count()
    total_appointments = Appointment.objects.filter(consultant=consultant).count() if consultant else 0

    context = {
        "consultant": consultant,
        "consultant_name": consultant_user.get_full_name(),
        "pending_verification": pending_verification,
        "approved_verification": approved_verification,
        "rejected_verification": rejected_verification,
        "total_students": total_students,
        "total_appointments": total_appointments,
        "appointments": [],
        "students": [],
    }

    return render(request, "ConsultApp/consultant-dashboard.html", context)


@login_required
def consultant_appointments_view(request):
    consultant_user = request.user
    try:
        consultant = Consultant.objects.get(user=consultant_user)
        appointments = Appointment.objects.filter(consultant=consultant).order_by('date', 'time')
    except Consultant.DoesNotExist:
        appointments = []

    return render(request, 'ConsultApp/consultant-appointments.html', {'appointments': appointments})


@login_required
def consultant_students_view(request):
    try:
        consultant = Consultant.objects.get(user=request.user)
        students = Student.objects.filter(assigned_consultant=consultant)
    except Consultant.DoesNotExist:
        students = []

    return render(request, "ConsultApp/consultant-students.html", {"students": students})


@login_required
def consultant_profile_view(request):
    user = request.user
    profile, created = Consultant.objects.get_or_create(user=user)

    if request.method == "POST":
        full_name = request.POST.get("full_name")
        email = request.POST.get("email")
        contact_number = request.POST.get("contact_number")
        expertise = request.POST.get("expertise")

        user.first_name = full_name.split()[0] if full_name else user.first_name
        user.last_name = " ".join(full_name.split()[1:]) if len(full_name.split()) > 1 else user.last_name
        user.email = email
        user.save()

        profile.contact_number = contact_number
        profile.expertise = expertise
        profile.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("consultant_profile")

    context = {"user": user, "profile": profile}
    return render(request, "ConsultApp/consultant-profile.html", context)


@login_required
def consultant_verification_view(request):
    consultant_user = request.user

    try:
        consultant = Consultant.objects.get(user=consultant_user)
        if consultant.is_verified:
            messages.info(request, "You are already verified!")
            return redirect('consultant_dashboard')
    except Consultant.DoesNotExist:
        pass

    has_pending_verification = Verification.objects.filter(
        consultant=consultant_user, status='pending'
    ).exists()

    if request.method == "POST":
        contact = request.POST.get("contact")
        expertise = request.POST.get("expertise")
        workplace = request.POST.get("workplace", "")
        qualification = request.POST.get("qualification")
        proof = request.FILES.get("license")

        Verification.objects.create(
            consultant=consultant_user,
            contact_number=contact,
            expertise=expertise,
            workplace=workplace,
            qualification=qualification,
            proof_document=proof,
            status='pending',
        )

        messages.success(request, "Verification submitted! Await admin approval.")
        return redirect('consultant_dashboard')

    return render(request, "ConsultApp/consultant-verification.html", {
        'has_pending_verification': has_pending_verification
    })

@login_required
def consultant_market(request):
    try:
        consultant = Consultant.objects.get(user=request.user)
    except Consultant.DoesNotExist:
        messages.error(request, "Consultant profile not found.")
        return redirect('consultant_dashboard')

    if not consultant.is_verified:
        messages.error(request, "You must be verified to register your availability.")
        return redirect('consultant_dashboard')

    if request.method == "POST":
        expertise = request.POST.get("expertise")
        profession = request.POST.get("profession")
        available_from_str = request.POST.get("available_from")
        available_to_str = request.POST.get("available_to") 
        rate_per_hour = request.POST.get("rate_per_hour")
        meeting_place = request.POST.get("meeting_place")
        description = request.POST.get("description", "")
        is_active = "is_active" in request.POST

        if not all([expertise, profession, available_from_str, available_to_str, rate_per_hour, meeting_place]):
            messages.error(request, "Please fill in all fields.")
            return render(request, "ConsultApp/consultant-market.html")

        try:
            available_from = datetime.strptime(available_from_str, "%I:%M %p").time()
            available_to = datetime.strptime(available_to_str, "%I:%M %p").time()
        except ValueError:
            return render(request, "ConsultApp/consultant-market.html", {
                "error": "Invalid time format. Please select valid times."
            })
        Market.objects.create(
            consultant=consultant,
            expertise=expertise,
            profession=profession,
            available_from=available_from,
            available_to=available_to,
            rate_per_hour=rate_per_hour,
            meeting_place=meeting_place,
            description=description,
            is_active=is_active,
        )

        messages.success(request, "✅ You are now listed in the market!")
        return redirect('consultant_dashboard')

    return render(request, "ConsultApp/consultant-market.html")


# 🔹 Student Views
@login_required
def student_dashboard(request):
    student = Student.objects.filter(user=request.user).first()

    if not student:
        messages.error(request, "Student profile not found.")
        return redirect('login_view')

    now = timezone.now()

    upcoming_sessions = Appointment.objects.filter(
        student=student, status__in=["confirmed", "pending"]
    ).order_by("date")[:5]

    recommended_consultants = (
        Market.objects
        .select_related("consultant__user")
        .filter(
            consultant__is_verified=True,
            is_active=True,
            available_from__lte=now,
            available_to__gte=now
        )
        .order_by("?")[:3]  
    )

    stats = {
        "current": Appointment.objects.filter(student=student, status="confirmed").count(),
        "previous": Appointment.objects.filter(student=student, status="completed").count(),
        "pending": Appointment.objects.filter(student=student, status="pending").count(),
        "cancelled": Appointment.objects.filter(student=student, status="cancelled").count(),
    }

    context = {
        "student_name": request.user.get_full_name(),
        "student": student,
        "recommended_consultants": recommended_consultants,
        "upcoming_sessions": upcoming_sessions,
        "stats": stats,
    }

    return render(request, "ConsultApp/student-dashboard.html", context)

@login_required
def student_profile_view(request):
    student = Student.objects.get(user=request.user)

    if request.method == "POST":
        student.student_department = request.POST.get("department")
        student.student_program = request.POST.get("program")
        student.student_year_level = request.POST.get("yearLevel")
        student.save()

        full_name = request.POST.get("fullName")
        if full_name:
            request.user.first_name = full_name.split(" ")[0]
            if len(full_name.split(" ")) > 1:
                request.user.last_name = " ".join(full_name.split(" ")[1:])
            request.user.save()

        return redirect("student_profile")

    context = {"student": student}
    return render(request, "ConsultApp/student-profile.html", context)

@login_required
def student_history_view(request):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return render(request, "ConsultApp/error.html", {"message": "Student record not found."})

    appointments = Appointment.objects.filter(
        student=student, status='completed'
    ).select_related('consultant__user')

    consultants = Consultant.objects.select_related('user').all()

    context = {"appointments": appointments, "consultants": consultants}
    return render(request, "ConsultApp/student-history.html", context)

@login_required
def appointments_view(request):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return render(request, "ConsultApp/error.html", {"message": "Student record not found."})

    appointments = Appointment.objects.filter(student=student).select_related('consultant__user')
    consultants = Consultant.objects.select_related('user').all()

    context = {"appointments": appointments, "consultants": consultants}
    return render(request, "ConsultApp/appointments.html", context)

# 🔹 Admin Views
def is_admin(user):
    return user.is_superuser or getattr(user, "user_type", "") == "Admin"

@login_required
@user_passes_test(is_admin)
def admin_dashboard(request):
    total_students = Student.objects.count()
    total_consultants = Consultant.objects.count()
    pending_approvals = Verification.objects.filter(status='pending').count()
    active_bookings = Appointment.objects.count()
    recent_users = User.objects.order_by('-date_joined')[:5]
    verification_requests = Verification.objects.filter(status='pending').select_related('consultant')

    return render(request, "ConsultApp/admin-dashboard.html", {
        "total_students": total_students,
        "total_consultants": total_consultants,
        "pending_approvals": pending_approvals,
        "active_bookings": active_bookings,
        "recent_users": recent_users,
        "verification_requests": verification_requests,
    })

@login_required
@user_passes_test(is_admin)
def admin_students_view(request):
    students = Student.objects.select_related('user').all()
    return render(request, "ConsultApp/admin-students.html", {"students": students})

@login_required
@user_passes_test(is_admin)
def admin_consultants_view(request):
    consultants = Consultant.objects.select_related('user').all()
    return render(request, "ConsultApp/admin-consultants.html", {"consultants": consultants})

@login_required
@user_passes_test(is_admin)
def admin_reports_view(request):
    return render(request, "ConsultApp/admin-reports.html")

@login_required
@user_passes_test(is_admin)
def admin_profile_view(request):
    admin_user = request.user
    admin_profile, _ = Admin.objects.get_or_create(user=admin_user)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        contact = request.POST.get("contact", "").strip()

        name_parts = full_name.split()
        if len(name_parts) == 1:
            admin_user.first_name = full_name
            admin_user.last_name = ""
        else:
            admin_user.first_name = " ".join(name_parts[:-1])
            admin_user.last_name = name_parts[-1]

        admin_user.email = email
        admin_user.save()

        admin_profile.contact_number = contact
        admin_profile.save()

        messages.success(request, "Profile updated successfully!")
        return redirect("admin_profile")

    context = {
        "admin_name": f"{admin_user.first_name} {admin_user.last_name}".strip(),
        "admin_email": admin_user.email,
        "admin_contact": admin_profile.contact_number or "Not set",
        "admin_role": "System Administrator",
    }
    return render(request, "ConsultApp/admin-profile.html", context)


# 🔹 Verification Modal
@login_required
@user_passes_test(is_admin)
def verification_details(request, verification_id):
    verification = get_object_or_404(Verification, id=verification_id)
    return render(request, "ConsultApp/verification-details.html", {"verification": verification})

# 🔹 Approve / Reject Consultant
@require_POST
@login_required
@user_passes_test(is_admin)
def approve_consultant(request, verification_id):
    verification = get_object_or_404(Verification, id=verification_id)
    verification.status = 'approved'
    verification.reviewed_at = timezone.now()
    verification.save()

    try:
        consultant = Consultant.objects.get(user=verification.consultant)
        consultant.is_verified = True
        consultant.save()
        messages.success(request, f"{verification.consultant.get_full_name()} has been approved as a consultant.")
    except Consultant.DoesNotExist:
        messages.error(request, "Consultant profile not found.")

    return redirect('admin_dashboard')

@require_POST
@login_required
@user_passes_test(is_admin)
def reject_consultant(request, verification_id):
    verification = get_object_or_404(Verification, id=verification_id)
    verification.status = 'rejected'
    verification.reviewed_at = timezone.now()
    verification.save()

    messages.info(request, f"{verification.consultant.get_full_name()}'s verification was rejected.")
    return redirect('admin_dashboard')

@csrf_exempt
def forgot_password_view(request):
    if request.method == "POST":
        email = request.POST.get("email")
        user = User.objects.filter(email=email).first()

        if not user:
            messages.error(request, "No account found with that email.")
            return render(request, "ConsultApp/forgot-password.html")

        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        reset_link = request.build_absolute_uri(f"/reset-password/{uid}/{token}/")

        subject = "Password Reset Request"
        message = render_to_string("ConsultApp/password-reset-email.html", {
            "user": user,
            "reset_link": reset_link
        })
        send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [user.email])

        messages.success(request, "Password reset link has been sent to your email.")
        return redirect("login")

    return render(request, "ConsultApp/forgot-password.html")

@csrf_exempt
def reset_password_view(request, uidb64, token):
    try:
        uid = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except (TypeError, ValueError, OverflowError, User.DoesNotExist):
        user = None

    if user is not None and default_token_generator.check_token(user, token):
        if request.method == "POST":
            new_password = request.POST.get("password")
            confirm_password = request.POST.get("confirm_password")

            if new_password != confirm_password:
                messages.error(request, "Passwords do not match.")
                return render(request, "ConsultApp/reset-password.html")

            if len(new_password) < 8:
                messages.error(request, "Password must be at least 8 characters long.")
                return render(request, "ConsultApp/reset-password.html")

            user.set_password(new_password)
            user.save()
            messages.success(request, "Password reset successful. You can now log in.")
            return redirect("login")

        return render(request, "ConsultApp/reset-password.html")
    else:
        messages.error(request, "The password reset link is invalid or has expired.")
        return redirect("forgot_password")
