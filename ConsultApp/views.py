from django.views.decorators.csrf import csrf_exempt
from django.shortcuts import redirect, render, get_object_or_404
from django.contrib.auth import authenticate, login, get_user_model, logout
from django.contrib import messages
from django.contrib.auth.decorators import login_required, user_passes_test
from django.utils import timezone
from django.views.decorators.http import require_POST
from datetime import datetime, timedelta, time as dt_time, datetime as dt_datetime
from .models import User, Student, Consultant, Admin, Appointment, Verification, Market, Feedback
from django.db.models import Prefetch, Case, When, Value, BooleanField
from supabase import create_client, Client 
from django.core.files.uploadedfile import UploadedFile
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.conf import settings
from django.urls import reverse
from django.db.models import Q
import re
import mimetypes
import json

User = get_user_model()

# Initializing client connection
try:
    supabase: Client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
except Exception as e:
    print(f"Supabase Client Error: {e}")
    supabase = None

# Documents image/file helper function
def get_verification_documents(user_id):
    if not supabase:
        return {}
        
    documents = {}
    try:
        files = supabase.storage.from_("verification_documents").list(f"{user_id}")
        
        for file_obj in files:
            file_name = file_obj.get('name', '')
            
            key = None
            if file_name.startswith('validId'): key = 'validId'
            elif file_name.startswith('license'): key = 'license'
            elif file_name.startswith('profilePhoto'): key = 'profilePhoto'
            
            if key:
                path = f"{user_id}/{file_name}"
                res = supabase.storage.from_("verification_documents").create_signed_url(path, 600)
                
                if isinstance(res, dict) and 'signedURL' in res:
                    documents[key] = res['signedURL']
                elif isinstance(res, str):
                    documents[key] = res
                    
    except Exception as e:
        print(f"Error fetching documents for {user_id}: {e}")
        
    return documents

# Avatar image helper function
def get_avatar_url(user_id):
    if not supabase:
        return None
    try:
        # Construct path: user_id/profile.png
        storage_path = f"{user_id}/profile.png"
        return supabase.storage.from_("avatars").get_public_url(storage_path)
    except Exception:
        return None

# Validation helper functions
def validate_name(name):
    if not name or not name.strip():
        return False, "Name cannot be empty."
    if not re.match(r'^[a-zA-Z\s\-]+$', name):
        return False, "Name can only contain letters, spaces, and hyphens."
    if len(name) > 100:
        return False, "Name is too long (maximum 100 characters)."
    return True, ""

def validate_contact(contact):
    if not contact or not contact.strip():
        return False, "Contact number cannot be empty."
    if not re.match(r'^[\d\s\-\(\)\+]+$', contact):
        return False, "Contact number can only contain numbers, spaces, hyphens, parentheses, and plus signs."
    if len(contact) > 11:
        return False, "Contact number is too long (maximum 11 characters)."
    return True, ""

def validate_text_field(text, field_name, max_length=100, allow_empty=False):
    if not text or not text.strip():
        if allow_empty:
            return True, ""
        return False, f"{field_name} cannot be empty."
    if not re.match(r'^[a-zA-Z0-9\s\-]+$', text):
        return False, f"{field_name} can only contain letters, numbers, spaces, and hyphens."
    if len(text) > max_length:
        return False, f"{field_name} is too long (maximum {max_length} characters)."
    return True, ""

def validate_expertise_list(text, field_name="Expertise", max_length=1000):
    if not text:
        return False, "Please select at least one expertise."
        
    if not re.match(r"^[a-zA-Z0-9\s\-\,\.\/\&\+]+$", text):
        return False, "Expertise contains invalid characters."
        
    if len(text) > max_length:
        return False, f"Too many items selected (max {max_length} characters)."
    return True, ""

# 🔹 Landing Page
def home_view(request):
    return render(request, "ConsultApp/landing-page.html")

# 🔹 Auth Pages
def login_register_view(request):
    return render(request, "ConsultApp/login-register-new.html")

# 🔹 Register View
@csrf_exempt
def register_view(request):
    if request.method == "POST":
        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("signup_email")
        password = request.POST.get("password")
        confirm_password = request.POST.get("confirmPassword")
        role = request.POST.get("role")
        fields = [full_name, email, password, confirm_password, role]
        errors = False
        
        if not any(fields):
            messages.error(request, "Please fill out the registration form.", extra_tags="general_error")
            return redirect(request.path_info + '?show_signup=true')
  
        if not full_name:
            messages.error(request, "Full Name is required.", extra_tags="full_name_error")
            errors = True
        if not email:
            messages.error(request, "Email is required.", extra_tags="email_error")
            errors = True
        if not password:
            messages.error(request, "Password is required.", extra_tags="password_error")
            errors = True
        if not confirm_password:
            messages.error(request, "Confirm password is required.", extra_tags="confirm_password_error")
            errors = True
        if not role:
            messages.error(request, "Please select a role.", extra_tags="role_error")
            errors = True

        if errors:
            return redirect(request.path_info + '?show_signup=true')

        if password and confirm_password and password != confirm_password:
            messages.error(request, "Passwords do not match.", extra_tags="confirm_password_error")
            return redirect(request.path_info + '?show_signup=true')

        if User.objects.filter(email__iexact=email).exists():
            messages.error(request, "Email is already registered.", extra_tags="email_error")
            return redirect(request.path_info + '?show_signup=true')

        name_parts = full_name.split()
        if len(name_parts) == 1:
            first_name = name_parts[0].title()
            last_name = ""
        else:
            first_name = " ".join(name_parts[:-1]).title()
            last_name = name_parts[-1].title()

        if User.objects.filter(first_name__iexact=first_name, last_name__iexact=last_name).exists():
            messages.error(request, "A user with that name already exists.", extra_tags="full_name_error")
            return redirect(request.path_info + '?show_signup=true')

        if not (email.endswith("@cit.edu") or email.endswith("@gmail.com")):
            messages.error(request, "Please use your institutional or personal email address.", extra_tags="email_error")
            return redirect(request.path_info + '?show_signup=true')

        if len(password) < 8:
            messages.error(request, "Password must be at least 8 characters long.", extra_tags="password_error")
            return redirect(request.path_info + '?show_signup=true')

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

        messages.success(request, f"Account created successfully as {role.title()}!", extra_tags="success")
        response = redirect("login")
        response["Clear-SessionStorage"] = "true"
        return response

    return render(request, "ConsultApp/login-register-new.html")

