from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta, time as dt_time, datetime as dt_datetime
from .models import User, Student, Consultant, Admin, Appointment, Verification, Market

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
import re

User = get_user_model()

# Validation helper functions
def validate_name(name):
    """Validate name: only letters, spaces, hyphens. Max 100 chars."""
    if not name or not name.strip():
        return False, "Name cannot be empty."
    if not re.match(r'^[a-zA-Z\s\-]+$', name):
        return False, "Name can only contain letters, spaces, and hyphens."
    if len(name) > 100:
        return False, "Name is too long (maximum 100 characters)."
    return True, ""

def validate_contact(contact):
    """Validate contact: digits, spaces, hyphens, parentheses, plus. Max 20 chars."""
    if not contact or not contact.strip():
        return False, "Contact number cannot be empty."
    if not re.match(r'^[\d\s\-\(\)\+]+$', contact):
        return False, "Contact number can only contain numbers, spaces, hyphens, parentheses, and plus signs."
    if len(contact) > 20:
        return False, "Contact number is too long (maximum 20 characters)."
    return True, ""

def validate_text_field(text, field_name, max_length=100, allow_empty=False):
    """Validate text field: alphanumeric, spaces, hyphens only."""
    if not text or not text.strip():
        if allow_empty:
            return True, ""
        return False, f"{field_name} cannot be empty."
    if not re.match(r'^[a-zA-Z0-9\s\-]+$', text):
        return False, f"{field_name} can only contain letters, numbers, spaces, and hyphens."
    if len(text) > max_length:
        return False, f"{field_name} is too long (maximum {max_length} characters)."
    return True, ""

# 🔹 Landing Page
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
        # elif role == "admin":
        #     user.is_staff = True
        #     user.is_superuser = True
        #     user.save()
        #     Admin.objects.create(
        #         user=user,
        #         contact_number=request.POST.get("contact_number_admin") or ""
        #     )

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
    if not pending_verification and not approved_verification:
        rejected_verification = Verification.objects.filter(
            consultant=consultant_user,
            status='rejected'
        ).order_by('-reviewed_at').first()

    total_students = Student.objects.count()
    total_appointments = Appointment.objects.filter(consultant=consultant).count() if consultant else 0

    pending_appointments = Appointment.objects.filter(consultant=consultant, status='pending')
    confirmed_appointments = Appointment.objects.filter(consultant=consultant, status='confirmed')
    cancelled_appointments = Appointment.objects.filter(consultant=consultant, status='cancelled')

    market_listing = Market.objects.filter(consultant=consultant).first() if consultant else None

    context = {
        "consultant": consultant,
        "consultant_name": consultant_user.get_full_name(),
        "pending_verification": pending_verification,
        "approved_verification": approved_verification,
        "rejected_verification": rejected_verification,
        "total_students": total_students,
        "total_appointments": total_appointments,
        "appointments": confirmed_appointments,
        "students": [],
        "pending_appointments": pending_appointments,
        "cancelled_appointments": cancelled_appointments,
        "market_listing": market_listing,  
    }

    return render(request, "ConsultApp/consultant-dashboard.html", context)

