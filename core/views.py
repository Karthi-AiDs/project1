from django.shortcuts import render, redirect
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.core.files.storage import FileSystemStorage
from datetime import datetime

from .models import Attendance, Payroll, Vendor, Material
from .forms import AttendanceForm, PayrollForm, VendorForm, MaterialForm

User = get_user_model()
@login_required
def payroll_view(request):
    if request.method == 'POST':
        start_date = request.POST.get('start_date')
        end_date = request.POST.get('end_date')
        total_hours = float(request.POST.get('total_hours'))
        hourly_rate = float(request.POST.get('hourly_rate'))
        location = request.POST.get('location')

        calculated_salary = total_hours * hourly_rate

        Payroll.objects.create(
            user=request.user,
            start_date=start_date,
            end_date=end_date,
            total_hours=total_hours,
            hourly_rate=hourly_rate,
            location=location,
            calculated_salary=calculated_salary
        )
        messages.success(request, "Payroll record created.")
        return redirect('payroll_view')

    payrolls = Payroll.objects.filter(user=request.user)
    return render(request, 'core/payroll.html', {'payrolls': payrolls})


@login_required
def materials_view(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        quantity = request.POST.get('quantity')
        unit = request.POST.get('unit')
        vendor_input = request.POST.get('vendor')
        purchase_date = request.POST.get('purchase_date')
        barcode = request.POST.get('barcode')
        photo = request.FILES.get('photo')

        if vendor_input:
            try:
                vendor = Vendor.objects.get(id=vendor_input)
            except Vendor.DoesNotExist:
                vendor = None
        else:
            vendor = None

        Material.objects.create(
            name=name,
            quantity=quantity,
            unit=unit,
            vendor=vendor,
            purchase_date=purchase_date,
            barcode=barcode,
            photo=photo,
            submitted_by=request.user
        )
        messages.success(request, "Material submitted successfully.")
        print("Material POST received:", name, quantity, vendor)
        return redirect('materials')

    vendors = Vendor.objects.all()
    materials = Material.objects.all()
    return render(request, 'materials.html', {'vendors': vendors, 'materials': materials})

@login_required
def vendor_view(request):
    vendors = Vendor.objects.all()  # Get all vendors
    return render(request, 'vendor.html', {'vendors': vendors})


# ----------------- AUTHENTICATION -----------------

def login_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        selected_role = request.POST.get('role')

        user = authenticate(request, email=email, password=password)
        if user is not None:
            if user.role != selected_role:
                messages.error(request, 'Selected role does not match the user\'s role.')
                return redirect('login')

            login(request, user)

            if selected_role == 'admin':
                return redirect('admin_dashboard')
            elif selected_role == 'engineer':
                return redirect('site_dashboard')
            elif selected_role == 'temp_user':
                return redirect('temp_user_home')
            elif selected_role == 'regular_user':
                return redirect('user_dashboard')
            else:
                messages.error(request, 'Unknown role.')
                return redirect('login')
        else:
            messages.error(request, 'Invalid email or password.')
            return redirect('login')

    return render(request, 'login.html')


def signup_view(request):
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        phone = request.POST.get('phone')
        role = request.POST.get('role')

        if User.objects.filter(email=email).exists():
            messages.error(request, 'Email already exists.')
        else:
            user = User.objects.create_user(
                email=email,
                password=password,
                phone=phone,
                role=role
            )
            messages.success(request, 'Account created! Please login.')
            return redirect('login')

    return render(request, 'login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('login')


# ----------------- DASHBOARDS -----------------

@login_required
def admin_dashboard(request):
    role_counts = [
        User.objects.filter(role='admin').count(),
        User.objects.filter(role='engineer').count(),
        User.objects.filter(role='regular_user').count(),
        User.objects.filter(role='temp_user').count()
    ]
    attendance_data = [10, 20, 30, 25, 40, 50]  # dummy

    return render(request, 'admindash.html', {
        'role_counts': role_counts,
        'attendance_data': attendance_data,
    })

@login_required
def site_dashboard(request):
    return render(request, 'dashboard.html')

@login_required
def user_dashboard(request):
    return render(request, 'userdash.html')

@login_required
def temp_user_home(request):
    return render(request, 'temp_user_home.html')


# ----------------- PROFILE -----------------

@login_required
def update_profile(request):
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('firstName', user.first_name)
        user.last_name = request.POST.get('lastName', user.last_name)
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
            update_session_auth_hash(request, user)
        user.save()
        messages.success(request, "Profile updated successfully.")
    return redirect('settings')


# ----------------- FEATURE MODULES -----------------

@login_required
def add_attendance(request):
    form = AttendanceForm(request.POST or None)
    if form.is_valid():
        attendance = form.save(commit=False)
        attendance.user = request.user
        attendance.save()
        return redirect('site_dashboard')
    return render(request, 'core/form.html', {'form': form, 'title': 'Add Attendance'})


@login_required
def add_material(request):
    form = MaterialForm(request.POST or None, request.FILES or None)
    if form.is_valid():
        material = form.save(commit=False)
        material.submitted_by = request.user
        material.save()
        return redirect('site_dashboard')
    return render(request, 'core/form.html', {'form': form, 'title': 'Add Material'})


@login_required
def add_vendor(request):
    form = VendorForm(request.POST or None)
    if form.is_valid():
        form.save()
        return redirect('site_dashboard')
    return render(request, 'core/form.html', {'form': form, 'title': 'Add Vendor'})


@login_required
def add_payroll(request):
    if request.method == 'POST':
        form = PayrollForm(request.POST)
        if form.is_valid():
            payroll = form.save(commit=False)
            payroll.user = request.user
            # No need to set payroll.is_approved manually if default=False is in model
            payroll.save()
            return redirect('payroll')
    else:
        form = PayrollForm()
    return render(request, 'payroll.html', {'form': form})

# ----------------- MODULE VIEW PAGES -----------------

@login_required
def attendance_view(request):
    return render(request, 'attendance.html')



@login_required
def reports_view(request):
    return render(request, 'reports.html')

@login_required
def payroll_view(request):
    payrolls = Payroll.objects.all()  # shows only current user's records
    return render(request, 'payroll.html', {'payrolls': payrolls})



@login_required
def settings_view(request):
    return render(request, 'settings.html')

def dashboard_view(request):
    return render(request, 'dashboard.html')

def notifications(request):
    return render(request, 'core/notifications.html')