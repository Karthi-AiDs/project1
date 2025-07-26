from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Attendance, Vendor, Material, Payroll, LoginLog, LoginSession, MFAToken, Employee

class UserAdmin(BaseUserAdmin):
    model = User
    list_display = ['email', 'role', 'is_approved', 'is_blocked']
    list_filter = ['role', 'is_approved']
    fieldsets = (
        (None, {'fields': ('email', 'password', 'role')}),
        ('Permissions', {'fields': ('is_staff', 'is_active', 'is_superuser')}),
        ('Approval Info', {'fields': ('is_approved', 'approved_by', 'approved_at')}),
    )
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'password1', 'password2', 'role')}
        ),
    )
    search_fields = ('email',)
    ordering = ('email',)

admin.site.register(User, UserAdmin)
admin.site.register(Employee)
admin.site.register(Attendance)
admin.site.register(Vendor)
admin.site.register(Material)
admin.site.register(Payroll)
admin.site.register(LoginLog)
admin.site.register(LoginSession)
admin.site.register(MFAToken)