# 🔹 Login View
@csrf_exempt
def login_view(request):
    if request.method == "POST":
        email = request.POST.get("login_email", "").strip()
        password = request.POST.get("password", "")
        errors = False
        fields = [email, password]

        if not any(fields):
            messages.error(request, "Please enter your email and password.", extra_tags="general_login_error")
            return redirect("login")
        
        if not email:
            messages.error(request, "Email is required.", extra_tags="login_email_error")
            errors = True
        if not password:
            messages.error(request, "Password is required.", extra_tags="login_password_error")
            errors = True
        
        if errors:
            return redirect("login")

        user = authenticate(request, email=email, password=password)

        if user is None:
            messages.error(request, "Invalid credentials. Please try again or register your account.", extra_tags="general_login_error")
            return render(request, "ConsultApp/login-register-new.html")

        if user is not None:
            login(request, user)
            if user.role == "student":
                return redirect("student_dashboard")
            elif user.role == "consultant":
                return redirect("consultant_dashboard")
            elif user.role == "admin":
                return redirect("admin_dashboard")
        else:
            messages.error(request, "Invalid credentials. Please try again.", extra_tags="general_login_error")
            return redirect("login")

    return render(request, "ConsultApp/login-register-new.html", {"form_source":"login"})

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
    
    base_avatar_url = get_avatar_url(consultant_user.id)
    avatar_url = None
    if base_avatar_url:
        timestamp = request.session.get('avatar_version', int(datetime.now().timestamp()))
        avatar_url = f"{base_avatar_url}?t={timestamp}"

    def attach_avatar(person):
        user_id = person.user.id if hasattr(person, 'user') else person.student.user.id
        url = get_avatar_url(user_id)
        return f"{url}?t={timestamp}" if url else None

    pending_verification = Verification.objects.filter(
        consultant=consultant_user, status='pending'
    ).exists()

    approved_verification = Verification.objects.filter(
        consultant=consultant_user, status='approved'
    ).order_by('-reviewed_at').first()

    rejected_verification = None
    if not pending_verification and not approved_verification:
        rejected_verification = Verification.objects.filter(
            consultant=consultant_user, status='rejected'
        ).order_by('-reviewed_at').first()

    total_students = Student.objects.count()
    total_appointments = Appointment.objects.filter(consultant=consultant).count() if consultant else 0
        
    assigned_students = list(Student.objects.filter(
        student_appointments__consultant=consultant,
        student_appointments__status='confirmed'
    ).select_related('user').distinct()) if consultant else []

    for stud in assigned_students:
        stud.avatar_url = attach_avatar(stud)

    pending_appointments = list(Appointment.objects.filter(
        consultant=consultant, status='pending'
    ).select_related('student__user'))
    
    for appt in pending_appointments:
        appt.student.avatar_url = attach_avatar(appt.student)

    confirmed_appointments = list(Appointment.objects.filter(
        consultant=consultant, status='confirmed'
    ).select_related('student__user'))

    for appt in confirmed_appointments:
        appt.student.avatar_url = attach_avatar(appt.student)
    
    cancelled_appointments = Appointment.objects.filter(consultant=consultant, status='cancelled')

    market_listing = Market.objects.filter(consultant=consultant).first() if consultant else None
    
    if market_listing and consultant and consultant.expertise:
        market_listing.expertise_list = [
            x.strip() for x in consultant.expertise.split(',') if x.strip()
        ]

    if consultant and consultant.expertise:
        consultant.expertise_list = [
            x.strip() for x in consultant.expertise.split(',') if x.strip()
        ]

    consultant_feedbacks = []
    average_rating = 0
    
    if consultant:
        consultant_feedbacks = Feedback.objects.filter(
            consultant=consultant
        ).select_related('student__user').order_by('-created_at')[:10]
        
        if consultant_feedbacks:
            total = sum(f.rating for f in consultant_feedbacks)
            average_rating = total / len(consultant_feedbacks)

    context = {
        "consultant": consultant,
        "consultant_name": consultant_user.get_full_name(),
        "pending_verification": pending_verification,
        "approved_verification": approved_verification,
        "rejected_verification": rejected_verification,
        "total_students": total_students,
        "total_appointments": total_appointments,
        "appointments": confirmed_appointments,
        "students": assigned_students,
        "pending_appointments": pending_appointments,
        "cancelled_appointments": cancelled_appointments,
        "market_listing": market_listing,
        "consultant_feedbacks": consultant_feedbacks,
        "average_rating": average_rating,
        "avatar_url": avatar_url,
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
            appointment.status = 'rejected' 
            appointment.save()
            messages.warning(
                request,
                f"Appointment with {appointment.student.user.get_full_name()} rejected."
            )

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

from django.utils import timezone

@login_required
def consultant_history_view(request):
    consultant_user = request.user
    
    try:
        consultant = Consultant.objects.get(user=consultant_user)
    except Consultant.DoesNotExist:
        return render(request, "ConsultApp/error.html", {"message": "Consultant record not found."})

    now = timezone.now().date()
    current_time = timezone.now().time()
    
    active_appts = Appointment.objects.filter(consultant=consultant, status='confirmed')
    
    for appt in active_appts:
        if appt.date < now or (appt.date == now and appt.time < current_time):
            appt.status = 'completed'
            appt.save()
            student = appt.student
            student.sessions_completed += 1
            student.save()

    appointments = Appointment.objects.filter(
        consultant=consultant,
        status__in=['completed', 'cancelled', 'disputed', 'pending_student_review', 'rejected']
    ).select_related('student__user').order_by('-date', '-time')
    
    for appt in appointments:
        appt.was_disputed = (appt.status == 'cancelled' and appt.student_dispute_remark)

    context = {"appointments": appointments}
    return render(request, "ConsultApp/consultant-history.html", context)

@login_required
def consultant_students_view(request):
    try:
        consultant = Consultant.objects.get(user=request.user)
        students = list(Student.objects.filter(
            student_appointments__consultant=consultant,
            student_appointments__status='confirmed' 
        ).select_related('user').distinct()) 
        
        timestamp = int(datetime.now().timestamp())
        
        for student in students:
            url = get_avatar_url(student.user.id)
            if url:
                student.avatar_url = f"{url}?t={timestamp}"
            else:
                student.avatar_url = None
                
    except Consultant.DoesNotExist:
        students = []

    return render(request, "ConsultApp/consultant-students.html", {"students": students})
@login_required
def consultant_profile_view(request):
    user = request.user
    profile, created = Consultant.objects.get_or_create(user=user)
    base_avatar_url = get_avatar_url(user.id)
    avatar_url = None
    if base_avatar_url:
        timestamp = request.session.get('avatar_version', int(datetime.now().timestamp()))
        avatar_url = f"{base_avatar_url}?t={timestamp}"
        
    EXPERTISE_OPTIONS = [
        "Research Methodology", "Data Analysis", "Statistical Analysis", 
        "Qualitative Research", "Quantitative Research", "Machine Learning", 
        "Artificial Intelligence", "Web Development", "Mobile Development", 
        "Database Design", "Cybersecurity", "Network Administration", 
        "UI/UX Design", "System Analysis", "Software Engineering", "Thesis Writing"
    ]
    
    total_fields = 6  
    completed = 0
    missing_fields = []

    if user.first_name: completed += 1
    else: missing_fields.append("First Name")

    if user.last_name: completed += 1
    else: missing_fields.append("Last Name")

    if user.email: completed += 1
    else: missing_fields.append("Email Address")

    if profile.contact_number: completed += 1
    else: missing_fields.append("Contact Number")

    if profile.expertise: completed += 1
    else: missing_fields.append("Expertise")

    if profile.workplace: completed += 1
    else: missing_fields.append("Workplace")

    if profile.is_verified:
        completed += 1
        total_fields += 1
    else:
        missing_fields.append("Verification Status")

    completion_percentage = int((completed / total_fields) * 100)

    if request.method == "POST":
        upload_error_occurred = False

        if "remove_avatar" in request.POST:
            try:
                file_path = f"{user.id}/profile.png"
                supabase.storage.from_("avatars").remove([file_path])
                request.session['avatar_version'] = int(datetime.now().timestamp())
            except Exception as e:
                messages.error(request, f"Failed to remove image: {e}", extra_tags="general_error")
        
        if "avatar_upload" in request.FILES and supabase:
            uploaded_file = request.FILES["avatar_upload"]
            
            content_type = getattr(uploaded_file, 'content_type', '')
            if not content_type:
                 content_type, _ = mimetypes.guess_type(uploaded_file.name)

            if content_type and content_type.startswith('image/'):
                try:
                    file_path = f"{user.id}/profile.png"
                    file_data = uploaded_file.read()

                    supabase.storage.from_("avatars").upload(
                        file_path, 
                        file_data, 
                        file_options={"content-type": content_type, "upsert": "true"}
                    )
                    
                    request.session['avatar_version'] = int(datetime.now().timestamp())
                except Exception as e:
                    messages.error(request, f"Image upload failed: {e}", extra_tags="general_error")
                    upload_error_occurred = True
            else:
                messages.error(request, "File must be a valid image.", extra_tags="general_error")
                upload_error_occurred = True

        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        contact_number = request.POST.get("contact_number", "").strip()
        workplace = request.POST.get("workplace", "").strip()
        expertise_list = request.POST.getlist("expertise")
        expertise_str = ", ".join(expertise_list)
        
        errors = False

        is_valid_name, name_error = validate_name(full_name)
        if not is_valid_name:
            messages.error(request, name_error, extra_tags="full_name_error")
            errors = True

        if not email:
            messages.error(request, "Email cannot be empty.", extra_tags="email_error")
            errors = True
        elif User.objects.filter(email=email).exclude(pk=user.pk).exists():
            messages.error(request, "This email is already in use by another account.", extra_tags="email_error")
            errors = True

        if contact_number:
            if not re.match(r'^09[0-9]{9}$', contact_number):
                messages.error(request, "Contact number must be exactly 11 digits starting with 09 (e.g., 09123456789).", extra_tags="contact_number_error")
                errors = True

        if len(expertise_str) > 1000: 
            messages.error(request, "Too many expertise selected.", extra_tags="expertise_error")
            errors = True
        if not expertise_list:
            messages.error(request, "Please select at least one expertise.", extra_tags="expertise_error")
            errors = True

        is_valid_work, work_error = validate_text_field(workplace, "Workplace", max_length=150)
        if not is_valid_work:
            messages.error(request, work_error, extra_tags="workplace_error")
            errors = True

        if errors:
            return redirect("consultant_profile")
        
        try:
            name_parts = full_name.split()
            if len(name_parts) == 1:
                user.first_name = name_parts[0].title()
                user.last_name = ""
            else:
                user.first_name = " ".join(name_parts[:-1]).title()
                user.last_name = name_parts[-1].title()
            user.email = email
            user.save()

            profile.contact_number = contact_number
            profile.expertise = expertise_str
            profile.workplace = workplace
            profile.save()

            if not upload_error_occurred:
                messages.success(request, "Profile updated successfully!", extra_tags="success")
            else:
                 messages.warning(request, "Info updated, but image upload failed.", extra_tags="general_error")

            return redirect("consultant_profile")

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}", extra_tags="general_error")
            return redirect("consultant_profile")
    
    current_expertise_list = []
    if profile.expertise:
        current_expertise_list = [x.strip() for x in profile.expertise.split(',')]

    context = {
        "user": user,
        "profile": profile,
        "completion_percentage": completion_percentage,
        "missing_fields": missing_fields,
        "avatar_url": avatar_url,
        "expertise_options": EXPERTISE_OPTIONS, 
        "current_expertise_list": current_expertise_list, 
    }
    return render(request, "ConsultApp/consultant-profile.html", context)

