from itertools import count
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.views.decorators.http import require_POST
from django.contrib.auth import authenticate, login, logout, update_session_auth_hash
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.http import HttpResponse, JsonResponse
from django.utils.timezone import now
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from datetime import date
from .models import Attendance, Payroll, Vendor, Material, TempUserReport,Employee,Report
from .forms import TempUserReportForm
from .forms import AttendanceForm, PayrollForm, VendorForm, MaterialForm
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.dateparse import parse_date
from django.contrib.auth.models import User
import json

User = get_user_model()

# ----------------- PAYROLL -----------------
@login_required
def payroll_view(request):
    if request.method == 'POST':
        try:
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')
            total_hours = float(request.POST.get('total_hours'))
            hourly_rate = float(request.POST.get('hourly_rate'))
            location = request.POST.get('location')
            employee_name = request.POST.get('employee_name')
            calculated_salary = total_hours * hourly_rate

            Payroll.objects.create(
                user=request.user,
                employee_name=employee_name,
                start_date=start_date,
                end_date=end_date,
                total_hours=total_hours,
                hourly_rate=hourly_rate,
                location=location,
                calculated_salary=calculated_salary
            )
            messages.success(request, "Payroll record created.")
            return redirect('payroll')
        except Exception as e:
            messages.error(request, f"Error creating payroll: {e}")

    payrolls = Payroll.objects.filter(user=request.user).order_by('-start_date')
    paginator = Paginator(payrolls, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    return render(request, 'payroll.html', {'page_obj': page_obj})


# ----------------- MATERIAL -----------------
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

        vendor = Vendor.objects.filter(id=vendor_input).first() if vendor_input else None

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
        return redirect('materials')

    vendors = Vendor.objects.all()
    materials = Material.objects.all()
    return render(request, 'materials.html', {'vendors': vendors, 'materials': materials})


# ----------------- VENDOR -----------------
@login_required
def vendor_view(request):
    vendors = Vendor.objects.all()
    return render(request, 'vendor.html', {'vendors': vendors})


# ----------------- AUTH -----------------
def login_view(request):
    storage = messages.get_messages(request)
    list(storage) 
    if request.method == 'POST':
        email = request.POST.get('email')
        password = request.POST.get('password')
        selected_role = request.POST.get('role')

        user = authenticate(request, email=email, password=password)
        if user:
            if user.role != selected_role:
                messages.error(request, "Selected role doesn't match.")
                return redirect('login')

            login(request, user)
            if user.role == 'admin':
                return redirect('admin_dashboard')
            elif user.role == 'engineer':
                return redirect('site_dashboard')
            elif user.role == 'regular_user':
                return redirect('user_dashboard')
            elif user.role == 'temp_user':
                return redirect('temp_user_home')
        messages.error(request, 'Invalid credentials')
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
            user = User.objects.create_user(email=email, password=password, phone=phone, role=role)
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
    User = get_user_model()
    total_users = User.objects.count()
    admin_count = User.objects.filter(role='admin').count()
    engineer_count = User.objects.filter(role='engineer').count()
    regular_count = User.objects.filter(role='regular_user').count()
    temp_count = User.objects.filter(role='temp_user').count()

    context = {
        'total_users': total_users,
        'admin_count': admin_count,
        'engineer_count': engineer_count,
        'regular_count': regular_count,
        'temp_count': temp_count,
    }
    return render(request, 'admindash.html', context)


@login_required
def site_dashboard(request):
    return render(request, 'dashboard.html')


@login_required
def user_dashboard(request):
    user = request.user

    try:
        employee = Employee.objects.get(user=user)
    except Employee.DoesNotExist:
        messages.error(request, "No employee profile found. Please contact admin.")
        return redirect('login')  # or 'home' or any other safe fallback view

    # Only reached if employee exists
    attendance_qs = Attendance.objects.filter(user=user)
    attendance_present = 25
    attendance_total = 30
    absent_days = 5

    attendance_percent = (attendance_present / attendance_total * 100) if attendance_total > 0 else 0
    recent_reports = Report.objects.filter(user=user).order_by('-created_at')[:3] 

    context = {
        'user': user,
        'employee': employee,
        'attendance_present': attendance_present,
        'attendance_total': attendance_total,
        'absent_days': absent_days,
        'attendance_percent': round(attendance_percent, 2),
        'notifications': [],
        'reports': recent_reports,
    }

    return render(request, 'userdash.html', context)

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


# ----------------- ADD MODULES -----------------
@login_required
def add_attendance(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        gps_location = request.POST.get('gps_location')

        today = date.today()
        user = request.user

        attendance, created = Attendance.objects.get_or_create(user=user, date=today)

        if action == 'in' and not attendance.clock_in:
            attendance.clock_in = request.POST.get('clock_in_time')
            attendance.gps = gps_location
            messages.success(request, "You Checked In Successfully.")
        elif action == 'out' and not attendance.clock_out:
            attendance.clock_out = request.POST.get('clock_out_time')
            attendance.gps = gps_location
            messages.success(request, "You Checked Out Successfully")
        else:
            messages.warning(request, "You've already completed this action.")

        attendance.save()
    return redirect('attendance')

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


# ----------------- MODULE PAGES -----------------
@login_required
def attendance_view(request):
    return render(request, 'attendance.html')

@login_required
def settings_view(request):
    user = request.user

    if request.method == 'POST':
        user.first_name = request.POST.get('firstName')
        user.last_name = request.POST.get('lastName')
        password = request.POST.get('password')
        
        if password:
            user.set_password(password)
        user.save()
        messages.success(request, 'Settings updated successfully.')
        return redirect('settings')

    return render(request, 'settings.html', {'user': user})


def dashboard_view(request):
    return render(request, 'dashboard.html')

def notifications(request):
    return render(request, 'core/notifications.html')


@login_required
def attendance_view(request):
    user = request.user
    clock_records = Attendance.objects.filter(user=user).order_by('-date')[:10]

    return render(request, 'attendance.html', {
        'clock_records': clock_records,
    })


@login_required
def reports_view(request):
    return render(request, 'reports.html')

@login_required
def fetch_report_data(request):
    report_type = request.GET.get('type')
    start = request.GET.get('start')
    end = request.GET.get('end')

    start_date = datetime.datetime.strptime(start, '%Y-%m-%d').date()
    end_date = datetime.datetime.strptime(end, '%Y-%m-%d').date()

    if report_type == 'attendance':
        records = Attendance.objects.filter(date__range=(start_date, end_date))
        present = records.filter(status='Present').count()
        absent = records.filter(status='Absent').count()

        data = {
            'chart': {
                'labels': ['Present', 'Absent'],
                'datasets': [{
                    'data': [present, absent],
                    'backgroundColor': ['#16a34a', '#dc2626']
                }]
            },
            'rows': [
                {'name': a.user.username, 'date': a.date.strftime('%Y-%m-%d'), 'status': a.status}
                for a in records
            ]
        }

    elif report_type == 'payroll':
        records = Payroll.objects.filter(start_date__range=(start_date, end_date))
        site_totals = records.values('location').annotate(total=sum('calculated_salary'))

        data = {
            'chart': {
                'labels': [r['location'] for r in site_totals],
                'datasets': [{
                    'label': 'Salary Paid',
                    'data': [float(r['total']) for r in site_totals],
                    'backgroundColor': '#38bdf8'
                }]
            },
            'rows': [
                {'name': p.user.username, 'date': p.start_date.strftime('%Y-%m-%d'), 'status': f"₹{p.calculated_salary:.2f}"}
                for p in records
            ]
        }

    elif report_type == 'vendor':
        records = Vendor.objects.filter(date__range=(start_date, end_date))
        vendor_counts = records.values('category').annotate(total=count('id'))

        data = {
            'chart': {
                'labels': [v['category'] for v in vendor_counts],
                'datasets': [{
                    'data': [v['total'] for v in vendor_counts],
                    'backgroundColor': ['#facc15', '#f87171', '#34d399']
                }]
            },
            'rows': [
                {'name': v.vendor_name, 'date': v.date.strftime('%Y-%m-%d'), 'status': v.status}
                for v in records
            ]
        }

    else:
        data = {'chart': {}, 'rows': []}

    return JsonResponse(data)


@csrf_exempt
def generate_report_api(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        report_type = data.get('type')
        start = parse_date(data.get('start'))
        end = parse_date(data.get('end'))

        rows = []
        chart = {}

        if report_type == 'attendance':
            records = Attendance.objects.filter(date__range=(start, end))
            for r in records:
                rows.append({
                    'name': r.user.get_full_name() or r.user.username,
                    'date': str(r.date),
                    'status': 'Present' if r.clock_in else 'Absent'
                })
            chart = {
                'labels': ['Present', 'Absent'],
                'datasets': [{
                    'data': [
                        records.filter(clock_in__isnull=False).count(),
                        records.filter(clock_in__isnull=True).count()
                    ],
                    'backgroundColor': ['#16a34a', '#dc2626']
                }]
            }

        elif report_type == 'payroll':
            records = Payroll.objects.filter(start_date__gte=start, end_date__lte=end)
            site_totals = {}
            for r in records:
                site_totals[r.location] = site_totals.get(r.location, 0) + r.calculated_salary
                rows.append({
                    'name': r.user.get_full_name() or r.user.username,
                    'date': f"{r.start_date} - {r.end_date}",
                    'status': f"₹{r.calculated_salary}"
                })
            chart = {
                'labels': list(site_totals.keys()),
                'datasets': [{
                    'label': 'Salary Paid',
                    'data': list(site_totals.values()),
                    'backgroundColor': '#38bdf8'
                }]
            }

        elif report_type == 'vendor':
            # Example only if Vendor model exists
            rows = [
                { 'name': 'Ram Traders', 'date': '2025-07-11', 'status': 'Paid' },
                { 'name': 'Sai Bricks', 'date': '2025-07-11', 'status': 'Pending' }
            ]
            chart = {
                'labels': ['Cement', 'Steel', 'Sand'],
                'datasets': [{
                    'label': 'Transactions',
                    'data': [40, 25, 35],
                    'backgroundColor': ['#facc15', '#f87171', '#34d399']
                }]
            }

        return JsonResponse({'rows': rows, 'chart': chart})

    return JsonResponse({'error': 'Invalid method'}, status=400)

# -------------- VENDOR PAGE ----------------------

def vendor_management(request):
    today = now().date()
    current_month = today.month
    current_year = today.year

    # Total Outstanding (Pending or Unpaid)
    total_outstanding = Transaction.objects.filter(status__in=['Pending', 'Unpaid']).aggregate(total=Sum('amount'))['total'] or 0

    # This Month's Transactions (Any status)
    this_month = Transaction.objects.filter(date__month=current_month, date__year=current_year).aggregate(total=Sum('amount'))['total'] or 0

    # Overdue Payments (Pending and due_date passed)
    overdue = Transaction.objects.filter(status='Pending', due_date__lt=today).aggregate(total=Sum('amount'))['total'] or 0

    return render(request, 'vendor.html', {
        'vendors': Vendor.objects.all(),
        'transactions': Transaction.objects.select_related('vendor').all(),
        'gps_equipment': Equipment.objects.select_related('vendor').all(),
        'service_history': ServiceHistory.objects.select_related('equipment').all(),
        'total_outstanding': total_outstanding,
        'this_month': this_month,
        'overdue': overdue,
        'active_vendors': Vendor.objects.filter(is_active=True).count()
    })

# -------------------- TEMPORARY USER ----------------------------------


@login_required
def temp_user_home(request):
    if request.user.role != 'temp_user':
        return redirect('dashboard')

    today = now().date()
    existing = TempUserReport.objects.filter(user=request.user, date=today).first()
    form = TempUserReportForm(request.POST or None, instance=existing)

    if request.method == 'POST' and form.is_valid():
        report = form.save(commit=False)
        report.user = request.user
        report.date = today
        report.save()
        messages.success(request, "Report submitted successfully.")
        return redirect('temp_user_home')

    reports = TempUserReport.objects.filter(user=request.user).order_by('-date')

    return render(request, 'temp_user_home.html', {
        'form': form,
        'existing': existing,
        'reports': reports,
        'current_time': now(),
    })

def temp_user_form(request):
    user = request.user
    today = timezone.now().date()
    existing = TempUserReport.objects.filter(user=user, date=today).first()

    if request.method == 'POST':
        if existing:
            form = TempUserReportForm(request.POST, instance=existing)
        else:
            form = TempUserReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = user
            report.date = today
            report.save()
            return redirect('temp_user_form')  # redirect to same page
    else:
        form = TempUserReportForm(instance=existing)

    reports = TempUserReport.objects.filter(user=user).order_by('-date')
    context = {
        'form': form,
        'existing': existing,
        'reports': reports,
        'current_time': timezone.now()
    }
    return render(request, 'tempuser_form.html', context)

# ----------- USER MANAGEMENT ----------------

def user_management(request):
    users = User.objects.all()
    return render(request, 'user_management.html', {'users': users})

@require_POST
def add_user(request):
    email = request.POST.get('email')
    role = request.POST.get('role')
    password = request.POST.get('password')

    if email and role:
        user = User.objects.create_user(email=email, password='default123', role=role)
        messages.success(request, 'User added with default password.')
    return redirect('user_management')

@require_POST
def delete_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    user.delete()
    messages.success(request, 'User deleted.')
    return redirect('user_management')
