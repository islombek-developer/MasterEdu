from django.contrib import admin
from .models import Teacher, Sciences, Group, Schedule, LessonMaterial,Category, Quiz, Question, Answer, QuizAttempt, UserAnswer

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'group', 'category', 'difficulty', 'time_limit_minutes', 'passing_score', 'is_active')
    list_filter = ('category', 'difficulty', 'is_active')
    search_fields = ('title', 'teacher__user__username', 'group__name')
    ordering = ('-created_at',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('text', 'quiz', 'points', 'created_at')
    search_fields = ('text', 'quiz__title')
    list_filter = ('quiz',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('text', 'question', 'is_correct')
    list_filter = ('is_correct',)
    search_fields = ('text', 'question__text')


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'started_at', 'completed_at', 'is_completed', 'passed')
    list_filter = ('quiz', 'is_completed')
    search_fields = ('student__user__username', 'quiz__title')


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_answer', 'is_correct')
    search_fields = ('attempt__student__user__username', 'question__text', 'selected_answer__text')
    list_filter = ('is_correct',)



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
