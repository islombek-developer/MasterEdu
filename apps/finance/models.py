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
    TRANSFER = 'transfer', 'O\'tkazma'
    OTHER = 'other', 'Boshqa'

class StudentDebt(models.Model):
    student = models.OneToOneField('student.Student', on_delete=models.CASCADE, related_name="debt")
    total_debt = models.IntegerField(default=0) 
    balance = models.IntegerField(default=0) 
    last_payment_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.student.get_full_name()} - {self.total_debt} so'm"

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
        student_groups = StudentGroup.objects.filter(student=self.student_group.student, status='active')
        
        total_required = 0
        total_paid = 0
        
        for sg in student_groups:
            # Har bir guruh uchun to'lovlar summasi
            payments = StudentPayment.objects.filter(student_group=sg)
            paid = payments.aggregate(Sum('amount'))['amount__sum'] or 0
            total_paid += paid
            
            # Har bir guruh uchun to'lanishi kerak bo'lgan summa (guruhning oylik narxidan kelib chiqib)
            from django.utils import timezone
            months_passed = (timezone.now().date() - sg.joined_date).days // 30 + 1
            required = sg.group.price_per_month * months_passed
            total_required += required
        
        debt.total_debt = max(0, total_required - total_paid)
        debt.balance = max(0, total_paid - total_required)
        debt.save()

    def __str__(self):
        return f"{self.student_group.student.get_full_name()} - {self.payment_date} - {self.amount}"

class ExpenseCategory(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    is_salary = models.BooleanField(default=False)  # Ish haqi toifasi ekanligini belgilash
    
    class Meta:
        verbose_name_plural = "Expense Categories"
    
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
    month = models.DateField()  # Oy va yil uchun
    paid_date = models.DateField(default=date.today)
    payment_type = models.CharField(max_length=20, choices=PaymentType.choices, default=PaymentType.CASH)
    paid_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='paid_salaries')
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='teacher_salaries')
    note = models.TextField(blank=True, null=True)
    
    # Avtomatik xarajat yaratish uchun
    expense = models.OneToOneField(Expense, on_delete=models.SET_NULL, null=True, blank=True, related_name='salary')

    class Meta:
        verbose_name_plural = "Salaries"

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        
        # Ish haqi to'langanda, xarajatlar jadvaliga ham qo'shish
        if is_new and not self.expense:
            salary_category, _ = ExpenseCategory.objects.get_or_create(
                name="O'qituvchi maoshi",
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
        # O'quvchilar to'lovlari
        from apps.finance.models import StudentPayment
        student_payments = StudentPayment.objects.filter(
            branch=self.branch,
            payment_date__gte=self.start_date,
            payment_date__lte=self.end_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Qo'shimcha daromadlar
        additional = AdditionalIncome.objects.filter(
            branch=self.branch,
            date__gte=self.start_date,
            date__lte=self.end_date
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Ish haqi xarajatlari
        salaries = Expense.objects.filter(
            branch=self.branch,
            date__gte=self.start_date,
            date__lte=self.end_date,
            category__is_salary=True
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Boshqa xarajatlar
        other_exp = Expense.objects.filter(
            branch=self.branch,
            date__gte=self.start_date,
            date__lte=self.end_date,
            category__is_salary=False
        ).aggregate(Sum('amount'))['amount__sum'] or 0
        
        # Natijalarni saqlash
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