@login_required
def update_appointment_status(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id)

    if request.method == 'POST':
        action = request.POST.get('action')

        if action in ['approve', 'accept']:
            appointment.status = 'confirmed'
            appointment.save()

            student = appointment.student
            consultant = appointment.consultant

            if not student.assigned_consultant:
                student.assigned_consultant = consultant

            if appointment.topic and (not student.student_program or student.student_program.lower() == "undecided"):
                student.student_program = appointment.topic

            student.save()

            messages.success(
                request,
                f"Appointment with {student.user.get_full_name()} approved successfully. "
                f"Student’s program and topic have been updated."
            )

        elif action in ['reject', 'decline']:
            appointment.status = 'cancelled'
            appointment.save()
            messages.warning(
                request,
                f"Appointment with {appointment.student.user.get_full_name()} rejected."
            )

    # ✅ Keep your original redirection
    next_url = request.GET.get('next') or request.META.get('HTTP_REFERER') or 'consultant_dashboard'
    return redirect(next_url)

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

    total_fields = 6  
    completed = 0
    missing_fields = []

    if user.first_name:
        completed += 1
    else:
        missing_fields.append("First Name")

    if user.last_name:
        completed += 1
    else:
        missing_fields.append("Last Name")

    if user.email:
        completed += 1
    else:
        missing_fields.append("Email Address")

    if profile.contact_number:
        completed += 1
    else:
        missing_fields.append("Contact Number")

    if profile.expertise:
        completed += 1
    else:
        missing_fields.append("Expertise")

    if profile.workplace:
        completed += 1
    else:
        missing_fields.append("Workplace")

    verification_complete = profile.is_verified
    if verification_complete:
        completed += 1
        total_fields += 1
    else:
        missing_fields.append("Verification Status")

    completion_percentage = int((completed / total_fields) * 100)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        contact_number = request.POST.get("contact_number", "").strip()
        expertise = request.POST.get("expertise", "").strip()
        workplace = request.POST.get("workplace", "").strip()

        # Validate name
        is_valid, error = validate_name(full_name)
        if not is_valid:
            messages.error(request, error)
            return redirect("consultant_profile")

        # Validate contact
        is_valid, error = validate_contact(contact_number)
        if not is_valid:
            messages.error(request, error)
            return redirect("consultant_profile")

        # Validate expertise
        is_valid, error = validate_text_field(expertise, "Expertise", max_length=100)
        if not is_valid:
            messages.error(request, error)
            return redirect("consultant_profile")

        # Validate workplace
        is_valid, error = validate_text_field(workplace, "Workplace", max_length=150)
        if not is_valid:
            messages.error(request, error)
            return redirect("consultant_profile")

    context = {
        "user": user,
        "profile": profile,
        "completion_percentage": completion_percentage,
        "missing_fields": missing_fields,
    }
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

@login_required
@require_POST
def toggle_market_status(request, market_id):
    try:
        consultant = Consultant.objects.get(user=request.user)
        market_listing = get_object_or_404(Market, id=market_id, consultant=consultant)
        
        # Toggle the status - this flips True to False or False to True
        market_listing.is_active = not market_listing.is_active
        market_listing.save()
        
        if market_listing.is_active:
            messages.success(request, "✅ You are now available for bookings!")
        else:
            messages.info(request, "⏸ You are now unavailable. Students cannot book you at this time.")
        
    except Consultant.DoesNotExist:
        messages.error(request, "Consultant profile not found.")
    
    return redirect('consultant_dashboard')

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

    query = request.GET.get("q", "").strip()

    recommended_consultants = Market.objects.select_related("consultant__user").filter(
        consultant__is_verified=True,
        is_active=True,
    )

    if query:
        # Filter results by first name, last name, expertise, profession
        recommended_consultants = recommended_consultants.filter(
            Q(consultant__user__first_name__icontains=query) |
            Q(consultant__user__last_name__icontains=query) |
            Q(expertise__icontains=query) |
            Q(profession__icontains=query)
        )
    else:
        # Default: show 3 random consultants
        recommended_consultants = recommended_consultants.order_by("?")[:3]

    # Statistics
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
        "query": query,
    }

    return render(request, "ConsultApp/student-dashboard.html", context)

