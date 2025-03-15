from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from datetime import timedelta,time,timezone,date,datetime
from django.core.validators import MaxLengthValidator,MinLengthValidator
from django.db.models import Sum
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver


class Branch(models.Model):
    name = models.CharField(max_length=150)
    address = models.CharField(max_length=200, blank=True, null=True)
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class User(AbstractUser):
    USER_ROLE = (
        ('owner', 'owner'),
        ('admin', 'admin'),
        ('teacher', 'teacher'),
        ('student', 'student'),
    )
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='profile_pics/default.jpg')
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    jobs = models.CharField(max_length=200, blank=True, null=True)
    user_role = models.CharField(max_length=100, choices=USER_ROLE, default="student")
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True, related_name='users')
    created_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='created_users')
    managed_by = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='managed_users')
    
    @property
    def full_name(self):
        return f'{self.first_name}--{self.last_name}'
    
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
        
        if self.user_role != 'admin' and self.branch is not None:
            self.branch = None
            
        super().save(*args, **kwargs)
        
        if self.user_role == 'teacher' and not hasattr(self, 'teacher'):
            Teacher.objects.create(user=self)
    
    def get_managed_teachers(self):
        if self.user_role == 'admin':
            return User.objects.filter(
                user_role='teacher',
                branch=self.branch,
                managed_by=self
            )
        return User.objects.none()
            
    def can_manage_user(self, user):
        if self.user_role == 'owner':
            return user.user_role != 'owner' 
        elif self.user_role == 'admin':
            return (user.user_role in ['teacher', 'student']) and user.branch == self.branch
        return False
        
    def can_create_branch(self):
        return self.user_role in ['owner', 'admin']
        
    def can_create_teacher(self):
        return self.user_role in ['owner', 'admin']

    def __str__(self):
        return f"{self.username} ({self.get_user_role_display()})"


class Teacher(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    subject = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def admin(self):
        if self.user.managed_by and self.user.managed_by.user_role == 'admin':
            return self.user.managed_by
        return None
    
    @property
    def branch(self):

        return self.user.branch or (self.admin.branch if self.admin else None)
    
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return self.get_full_name()


class Group(models.Model):
    WEEK_CHOISE = (
        ('juft', 'juft'),
        ('toq', 'toq'),
        ('INDUVIDUAL', 'INDUVIDUAL')
    )
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='teacher_groups')
    title = models.CharField(max_length=150)
    week = models.CharField(max_length=15, choices=WEEK_CHOISE, default='juft')
    created_at = models.DateTimeField()
    updated_at = models.DateTimeField()

    def __str__(self):
        return f"{self.title} - {self.teacher.get_full_name()} "


class Student(models.Model):
    user = models.ForeignKey(User,on_delete=models.CASCADE)
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=14, null=True, blank=True)
    home_phone = models.CharField(max_length=14, null=True, blank=True)
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='students')
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def branch(self):
        return self.group.branch
        
    def __str__(self):
        return f'{self.first_name} {self.last_name}'


class Attendance(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='group_attendances')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='student_attendances')
    date = models.DateField(default=timezone.localdate)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


        
    def __str__(self):
        return f"{self.student} - {self.date} - {'Present' if self.status else 'Absent'}"


class StudentDebt(models.Model):
    student = models.OneToOneField(Student, on_delete=models.CASCADE, related_name="debt")
    total_debt = models.IntegerField(default=0) 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.user.get_full_name()} - {self.total_debt} so‘m"


class DailyPayment(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='payments')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(default=date.today)
    remaining_amount = models.IntegerField(blank=True, null=True)
    paid_amount = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  

        StudentPaymentHistory.objects.create(
            student=self.student,
            payment=self,
            amount=self.paid_amount
        )
        debt, created = StudentDebt.objects.get_or_create(student=self.student)
        total_remaining = DailyPayment.objects.filter(student=self.student).aggregate(Sum('remaining_amount'))['remaining_amount__sum'] or 0
        debt.total_debt = total_remaining
        debt.save()

    def __str__(self):
        return f"{self.student.first_name} - {self.payment_date} - {self.paid_amount}"
    
class StudentPaymentHistory(models.Model):
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    payment = models.ForeignKey(DailyPayment,on_delete=models.CASCADE)
    amount = models.IntegerField()
    date = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student} - {self.date.strftime('%Y-%m-%d %H:%M')} - {self.amount}"

class Schedule(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='schedules')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schedules')
    subject = models.CharField(max_length=255,blank=True, null=True)
    day_of_week = models.CharField(max_length=10, choices=[
        ('Monday', 'Monday'), ('Tuesday', 'Tuesday'), ('Wednesday', 'Wednesday'), 
        ('Thursday', 'Thursday'), ('Friday', 'Friday'), ('Saturday', 'Saturday'), ('Sunday', 'Sunday')
    ])
    start_time = models.TimeField()
    end_time = models.TimeField()

    def __str__(self):
        return f"{self.group.name} - {self.subject} ({self.day_of_week})"
    
class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    group = models.ForeignKey(Group,on_delete=models.CASCADE,blank=True, null=True)
    title = models.CharField(max_length=255)
    message = models.TextField()
    is_read = models.BooleanField(default=False,blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.full_name} - {self.title}"

class Expense(models.Model):
    category = models.CharField(max_length=100)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    date = models.DateField(auto_now_add=True)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.category} - {self.amount} so'm ({self.date})"
    
class Salary(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.CharField(max_length=20)
    paid_date = models.DateField(auto_now_add=True)


    def save(self, *args, **kwargs):
        if self.user.user_role in ['teacher', 'admin']:
            super().save(*args, **kwargs) 
        else:
            raise ValueError("Faqat teacher va admin foydalanuvchilar uchun ma'lumot qo'shish mumkin")


    def __str__(self):
        return f'{self.user.first_name}'

class Satus(models.TextChoices):
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    LATE = 'late', 'Late'


class AttendanceReport(models.Model):
    attendance = models.ForeignKey(Attendance, on_delete=models.CASCADE, related_name='reports')
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='attendance_reports')
    status = models.CharField(choices=Satus.choices, max_length=10, default=Satus.ABSENT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
