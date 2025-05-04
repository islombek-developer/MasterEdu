
from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.utils import timezone
from django.db.models import Q
from django.shortcuts import get_object_or_404


from apps.teacher.models import (
    Teacher, Sciences, Group, Schedule, LessonMaterial,
    Category, Quiz, Question, Answer, QuizAssignment,
    QuizAttempt, UserAnswer
)
from apps.teacher.v1.serializers.serializers import (
    TeacherSerializer, TeacherCreateUpdateSerializer,
    SciencesSerializer, GroupSerializer, GroupCreateUpdateSerializer,
    ScheduleSerializer, LessonMaterialSerializer,
    CategorySerializer, QuizListSerializer, QuizDetailSerializer,
    QuizCreateUpdateSerializer, QuestionSerializer, QuestionCreateUpdateSerializer,
    QuizAssignmentSerializer, QuizAttemptListSerializer, QuizAttemptDetailSerializer,
    UserAnswerSerializer, UserAnswerCreateSerializer,
    StudentQuizSerializer, StudentQuizDetailSerializer
)
from apps.users.permissions import (
    IsAdmin, IsTeacher, IsOwnerTeacher, IsStudent, IsAdminOrTeacher
)
from apps.student.models import Student


class TeacherViewSet(viewsets.ModelViewSet):
    queryset = Teacher.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['user__first_name', 'user__last_name', 'speciality']
    ordering_fields = ['user__first_name', 'experience_years', 'hourly_rate', 'created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return TeacherCreateUpdateSerializer
        return TeacherSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrTeacher])
    def groups(self, request, pk=None):
        teacher = self.get_object()
        groups = Group.objects.filter(teacher=teacher)
        serializer = GroupSerializer(groups, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrTeacher])
    def schedule(self, request, pk=None):
        teacher = self.get_object()
        schedules = Schedule.objects.filter(teacher=teacher).order_by('day_of_week', 'start_time')
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsAdminOrTeacher])
    def quizzes(self, request, pk=None):
        teacher = self.get_object()
        quizzes = Quiz.objects.filter(teacher=teacher)
        serializer = QuizListSerializer(quizzes, many=True)
        return Response(serializer.data)


class SciencesViewSet(viewsets.ModelViewSet):
    queryset = Sciences.objects.all()
    serializer_class = SciencesSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]


class GroupViewSet(viewsets.ModelViewSet):
    queryset = Group.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'teacher__user__first_name', 'teacher__user__last_name', 'science__name']
    ordering_fields = ['title', 'price_per_month', 'created_at']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return GroupCreateUpdateSerializer
        return GroupSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsAdmin]
        else:
            permission_classes = [IsAdminOrTeacher]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Group.objects.all()
        
        # Filter by teacher if specified
        teacher_id = self.request.query_params.get('teacher_id', None)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by science if specified
        science_id = self.request.query_params.get('science_id', None)
        if science_id:
            queryset = queryset.filter(science_id=science_id)
        
        # Filter by branch if specified
        branch_id = self.request.query_params.get('branch_id', None)
        if branch_id:
            queryset = queryset.filter(branch_id=branch_id)
        
        # Filter by status if specified
        status_filter = self.request.query_params.get('status', None)
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def schedules(self, request, pk=None):
        group = self.get_object()
        schedules = Schedule.objects.filter(group=group).order_by('day_of_week', 'start_time')
        serializer = ScheduleSerializer(schedules, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def materials(self, request, pk=None):
        group = self.get_object()
        materials = LessonMaterial.objects.filter(group=group).order_by('-created_at')
        serializer = LessonMaterialSerializer(materials, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def students(self, request, pk=None):
        group = self.get_object()
        from apps.student.serializers import StudentSerializer
        students = Student.objects.filter(groups=group)
        serializer = StudentSerializer(students, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        group = self.get_object()
        assignments = QuizAssignment.objects.filter(group=group).order_by('-start_time')
        serializer = QuizAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)


class ScheduleViewSet(viewsets.ModelViewSet):
    queryset = Schedule.objects.all()
    serializer_class = ScheduleSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['day_of_week', 'start_time', 'end_time']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Schedule.objects.all()
        
        # Filter by group if specified
        group_id = self.request.query_params.get('group_id', None)
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        # Filter by teacher if specified
        teacher_id = self.request.query_params.get('teacher_id', None)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by day if specified
        day = self.request.query_params.get('day', None)
        if day:
            queryset = queryset.filter(day_of_week=day)
        
        return queryset


class LessonMaterialViewSet(viewsets.ModelViewSet):
    queryset = LessonMaterial.objects.all()
    serializer_class = LessonMaterialSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description']
    ordering_fields = ['created_at', 'title']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminOrTeacher]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = LessonMaterial.objects.all()
        
        # Filter by group if specified
        group_id = self.request.query_params.get('group_id', None)
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdmin]
        return [permission() for permission in permission_classes]


