from rest_framework import serializers
from apps.student.models import Student, StudentGroup, Attendance, StudentProgress
from apps.users.models import User
from apps.teacher.models import Group, QuizAttempt, UserAnswer


class UserBasicSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'email', 'phone_number']


class StudentSerializer(serializers.ModelSerializer):
    user = UserBasicSerializer(read_only=True)
    full_name = serializers.CharField(source='get_full_name', read_only=True)
    
    class Meta:
        model = Student
        fields = ['id', 'user', 'full_name', 'home_phone', 'parent_name', 'parent_phone', 
                 'date_of_birth', 'status', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at']


class StudentCreateSerializer(serializers.ModelSerializer):
    first_name = serializers.CharField(write_only=True)
    last_name = serializers.CharField(write_only=True)
    email = serializers.EmailField(write_only=True)
    phone_number = serializers.CharField(write_only=True)
    password = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Student
        fields = ['first_name', 'last_name', 'email', 'phone_number', 'password',
                 'home_phone', 'parent_name', 'parent_phone', 'date_of_birth']
    
    def create(self, validated_data):
        user_data = {
            'first_name': validated_data.pop('first_name'),
            'last_name': validated_data.pop('last_name'),
            'email': validated_data.pop('email'),
            'phone_number': validated_data.pop('phone_number'),
            'user_role': 'student'  
        }
        
        if 'password' in validated_data:
            user_data['password'] = validated_data.pop('password')
        
        user = User.objects.create_user(**user_data)
        student = Student.objects.create(user=user, **validated_data)
        return student


class GroupBasicSerializer(serializers.ModelSerializer):
    teacher_name = serializers.CharField(source='teacher.get_full_name', read_only=True)
    science_name = serializers.CharField(source='science.name', read_only=True)
    
    class Meta:
        model = Group
        fields = ['id', 'title', 'teacher_name', 'science_name', 'start_time', 
                 'end_time', 'price_per_month']


class StudentGroupSerializer(serializers.ModelSerializer):
    group = GroupBasicSerializer(read_only=True)
    student = serializers.StringRelatedField(read_only=True)
    
    class Meta:
        model = StudentGroup
        fields = ['id', 'student', 'group', 'joined_date', 'status', 'notes']
        read_only_fields = ['joined_date']


class StudentGroupCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudentGroup
        fields = ['student', 'group', 'notes', 'status']
    
    def validate(self, data):
        if data['group'].is_full():
            raise serializers.ValidationError("This group is already full.")
            
        if StudentGroup.objects.filter(student=data['student'], group=data['group']).exists():
            raise serializers.ValidationError("Student is already enrolled in this group.")
            
        return data


class AttendanceSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student_group.student.get_full_name', read_only=True)
    group_title = serializers.CharField(source='student_group.group.title', read_only=True)
    marked_by_name = serializers.CharField(source='marked_by.get_full_name', read_only=True)
    
    class Meta:
        model = Attendance
        fields = ['id', 'student_group', 'student_name', 'group_title', 'date', 
                 'status', 'note', 'marked_by', 'marked_by_name', 'created_at', 'updated_at']
        read_only_fields = ['created_at', 'updated_at', 'marked_by']
    
    def create(self, validated_data):
        validated_data['marked_by'] = self.context['request'].user
        return super().create(validated_data)


class BulkAttendanceCreateSerializer(serializers.Serializer):
    group_id = serializers.IntegerField()
    date = serializers.DateField()
    attendance_data = serializers.ListField(
        child=serializers.DictField(
            child=serializers.CharField(),
            allow_empty=False
        )
    )


class StudentProgressSerializer(serializers.ModelSerializer):
    student_name = serializers.CharField(source='student_group.student.get_full_name', read_only=True)
    group_title = serializers.CharField(source='student_group.group.title', read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    class Meta:
        model = StudentProgress
        fields = ['id', 'student_group', 'student_name', 'group_title', 'date', 
                 'grade', 'comments', 'created_by', 'created_by_name', 'created_at']
        read_only_fields = ['created_at', 'created_by']
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AnswerSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserAnswer
        fields = ['id', 'question', 'selected_answer', 'written_answer', 'is_correct']
        read_only_fields = ['is_correct']


class QuizAttemptSerializer(serializers.ModelSerializer):
    user_answers = AnswerSerializer(many=True, read_only=True)
    quiz_title = serializers.CharField(source='quiz.title', read_only=True)
    score_percentage = serializers.IntegerField(read_only=True)
    time_taken = serializers.IntegerField(read_only=True)
    passed = serializers.BooleanField(read_only=True)
    
    class Meta:
        model = QuizAttempt
        fields = ['id', 'quiz', 'quiz_title', 'student', 'started_at', 'completed_at', 
                 'is_completed', 'score', 'score_percentage', 'time_taken', 'passed', 'user_answers']
        read_only_fields = ['started_at', 'score', 'score_percentage']


