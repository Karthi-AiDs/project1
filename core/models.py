from django.db import models
from django.utils.timezone import now
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# ------------------------------------
# Custom User Manager
# ------------------------------------

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("Email must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if not extra_fields.get('is_staff'):
            raise ValueError("Superuser must have is_staff=True.")
        if not extra_fields.get('is_superuser'):
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)

# ------------------------------------
# 1. User Authentication – Ashika
# ------------------------------------

ROLE_CHOICES = (
    ('admin', 'Admin'),
    ('engineer', 'Engineer'),
    ('temp_user', 'Temporary User'),
    ('regular_user', 'Regular User'),
)

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=15, blank=True)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='regular_user')
    
    is_approved = models.BooleanField(default=False)
    is_blocked = models.BooleanField(default=False)
    approved_by = models.IntegerField(null=True, blank=True)
    approved_at = models.DateTimeField(null=True, blank=True)
    failed_login_attempts = models.IntegerField(default=0)
    last_failed_login = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=now)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

class LoginLog(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    login_time = models.DateTimeField(default=now)
    successful = models.BooleanField(default=False)
    failure_reason = models.CharField(max_length=255, blank=True, null=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    device_info = models.CharField(max_length=255, null=True, blank=True)
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"{self.user} @ {self.login_time}"

class LoginSession(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    login_time = models.DateTimeField(default=now)
    logout_time = models.DateTimeField(null=True, blank=True)
    session_token = models.CharField(max_length=255, null=True, blank=True)
    ip_address = models.CharField(max_length=45, null=True, blank=True)
    device_info = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"Session for {self.user}"

class MFAToken(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    token = models.CharField(max_length=10)
    is_used = models.BooleanField(default=False)
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(default=now)

    def __str__(self):
        return f"MFA for {self.user}"

# ------------------------------------
# 2. Attendance Tracking – Aswini
# ------------------------------------

class Attendance(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, limit_choices_to={'role': 'regular_user'})
    date = models.DateField()
    check_in = models.TimeField()
    check_out = models.TimeField()
    gps_location = models.CharField(max_length=100)
    overtime_hours = models.FloatField(default=0)
    status = models.CharField(max_length=10, choices=[('Present', 'Present'), ('Absent', 'Absent')])

    def __str__(self):
        return f"{self.user.email} - {self.date}"

# ------------------------------------
# 3. Vendor Management – Avanthykkha
# ------------------------------------

class Vendor(models.Model):
    name = models.CharField(max_length=100)
    contact_person = models.CharField(max_length=100)
    phone = models.CharField(max_length=15)
    email = models.EmailField()
    address = models.TextField()
    gps_location = models.CharField(max_length=100, blank=True)
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='vendor_approvals')

    def __str__(self):
        return self.name

# ------------------------------------
# 4. Material Management – Kalpanaa
# ------------------------------------

class Material(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.FloatField()
    unit = models.CharField(max_length=20)
    vendor = models.ForeignKey(Vendor, on_delete=models.SET_NULL, null=True, blank=True)
    purchase_date = models.DateField()
    barcode = models.CharField(max_length=100, blank=True, null=True)
    photo = models.ImageField(upload_to='materials/')
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, limit_choices_to={'role': 'temp_user'})
    is_approved = models.BooleanField(default=False)
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


    def __str__(self):
        return self.name

# ------------------------------------
# 5. Payroll Management – Karthikeyan
# ------------------------------------
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class Payroll(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    start_date = models.DateField()
    end_date = models.DateField()
    total_hours = models.DecimalField(max_digits=5, decimal_places=2)
    hourly_rate = models.DecimalField(max_digits=7, decimal_places=2)
    location = models.CharField(max_length=100)
    calculated_salary = models.FloatField(default=0.0)
    is_approved = models.BooleanField(default=False)  # this caused your IntegrityError

    def save(self, *args, **kwargs):
        self.calculated_salary = self.total_hours * self.hourly_rate
        super().save(*args, **kwargs)
