from django.contrib import admin
from .models import (
    StudentDebt, StudentPayment, ExpenseCategory, Expense,
    Salary, AdditionalIncome, FinancialReport
)

@admin.register(StudentDebt)
class StudentDebtAdmin(admin.ModelAdmin):
    list_display = ('student', 'total_debt', 'balance', 'last_payment_date', 'updated_at')
    search_fields = ('student__user__first_name', 'student__user__last_name')
    list_filter = ('last_payment_date',)

@admin.register(StudentPayment)
class StudentPaymentAdmin(admin.ModelAdmin):
    list_display = ('student_group', 'payment_date', 'amount', 'payment_type', 'received_by', 'branch')
    list_filter = ('payment_date', 'payment_type', 'branch')
    search_fields = ('student_group__student__user__first_name', 'student_group__student__user__last_name', 'receipt_number')

@admin.register(ExpenseCategory)
class ExpenseCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'is_salary')
    list_filter = ('is_salary',)
    search_fields = ('name',)

@admin.register(Expense)
class ExpenseAdmin(admin.ModelAdmin):
    list_display = ('category', 'amount', 'payment_type', 'date', 'recipient', 'branch')
    list_filter = ('category', 'payment_type', 'date', 'branch')
    search_fields = ('description', 'recipient', 'receipt_number')

@admin.register(Salary)
class SalaryAdmin(admin.ModelAdmin):
    list_display = ('teacher', 'amount', 'month', 'paid_date', 'payment_type', 'branch')
    list_filter = ('month', 'payment_type', 'branch')
    search_fields = ('teacher__user__first_name', 'teacher__user__last_name')

@admin.register(AdditionalIncome)
class AdditionalIncomeAdmin(admin.ModelAdmin):
    list_display = ('title', 'amount', 'payment_type', 'date', 'branch')
    list_filter = ('payment_type', 'date', 'branch')
    search_fields = ('title', 'description', 'receipt_number')

@admin.register(FinancialReport)
class FinancialReportAdmin(admin.ModelAdmin):
    list_display = ('branch', 'period', 'start_date', 'end_date', 'total_income', 'salary_expenses')
    list_filter = ('period', 'branch')
    search_fields = ('branch__name',)
