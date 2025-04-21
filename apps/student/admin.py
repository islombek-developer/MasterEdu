from django.contrib import admin
from .models import Student, StudentGroup, Attendance, StudentProgress

@admin.register(Student)
class StudentAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'status', 'date_of_birth', 'branch', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'parent_name', 'parent_phone')
    list_filter = ('status', 'created_at')
    readonly_fields = ('created_at', 'updated_at')

@admin.register(StudentGroup)
class StudentGroupAdmin(admin.ModelAdmin):
    list_display = ('student', 'group', 'joined_date', 'status')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'group__title')
    list_filter = ('status', 'joined_date', 'group')
    raw_id_fields = ('student', 'group')

@admin.register(Attendance)
class AttendanceAdmin(admin.ModelAdmin):
    list_display = ('student_group', 'date', 'status', 'marked_by')
    search_fields = ('student_group__student__user__first_name', 'student_group__student__user__last_name')
    list_filter = ('date', 'status')
    raw_id_fields = ('student_group', 'marked_by')

@admin.register(StudentProgress)
class StudentProgressAdmin(admin.ModelAdmin):
    list_display = ('student_group', 'date', 'grade', 'created_by')
    search_fields = ('student_group__student__user__first_name', 'student_group__student__user__last_name')
    list_filter = ('date', 'grade')
    raw_id_fields = ('student_group', 'created_by')
