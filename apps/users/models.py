from django.db import models
from django.contrib.auth.models import AbstractUser
import random
from datetime import timedelta,time,timezone,date,datetime
from django.core.validators import MaxLengthValidator,MinLengthValidator
from django.db.models import Sum

class User(AbstractUser):
    USER_ROLE = (
        ('owner','owner'),
        ('admin','admin'),
        ('teacher','teacher'),
    )
    image = models.ImageField(upload_to='profile_pics/', blank=True, null=True, default='profile_pics/default.jpg')
    phone_number = models.CharField(max_length=13, blank=True, null=True)
    address = models.CharField(max_length=200, blank=True, null=True)
    jobs = models.CharField(max_length=200, blank=True, null=True)
    user_role = models.CharField(max_length=100,choices=USER_ROLE,default="teacher")
    
    # otp_code = models.CharField(max_length=6, blank=True, null=True)
    # is_verified = models.BooleanField(default=False)

    # def generate_otp(self):
    #     self.otp_code = str(random.randint(100000, 999999))
    #     self.save()
    #     return self.otp_code
    
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
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
