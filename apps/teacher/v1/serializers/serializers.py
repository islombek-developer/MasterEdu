from rest_framework import serializers
from django.db.models import Avg, Count
from apps.teacher.models import (
    Teacher, Sciences, Group, Schedule, LessonMaterial, 
    Category, Quiz, Question, Answer, QuizAssignment, 
    QuizAttempt, UserAnswer
)
from apps.users.models import User
from apps.student.models import Student
from apps.users.v1.serializers.serializers import UserSerializer, BranchSerializer


class TeacherSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    full_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    total_groups = serializers.SerializerMethodField()
    
    class Meta:
        model = Teacher
        fields = ['id', 'user', 'full_name', 'date_of_birth', 'speciality', 
                 'education', 'experience_years', 'hourly_rate', 
                 'branch_name', 'total_groups', 'created_at', 'updated_at']
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    
    def get_branch_name(self, obj):
        branch = obj.branch
        return branch.name if branch else None
    
    def get_total_groups(self, obj):
        return obj.teacher_groups.count()


class TeacherCreateUpdateSerializer(serializers.ModelSerializer):
    user_id = serializers.IntegerField(write_only=True)
    
    class Meta:
        model = Teacher
        fields = ['id', 'user_id', 'date_of_birth', 'speciality', 
                 'education', 'experience_years', 'hourly_rate']
    
    def validate_user_id(self, value):
        try:
            user = User.objects.get(id=value)
            if hasattr(user, 'teacher'):
                raise serializers.ValidationError("This user already has a teacher profile")
            return value
        except User.DoesNotExist:
            raise serializers.ValidationError("User does not exist")

    def create(self, validated_data):
        user_id = validated_data.pop('user_id')
        user = User.objects.get(id=user_id)
        teacher = Teacher.objects.create(user=user, **validated_data)
        return teacher


class SciencesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sciences
        fields = ['id', 'name', 'description', 'status']


class ScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['id', 'group', 'teacher', 'day_of_week', 'day_name', 'start_time', 'end_time', 'room']


class GroupScheduleSerializer(serializers.ModelSerializer):
    day_name = serializers.CharField(source='get_day_of_week_display', read_only=True)
    
    class Meta:
        model = Schedule
        fields = ['id', 'day_of_week', 'day_name', 'start_time', 'end_time', 'room']


class LessonMaterialSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = LessonMaterial
        fields = ['id', 'group', 'title', 'description', 'file', 'link', 
                 'created_at', 'created_by', 'created_by_name']
    
    def get_created_by_name(self, obj):
        if obj.created_by:
            return f"{obj.created_by.first_name} {obj.created_by.last_name}"
        return None


class GroupSerializer(serializers.ModelSerializer):
    teacher_name = serializers.SerializerMethodField()
    science_name = serializers.SerializerMethodField()
    branch_name = serializers.SerializerMethodField()
    schedules = GroupScheduleSerializer(many=True, read_only=True)
    current_students = serializers.SerializerMethodField()
    
    class Meta:
        model = Group
        fields = ['id', 'title', 'teacher', 'teacher_name', 'science', 
                 'science_name', 'branch', 'branch_name', 'week_type', 
                 'start_time', 'end_time', 'max_students', 'current_students',
                 'price_per_month', 'status', 'schedules', 'created_at', 'updated_at']
    
    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name()
    
    def get_science_name(self, obj):
        return obj.science.name
    
    def get_branch_name(self, obj):
        return obj.branch.name
    
    def get_current_students(self, obj):
        return obj.student_set.count()


class GroupCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Group
        fields = ['id', 'title', 'teacher', 'science', 'branch', 'week_type', 
                 'start_time', 'end_time', 'max_students', 'price_per_month', 'status']
    
    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    {"time_error": "End time must be after start time"}
                )
        return data


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ['id', 'name', 'description']


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Answer
        fields = ['id', 'text', 'is_correct']


class QuestionSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = Question
        fields = ['id', 'text', 'points', 'explanation', 'answers', 'created_at']


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    answers = AnswerSerializer(many=True)
    
    class Meta:
        model = Question
        fields = ['id', 'quiz', 'text', 'points', 'explanation', 'answers']
    
    def create(self, validated_data):
        answers_data = validated_data.pop('answers')
        question = Question.objects.create(**validated_data)
        
        for answer_data in answers_data:
            Answer.objects.create(question=question, **answer_data)
        
        return question
    
    def update(self, instance, validated_data):
        answers_data = validated_data.pop('answers', None)
        
        # Update question fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update answers if provided
        if answers_data is not None:
            # Delete existing answers
            instance.answers.all().delete()
            
            # Create new answers
            for answer_data in answers_data:
                Answer.objects.create(question=instance, **answer_data)
        
        return instance


