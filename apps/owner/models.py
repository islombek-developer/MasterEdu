from django.db import models
from apps.users.models import Branch, User, Status
from django.utils import timezone
import datetime

class SubscriptionPlan(models.Model):
    """O'quv markazlar uchun obuna rejasi"""
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_days = models.IntegerField(help_text="Obuna davomiyligi kunlarda")
    features = models.JSONField(default=dict, help_text="Reja bo'yicha mavjud funksiyalar")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_plans')
    
    def __str__(self):
        return f"{self.name} - {self.price}"

class BranchSubscription(models.Model):
    """O'quv markaz obunasi"""
    PAYMENT_STATUS = (
        ('pending', 'Kutilmoqda'),
        ('paid', 'To\'langan'),
        ('cancelled', 'Bekor qilingan'),
        ('expired', 'Muddati tugagan'),
    )
    
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='subscriptions')
    plan = models.ForeignKey(SubscriptionPlan, on_delete=models.CASCADE, related_name='subscriptions')
    start_date = models.DateField()
    end_date = models.DateField()
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    amount_paid = models.DecimalField(max_digits=10, decimal_places=2)
    payment_method = models.CharField(max_length=50, blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    is_active = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='created_subscriptions')
    
    def __str__(self):
        return f"{self.branch.name} - {self.plan.name} ({self.start_date} to {self.end_date})"
    
    def is_expired(self):
        return self.end_date < timezone.now().date()
    
    def days_remaining(self):
        if self.is_expired():
            return 0
        delta = self.end_date - timezone.now().date()
        return delta.days
    
    def activate(self):
        self.is_active = True
        self.payment_status = 'paid'
        self.save()
    
    def deactivate(self):
        self.is_active = False
        self.save()
        
    def extend(self, days):
        """Obunani belgilangan kun soniga uzaytirish"""
        self.end_date = self.end_date + datetime.timedelta(days=days)
        self.save()

class SubscriptionPayment(models.Model):
    """Obuna to'lovlari"""
    subscription = models.ForeignKey(BranchSubscription, on_delete=models.CASCADE, related_name='payments')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_date = models.DateTimeField(default=timezone.now)
    payment_method = models.CharField(max_length=50)
    transaction_id = models.CharField(max_length=100, blank=True, null=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='recorded_payments')
    
    def __str__(self):
        return f"{self.subscription.branch.name} - {self.amount} ({self.payment_date.strftime('%Y-%m-%d')})"

class BranchSettings(models.Model):
    branch = models.OneToOneField('users.Branch', on_delete=models.CASCADE, related_name='settings')
    working_days = models.CharField(max_length=100, default="1,2,3,4,5,6")  
    working_start_time = models.TimeField(default='08:00:00')
    working_end_time = models.TimeField(default='20:00:00')
    lesson_duration = models.IntegerField(default=90) 
    break_duration = models.IntegerField(default=10) 
    tax_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)  
    
    def __str__(self):
        return f"{self.branch.name} - Sozlamalar"

class Role(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    permissions = models.JSONField(default=dict)  
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_roles')
    
    def __str__(self):
        return self.name

class BranchReport(models.Model):
    REPORT_PERIOD = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    )
    
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='reports')
    period = models.CharField(max_length=20, choices=REPORT_PERIOD)
    start_date = models.DateField()
    end_date = models.DateField()
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expense = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    student_count = models.IntegerField(default=0)
    attendance_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_reports')
    
    def __str__(self):
        return f"{self.branch.name} - {self.get_period_display()} ({self.start_date} - {self.end_date})"

