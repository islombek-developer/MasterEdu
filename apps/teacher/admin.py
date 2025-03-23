from django.contrib import admin
from .models import Category,Question,Quiz,QuizAttempt,Answer,UserAnswer

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'description')
    search_fields = ('name',)


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = ('title', 'teacher', 'category', 'group', 'difficulty', 'time_limit_minutes', 'passing_score', 'is_active', 'start_time', 'end_time', 'created_at')
    list_filter = ('teacher', 'category', 'group', 'difficulty', 'is_active')
    search_fields = ('title',)
    ordering = ('-created_at',)


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ('quiz', 'text', 'points', 'created_at')
    list_filter = ('quiz',)
    search_fields = ('text',)


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ('question', 'text', 'is_correct')
    list_filter = ('question', 'is_correct')
    search_fields = ('text',)


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('student', 'quiz', 'score', 'started_at', 'completed_at', 'is_completed')
    list_filter = ('quiz', 'student', 'is_completed')
    search_fields = ('student__username', 'quiz__title')
    ordering = ('-started_at',)


@admin.register(UserAnswer)
class UserAnswerAdmin(admin.ModelAdmin):
    list_display = ('attempt', 'question', 'selected_answer', 'written_answer', 'is_correct')
    list_filter = ('attempt__quiz', 'is_correct')
    search_fields = ('attempt__student__username', 'question__text')
