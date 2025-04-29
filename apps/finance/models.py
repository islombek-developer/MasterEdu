from django.db import models
from django.db.models import Sum
from datetime import date

class PaymentPeriod(models.TextChoices):
    DAILY = 'daily', 'Kunlik'
    WEEKLY = 'weekly', 'Haftalik'
    MONTHLY = 'monthly', 'Oylik'
    QUARTERLY = 'quarterly', 'Choraklik'
    YEARLY = 'yearly', 'Yillik'

class PaymentType(models.TextChoices):
    CASH = 'cash', 'Naqd'
    CARD = 'card', 'Karta'
    TRANSFER = 'transfer', 'Otkazma'
    OTHER = 'other', 'Boshqa'

class StudentDebt(models.Model):
    student = models.OneToOneField('student.Student', on_delete=models.CASCADE, related_name="debt")
    total_debt = models.IntegerField(default=0) 
    balance = models.IntegerField(default=0) 
    last_payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.total_debt} som"

class StudentPayment(models.Model):
    student_group = models.ForeignKey('student.StudentGroup', on_delete=models.CASCADE, related_name='payments')
    payment_date = models.DateField(default=date.today)
    period = models.CharField(max_length=20, choices=PaymentPeriod.choices, default=PaymentPeriod.MONTHLY)
    period_start = models.DateField(null=True, blank=True)
    period_end = models.DateField(null=True, blank=True)
    amount = models.IntegerField()
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices, default=PaymentType.CASH)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    note = models.TextField(blank=True, null=True)
    received_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='received_payments')
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='student_payments')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)  
        
        debt, created = StudentDebt.objects.get_or_create(student=self.student_group.student)
        debt.last_payment_date = self.payment_date
        
        # Qarzni qayta hisoblash
        from apps.student.models import StudentGroup
        from django.utils import timezone
        import calendar
        from datetime import datetime
        
        student_groups = StudentGroup.objects.filter(student=self.student_group.student, status='active')
        
        total_required = 0
        total_paid = 0
        total_remaining = 0
        
        for sg in student_groups:
            payments = StudentPayment.objects.filter(student_group=sg)
            paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
            total_paid += paid
            
            joined_date = sg.joined_date
            today = timezone.now().date()
            
            from apps.student.models import Attendance
            attended_lessons = Attendance.objects.filter(
                student=sg.student,
                group=sg.group,
                date__gte=joined_date,
                date__lte=today,
                status='present'
            ).count()
            lessons_per_week = sg.group.lessons_per_week if hasattr(sg.group, 'lessons_per_week') else 3
            lessons_per_month = lessons_per_week * 4  
            price_per_lesson = sg.group.price_per_month / lessons_per_month
            
            current_month_start = datetime(today.year, today.month, 1).date()
            days_in_month = calendar.monthrange(today.year, today.month)[1]
            current_month_end = datetime(today.year, today.month, days_in_month).date()
            
            if joined_date.month == today.month and joined_date.year == today.year:
                remaining_days = days_in_month - joined_date.day + 1
                first_month_payment = (sg.group.price_per_month * remaining_days) / days_in_month
                
                expected_lessons = (lessons_per_month * remaining_days / days_in_month)
                
                lessons_remaining = expected_lessons - attended_lessons
                remaining_payment = max(0, price_per_lesson * lessons_remaining)
                
                total_required += first_month_payment
                total_remaining += remaining_payment
                
            else:
                months_passed = (today.year - joined_date.year) * 12 + today.month - joined_date.month
                
                if joined_date.day > 1 and months_passed > 0:
                    days_in_first_month = calendar.monthrange(joined_date.year, joined_date.month)[1]
                    remaining_days = days_in_first_month - joined_date.day + 1
                    first_month_payment = (sg.group.price_per_month * remaining_days) / days_in_first_month
                    full_months_payment = sg.group.price_per_month * (months_passed - 1)
                    
                    current_month_attended = Attendance.objects.filter(
                        student=sg.student,
                        group=sg.group,
                        date__gte=current_month_start,
                        date__lte=today,
                        status='present'
                    ).count()
                    
                    remaining_lessons = lessons_per_month - current_month_attended
                    current_month_remaining = max(0, price_per_lesson * remaining_lessons)
                    
                    total_required += first_month_payment + full_months_payment + sg.group.price_per_month
                    total_remaining += current_month_remaining
                else:
                    required = sg.group.price_per_month * months_passed
                    
                    current_month_attended = Attendance.objects.filter(
                        student=sg.student,
                        group=sg.group,
                        date__gte=current_month_start,
                        date__lte=today,
                        status='present'
                    ).count()
                    
                    remaining_lessons = lessons_per_month - current_month_attended
                    current_month_remaining = max(0, price_per_lesson * remaining_lessons)
                    
                    total_required += required
                    total_remaining += current_month_remaining
        
        debt.total_debt = max(0, total_required - total_paid)
        debt.current_month_remaining = total_remaining
        debt.balance = max(0, total_paid - total_required)
        debt.save()

    def __str__(self):
        return f"{self.student_group.student.get_full_name()} - {self.payment_date} - {self.amount}"

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_salary = models.BooleanField(default=False)  
    
    
    def __str__(self):
        return self.name

