from django.contrib import admin
from .models import (Branch,User,Teacher,Student,DailyPayment,Attendance,Group,
StudentPaymentHistory, Schedule, Notification,StudentDebt,Salary,Expense,AttendanceReport)

@admin.register(StudentPaymentHistory)
class StudentPaymentHistoryAdmin(admin.ModelAdmin):
    list_display = ('student', 'payment', 'amount', 'date')
    search_fields = ('student__user__username', 'student__user__full_name')
    list_filter = ('date',)

@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('group', 'teacher', 'subject', 'day_of_week', 'start_time', 'end_time')
    search_fields = ('group__name', 'teacher__user__full_name', 'subject')
    list_filter = ('day_of_week', 'teacher')

@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('user', 'title', 'is_read', 'created_at')
    search_fields = ('user__username', 'user__full_name', 'title')
    list_filter = ('is_read', 'created_at')

class TeacherAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and request.user.user_role == 'admin':
            form.base_fields['branch'].queryset = Branch.objects.filter(id=request.user.branch.id)
        return form
    
    def save_model(self, request, obj, form, change):
        if not change:  
            if not request.user.is_superuser and request.user.user_role == 'admin':
                if obj.user:
                    obj.user.managed_by = request.user
                    obj.user.branch = request.user.branch
                    obj.user.save()
                obj.branch = request.user.branch
        super().save_model(request, obj, form, change)

admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Branch)
admin.site.register(Group)
admin.site.register(Student)
admin.site.register(DailyPayment)
admin.site.register(Attendance)
admin.site.register(User)
admin.site.register(Salary)
admin.site.register(StudentDebt)
admin.site.register(Expense)
admin.site.register(AttendanceReport)
