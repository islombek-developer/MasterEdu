from rest_framework import serializers
from django.contrib.auth import aauthenticate
from django.contrib.auth.password_validation import validate_password
from .models import (Branch,User,Teacher,Student,DailyPayment,Attendance,Group,
StudentPaymentHistory, Schedule, Notification,StudentDebt,Salary,Expense,AttendanceReport)


class Loginserializers(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only = True)

    def validate(self, data):
        username = data.get('username')
        password = data.get('password')
        
        if username and password:
            user = aauthenticate(username=username,password=password)
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("Foydalanuvchi hisobi o'chirilgan")
                data['user']=user
                return data
            raise serializers.ValidationError("parol yoki username xato")
        raise serializers.ValidationError("Foydalanuvchi nomi va parolni kiritish kerak")


class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = '__all__'

    def validate(self, attrs):
        if attrs['password'] != attrs['username']:
            raise serializers.ValidationError({'password':'parol moskelmadi'})
        if attrs['user_role'] not in attrs['teacher','admin']:
            raise serializers.ValidationError({'user_role':'user_role tanlang teacher yoki admin'})
        return attrs
    
    def create(self, validated_data):
        validated_data.pop('password2')

        user=User.objects.create(
            username=validated_data['username'],
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            image=validated_data.get('image', None),
            phone_number=validated_data.get('phone_number', ''),
            address=validated_data.get('address', ''),
            jobs=validated_data.get('jobs', ''),
            user_role=validated_data['user_role']
        )
        user.set_password(validated_data['password'])
        user.save()

    
        

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