@login_required
def consultant_verification_view(request):
    consultant_user = request.user
    consultant, created = Consultant.objects.get_or_create(user=consultant_user)

    if consultant.is_verified:
        messages.info(request, "You are already a verified consultant!")
        return redirect('consultant_dashboard')

    has_pending_verification = Verification.objects.filter(
        consultant=consultant_user, status='pending'
    ).exists()

    EXPERTISE_OPTIONS = [
        "Research Methodology", "Data Analysis", "Statistical Analysis", 
        "Qualitative Research", "Quantitative Research", "Machine Learning", 
        "Artificial Intelligence", "Web Development", "Mobile Development", 
        "Database Design", "Cybersecurity", "Network Administration", 
        "UI/UX Design", "System Analysis", "Software Engineering", "Thesis Writing"
    ]

    if request.method == "POST":
        if has_pending_verification:
            messages.warning(request, "You already have a verification request under review.")
            return redirect('consultant_dashboard')

        full_name = request.POST.get("fullName", "").strip()
        contact = request.POST.get("contact", "").strip()
        expertise_list = request.POST.getlist("expertise")
        workplace = request.POST.get("workplace", "").strip()
        qualification = request.POST.get("qualification", "").strip()
        bio = request.POST.get("bio", "").strip()
        valid_id = request.FILES.get("validId")
        license_doc = request.FILES.get("license")
        profile_photo = request.FILES.get("profilePhoto")
        
        expertise_str = ", ".join(expertise_list)
        
        field_errors = {} 

        # Validate Name
        is_valid_name, name_msg = validate_name(full_name)
        if not is_valid_name:
            field_errors['fullName'] = name_msg

        # Validate Contact
        is_valid_contact, contact_msg = validate_contact(contact)
        if not is_valid_contact:
            field_errors['contact'] = contact_msg

        # Validate Workplace
        is_valid_work, work_msg = validate_text_field(workplace, "Workplace", max_length=150)
        if not is_valid_work:
            field_errors['workplace'] = work_msg

        # Validate Qualification
        is_valid_qual, qual_msg = validate_text_field(qualification, "Qualification", max_length=500)
        if not is_valid_qual:
            field_errors['qualification'] = qual_msg

        # Validate Expertise
        is_valid_exp, exp_msg = validate_expertise_list(expertise_str, max_length=1000)
        if not is_valid_exp:
            field_errors['expertise'] = exp_msg

        # Validate Files
        uploaded_files = {'validId': valid_id, 'license': license_doc, 'profilePhoto': profile_photo}
        files_present = [f for f in uploaded_files.values() if f]

        if not files_present:
            field_errors['validId'] = "Please upload at least one document."
        else:
            for field_name, file_obj in uploaded_files.items():
                if file_obj:
                    if file_obj.size > 10 * 1024 * 1024:
                        field_errors[field_name] = f"File too large (Max 10MB)."
                    elif file_obj.content_type not in ['image/jpeg', 'image/png', 'application/pdf']:
                        field_errors[field_name] = f"Invalid format (JPG, PNG, PDF only)."

        if field_errors:
            submitted_data = {
                'contact': contact, 'workplace': workplace, 
                'qualification': qualification, 'bio': bio, 
                'expertise_list': expertise_list
            }
            return render(request, "ConsultApp/consultant-verification.html", {
                'has_pending_verification': has_pending_verification,
                'user_full_name': full_name or consultant_user.get_full_name(),
                'submitted_data': submitted_data,
                'expertise_options': EXPERTISE_OPTIONS,
                'field_errors': field_errors 
            })

        try:
            consultant.contact_number = contact
            consultant.expertise = expertise_str
            consultant.workplace = workplace
            consultant.save()
            
            Verification.objects.create(
                consultant=consultant_user,
                qualification=qualification,
                bio=bio,
                valid_id=valid_id,        
                license=license_doc,        
                profile_photo=profile_photo, 
                status='pending',
            )
            messages.success(request, "Verification submitted successfully! Please wait for admin approval.")
            return redirect('consultant_dashboard')

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}")
            return redirect('consultant_verification')

    prefilled_data = {}
    if consultant.contact_number:
        prefilled_data['contact'] = consultant.contact_number
    if consultant.workplace:
        prefilled_data['workplace'] = consultant.workplace
    
    current_expertise_list = []
    if consultant.expertise:
        current_expertise_list = [x.strip() for x in consultant.expertise.split(',')]
        prefilled_data['expertise_list'] = current_expertise_list

    context = {
        'has_pending_verification': has_pending_verification,
        'user_full_name': consultant_user.get_full_name(),
        'submitted_data': prefilled_data,
        'expertise_options': EXPERTISE_OPTIONS,
        'current_expertise_list': current_expertise_list
    }

    return render(request, "ConsultApp/consultant-verification.html", context)