class QuizListSerializer(serializers.ModelSerializer):
    category_name = serializers.CharField(source='category.name', read_only=True)
    teacher_name = serializers.SerializerMethodField()
    questions_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'category', 'category_name', 'teacher', 
                 'teacher_name', 'difficulty', 'time_limit_minutes', 
                 'passing_score', 'is_active', 'questions_count', 
                 'max_attempts', 'created_at']
    
    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name()
    
    def get_questions_count(self, obj):
        return obj.questions.count()


class QuizDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    teacher_name = serializers.SerializerMethodField()
    questions = QuestionSerializer(many=True, read_only=True)
    
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'category', 'teacher', 
                 'teacher_name', 'difficulty', 'time_limit_minutes', 
                 'passing_score', 'is_active', 'max_attempts', 
                 'topic', 'questions', 'created_at', 'updated_at']
    
    def get_teacher_name(self, obj):
        return obj.teacher.get_full_name()


class QuizCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Quiz
        fields = ['id', 'title', 'description', 'category', 'teacher', 
                 'difficulty', 'time_limit_minutes', 'passing_score', 
                 'is_active', 'max_attempts', 'topic']


class QuizAssignmentSerializer(serializers.ModelSerializer):
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    group_title = serializers.CharField(source='group.title', read_only=True)
    
    class Meta:
        model = QuizAssignment
        fields = ['id', 'quiz', 'quiz_title', 'group', 'group_title', 
                 'start_time', 'end_time', 'is_active', 'created_at']

    def validate(self, data):
        if data.get('start_time') and data.get('end_time'):
            if data['start_time'] >= data['end_time']:
                raise serializers.ValidationError(
                    {"time_error": "End time must be after start time"}
                )
        return data


class UserAnswerSerializer(serializers.ModelSerializer):
    question_text = serializers.CharField(source='question.text', read_only=True)
    selected_answer_text = serializers.CharField(source='selected_answer.text', read_only=True)
    
    class Meta:
        model = UserAnswer
        fields = ['id', 'question', 'question_text', 'selected_answer', 
                 'selected_answer_text', 'written_answer', 'is_correct']


class QuizAttemptListSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    time_taken_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizAttempt
        fields = ['id', 'student', 'student_name', 'quiz', 'quiz_title', 
                 'quiz_assignment', 'score', 'started_at', 'completed_at', 
                 'is_completed', 'time_taken_minutes', 'passed']
    
    def get_student_name(self, obj):
        return f"{obj.student.user.first_name} {obj.student.user.last_name}"
    
    def get_time_taken_minutes(self, obj):
        return obj.time_taken


class QuizAttemptDetailSerializer(serializers.ModelSerializer):
    student_name = serializers.SerializerMethodField()
    quiz = QuizListSerializer(read_only=True)
    user_answers = UserAnswerSerializer(many=True, read_only=True)
    score_percentage = serializers.SerializerMethodField()
    time_taken_minutes = serializers.SerializerMethodField()
    
    class Meta:
        model = QuizAttempt
        fields = ['id', 'student', 'student_name', 'quiz', 'quiz_assignment', 
                 'score', 'score_percentage', 'started_at', 'completed_at', 
                 'is_completed', 'time_taken_minutes', 'passed', 'user_answers']
    
    def get_student_name(self, obj):
        return f"{obj.student.user.first_name} {obj.student.user.last_name}"
    
    def get_score_percentage(self, obj):
        return obj.score_percentage()
    
    def get_time_taken_minutes(self, obj):
        return obj.time_taken


class StudentQuizSerializer(serializers.ModelSerializer):
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'started_at', 'completed_at', 'is_completed', 'score', 'passed']


class StudentQuizDetailSerializer(serializers.ModelSerializer):
    quiz = QuizDetailSerializer(read_only=True)
    user_answers = UserAnswerSerializer(many=True, read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'started_at', 'completed_at', 'is_completed', 
                 'score', 'passed', 'user_answers']


class UserAnswerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['question', 'selected_answer', 'written_answer']
    
    def validate(self, data):
        question = data.get('question')
        selected_answer = data.get('selected_answer')
        
        if selected_answer and selected_answer.question != question:
            raise serializers.ValidationError(
                {"answer_error": "Selected answer does not belong to this question"}
            )
        
        return data

