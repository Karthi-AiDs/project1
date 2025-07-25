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
    path('users/',views.user_management,name='user_management'),

    # Feature Views
    path('attendance/', views.attendance_view, name='attendance'),
    path('vendor/', views.vendor_view, name='vendor'),
    path('reports/', views.reports_view, name='reports'),
    path('reports/fetch/', views.fetch_report_data, name='fetch_report_data'),
    path('settings/', views.settings_view, name='settings'),
    path('payroll/', views.payroll_view, name='payroll'),
    path('materials/', views.materials_view, name='materials'),
    path('notifications/', views.notifications, name='notifications'),
    
    # Form Submissions (if needed)
    path('add_attendance/', views.add_attendance, name='add_attendance'),
    path('add_vendor/', views.add_vendor, name='add_vendor'),
    path('add_material/', views.add_material, name='add_material'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    

    # Profile update (optional)
    path('update_profile/', views.update_profile, name='update_profile'),
    ]

