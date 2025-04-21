from django.contrib import admin
from .models import Teacher, Sciences, Group, Schedule, LessonMaterial


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'speciality', 'experience_years', 'hourly_rate', 'created_at')
    search_fields = ('user__first_name', 'user__last_name', 'speciality')
    list_filter = ('experience_years', 'created_at')
    ordering = ('-created_at',)


@admin.register(Sciences)
class SciencesAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    search_fields = ('name',)
    list_filter = ('status',)


class ScheduleInline(admin.TabularInline):
    model = Schedule
    extra = 1


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'science', 'branch', 'week_type', 'start_time', 'end_time', 'price_per_month', 'status')
    search_fields = ('title', 'teacher__user__first_name', 'teacher__user__last_name')
    list_filter = ('branch', 'science', 'status', 'week_type')
    inlines = [ScheduleInline]


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('group', 'teacher', 'day_of_week', 'start_time', 'end_time', 'room')
    search_fields = ('group__title', 'teacher__user__first_name', 'teacher__user__last_name')
    list_filter = ('day_of_week', 'group', 'teacher')


@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'created_by', 'created_at')
    search_fields = ('title', 'description', 'group__title', 'created_by__first_name')
    list_filter = ('group', 'created_at')
