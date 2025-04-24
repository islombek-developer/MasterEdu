
from django.utils import timezone
from django.db import models
from apps.users.models import User, Status
from apps.student.models import Student

class Teacher(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE)
    date_of_birth = models.DateField(null=True, blank=True)
    speciality = models.CharField(max_length=200, blank=True, null=True)
    education = models.CharField(max_length=200, blank=True, null=True)
    experience_years = models.PositiveIntegerField(default=0)
    hourly_rate = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    @property
    def admin(self):
        if self.user.managed_by and self.user.managed_by.user_role == 'admin':
            return self.user.managed_by
        return None
    
    @property
    def branch(self):
        return self.user.branch.first() or (self.admin.branch.first() if self.admin else None)
    
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return self.get_full_name()

class Sciences(models.Model):
    name = models.CharField(max_length=150)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(choices=Status.choices, max_length=15, default=Status.ACTIVE)
    
    class Meta:
        verbose_name = "Science"
        verbose_name_plural = "Sciences"

    def __str__(self):
        return self.name

class Group(models.Model):
    WEEK_CHOICES = (
        ('even', 'Even'),
        ('odd', 'Odd'),
        ('individual', 'Individual'),
        ('daily', 'Daily'),
    )
    title = models.CharField(max_length=150)
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='teacher_groups')
    science = models.ForeignKey(Sciences, on_delete=models.CASCADE)
    branch = models.ForeignKey('users.Branch', on_delete=models.CASCADE, related_name='groups')
    week_type = models.CharField(max_length=15, choices=WEEK_CHOICES, default='daily')
    start_time = models.TimeField()
    end_time = models.TimeField()
    max_students = models.PositiveIntegerField(default=15)
    price_per_month = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(choices=Status.choices, max_length=15, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.title} - {self.teacher.get_full_name()}"

    def is_full(self):
        return self.student_set.count() >= self.max_students


class Schedule(models.Model):
    DAY_CHOICES = [
        ('1', 'Monday'), 
        ('2', 'Tuesday'), 
        ('3', 'Wednesday'), 
        ('4', 'Thursday'), 
        ('5', 'Friday'), 
        ('6', 'Saturday'), 
        ('7', 'Sunday')
    ]
    
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='schedules')
    teacher = models.ForeignKey(Teacher, on_delete=models.CASCADE, related_name='schedules')
    day_of_week = models.CharField(max_length=10, choices=DAY_CHOICES)
    start_time = models.TimeField()
    end_time = models.TimeField()
    room = models.CharField(max_length=50, blank=True, null=True)  

    class Meta:
        unique_together = ['group', 'day_of_week', 'start_time']

    def __str__(self):
        return f"{self.group.title} - {self.get_day_of_week_display()} ({self.start_time}-{self.end_time})"

class LessonMaterial(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name='materials')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(upload_to='lesson_materials/', blank=True, null=True)
    link = models.URLField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='uploaded_materials')
    
    def __str__(self):
        return f"{self.group.title} - {self.title}"


class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name = "Kategoriya"
        verbose_name_plural = "Kategoriyalar"


class Quiz(models.Model):
    DIFFICULTY_CHOICES = [
        ('easy', 'Oson'),
        ('medium', 'O\'rta'),
        ('hard', 'Qiyin'),
    ]
    
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="quizzes")
    teacher = models.ForeignKey('Teacher', on_delete=models.CASCADE)
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES, default='medium')
    time_limit_minutes = models.IntegerField(default=30)
    passing_score = models.PositiveIntegerField(default=70)
    is_active = models.BooleanField(default=True)
    max_attempts = models.PositiveIntegerField(default=1, help_text="Maximum number of times a student can attempt this quiz")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    topic = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Test uchun asosiy mavzu (AI generatsiyasi uchun muhim)"
    )
    
    def __str__(self):
        return self.title
    
    class Meta:
        verbose_name = "Test"
        verbose_name_plural = "Testlar"


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    text = models.TextField()
    points = models.PositiveIntegerField(default=1)
    explanation = models.TextField(blank=True, help_text="Javobdan so'ng ko'rsatiladigan tushuntirish")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.text[:50] + ('...' if len(self.text) > 50 else '')
    
    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"
        ordering = ['quiz', 'id']


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    text = models.CharField(max_length=255)
    is_correct = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.text} - {'✓' if self.is_correct else '✗'}"
    
    class Meta:
        verbose_name = "Javob"
        verbose_name_plural = "Javoblar"


class QuizAssignment(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="assignments")
    group = models.ForeignKey('Group', on_delete=models.CASCADE, related_name="quiz_assignments")
    start_time = models.DateTimeField(help_text="Testni boshlash vaqti")
    end_time = models.DateTimeField(help_text="Testni yakunlash vaqti")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.quiz.title} for {self.group.title} ({self.start_time.strftime('%Y-%m-%d')})"
    
    class Meta:
        verbose_name = "Test tayinlash"
        verbose_name_plural = "Test tayinlashlar"


class QuizAttempt(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE)
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="attempts")
    quiz_assignment = models.ForeignKey(QuizAssignment, on_delete=models.CASCADE, related_name="attempts", null=True)
    score = models.FloatField(null=True, blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    is_completed = models.BooleanField(default=False)
    
    @property
    def time_taken(self):
        if self.completed_at:
            return (self.completed_at - self.started_at).total_seconds() // 60
        return None
    
    @property
    def passed(self):
        if self.score is None:
            return False
        return self.score >= self.quiz.passing_score
    
    def __str__(self):
        return f"{self.student.username} - {self.quiz.title} ({self.started_at.strftime('%Y-%m-%d')})"
    
    class Meta:
        verbose_name = "Test urinishi"
        verbose_name_plural = "Test urinishlari"

    def duration(self):
        if self.completed_at:
            return self.completed_at - self.started_at
        elif self.is_completed: 
            return self.quiz.time_limit_minutes * 60
        else:
            return timezone.now() - self.started_at

    def score_percentage(self):
        total_questions = self.user_answers.count()
        if total_questions > 0:
            correct_answers = self.user_answers.filter(is_correct=True).count()
            return round((correct_answers / total_questions) * 100)
        return 0
    
    @classmethod
    def get_attempts_count(cls, student, quiz):
        """Return the number of attempts a student has made for a specific quiz"""
        return cls.objects.filter(student=student, quiz=quiz).count()


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, related_name="user_answers")
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="user_answers")
    selected_answer = models.ForeignKey(Answer, on_delete=models.SET_NULL, null=True, blank=True, related_name="user_selections")
    written_answer = models.TextField(null=True, blank=True)
    is_correct = models.BooleanField(null=True, blank=True)
    
    def __str__(self):
        if self.selected_answer:
            return f"{self.attempt.student.username} - {self.question.text[:30]}... - {self.selected_answer.text}"
        return f"{self.attempt.student.username} - {self.question.text[:30]}... - {self.written_answer[:30] if self.written_answer else 'No answer'}"
    
    class Meta:
        verbose_name = "Foydalanuvchi javobi"
        verbose_name_plural = "Foydalanuvchi javoblari"
        unique_together = ['attempt', 'question']