@login_required
def student_profile_view(request):
    student = Student.objects.get(user=request.user)
    user = request.user

    total_fields = 5
    completed = 0
    missing_fields = []

    if user.first_name:
        completed += 1
    else:
        missing_fields.append("First Name")

    if user.last_name:
        completed += 1
    else:
        missing_fields.append("Last Name")

    if student.student_department:
        completed += 1
    else:
        missing_fields.append("Department")

    if student.student_program:
        completed += 1
    else:
        missing_fields.append("Program")

    if student.student_year_level and student.student_year_level > 0:
        completed += 1
    else:
        missing_fields.append("Year Level")

    completion_percentage = int((completed / total_fields) * 100)

    if request.method == "POST":
        full_name = request.POST.get("fullName", "").strip()
        department = request.POST.get("department", "").strip()
        program = request.POST.get("program", "").strip()
        year_level = request.POST.get("yearLevel", "0")

        # Validate name
        if full_name:
            is_valid, error = validate_name(full_name)
            if not is_valid:
                messages.error(request, error)
                return redirect("student_profile")
            
            user.first_name = full_name.split(" ")[0]
            if len(full_name.split(" ")) > 1:
                user.last_name = " ".join(full_name.split(" ")[1:])
            user.save()

        # Validate department
        if department:
            is_valid, error = validate_text_field(department, "Department", max_length=100)
            if not is_valid:
                messages.error(request, error)
                return redirect("student_profile")
            student.student_department = department

        # Validate program
        if program:
            is_valid, error = validate_text_field(program, "Program", max_length=150)
            if not is_valid:
                messages.error(request, error)
                return redirect("student_profile")
            student.student_program = program

        # Validate year level
        try:
            year_level_int = int(year_level)
            if year_level_int < 0 or year_level_int > 6:
                messages.error(request, "Please select a valid year level.")
                return redirect("student_profile")
            student.student_year_level = year_level_int
        except ValueError:
            messages.error(request, "Invalid year level.")
            return redirect("student_profile")

        student.save()
        messages.success(request, "Profile updated successfully!")
        return redirect("student_profile")

    context = {
        "student": student,
        "completion_percentage": completion_percentage,
        "missing_fields": missing_fields,
    }
    return render(request, "ConsultApp/student-profile.html", context)


@login_required
def student_history_view(request):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return render(request, "ConsultApp/error.html", {"message": "Student record not found."})

    appointments = Appointment.objects.filter(
        student=student,
        status__in=['completed', 'cancelled']
    ).select_related('consultant__user').order_by('-date', '-time')

    consultants = Consultant.objects.select_related('user').all()

    context = {"appointments": appointments, "consultants": consultants}
    return render(request, "ConsultApp/student-history.html", context)

@login_required
def student_appointments_view(request):
    student = get_object_or_404(Student, user=request.user)

    now = timezone.now().date()
    current_time = timezone.now().time()
    appointments = Appointment.objects.filter(student=student)

    for appt in appointments:
        if appt.status in ["pending", "confirmed"]:
            if appt.date < now or (appt.date == now and appt.time < current_time):
                appt.status = "completed"
                appt.save()

    active_appointments = Appointment.objects.filter(
        student=student,
        status__in=["pending", "confirmed"]
    ).order_by('date', 'time')

    consultants = Consultant.objects.all()

    return render(request, "ConsultApp/student-appointments.html", {
        "appointments": active_appointments,
        "consultants": consultants
    })

