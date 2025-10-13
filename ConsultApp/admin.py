from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Student, Consultant, Admin


# Custom User Admin
@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('email', 'first_name', 'last_name', 'role', 'is_staff', 'is_active')
    list_filter = ('role', 'is_staff', 'is_active')
    ordering = ('email',)
    search_fields = ('email', 'first_name', 'last_name')

    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal Info', {'fields': ('first_name', 'last_name')}),
        ('Role', {'fields': ('role',)}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important Dates', {'fields': ('last_login', 'date_joined')}),
    )

    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role', 'is_staff', 'is_active'),
        }),
    )

    # Since we removed username, exclude it entirely
    exclude = ('username',)


# Inline profiles for each role
class StudentInline(admin.StackedInline):
    model = Student
    can_delete = False
    verbose_name_plural = 'Student Profile'


class ConsultantInline(admin.StackedInline):
    model = Consultant
    can_delete = False
    verbose_name_plural = 'Consultant Profile'


class AdminInline(admin.StackedInline):
    model = Admin
    can_delete = False
    verbose_name_plural = 'Admin Profile'


# Role-based inline attachment
class CustomUserAdmin(UserAdmin):
    inlines = []

    def get_inlines(self, request, obj):
        if obj and obj.role == 'student':
            return [StudentInline]
        elif obj and obj.role == 'consultant':
            return [ConsultantInline]
        elif obj and obj.role == 'admin':
            return [AdminInline]
        return []


# Re-register User model with custom inline handling
admin.site.unregister(User)
admin.site.register(User, CustomUserAdmin)


# Register role models separately (optional)
@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('user', 'student_year_level', 'student_department', 'student_course', 'student_program')
    search_fields = ('user__email', 'student_course')


@admin.register(Consultant)
class ConsultantAdmin(admin.ModelAdmin):
    list_display = ('user', 'expertise', 'workplace', 'is_verified')
    search_fields = ('user__email', 'expertise')


@admin.register(Admin)
class AdminProfileAdmin(admin.ModelAdmin):
    list_display = ('user', 'contact_number')
    search_fields = ('user__email',)