@login_required
def consultant_market(request):
    EXPERTISE_OPTIONS = [
        "Research Methodology", "Data Analysis", "Statistical Analysis", 
        "Qualitative Research", "Quantitative Research", "Machine Learning", 
        "Artificial Intelligence", "Web Development", "Mobile Development", 
        "Database Design", "Cybersecurity", "Network Administration", 
        "UI/UX Design", "System Analysis", "Software Engineering", "Thesis Writing"
    ]
    meeting_places_options = [
        "Online (Zoom)",
        "Online (Google Meet)",
        "Online (Microsoft Teams)",
        "CIT Campus",
        "Coffee Shop",
        "Library",
        "Consultant Office"
    ]
    try:
        consultant = Consultant.objects.get(user=request.user)
    except Consultant.DoesNotExist:
        messages.error(request, "Consultant profile not found.")
        return redirect('consultant_dashboard')

    if not consultant.is_verified:
        messages.error(request, "You must be verified to register your availability.")
        return redirect('consultant_dashboard')

    verification = Verification.objects.filter(
        consultant=request.user,
        status='approved'
    ).order_by('-reviewed_at').first()

    market_listing = Market.objects.filter(consultant=consultant).first()

    if request.method == "POST":
        expertise_list = request.POST.getlist("expertise")
        days_list = request.POST.getlist("available_days")
        profession = request.POST.get("profession", "").strip()
        workplace = request.POST.get("workplace", "").strip()
        available_from_str = request.POST.get("available_from", "").strip()
        available_to_str = request.POST.get("available_to", "").strip()
        rate_per_hour = request.POST.get("rate_per_hour", "").strip()
        meeting_place = request.POST.get("meeting_place", "").strip()
        description = request.POST.get("description", "").strip()

        expertise_str = ", ".join(expertise_list) if expertise_list else ""
        days_str = ",".join(days_list) if days_list else ""

        errors = False

        if not profession:
            messages.error(request, "Profession is required.")
            errors = True
        
        if not workplace:
            messages.error(request, "Workplace is required.")
            errors = True

        if not expertise_list:
            messages.error(request, "Please select at least one area of expertise.")
            errors = True
        
        if not days_list:
            messages.error(request, "Please select at least one available day.")
            errors = True

        available_from = None
        available_to = None
        try:
            available_from = datetime.strptime(available_from_str, "%H:%M").time()
            available_to = datetime.strptime(available_to_str, "%H:%M").time()
            if available_from >= available_to:
                messages.error(request, "End time must be after Start time.")
                errors = True
        except ValueError:
            messages.error(request, "Invalid time format.")
            errors = True

        rate = 0
        try:
            rate = int(rate_per_hour)
            if rate < 100 or rate > 10000:
                messages.error(request, "Rate must be between ₱100 and ₱10,000.")
                errors = True
        except ValueError:
            messages.error(request, "Invalid rate amount.")
            errors = True

        if errors:
            submitted_data = {
                'expertise_list': expertise_list,
                'days_list': days_list,
                'profession': profession,
                'workplace': workplace,
                'available_from': available_from_str,
                'available_to': available_to_str,
                'rate_per_hour': rate_per_hour,
                'meeting_place': meeting_place,
                'description': description
            }
            return render(request, "ConsultApp/consultant-market.html", {
                'market_listing': market_listing, 
                'submitted_data': submitted_data,
                'verification': verification,
                'consultant': consultant,
                'expertise_options': EXPERTISE_OPTIONS, 
                'days_options': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            })

        consultant.workplace = workplace
        consultant.expertise = expertise_str
        consultant.save()

        if market_listing:
            market_listing.profession = profession
            market_listing.available_from = available_from
            market_listing.available_to = available_to
            market_listing.available_days = days_str
            market_listing.rate_per_hour = rate
            market_listing.meeting_place = meeting_place
            market_listing.description = description
            market_listing.is_active = True
            market_listing.save()
            messages.success(request, "✅ Market listing updated successfully!")
        else:
            Market.objects.create(
                consultant=consultant,
                profession=profession,
                available_from=available_from,
                available_to=available_to,
                available_days=days_str,
                rate_per_hour=rate,
                meeting_place=meeting_place,
                description=description,
                is_active=True,
            )
            messages.success(request, "✅ You are now listed in the market!")
        
        return redirect('consultant_dashboard')
    
    submitted_data = {}
    if market_listing:
        submitted_data = {
            'expertise_list': [x.strip() for x in consultant.expertise.split(',')] if consultant.expertise else [],
            'days_list': [x.strip() for x in market_listing.available_days.split(',')] if market_listing.available_days else [],
            'profession': market_listing.profession,
            'workplace': consultant.workplace, 
            'available_from': market_listing.available_from.strftime("%H:%M") if market_listing.available_from else "",
            'available_to': market_listing.available_to.strftime("%H:%M") if market_listing.available_to else "",
            'rate_per_hour': market_listing.rate_per_hour,
            'meeting_place': market_listing.meeting_place,
            'description': market_listing.description
        }
    else:
        submitted_data['profession'] = verification.qualification if verification else "" 
        submitted_data['workplace'] = consultant.workplace
        if consultant.expertise:
             submitted_data['expertise_list'] = [x.strip() for x in consultant.expertise.split(',')]

    context = {
        'market_listing': market_listing,
        'submitted_data': submitted_data,
        'verification': verification,
        'consultant': consultant,
        'expertise_options': EXPERTISE_OPTIONS, 
        'days_options': ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'],
        'meeting_places_options': meeting_places_options,
    }
    return render(request, "ConsultApp/consultant-market.html", context)

@login_required
@require_POST
def toggle_market_status(request, market_id):
    try:
        consultant = Consultant.objects.get(user=request.user)
        market_listing = get_object_or_404(Market, id=market_id, consultant=consultant)
        
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

    timestamp = request.session.get('avatar_version', int(datetime.now().timestamp()))
    
    base_avatar_url = get_avatar_url(request.user.id)
    avatar_url = None
    
    if base_avatar_url:
        avatar_url = f"{base_avatar_url}?t={timestamp}"

    pending_consultant_ids = set(Appointment.objects.filter(
        student=student, 
        status='pending'
    ).values_list('consultant__user__id', flat=True))

    upcoming_sessions = Appointment.objects.filter(
        student=student, status__in=["confirmed", "pending"]
    ).order_by("date")[:5]

    pending_reviews = Appointment.objects.filter(
        student=student,
        status='pending_student_review'
    ).select_related('consultant__user').order_by('date')

    query = request.GET.get("q", "").strip()

    consultants_qs = Market.objects.select_related("consultant__user").filter(
        consultant__is_verified=True,
        is_active=True,
    )

    if query:
        consultants_qs = consultants_qs.filter(
            Q(consultant__user__first_name__icontains=query) |
            Q(consultant__user__last_name__icontains=query) |
            Q(consultant__expertise__icontains=query) |
            Q(profession__icontains=query)
        )
    else:
        consultants_qs = consultants_qs.order_by("?")[:3]

    recommended_consultants = list(consultants_qs)

    for market in recommended_consultants:
        c_url = get_avatar_url(market.consultant.user.id)
        if c_url:
            market.consultant.avatar_url = f"{c_url}?t={timestamp}"
        else:
            market.consultant.avatar_url = None

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
        "pending_reviews": pending_reviews, 
        "stats": stats,
        "query": query,
        "avatar_url": avatar_url,
        "pending_consultant_ids": pending_consultant_ids,
    }

    return render(request, "ConsultApp/student-dashboard.html", context)