@login_required
def book_appointment(request, consultant_id=None):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')

    def get_market_for_consultant(consultant_obj):
        """Get active market listing for consultant"""
        return Market.objects.filter(
            consultant=consultant_obj, 
            is_active=True
        ).order_by('-updated_at').first()

    def generate_hourly_slots(available_from, available_to):
        slots = []
        if not available_from or not available_to:
            return slots
        start_min = available_from.hour * 60 + available_from.minute
        end_min = available_to.hour * 60 + available_to.minute
        cur = start_min
        while cur + 60 <= end_min:
            hh = cur // 60
            mm = cur % 60
            slots.append(f"{hh:02d}:{mm:02d}")
            cur += 60
        return slots

    consultant = None
    market = None

    if consultant_id:
        try:
            consultant = Consultant.objects.get(user__id=consultant_id, is_verified=True)
            market = get_market_for_consultant(consultant)
            if not market:
                messages.error(request, "This consultant is currently unavailable for bookings.")
                return redirect('student_dashboard')
        except Consultant.DoesNotExist:
            messages.error(request, "Consultant not found.")
            return redirect('student_dashboard')

    consultants_with_market = Consultant.objects.filter(
        is_verified=True,
        market_listings__is_active=True
    ).select_related("user").distinct()

    if request.method == "POST":
        if not consultant:
            form_consultant_id = request.POST.get("consultant_id")
            if not form_consultant_id:
                messages.error(request, "Please select a consultant.")
                return render(request, "ConsultApp/book_appointment.html", {
                    "consultant": None,
                    "market": None,
                    "consultants": consultants_with_market,
                    "slots": [],
                    "today": timezone.localdate().isoformat(),
                })
            
            try:
                consultant = Consultant.objects.get(user__id=int(form_consultant_id), is_verified=True)
                market = get_market_for_consultant(consultant)
                if not market:
                    messages.error(request, "Selected consultant is currently unavailable.")
                    return render(request, "ConsultApp/book_appointment.html", {
                        "consultant": None,
                        "market": None,
                        "consultants": consultants_with_market,
                        "slots": [],
                        "today": timezone.localdate().isoformat(),
                    })
            except (Consultant.DoesNotExist, ValueError):
                messages.error(request, "Invalid consultant selected.")
                return render(request, "ConsultApp/book_appointment.html", {
                    "consultant": None,
                    "market": None,
                    "consultants": consultants_with_market,
                    "slots": [],
                    "today": timezone.localdate().isoformat(),
                })

        date_str = request.POST.get("date", "").strip()
        start_time_str = request.POST.get("start_time", "").strip()
        duration_hours_str = request.POST.get("duration_hours", "1")
        topic = request.POST.get("topic", "").strip()
        research_title = request.POST.get("research_title", "").strip()

        if not date_str or not start_time_str or not topic:
            messages.error(request, "Please fill in all required fields (Date, Time, Topic).")
            slots = generate_hourly_slots(market.available_from, market.available_to)
            return render(request, "ConsultApp/book_appointment.html", {
                "consultant": consultant,
                "market": market,
                "consultants": consultants_with_market,
                "slots": slots,
                "today": timezone.localdate().isoformat(),
            })

        try:
            duration_hours = int(duration_hours_str)
            if duration_hours < 1:
                duration_hours = 1
        except ValueError:
            duration_hours = 1

        try:
            date_obj = dt_datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time_obj = dt_datetime.strptime(start_time_str, "%H:%M").time()
        except ValueError:
            messages.error(request, "Invalid date or time format. Please use the date picker.")
            slots = generate_hourly_slots(market.available_from, market.available_to)
            return render(request, "ConsultApp/book_appointment.html", {
                "consultant": consultant,
                "market": market,
                "consultants": consultants_with_market,
                "slots": slots,
                "today": timezone.localdate().isoformat(),
            })

        if date_obj < timezone.localdate():
            messages.error(request, "Cannot book appointments in the past.")
            slots = generate_hourly_slots(market.available_from, market.available_to)
            return render(request, "ConsultApp/book_appointment.html", {
                "consultant": consultant,
                "market": market,
                "consultants": consultants_with_market,
                "slots": slots,
                "today": timezone.localdate().isoformat(),
            })

        available_from = market.available_from
        available_to = market.available_to
        start_dt = dt_datetime.combine(date_obj, start_time_obj)
        end_dt = start_dt + timedelta(hours=duration_hours)
        end_time_obj = end_dt.time()

        if not (available_from <= start_time_obj and end_time_obj <= available_to):
            messages.error(
                request, 
                f"Selected time is outside consultant's availability "
                f"({available_from.strftime('%I:%M %p')} - {available_to.strftime('%I:%M %p')})."
            )
            slots = generate_hourly_slots(market.available_from, market.available_to)
            return render(request, "ConsultApp/book_appointment.html", {
                "consultant": consultant,
                "market": market,
                "consultants": consultants_with_market,
                "slots": slots,
                "today": timezone.localdate().isoformat(),
            })

        conflicts = []
        existing_appts = Appointment.objects.filter(
            consultant=consultant, 
            date=date_obj,
            status__in=['pending', 'confirmed']  
        )
        
        for ap in existing_appts:
            ap_start = dt_datetime.combine(date_obj, ap.time)
            ap_end = ap_start + timedelta(minutes=ap.duration_minutes or 60)
            if (start_dt < ap_end) and (end_dt > ap_start):
                conflicts.append(ap)
        
        if conflicts:
            messages.error(
                request, 
                "This time slot conflicts with an existing appointment. "
                "Please choose another time."
            )
            slots = generate_hourly_slots(market.available_from, market.available_to)
            return render(request, "ConsultApp/book_appointment.html", {
                "consultant": consultant,
                "market": market,
                "consultants": consultants_with_market,
                "slots": slots,
                "today": timezone.localdate().isoformat(),
            })

        try:
            appointment = Appointment.objects.create(
                consultant=consultant,
                student=student,
                topic=topic,
                research_title=research_title,
                date=date_obj,
                time=start_time_obj,
                duration_minutes=duration_hours * 60,
                status="pending",
            )
            
            consultant_name = consultant.user.get_full_name()
            messages.success(
                request, 
                f"✅ You successfully booked {consultant_name}! "
                f"Your appointment is pending confirmation."
            )
            
            return redirect('student_dashboard')
            
        except Exception as e:
            messages.error(request, f"Failed to create appointment: {str(e)}")
            slots = generate_hourly_slots(market.available_from, market.available_to)
            return render(request, "ConsultApp/book_appointment.html", {
                "consultant": consultant,
                "market": market,
                "consultants": consultants_with_market,
                "slots": slots,
                "today": timezone.localdate().isoformat(),
            })

    slots = []
    if market:
        slots = generate_hourly_slots(market.available_from, market.available_to)

    today_iso = timezone.localdate().isoformat()

    return render(request, "ConsultApp/book_appointment.html", {
        "consultant": consultant,
        "market": market,
        "consultants": consultants_with_market,
        "slots": slots,
        "today": today_iso,
    })

