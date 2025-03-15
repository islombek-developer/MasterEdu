from rest_framework import serializers
from .models import (Branch,User,Teacher,Student,DailyPayment,Attendance,Group,
StudentPaymentHistory, Schedule, Notification,StudentDebt,Salary,Expense,AttendanceReport)


class BranchSerializer(serializers.ModelSerializer):
    class Meta:
        model = Branch
        fields = '__all__'


class Teacherseritalizer(serializers.ModelSerializer):
    class Meta:
        model = Teacher
        fields = '__all__'

    def get_full_name(self, obj):
            return obj.get_full_name()
    
class Groupserializers(serializers.ModelSerializer):
    teacher = Teacherseritalizer()
    class Meta:
        model = Group
        fields = '__all__'

class Userserializers(serializers.ModelSerializer):
    branch_name = serializers.SerializerMethodField()
    teacher_details = serializers.SerializerMethodField()

    class Meta:
        model =User
        fields = '__all__'
        extra_kwargs = {
            'password': {'write_only': True},
            'branch': {'read_only': True},
            'created_by': {'read_only': True},
            'managed_by': {'read_only': True},
        }


    def get_branch(self,obj):
         return obj.branch.name if obj.branch else None
    
    def get_teacher_details(self,obj):
         if hasattr(obj,'teacher'):
              return Teacherseritalizer(obj.teacher).data
         return None

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
            
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        

        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
            
        instance.save()
        return instance
