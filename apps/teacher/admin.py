from django.contrib import admin
from .models import (
    Teacher, Sciences, Group, Schedule, LessonMaterial,
    Category, Quiz, Question, Answer, QuizAssignment, QuizAttempt, UserAnswer
)


@admin.register(Teacher)
class TeacherAdmin(admin.ModelAdmin):
    list_display = ('get_full_name', 'speciality', 'experience_years', 'hourly_rate')
    search_fields = ('user__first_name', 'user__last_name', 'speciality')
    list_filter = ('experience_years', 'speciality')


@admin.register(Sciences)
class SciencesAdmin(admin.ModelAdmin):
    list_display = ('name', 'status')
    search_fields = ('name',)
    list_filter = ('status',)


@admin.register(Group)
class GroupAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'science', 'branch', 'start_time', 'end_time', 'max_students', 'status')
    search_fields = ('title', 'teacher__user__first_name', 'teacher__user__last_name')
    list_filter = ('status', 'science', 'branch', 'week_type')


@admin.register(Schedule)
class ScheduleAdmin(admin.ModelAdmin):
    list_display = ('group', 'teacher', 'day_of_week', 'start_time', 'end_time', 'room')
    search_fields = ('group__title', 'teacher__user__first_name', 'teacher__user__last_name')
    list_filter = ('day_of_week',)


@admin.register(LessonMaterial)
class LessonMaterialAdmin(admin.ModelAdmin):
    list_display = ('title', 'group', 'created_at', 'created_by')
    search_fields = ('title', 'description', 'group__title')
    list_filter = ('created_at', 'group')


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name', 'description')


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 4


class QuestionInline(admin.StackedInline):
    model = Question
    extra = 1
    inlines = [AnswerInline]


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text', 'points')
    search_fields = ('text', 'quiz__title')
    list_filter = ('quiz', 'created_at')
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')
    search_fields = ('text', 'question__text')
    list_filter = ('is_correct', 'question__quiz')


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'difficulty', 'time_limit_minutes', 'passing_score', 'max_attempts', 'is_active')
    search_fields = ('title', 'description', 'topic')
    list_filter = ('is_active', 'difficulty', 'category', 'teacher')
    fieldsets = (
        (None, {
            'fields': ('title', 'description', 'teacher', 'category', 'topic')
        }),
        ('Settings', {
            'fields': ('difficulty', 'time_limit_minutes', 'passing_score', 'max_attempts', 'is_active')
        }),
    )


@admin.register(QuizAssignment)
class QuizAssignmentAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'group', 'start_time', 'end_time', 'is_active')
    search_fields = ('quiz__title', 'group__title')
    list_filter = ('is_active', 'start_time', 'end_time')
    date_hierarchy = 'start_time'


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ('question', 'selected_answer', 'written_answer', 'is_correct')
    can_delete = False


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'started_at', 'completed_at', 'is_completed', 'passed')
    search_fields = ('student__user__first_name', 'student__user__last_name', 'quiz__title')
    list_filter = ('is_completed', 'quiz', 'started_at')
    readonly_fields = ('student', 'quiz', 'quiz_assignment', 'score', 'started_at', 'completed_at', 'is_completed', 'passed', 'time_taken', 'score_percentage')
    date_hierarchy = 'started_at'
    inlines = [UserAnswerInline]

    def has_add_permission(self, request):
        return False


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_answer', 'is_correct')
    search_fields = ('attempt__student__user__username', 'question__text')
    list_filter = ('is_correct', 'attempt__quiz')
    readonly_fields = ('attempt', 'question', 'selected_answer', 'written_answer', 'is_correct')

    def has_add_permission(self, request):
        return False