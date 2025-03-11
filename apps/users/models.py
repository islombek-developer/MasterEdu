from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from datetime import timedelta,time,timezone,date,datetime
from django.core.validators import MaxLengthValidator,MinLengthValidator
from django.db.models import Sum
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
class User(AbstractUser):
    USER_ROLE = (
        ('owner','owner'),
        ('admin','admin'),
        ('teacher','teacher'),
        ('student','student'),
    )
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='profile_pics/default.jpg')
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    jobs = models.CharField(max_length=200, blank=True, null=True)
    user_role = models.CharField(max_length=100,choices=USER_ROLE,default="teacher")
    

    
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



class Teacher(models.Model):
    user = models.OneToOneField(User,on_delete=models.CASCADE)
    date_of = models.DateField(null=True,blank=True )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    
    def get_full_name(self):
        return f"{self.user.username} {self.user.last_name}"

    def __str__(self):
        return self.get_full_name()


class Group(models.Model):
    WEEK_CHOISE = (
        ('juft','juft'),
        ('toq','toq'),
        ('INDUVIDUAL','INDUVIDUAL')
    )
    teacher = models.ForeignKey(Teacher,on_delete=models.CASCADE,related_name='teacher')
    title = models.CharField(max_length=150)
    week = models.CharField(max_length=15,choices=WEEK_CHOISE,default='juft')

    def __str__(self):
        return self.title

class Student(models.Model):
    first_name = models.CharField(max_length=150)
    last_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=14,null=True,blank=True)
    home_phone = models.CharField(max_length=14,null=True,blank=True)
    group = models.ForeignKey(Group,on_delete=models.CASCADE,related_name='group')
    status = models.BooleanField(default=True)

    def __str__(self):
        return f'{self.first_name} -- {self.last_name}'

class Attendance(models.Model):
    group = models.ForeignKey(Group,on_delete=models.CASCADE,related_name='group_attend')
    student = models.ForeignKey(Student,on_delete=models.CASCADE,related_name='student_attend')
    date = models.DateField(default=timezone.localdate)
    status = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return str(self.date)
    
class DailyPayment(models.Model):
    group = models.ForeignKey(Group,on_delete=models.CASCADE)
    student = models.ForeignKey(Student,on_delete=models.CASCADE)
    payment_date = models.DateField(default=date.today)
    remaining_amount = models.IntegerField()
    paid_amount = models.IntegerField()
    note = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"

    def __str__(self):
        return f"{self.student.first_name} - {self.payment_date} - {self.paid_amount}"