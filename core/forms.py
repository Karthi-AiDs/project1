from django import forms
from .models import Attendance, Payroll, Material, Vendor, User, TempUserReport
from django.contrib.auth.forms import UserCreationForm

class CustomUserCreationForm(UserCreationForm):
    class Meta:
        model = User
        fields = ['email', 'phone', 'role', 'password1', 'password2']

class AttendanceForm(forms.ModelForm):
    class Meta:
        model = Attendance
        fields = ['date', 'clock_in', 'clock_out', 'gps']

class PayrollForm(forms.ModelForm):
    class Meta:
        model = Payroll
        exclude = ['user','calculated_salary', 'created_at']

class MaterialForm(forms.ModelForm):
    class Meta:
        model = Material
        exclude = ['submitted_by', 'submitted_at']

class VendorForm(forms.ModelForm):
    class Meta:
        model = Vendor
        fields = '__all__'

class TempUserReportForm(forms.ModelForm):
    class Meta:
        model = TempUserReport
        fields = ['site', 'hours', 'work_description']