class Expense(models.Model):
    category = models.ForeignKey(ExpenseCategory, on_delete=models.CASCADE, related_name='expenses')
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='expenses')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices, default=PaymentType.CASH)
    date = models.DateField(default=date.today)
    description = models.TextField(blank=True, null=True)
    recipient = models.CharField(max_length=200, blank=True, null=True)  # Pul oluvchi
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_expenses')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.category.name} - {self.amount} so'm ({self.date})"
    
class Salary(models.Model):
    teacher = models.ForeignKey('teacher.Teacher', on_delete=models.CASCADE, related_name='salaries')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    month = models.DateField()  
    paid_date = models.DateField(default=date.today)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices, default=PaymentType.CASH)
    paid_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='paid_salaries')
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='teacher_salaries')
    note = models.TextField(blank=True, null=True)
    expense = models.OneToOneField(Expense, on_delete=models.SET_NULL, null=True, blank=True, related_name='salary')

    class Meta:
        verbose_name_plural = "Salaries"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        if is_new and not self.expense:
            salary_category, _ = ExpenseCategory.objects.get_or_create(
                name="oqituvchi maoshi",
                defaults={'is_salary': True}
            )
            
            expense = Expense.objects.create(
                category=salary_category,
                branch=self.branch,
                amount=self.amount,
                payment_type=self.payment_type,
                date=self.paid_date,
                description=f"{self.teacher.get_full_name()} uchun {self.month.strftime('%B %Y')} oylik maoshi",
                recipient=self.teacher.get_full_name(),
                created_by=self.paid_by
            )
            
            self.expense = expense
            super().save(update_fields=['expense'])

    def __str__(self):
        return f'{self.teacher.get_full_name()} - {self.month.strftime("%B %Y")}'

class AdditionalIncome(models.Model):
    title = models.CharField(max_length=255)
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='additional_incomes')
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices, default=PaymentType.CASH)
    date = models.DateField(default=date.today)
    description = models.TextField(blank=True, null=True)
    receipt_number = models.CharField(max_length=50, blank=True, null=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_incomes')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.title} - {self.amount} so'm ({self.date})"

class FinancialReport(models.Model):
    REPORT_PERIOD = (
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('custom', 'Custom'),
    )
    
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='financial_reports')
    period = models.CharField(max_length=20, choices=REPORT_PERIOD)
    start_date = models.DateField()
    end_date = models.DateField()
    student_payments = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    additional_incomes = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_income = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    salary_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    other_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    total_expenses = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    net_profit = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='created_financial_reports')
    
    def calculate_report(self):
        from apps.finance.models import StudentPayment
        student_payments = StudentPayment.objects.filter(
            branch=self.branch,
            payment_date__gte=self.start_date,
            payment_date__lte=self.end_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        additional = AdditionalIncome.objects.filter(
            branch=self.branch,
            date__gte=self.start_date,
            date__lte=self.end_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        salaries = Expense.objects.filter(
            branch=self.branch,
            date__gte=self.start_date,
            date__lte=self.end_date,
            category__is_salary=True
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        other_exp = Expense.objects.filter(
            branch=self.branch,
            date__gte=self.start_date,
            date__lte=self.end_date,
            category__is_salary=False
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        self.student_payments = student_payments
        self.additional_incomes = additional
        self.total_income = student_payments + additional
        
        self.salary_expenses = salaries
        self.other_expenses = other_exp
        self.total_expenses = salaries + other_exp
        
        self.net_profit = self.total_income - self.total_expenses
    
    def save(self, *args, **kwargs):
        self.calculate_report()
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.branch.name} - {self.get_period_display()} ({self.start_date} - {self.end_date})"