@login_required
def cancel_appointment(request, appointment_id):
    student = get_object_or_404(Student, user=request.user)
    booking = get_object_or_404(Appointment, id=appointment_id, student=student)

    if booking.status != "pending":
        messages.error(request, "You can no longer cancel this appointment.")
        return redirect('student_appointments')

    booking.status = "cancelled"
    booking.save()

    messages.success(request, "Your appointment has been cancelled.")
    return redirect('student_appointments')

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

    completed = 0
    total_fields = 4

    if admin_user.first_name:
        completed += 1

    if admin_user.last_name:
        completed += 1

    if admin_user.email:
        completed += 1

    if admin_profile.contact_number:
        completed += 1

    progress_percentage = int((completed / total_fields) * 100)

    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        contact = request.POST.get("contact", "").strip()

        # Validate name
        is_valid, error = validate_name(full_name)
        if not is_valid:
            messages.error(request, error)
            return redirect("admin_profile")

        # Validate contact
        is_valid, error = validate_contact(contact)
        if not is_valid:
            messages.error(request, error)
            return redirect("admin_profile")
        
        parts = full_name.split()

        if len(parts) >= 2:
            admin_user.first_name = parts[0]
            admin_user.last_name = " ".join(parts[1:])
        else:
            admin_user.first_name = full_name
            admin_user.last_name = ""

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
        "profile_progress": progress_percentage,
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

# 🔹 Password Views
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

# 🔹 Appointment Views
@login_required
def all_consultants_view(request):
    consultants = (
        Market.objects
        .select_related("consultant__user")
        .filter(consultant__is_verified=True, is_active=True)
    )
    return render(request, "ConsultApp/all-consultants.html", {"consultants": consultants})