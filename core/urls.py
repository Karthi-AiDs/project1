from django.urls import path
from . import views

urlpatterns = [
    # Auth
    path('', views.login_view, name='login'),
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('signup/', views.signup_view, name='signup'),

    # Dashboards
    path('admin-dashboard/', views.admin_dashboard, name='admin_dashboard'),
    path('dashboard/', views.site_dashboard, name='site_dashboard'),  # For engineer role
    path('user-dashboard/', views.user_dashboard, name='user_dashboard'),
    path('temp-user-home/', views.temp_user_home, name='temp_user_home'),

    # Feature Views
    path('attendance/', views.attendance_view, name='attendance'),
    path('vendor/', views.vendor_view, name='vendor'),
    path('reports/', views.reports_view, name='reports'),
    path('settings/', views.settings_view, name='settings'),
    path('payroll/', views.payroll_view, name='payroll'),
    path('materials/', views.materials_view, name='materials'),
    path('notifications/', views.notifications, name='notifications'),
    
    # Form Submissions (if needed)
    path('add_attendance/', views.add_attendance, name='add_attendance'),
    path('add_vendor/', views.add_vendor, name='add_vendor'),
    path('add_material/', views.add_material, name='add_material'),
    path('add_payroll/', views.add_payroll, name='add_payroll'),

    # Profile update (optional)
    path('update_profile/', views.update_profile, name='update_profile'),
]
