from django.db import models
from django.contrib.auth.models import AbstractUser
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone


class Status(models.TextChoices):
    ACTIVE = 'active', 'Active'
    INACTIVE = 'inactive', 'Inactive'
    ARCHIVED = 'archived', 'Archived'

class Branch(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    status = models.CharField(choices=Status.choices, max_length=15, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name
    
    def has_active_subscription(self):
        from apps.owner.models import BranchSubscription
        """O'quv markaz aktiv obunaga ega ekanligini tekshirish"""
        active_subscription = BranchSubscription.objects.filter(
                branch=self,
                is_active=True,
                end_date__gte=timezone.now().date(),
                payment_status='paid'
            ).first()
        return active_subscription is not None

    def get_current_subscription(self):
        """O'quv markazning joriy obunasini olish"""
        from apps.owner.models import BranchSubscription
        return BranchSubscription.objects.filter(
            branch=self,
            is_active=True,
            end_date__gte=timezone.now().date()
        ).order_by('-end_date').first()

class User(AbstractUser):
    USER_ROLE = (
        ('owner', 'owner'),
        ('admin', 'admin'),
        ('teacher', 'teacher'),
        ('student', 'student'),
        ('parent', 'parent'),
    )
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='profile_pics/default.jpg')
    phone_number = models.CharField(max_length=13)
    address = models.CharField(max_length=200, blank=True, null=True)
    jobs = models.CharField(max_length=200, blank=True, null=True)
    user_role = models.CharField(max_length=100, choices=USER_ROLE, default="student")
    branch = models.ManyToManyField(Branch, blank=True, related_name='users')
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    managed_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_users')
    status = models.CharField(choices=Status.choices, max_length=15, default=Status.ACTIVE)
    telegram_chat_id = models.CharField(max_length=200, blank=True, null=True)  
    
    def full_name(self):
        return f'{self.first_name} {self.last_name}'
    
    def token(self):
        refresh = RefreshToken.for_user(self)
        return {
            'refresh_token': str(refresh),
            'access_token': str(refresh.access_token),
        }

    def check_hash_password(self):
        if not self.password.startswith('pbkdf2_sha256'):
            self.set_password(self.password)
    
    def save(self, *args, **kwargs):
        self.check_hash_password()
        
        if not self.username:
            self.username = self.phone_number
        
        super().save(*args, **kwargs)
        if self.user_role != 'admin':
            self.branch.clear()
        
        if self.user_role == 'teacher' and not hasattr(self, 'teacher'):
            from apps.teacher.models import Teacher
            Teacher.objects.create(user=self)
            
        if self.user_role == 'student' and not hasattr(self, 'student'):
            from apps.student.models import Student
            Student.objects.create(user=self)
    
    def get_managed_teachers(self):
        if self.user_role == 'admin':
            return User.objects.filter(
                user_role='teacher',
                branch__in=self.branch.all(),
                managed_by=self
            )
        return User.objects.none()
            
    def can_manage_user(self, user):
        if self.user_role == 'owner':
            return user.user_role != 'owner' 
        elif self.user_role == 'admin':
            return (user.user_role in ['teacher', 'student']) and user.branch.filter(id__in=self.branch.all()).exists()
        return False
        
    def can_create_branch(self):
        return self.user_role in ['owner', 'admin']
        
    def can_create_teacher(self):
        return self.user_role in ['owner', 'admin']

    def __str__(self):
        return f"{self.username} ({self.get_user_role_display()})"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_to = models.CharField(max_length=100, blank=True, null=True)  
    related_id = models.IntegerField(blank=True, null=True)  
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sent_notifications')

    def __str__(self):
        return f"{self.user.full_name()} - {self.title}"
