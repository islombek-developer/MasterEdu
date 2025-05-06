
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Avg, Count
from django.utils import timezone

from apps.student.models import Student, StudentGroup, Attendance, StudentProgress
from apps.teacher.models import QuizAttempt, Group
from apps.student.serializers import (
    StudentSerializer, StudentCreateSerializer, StudentGroupSerializer,
    StudentGroupCreateSerializer, AttendanceSerializer, BulkAttendanceCreateSerializer,
    StudentProgressSerializer, QuizAttemptSerializer
)
from apps.users.permissions import IsAdmin, IsTeacher, IsTeacherOrAdmin


class StudentViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing students.
    """
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status']
    search_fields = ['user__first_name', 'user__last_name', 'user__email', 'parent_name']
    ordering_fields = ['user__first_name', 'user__last_name', 'created_at']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return StudentCreateSerializer
        return StudentSerializer
    
    @action(detail=True, methods=['get'])
    def groups(self, request, pk=None):
        """Get all groups that the student is enrolled in"""
        student = self.get_object()
        enrollments = StudentGroup.objects.filter(student=student)
        serializer = StudentGroupSerializer(enrollments, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def attendances(self, request, pk=None):
        """Get student's attendance records"""
        student = self.get_object()
        student_groups = StudentGroup.objects.filter(student=student)
        
        # Filter parameters
        group_id = request.query_params.get('group_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        attendances = Attendance.objects.filter(student_group__in=student_groups)
        
        if group_id:
            attendances = attendances.filter(student_group__group_id=group_id)
        if start_date:
            attendances = attendances.filter(date__gte=start_date)
        if end_date:
            attendances = attendances.filter(date__lte=end_date)
            
        serializer = AttendanceSerializer(attendances, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """Get student's progress records"""
        student = self.get_object()
        student_groups = StudentGroup.objects.filter(student=student)
        
        # Filter parameters
        group_id = request.query_params.get('group_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        progress_records = StudentProgress.objects.filter(student_group__in=student_groups)
        
        if group_id:
            progress_records = progress_records.filter(student_group__group_id=group_id)
        if start_date:
            progress_records = progress_records.filter(date__gte=start_date)
        if end_date:
            progress_records = progress_records.filter(date__lte=end_date)
            
        serializer = StudentProgressSerializer(progress_records, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def quiz_attempts(self, request, pk=None):
        """Get student's quiz attempts"""
        student = self.get_object()
        quiz_attempts = QuizAttempt.objects.filter(student=student)
        
        # Filter parameters
        quiz_id = request.query_params.get('quiz_id')
        completed = request.query_params.get('completed')
        passed = request.query_params.get('passed')
        
        if quiz_id:
            quiz_attempts = quiz_attempts.filter(quiz_id=quiz_id)
        if completed:
            is_completed = completed.lower() == 'true'
            quiz_attempts = quiz_attempts.filter(is_completed=is_completed)
        if passed:
            # Custom filtering for passed property
            quiz_attempts = [attempt for attempt in quiz_attempts if attempt.passed == (passed.lower() == 'true')]
            
        serializer = QuizAttemptSerializer(quiz_attempts, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def statistics(self, request, pk=None):
        """Get statistics for a student"""
        student = self.get_object()
        student_groups = StudentGroup.objects.filter(student=student)
        
        # Attendance statistics
        attendance_stats = Attendance.objects.filter(student_group__in=student_groups).values(
            'status'
        ).annotate(count=Count('id'))
        
        # Progress statistics
        avg_grade = StudentProgress.objects.filter(student_group__in=student_groups).aggregate(
            avg_grade=Avg('grade')
        )
        
        # Quiz statistics
        quiz_stats = QuizAttempt.objects.filter(student=student).aggregate(
            total_attempts=Count('id'),
            completed_attempts=Count('id', filter=models.Q(is_completed=True)),
            avg_score=Avg('score', filter=models.Q(is_completed=True))
        )
        
        return Response({
            'attendance': attendance_stats,
            'progress': avg_grade,
            'quizzes': quiz_stats
        })


class StudentGroupViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student enrollments in groups.
    """
    queryset = StudentGroup.objects.all()
    serializer_class = StudentGroupSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student', 'group', 'status']
    ordering_fields = ['joined_date', 'status']
    
    def get_serializer_class(self):
        if self.action == 'create' or self.action == 'update':
            return StudentGroupCreateSerializer
        return StudentGroupSerializer
    
    @action(detail=False, methods=['get'])
    def by_group(self, request):
        """Get all students enrolled in a specific group"""
        group_id = request.query_params.get('group_id')
        if not group_id:
            return Response({"error": "Group ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        enrollments = self.queryset.filter(group_id=group_id)
        serializer = self.get_serializer(enrollments, many=True)
        return Response(serializer.data)


class AttendanceViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student attendance.
    """
    queryset = Attendance.objects.all()
    serializer_class = AttendanceSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student_group', 'student_group__student', 'student_group__group', 'date', 'status']
    ordering_fields = ['date', 'status', 'created_at']
    
    @action(detail=False, methods=['post'])
    def bulk_create(self, request):
        """Create attendance records for multiple students in a group at once"""
        serializer = BulkAttendanceCreateSerializer(data=request.data)
        
        if serializer.is_valid():
            group_id = serializer.validated_data['group_id']
            date = serializer.validated_data['date']
            attendance_data = serializer.validated_data['attendance_data']
            
            created_attendances = []
            errors = []
            
            for item in attendance_data:
                student_id = item.get('student_id')
                status = item.get('status')
                note = item.get('note', '')
                
                try:
                    student_group = StudentGroup.objects.get(student_id=student_id, group_id=group_id)
                    
                    # Update existing or create new attendance
                    attendance, created = Attendance.objects.update_or_create(
                        student_group=student_group,
                        date=date,
                        defaults={
                            'status': status,
                            'note': note,
                            'marked_by': request.user
                        }
                    )
                    created_attendances.append(attendance)
                except StudentGroup.DoesNotExist:
                    errors.append({
                        'student_id': student_id,
                        'error': 'Student is not enrolled in this group'
                    })
            
            if errors:
                return Response({
                    'created': AttendanceSerializer(created_attendances, many=True).data,
                    'errors': errors
                }, status=status.HTTP_207_MULTI_STATUS)
                
            return Response(
                AttendanceSerializer(created_attendances, many=True).data, 
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def by_group_date(self, request):
        """Get attendance records for a specific group on a specific date"""
        group_id = request.query_params.get('group_id')
        date = request.query_params.get('date', timezone.localdate())
        
        if not group_id:
            return Response({"error": "Group ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        attendances = self.queryset.filter(
            student_group__group_id=group_id,
            date=date
        )
        
        serializer = self.get_serializer(attendances, many=True)
        return Response(serializer.data)


class StudentProgressViewSet(viewsets.ModelViewSet):
    """
    API endpoint for managing student progress.
    """
    queryset = StudentProgress.objects.all()
    serializer_class = StudentProgressSerializer
    permission_classes = [IsAuthenticated, IsTeacherOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['student_group', 'student_group__student', 'student_group__group', 'date']
    ordering_fields = ['date', 'grade', 'created_at']
    
    @action(detail=False, methods=['get'])
    def by_group(self, request):
        """Get progress records for a specific group"""
        group_id = request.query_params.get('group_id')
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')
        
        if not group_id:
            return Response({"error": "Group ID is required"}, status=status.HTTP_400_BAD_REQUEST)
            
        progress_records = self.queryset.filter(student_group__group_id=group_id)
        
        if start_date:
            progress_records = progress_records.filter(date__gte=start_date)
        if end_date:
            progress_records = progress_records.filter(date__lte=end_date)
        
        serializer = self.get_serializer(progress_records, many=True)
        return Response(serializer.data)