@login_required
def student_profile_view(request):
    student = Student.objects.get(user=request.user)
    user = request.user
    base_avatar_url = get_avatar_url(user.id)
    avatar_url = None
    if base_avatar_url:
        timestamp = request.session.get('avatar_version', int(datetime.now().timestamp()))
        avatar_url = f"{base_avatar_url}?t={timestamp}"

    total_fields = 5
    completed = 0
    missing_fields = []

    if user.first_name: completed += 1
    else: missing_fields.append("First Name")

    if user.last_name: completed += 1
    else: missing_fields.append("Last Name")

    if student.student_department: completed += 1
    else: missing_fields.append("Department")

    if student.student_program: completed += 1
    else: missing_fields.append("Program")

    if student.student_year_level and student.student_year_level > 0:
        completed += 1
    else:
        missing_fields.append("Year Level")

    completion_percentage = int((completed / total_fields) * 100)

    if request.method == "POST":
        if request.POST.get("delete_avatar") == "true":
            try:
                file_path = f"{user.id}/profile.png"
                supabase.storage.from_("avatars").remove([file_path])
                
                request.session['avatar_version'] = int(datetime.now().timestamp())
                
                messages.success(request, "Profile photo removed.", extra_tags="success")
                return redirect("student_profile")
            except Exception as e:
                messages.error(request, f"Failed to remove photo: {e}", extra_tags="general_error")
                return redirect("student_profile")
            
        upload_error_occurred = False
        if "avatar_upload" in request.FILES and supabase:
            uploaded_file = request.FILES["avatar_upload"]
            
            content_type = getattr(uploaded_file, 'content_type', '')
            if not content_type:
                 content_type, _ = mimetypes.guess_type(uploaded_file.name)

            if content_type and content_type.startswith('image/'):
                try:
                    file_path = f"{user.id}/profile.png"
                    file_data = uploaded_file.read()

                    supabase.storage.from_("avatars").upload(
                        file_path, 
                        file_data, 
                        file_options={"content-type": content_type, "upsert": "true"}
                    )
                    
                    request.session['avatar_version'] = int(datetime.now().timestamp())
                except Exception as e:
                    messages.error(request, f"Image upload failed: {e}", extra_tags="general_error")
                    upload_error_occurred = True 
            else:
                messages.error(request, "File must be a valid image.", extra_tags="general_error")
                upload_error_occurred = True

        full_name = request.POST.get("fullName", "").strip()
        department = request.POST.get("department", "").strip()
        program = request.POST.get("program", "").strip()
        year_level = request.POST.get("yearLevel", "0")
        errors = False

        # Validate name
        is_valid_name, name_error = validate_name(full_name)
        if not is_valid_name:
            messages.error(request, name_error, extra_tags="full_name_error")
            errors = True
            
        user.first_name = full_name.split(" ")[0]
        if len(full_name.split(" ")) > 1:
            user.last_name = " ".join(full_name.split(" ")[1:])
        user.save()

        # Validate department
        is_valid_dept, dept_error = validate_text_field(department, "Department", max_length=100)
        if not is_valid_dept:
            messages.error(request, dept_error, extra_tags="department_error")
            errors = True

        # Validate program
        is_valid_prog, prog_error = validate_text_field(program, "Program", max_length=150)
        if not is_valid_prog:
            messages.error(request, prog_error, extra_tags="program_error")
            errors = True

        # Validate year level
        try:
            year_level_int = int(year_level)
            if year_level_int < 1 or year_level_int > 6:
                messages.error(request, "Please select a valid year level (1-6).", extra_tags="year_level_error")
                errors = True
        except ValueError:
            messages.error(request, "Invalid year level format.", extra_tags="year_level_error")
            errors = True

        if errors:
            return redirect("student_profile")
        
        try:
            name_parts = full_name.split()
            if len(name_parts) == 1:
                user.first_name = name_parts[0].title()
                user.last_name = ""
            else:
                user.first_name = " ".join(name_parts[:-1]).title()
                user.last_name = name_parts[-1].title()
            user.save()

            student.student_department = department
            student.student_program = program
            student.student_year_level = year_level_int
            student.save()
            if not upload_error_occurred:
                messages.success(request, "Profile updated successfully!", extra_tags="success")
            else:
                messages.warning(request, "Profile info updated, but image upload failed.", extra_tags="general_error")         
            return redirect("student_profile")

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}", extra_tags="general_error")
            return redirect("student_profile")

    context = {
        "student": student,
        "completion_percentage": completion_percentage,
        "missing_fields": missing_fields,
        "avatar_url": avatar_url,
    }
    return render(request, "ConsultApp/student-profile.html", context)

@login_required
def student_history_view(request):
    student = Student.objects.filter(user=request.user).first()
    if not student:
        return render(request, "ConsultApp/error.html", {"message": "Student record not found."})

    now = timezone.now().date()
    current_time = timezone.now().time()
    
    potential_updates = Appointment.objects.filter(
        student=student, 
        status__in=["pending", "confirmed"]
    )

    for appt in potential_updates:
        if appt.date < now or (appt.date == now and appt.time < current_time):
            appt.status = "completed"
            appt.save()
            
            student.sessions_completed += 1
            student.save()

    appointments = Appointment.objects.filter(
        student=student,
        status__in=['completed', 'cancelled', 'disputed', 'rejected']
    ).select_related('consultant__user', 'feedback').order_by('-date', '-time')
    
    for appt in appointments:
        appt.was_disputed = (appt.status == 'cancelled' and appt.student_dispute_remark)

    consultants = Consultant.objects.select_related('user').all()

    context = {"appointments": appointments, "consultants": consultants}
    return render(request, "ConsultApp/student-history.html", context)

@login_required
def submit_feedback(request):
    if request.method == "POST":
        student = Student.objects.filter(user=request.user).first()
        if not student:
            messages.error(request, "Student profile not found.")
            return redirect('student_history')
        
        appointment_id = request.POST.get('appointment_id')
        rating = request.POST.get('rating')
        comment = request.POST.get('comment', '').strip()

        try:
            appointment = Appointment.objects.get(
                id=appointment_id,
                student=student,
                status='completed'
            )
            
            if hasattr(appointment, 'feedback'):
                messages.warning(request, "You have already submitted feedback for this session.")
                return redirect('student_history')
            
            rating_int = int(rating)
            if rating_int < 1 or rating_int > 5:
                messages.error(request, "Please provide a valid rating (1-5 stars).")
                return redirect('student_history')
            
            from .models import Feedback
            Feedback.objects.create(
                appointment=appointment,
                student=student,
                consultant=appointment.consultant,
                rating=rating_int,
                comment=comment
            )
            
            messages.success(request, "✅ Thank you for your feedback!")
            return redirect('student_history')
            
        except Appointment.DoesNotExist:
            messages.error(request, "Appointment not found or cannot be reviewed.")
            return redirect('student_history')
        except ValueError:
            messages.error(request, "Invalid rating value.")
            return redirect('student_history')
    
    return redirect('student_history')

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
                
                student.sessions_completed += 1
                student.save()

    active_appointments = Appointment.objects.filter(
        student=student,
        status__in=["pending", "confirmed", "pending_student_review", "disputed"]
    ).order_by('date', 'time')

    consultants = Consultant.objects.all()

    return render(request, "ConsultApp/student-appointments.html", {
        "appointments": active_appointments,
        "consultants": consultants
    })