class QuizViewSet(viewsets.ModelViewSet):
    queryset = Quiz.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'topic', 'category__name']
    ordering_fields = ['title', 'difficulty', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizDetailSerializer
        elif self.action in ['create', 'update', 'partial_update']:
            return QuizCreateUpdateSerializer
        return QuizListSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminOrTeacher]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Quiz.objects.all()
        
        # If user is a teacher, only show their quizzes
        if self.request.user.user_role == 'teacher':
            teacher = get_object_or_404(Teacher, user=self.request.user)
            queryset = queryset.filter(teacher=teacher)
        
        # Filter by teacher if specified
        teacher_id = self.request.query_params.get('teacher_id', None)
        if teacher_id:
            queryset = queryset.filter(teacher_id=teacher_id)
        
        # Filter by category if specified
        category_id = self.request.query_params.get('category_id', None)
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        
        # Filter by difficulty if specified
        difficulty = self.request.query_params.get('difficulty', None)
        if difficulty:
            queryset = queryset.filter(difficulty=difficulty)
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def questions(self, request, pk=None):
        quiz = self.get_object()
        questions = Question.objects.filter(quiz=quiz)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def assignments(self, request, pk=None):
        quiz = self.get_object()
        assignments = QuizAssignment.objects.filter(quiz=quiz).order_by('-start_time')
        serializer = QuizAssignmentSerializer(assignments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attempts(self, request, pk=None):
        quiz = self.get_object()
        attempts = QuizAttempt.objects.filter(quiz=quiz).order_by('-started_at')
        serializer = QuizAttemptListSerializer(attempts, many=True)
        return Response(serializer.data)


class QuestionViewSet(viewsets.ModelViewSet):
    queryset = Question.objects.all()
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['text']
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return QuestionCreateUpdateSerializer
        return QuestionSerializer
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminOrTeacher]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = Question.objects.all()
        
        # Filter by quiz if specified
        quiz_id = self.request.query_params.get('quiz_id', None)
        if quiz_id:
            queryset = queryset.filter(quiz_id=quiz_id)
        
        return queryset


class QuizAssignmentViewSet(viewsets.ModelViewSet):
    queryset = QuizAssignment.objects.all()
    serializer_class = QuizAssignmentSerializer
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['start_time', 'end_time', 'created_at']
    
    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminOrTeacher]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = QuizAssignment.objects.all()
        
        # Filter by quiz if specified
        quiz_id = self.request.query_params.get('quiz_id', None)
        if quiz_id:
            queryset = queryset.filter(quiz_id=quiz_id)
        
        # Filter by group if specified
        group_id = self.request.query_params.get('group_id', None)
        if group_id:
            queryset = queryset.filter(group_id=group_id)
        
        # Filter by active status if specified
        is_active = self.request.query_params.get('is_active', None)
        if is_active is not None:
            is_active = is_active.lower() == 'true'
            queryset = queryset.filter(is_active=is_active)
        
        # Filter by date range if specified
        now = timezone.now()
        active_now = self.request.query_params.get('active_now', None)
        if active_now is not None and active_now.lower() == 'true':
            queryset = queryset.filter(start_time__lte=now, end_time__gte=now, is_active=True)
        
        return queryset
    
    @action(detail=True, methods=['get'])
    def attempts(self, request, pk=None):
        assignment = self.get_object()
        attempts = QuizAttempt.objects.filter(quiz_assignment=assignment).order_by('-started_at')
        serializer = QuizAttemptListSerializer(attempts, many=True)
        return Response(serializer.data)


class QuizAttemptViewSet(viewsets.ModelViewSet):
    queryset = QuizAttempt.objects.all()
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['started_at', 'completed_at', 'score']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return QuizAttemptDetailSerializer
        return QuizAttemptListSerializer
    
    def get_permissions(self):
        if self.action in ['create', 'submit_answers']:
            permission_classes = [IsStudent]
        elif self.action in ['list', 'retrieve']:
            permission_classes = [permissions.IsAuthenticated]
        else:
            permission_classes = [IsAdminOrTeacher]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        queryset = QuizAttempt.objects.all()
        
        if self.request.user.user_role == 'student':
            student = get_object_or_404(Student, user=self.request.user)
            queryset = queryset.filter(student=student)
        
        elif self.request.user.user_role == 'teacher':
            teacher = get_object_or_404(Teacher, user=self.request.user)
            queryset = queryset.filter(quiz__teacher=teacher)
        
        student_id = self.request.query_params.get('student_id', None)
        if student_id:
            queryset = queryset.filter(student_id=student_id)
        
        quiz_id = self.request.query_params.get('quiz_id', None)
        if quiz_id:
            queryset = queryset.filter(quiz_id=quiz_id)
        
    
        assignment_id = self.request.query_params.get('assignment_id', None)
        if assignment_id:
            queryset = queryset.filter(quiz_assignment_id=assignment_id)

        is_completed = self.request.query_params.get('is_completed', None)
        if is_completed is not None:
            is_completed = is_completed.lower() == 'true'
            queryset = queryset.filter(is_completed=is_completed)
      
        passed = self.request.query_params.get('passed', None)
        if passed is not None:
            passed = passed.lower() == 'true'
            if passed:
                queryset = queryset.filter(score__gte=models.F('quiz__passing_score'))
            else:
                queryset = queryset.filter(
                    Q(score__lt=models.F('quiz__passing_score')) | Q(score__isnull=True)
                )
        
        return queryset
    
    def create(self, request, *args, **kwargs):
        student = get_object_or_404(Student, user=request.user)
        quiz_id = request.data.get('quiz')
        quiz = get_object_or_404(Quiz, id=quiz_id)
        assignment_id = request.data.get('quiz_assignment')
        
        # Check attempts limit
        attempts_count = QuizAttempt.get_attempts_count(student, quiz)
        if attempts_count >= quiz.max_attempts:
            return Response(
                {"error": "Maximum number of attempts reached"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # If assignment provided, validate it's still active
        if assignment_id:
            assignment = get_object_or_404(QuizAssignment, id=assignment_id)
            now = timezone.now()
            if now < assignment.start_time or now > assignment.end_time or not assignment.is_active:
                return Response(
                    {"error": "The quiz assignment is not active at this time"},
                    status=status.HTTP_400_BAD_REQUEST
                )
        
        # Create new attempt
        attempt = QuizAttempt.objects.create(
            student=student,
            quiz=quiz,
            quiz_assignment_id=assignment_id if assignment_id else None
        )
        
        serializer = QuizAttemptDetailSerializer(attempt)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    @action(detail=True, methods=['post'], permission_classes=[IsStudent])
    def submit_answers(self, request, pk=None):
        attempt = self.get_object()
        student = get_object_or_404(Student, user=request.user)
        
        # Verify this attempt belongs to the student
        if attempt.student != student:
            return Response(
                {"error": "You do not have permission to submit answers for this attempt"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        # Verify attempt is not already completed
        if attempt.is_completed:
            return Response(
                {"error": "This quiz attempt has already been completed"},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Process answers
        answers_data = request.data.get('answers', [])
        correct_count = 0
        total_points = 0
        
        for answer_data in answers_data:
            question_id = answer_data.get('question')
            question = get_object_or_404(Question, id=question_id, quiz=attempt.quiz)
            selected_answer_id = answer_data.get('selected_answer')
            written_answer = answer_data.get('written_answer')
            
            # Skip if no answer was provided
            if not selected_answer_id and not written_answer:
                continue
            
            # Get the selected answer if provided
            selected_answer = None
            is_correct = False
            if selected_answer_id:
                selected_answer = get_object_or_404(Answer, id=selected_answer_id, question=question)
                is_correct = selected_answer.is_correct
            
            # Create or update user answer
            user_answer, created = UserAnswer.objects.update_or_create(
                attempt=attempt,
                question=question,
                defaults={
                    'selected_answer': selected_answer,
                    'written_answer': written_answer,
                    'is_correct': is_correct
                }
            )
            
            if is_correct:
                correct_count += 1
                total_points += question.points
        
        # Calculate score
        total_questions = attempt.quiz.questions.count()
        if total_questions > 0:
            score = (correct_count / total_questions) * 100
        else:
            score = 0
        
        # Complete the attempt
        attempt.score = score
        attempt.completed_at = timezone.now()
        attempt.is_completed = True
        attempt.save()
        
        serializer = QuizAttemptDetailSerializer(attempt)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[IsStudent])
    def questions(self, request, pk=None):
        attempt = self.get_object()
        student = get_object_or_404(Student, user=request.user)
        
        # Verify this attempt belongs to the student
        if attempt.student != student:
            return Response(
                {"error": "You do not have permission to view questions for this attempt"},
                status=status.HTTP_403_FORBIDDEN
            )
        
        questions = attempt.quiz.questions.all()
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def answers(self, request, pk=None):
        attempt = self.get_object()
        
        # Students can only view their own answers
        if self.request.user.user_role == 'student':
            student = get_object_or_404(Student, user=request.user)
            if attempt.student != student:
                return Response(
                    {"error": "You do not have permission to view these answers"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        # Teachers can only view answers for their quizzes
        elif self.request.user.user_role == 'teacher':
            teacher = get_object_or_404(Teacher, user=request.user)
            if attempt.quiz.teacher != teacher:
                return Response(
                    {"error": "You do not have permission to view these answers"},
                    status=status.HTTP_403_FORBIDDEN
                )
        
        user_answers = UserAnswer.objects.filter(attempt=attempt)
        serializer = UserAnswerSerializer(user_answers, many=True)
        return Response(serializer.data)


class StudentQuizViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Viewset for students to view their quiz attempts
    """
    serializer_class = StudentQuizSerializer
    permission_classes = [IsStudent]
    
    def get_queryset(self):
        student = get_object_or_404(Student, user=self.request.user)
        queryset = QuizAttempt.objects.filter(student=student).order_by('-started_at')
        
        # Filter by quiz if specified
        quiz_id = self.request.query_params.get('quiz_id', None)
        if quiz_id:
            queryset = queryset.filter(quiz_id=quiz_id)
        
        # Filter by completion status if specified
        is_completed = self.request.query_params.get('is_completed', None)
        if is_completed is not None:
            is_completed = is_completed.lower() == 'true'
            queryset = queryset.filter(is_completed=is_completed)
        
        return queryset
    
    def retrieve(self, request, pk=None):
        student = get_object_or_404(Student, user=request.user)
        attempt = get_object_or_404(QuizAttempt, pk=pk, student=student)
        serializer = StudentQuizDetailSerializer(attempt)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def available_quizzes(self, request):
        student = get_object_or_404(Student, user=request.user)
        
        # Get all groups the student is in
        student_groups = student.groups.all()
        
        # Get all active quiz assignments for these groups
        now = timezone.now()
        active_assignments = QuizAssignment.objects.filter(
            group__in=student_groups,
            start_time__lte=now,
            end_time__gte=now,
            is_active=True
        )
        
        response_data = []
        for assignment in active_assignments:
            quiz = assignment.quiz
            
            # Check attempts limit
            attempts_count = QuizAttempt.get_attempts_count(student, quiz)
            can_attempt = attempts_count < quiz.max_attempts
            
            # Get latest attempt if exists
            latest_attempt = None
            attempts = QuizAttempt.objects.filter(
                student=student,
                quiz=quiz,
                quiz_assignment=assignment
            ).order_by('-started_at')
            
            if attempts.exists():
                latest_attempt = StudentQuizSerializer(attempts.first()).data
            
            response_data.append({
                'quiz_assignment': {
                    'id': assignment.id,
                    'start_time': assignment.start_time,
                    'end_time': assignment.end_time,
                },
                'quiz': {
                    'id': quiz.id,
                    'title': quiz.title,
                    'category': quiz.category.name,
                    'difficulty': quiz.difficulty,
                    'time_limit_minutes': quiz.time_limit_minutes,
                    'passing_score': quiz.passing_score,
                },
                'group': {
                    'id': assignment.group.id,
                    'title': assignment.group.title,
                },
                'attempts_count': attempts_count,
                'max_attempts': quiz.max_attempts,
                'can_attempt': can_attempt,
                'latest_attempt': latest_attempt
            })
        
        return Response(response_data)


# URLs - urls.py

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeacherViewSet, SciencesViewSet, GroupViewSet, ScheduleViewSet,
    LessonMaterialViewSet, CategoryViewSet, QuizViewSet, QuestionViewSet,
    QuizAssignmentViewSet, QuizAttemptViewSet, StudentQuizViewSet
)