@login_required
def book_appointment(request, consultant_id=None):
    def get_market_for_consultant(consultant_obj):
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

    def get_unavailable_dates(market_obj):
        dates = []
        if not market_obj:
            return dates
        
        today_date = timezone.localdate()
        available_days_list = [day.strip().lower() for day in market_obj.get_available_days_list]
        
        for i in range(60):
            check_date = today_date + timedelta(days=i)
            day_name = check_date.strftime('%A').lower()
            if available_days_list and day_name not in available_days_list:
                dates.append(check_date.isoformat())
        return dates

    def attach_avatar(person, timestamp):
        try:
            person.avatar_url = None 
        except Exception as e:
            print(f"Error checking avatar for {person.user.id}: {e}")
            person.avatar_url = None

    student = Student.objects.filter(user=request.user).first()
    if not student:
        messages.error(request, "Student profile not found.")
        return redirect('student_dashboard')

    consultant = None
    market = None
    timestamp = int(datetime.now().timestamp())

    target_consultant_id = consultant_id or request.POST.get("consultant_id")
    if target_consultant_id:
        try:
            consultant = Consultant.objects.get(user__id=target_consultant_id, is_verified=True)
            market = get_market_for_consultant(consultant)
            attach_avatar(consultant, timestamp)
            
            if not market:
                messages.error(request, "⚠️ This consultant is currently unavailable.")
                return redirect('student_dashboard')
        except (Consultant.DoesNotExist, ValueError):
            messages.error(request, "Consultant not found.")
            return redirect('student_dashboard')
        
    if consultant and student:
        has_pending = Appointment.objects.filter(
            student=student,
            consultant=consultant,
            status='pending'
        ).exists()

        if has_pending:
            consultants_with_market = Consultant.objects.filter(
                is_verified=True, market_listings__is_active=True
            ).select_related("user").distinct()
            
            for c in consultants_with_market:
                attach_avatar(c, timestamp)
            
            slots = []
            if market:
                slots = generate_hourly_slots(market.available_from, market.available_to)

            context = {
                "consultant": consultant,
                "market": market,
                "consultants": consultants_with_market,
                "slots": slots,
                "today": timezone.localdate().isoformat(),
                "tomorrow": (timezone.localdate() + timedelta(days=1)).isoformat(),
                "unavailable_dates": "[]",
                "trigger_pending_modal": True,
                "modal_message": f"You already have a pending appointment with {consultant.user.get_full_name()}. Please wait for their response before booking another."
            }
            return render(request, "ConsultApp/book_appointment.html", context)

    consultants_with_market = Consultant.objects.filter(
        is_verified=True,
        market_listings__is_active=True
    ).select_related("user").distinct()

    for c in consultants_with_market:
        attach_avatar(c, timestamp)

    if request.method == "POST":
        if not consultant:
            messages.error(request, "⚠️ Please select a consultant.")
            return redirect('student_dashboard') 

        date_str = request.POST.get("date", "").strip()
        start_time_str = request.POST.get("start_time", "").strip()
        duration_hours_str = request.POST.get("duration_hours", "1")
        topic = request.POST.get("topic", "").strip()
        research_title = request.POST.get("research_title", "").strip()

        def get_error_context():
            slots = generate_hourly_slots(market.available_from, market.available_to)
            unavailable_dates = []
            if market:
                unavailable_dates = get_unavailable_dates(market)
            
            return {
                "consultant": consultant,
                "market": market,
                "consultants": consultants_with_market,
                "slots": slots,
                "today": timezone.localdate().isoformat(),
                "tomorrow": (timezone.localdate() + timedelta(days=1)).isoformat(),
                "unavailable_dates": json.dumps(unavailable_dates),
                "submitted_data": { 
                    "date": date_str, "start_time": start_time_str, 
                    "topic": topic, "research_title": research_title 
                }
            }

        if not date_str or not start_time_str or not topic:
            messages.error(request, "⚠️ Please fill in all required fields.")
            return render(request, "ConsultApp/book_appointment.html", get_error_context())

        try:
            duration_hours = int(duration_hours_str)
            if duration_hours < 1: duration_hours = 1
        except ValueError:
            duration_hours = 1

        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d").date()
            start_time_obj = datetime.strptime(start_time_str, "%H:%M").time()
        except ValueError:
            messages.error(request, "⚠️ Invalid date or time format.")
            return render(request, "ConsultApp/book_appointment.html", get_error_context())

        today = timezone.localdate()
        
        if date_obj < today:
            messages.error(request, "⚠️ Cannot book dates in the past.")
            return render(request, "ConsultApp/book_appointment.html", get_error_context())

        if date_obj == today:
            current_time = timezone.localtime().time()
            if start_time_obj <= current_time:
                messages.error(request, "⚠️ For same-day bookings, please select a future time.")
                return render(request, "ConsultApp/book_appointment.html", get_error_context())

        start_dt = datetime.combine(date_obj, start_time_obj)
        end_dt = start_dt + timedelta(hours=duration_hours)
        end_time_obj = end_dt.time()
        student_conflicts = Appointment.objects.filter(
            student=student,
            date=date_obj,
            status__in=['pending', 'confirmed']
        )

        for ap in student_conflicts:
            ap_start = datetime.combine(date_obj, ap.time)
            ap_end = ap_start + timedelta(minutes=ap.duration_minutes or 60)
            
            if (start_dt < ap_end) and (end_dt > ap_start):
                messages.error(request, f"⚠️ You are already busy from {ap.time.strftime('%H:%M')} to {ap_end.strftime('%H:%M')}.")
                return render(request, "ConsultApp/book_appointment.html", get_error_context())

        day_name = date_obj.strftime('%A').lower()
        available_days_list = market.get_available_days_list
        available_days_lower = [day.strip().lower() for day in available_days_list]
        
        if not available_days_lower or day_name not in available_days_lower:
            messages.error(request, f"⚠️ This consultant is unavailable on {date_obj.strftime('%A')}s.")
            return render(request, "ConsultApp/book_appointment.html", get_error_context())

        available_from = market.available_from
        available_to = market.available_to

        if not (available_from <= start_time_obj and end_time_obj <= available_to):
            messages.error(request, f"⚠️ Selected time is outside available hours ({available_from.strftime('%I:%M %p')} - {available_to.strftime('%I:%M %p')}).")
            return render(request, "ConsultApp/book_appointment.html", get_error_context())

        conflicts = []
        existing_appts = Appointment.objects.filter(
            consultant=consultant, 
            date=date_obj,
            status__in=['pending', 'confirmed']
        )
        for ap in existing_appts:
            ap_start = datetime.combine(date_obj, ap.time)
            ap_end = ap_start + timedelta(minutes=ap.duration_minutes or 60)
            if (start_dt < ap_end) and (end_dt > ap_start):
                conflicts.append(ap)
        
        if conflicts:
            messages.error(request, "⚠️ This time slot is already booked.")
            return render(request, "ConsultApp/book_appointment.html", get_error_context())

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
            messages.success(request, f"✅ Booking confirmed! Request sent to {consultant_name}.")
            return redirect('student_dashboard')
            
        except Exception as e:
            print(e)
            messages.error(request, "⚠️ Database error. Unable to book.")
            return render(request, "ConsultApp/book_appointment.html", get_error_context())

    slots = []
    unavailable_dates = []
    today = timezone.localdate()
    tomorrow = today + timedelta(days=1)
    
    if market and consultant:
        slots = generate_hourly_slots(market.available_from, market.available_to)
        unavailable_dates = get_unavailable_dates(market)

    return render(request, "ConsultApp/book_appointment.html", {
        "consultant": consultant,
        "market": market,
        "consultants": consultants_with_market,
        "slots": slots,
        "today": today.isoformat(),
        "tomorrow": tomorrow.isoformat(),
        "unavailable_dates": json.dumps(unavailable_dates),
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

@login_required
def consultant_details(request, consultant_user_id):
    try:
        consultant = Consultant.objects.get(user__id=consultant_user_id)
        market = Market.objects.filter(consultant=consultant, is_active=True).first()
        
        if not market:
            messages.error(request, "This consultant is not currently available.")
            return redirect('student_dashboard')
        
        from .models import Feedback
        feedbacks = Feedback.objects.filter(
            consultant=consultant
        ).select_related('student__user').order_by('-created_at')
        
        average_rating = 0
        if feedbacks.exists():
            total = sum(f.rating for f in feedbacks)
            average_rating = total / feedbacks.count()
        
        context = {
            'consultant': consultant,
            'market': market,
            'feedbacks': feedbacks,
            'average_rating': average_rating,
        }
        
        return render(request, 'ConsultApp/consultant-details.html', context)
        
    except Consultant.DoesNotExist:
        messages.error(request, "Consultant not found.")
        return redirect('student_dashboard')    

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
    disputed_appointments = Appointment.objects.filter(
        status='disputed'
    ).select_related('student__user', 'consultant__user').order_by('-disputed_at')

    return render(request, "ConsultApp/admin-dashboard.html", {
        "total_students": total_students,
        "total_consultants": total_consultants,
        "pending_approvals": pending_approvals,
        "active_bookings": active_bookings,
        "recent_users": recent_users,
        "verification_requests": verification_requests,
        "disputed_appointments": disputed_appointments,  
    })

@login_required
@user_passes_test(is_admin)
def admin_students_view(request):
    students = Student.objects.select_related('user').all()
    return render(request, "ConsultApp/admin-students.html", {"students": students})

@login_required
@user_passes_test(is_admin)
def admin_consultants_view(request):
    consultants = Consultant.objects.select_related('user').annotate(
        has_pending_verification=Case(
            When(
                user__verification__status='pending',
                then=Value(True)
            ),
            default=Value(False),
            output_field=BooleanField()
        )
    ).all()
    
    verifications_prefetch = Prefetch(
        'user__verification_set',
        queryset=Verification.objects.order_by('-created_at'),
        to_attr='latest_verification'
    )

    consultants = Consultant.objects.select_related('user').prefetch_related(verifications_prefetch).annotate(
        has_pending_verification=Case(
            When(user__verification__status='pending', then=Value(True)),
            default=Value(False),
            output_field=BooleanField()
        )
    ).all()
    
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
    avatar_path = f"{admin_user.id}/profile.png"
    avatar_url = None

    try:
        base_avatar_url = supabase.storage.from_("avatars").get_public_url(avatar_path)
    except:
        base_avatar_url = None
    if base_avatar_url:
        timestamp = request.session.get('admin_avatar_version', int(datetime.now().timestamp()))
        avatar_url = f"{base_avatar_url}?t={timestamp}"

    
    completed = 0
    total_fields = 4
    missing_fields = []

    if admin_user.first_name: completed += 1
    else: missing_fields.append("First Name")

    if admin_user.last_name: completed += 1
    else: missing_fields.append("Last Name")

    if admin_user.email: completed += 1
    else: missing_fields.append("Email Address")

    if admin_profile.contact_number: completed += 1
    else: missing_fields.append("Contact Number")

    progress_percentage = int((completed / total_fields) * 100)

    if request.method == "POST":
        if request.POST.get("delete_avatar") == "true":
            try:
                supabase.storage.from_("avatars").remove([avatar_path])
                request.session['admin_avatar_version'] = int(datetime.now().timestamp())
                messages.success(request, "Profile photo removed.", extra_tags="success")
                return redirect("admin_profile")
            except Exception as e:
                messages.error(request, f"Failed to remove photo: {e}", extra_tags="general_error")
                return redirect("admin_profile")

        upload_error_occurred = False
        if "avatar_upload" in request.FILES:
            uploaded_file = request.FILES["avatar_upload"]
            content_type = getattr(uploaded_file, 'content_type', '')
            if not content_type:
                 content_type, _ = mimetypes.guess_type(uploaded_file.name)

            if content_type and content_type.startswith('image/'):
                try:
                    file_data = uploaded_file.read()
                    supabase.storage.from_("avatars").upload(
                        avatar_path, 
                        file_data, 
                        file_options={"content-type": content_type, "upsert": "true"}
                    )
                    request.session['admin_avatar_version'] = int(datetime.now().timestamp())
                except Exception as e:
                    messages.error(request, f"Image upload failed: {e}", extra_tags="general_error")
                    upload_error_occurred = True
            else:
                messages.error(request, "File must be a valid image.", extra_tags="general_error")
                upload_error_occurred = True
        

        full_name = request.POST.get("full_name", "").strip()
        email = request.POST.get("email", "").strip()
        contact = request.POST.get("contact", "").strip()
        errors = False

        # Validate name
        is_valid_name, name_error = validate_name(full_name)
        if not is_valid_name:
            messages.error(request, name_error, extra_tags="full_name_error")
            errors = True

        # Validate email
        if not email:
            messages.error(request, "Email cannot be empty.", extra_tags="email_error")
            errors = True
        elif User.objects.filter(email=email).exclude(pk=admin_user.pk).exists():
            messages.error(request, "This email is already in use by another account.", extra_tags="email_error")
            errors = True

        # Validate contact
        if contact:
            if not re.match(r'^09[0-9]{9}$', contact):
                messages.error(request, "Contact number must be exactly 11 digits starting with 09 (e.g., 09123456789).", extra_tags="contact_error")
                errors = True

        if errors:
            return redirect("admin_profile")
        
        try:
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

            if not upload_error_occurred:
                messages.success(request, "Profile updated successfully!", extra_tags="success")
            else:
                messages.warning(request, "Info updated, but image failed to upload.", extra_tags="general_error")

            messages.success(request, "Profile updated successfully!", extra_tags="success")
            return redirect("admin_profile")

        except Exception as e:
            messages.error(request, f"An unexpected error occurred: {e}", extra_tags="general_error")
            return redirect("admin_profile")
        
    context = {
        "admin_name": f"{admin_user.first_name} {admin_user.last_name}".strip(),
        "admin_user": admin_user,
        "admin_email": admin_user.email,
        "admin_contact": admin_profile.contact_number or "Not set",
        "admin_role": "System Administrator",
        "profile_progress": progress_percentage,
        "missing_fields": missing_fields,
        "avatar_url": avatar_url,
    }
    
    return render(request, "ConsultApp/admin-profile.html", context)

@login_required
@user_passes_test(is_admin)
def sync_sessions_completed(request):
    students = Student.objects.all()
    updated_count = 0
    
    for student in students:
        actual_completed = Appointment.objects.filter(
            student=student,
            status='completed'
        ).count()
        
        if student.sessions_completed != actual_completed:
            student.sessions_completed = actual_completed
            student.save()
            updated_count += 1
    
    messages.success(
        request, 
        f"✅ Synced sessions completed for {updated_count} students!"
    )
    return redirect('admin_dashboard')


# 🔹 Verification Details 
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

    try:
        consultant = verification.consultant.consultant

        if verification.contact_number:
            consultant.contact_number = verification.contact_number
        if verification.expertise:
            consultant.expertise = verification.expertise
        if verification.workplace:
            consultant.workplace = verification.workplace
        
        consultant.is_verified = True
        consultant.save()

        verification.status = 'approved'
        verification.reviewed_at = timezone.now() 
        verification.save()

        messages.success(request, f"{verification.consultant.get_full_name()} has been approved and their profile updated.")

    except Consultant.DoesNotExist:
        messages.error(request, "Consultant profile not found.")
    except Exception as e:
        messages.error(request, f"An error occurred: {e}")

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

@login_required
@user_passes_test(is_admin)
def student_profile_admin_view(request, student_id):
    student = get_object_or_404(Student, user__id=student_id)
    user = student.user
    
    context = {
        "student": student,
        "user": user,
        "full_name": user.get_full_name(),
        "email": user.email,
        "department": student.student_department or "N/A",
        "course": student.student_course or "N/A",
        "program": student.student_program or "N/A",
        "year_level": student.student_year_level if student.student_year_level > 0 else "N/A",
        "assigned_consultant": student.assigned_consultant.user.get_full_name() if student.assigned_consultant else "None",
        "sessions_completed": student.sessions_completed,
        "date_joined": user.date_joined,
        "is_active": user.is_active,
    }
    
    return render(request, "ConsultApp/admin-student-details.html", context)

@login_required
@user_passes_test(is_admin)
def consultant_profile_admin_view(request, consultant_id):
    consultant = get_object_or_404(Consultant, user__id=consultant_id)
    user = consultant.user
    
    verification = Verification.objects.filter(
        consultant=user,
        status='approved'
    ).order_by('-reviewed_at').first()
    
    pending_verification = Verification.objects.filter(
        consultant=user,
        status='pending'
    ).order_by('-created_at').first()

    market_listing = Market.objects.filter(consultant=consultant).first()
    
    assigned_students_count = Student.objects.filter(assigned_consultant=consultant).count()
    
    if consultant.is_verified:
        status_context = 'verified'
    elif pending_verification:
        status_context = 'pending'
    elif user.is_active:
        status_context = 'not_verified' 
    else:
        status_context = 'inactive'
    
    context = {
        "consultant": consultant,
        "user": user,
        "full_name": user.get_full_name(),
        "email": user.email,
        "contact_number": consultant.contact_number or "N/A",
        "expertise": consultant.expertise or "N/A",
        "workplace": consultant.workplace or "N/A",
        "is_verified": consultant.is_verified,
        "verification": verification,
        "market_listing": market_listing,
        "assigned_students_count": assigned_students_count,
        "date_joined": user.date_joined,
        "is_active": user.is_active,
        "consultant_status": status_context, 
        "pending_verification": pending_verification,
    }
    
    return render(request, "ConsultApp/admin-consultant-details.html", context)

@login_required
@require_POST
def mark_meeting_status(request, appointment_id):
    consultant = get_object_or_404(Consultant, user=request.user)
    appointment = get_object_or_404(
        Appointment, 
        id=appointment_id, 
        consultant=consultant,
        status='confirmed'
    )
    
    action = request.POST.get('action')
    
    if action == 'completed':
        appointment.consultant_marked_as = 'completed'
        appointment.status = 'pending_student_review'
        appointment.save()
        messages.success(request, "✅ Meeting marked as completed. Awaiting student confirmation.")
    elif action == 'not_completed':
        appointment.consultant_marked_as = 'not_completed'
        appointment.status = 'pending_student_review'
        appointment.save()
        messages.info(request, "Meeting marked as not completed. Student will be notified.")
    else:
        messages.error(request, "Invalid action.")
    
    return redirect('consultant_history')


@login_required
@require_POST
def student_confirm_or_dispute(request, appointment_id):
    student = get_object_or_404(Student, user=request.user)
    appointment = get_object_or_404(
        Appointment,
        id=appointment_id,
        student=student,
        status='pending_student_review'
    )
    
    action = request.POST.get('action')
    
    if action == 'confirm':
        if appointment.consultant_marked_as == 'completed':
            appointment.status = 'completed'
            student.sessions_completed += 1
            student.save()
            messages.success(request, "✅ Meeting confirmed as completed!")
        else:
            appointment.status = 'cancelled'
            messages.info(request, "Meeting confirmed as not completed.")
        appointment.save()
        
    elif action == 'dispute':
        remark = request.POST.get('dispute_remark', '').strip()
        
        if not remark:
            messages.error(request, "Please provide a reason for your dispute.")
            return redirect('student_appointments')
        
        if len(remark) < 10:
            messages.error(request, "Please provide a more detailed explanation (at least 10 characters).")
            return redirect('student_appointments')
        
        appointment.student_dispute_remark = remark
        appointment.status = 'disputed'
        appointment.disputed_at = timezone.now()
        appointment.save()
        
        messages.warning(
            request, 
            "⚠️ Dispute submitted. An administrator will review this case."
        )
    else:
        messages.error(request, "Invalid action.")
    
    return redirect('student_appointments')


@login_required
@user_passes_test(is_admin)
@require_POST
def admin_resolve_dispute(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, status='disputed')
    
    decision = request.POST.get('decision')
    
    if decision == 'mark_completed':
        appointment.status = 'completed'
        student = appointment.student
        student.sessions_completed += 1
        student.save()
        messages.success(request, "✅ Dispute resolved: Meeting marked as completed.")
        
    elif decision == 'mark_not_completed':
        appointment.status = 'cancelled'
        messages.success(request, "Dispute resolved: Meeting marked as not completed.")
        
    else:
        messages.error(request, "Invalid decision.")
        return redirect('admin_dashboard')
    
    appointment.save()
    return redirect('admin_dashboard')

@login_required
@user_passes_test(is_admin)
@require_POST
def admin_resolve_dispute(request, appointment_id):
    appointment = get_object_or_404(Appointment, id=appointment_id, status='disputed')
    
    decision = request.POST.get('decision')
    
    if decision == 'mark_completed':
        appointment.status = 'completed'
        student = appointment.student
        student.sessions_completed += 1
        student.save()
        messages.success(request, "✅ Dispute resolved: Meeting marked as completed.")
        
    elif decision == 'mark_not_completed':
        appointment.status = 'cancelled'
        messages.success(request, "Dispute resolved: Meeting marked as not completed.")
        
    else:
        messages.error(request, "Invalid decision.")
        return redirect('admin_dashboard')
    
    appointment.save()
    return redirect('admin_dashboard')