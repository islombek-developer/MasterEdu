from rest_framework import serializers
from django.contrib.auth import aauthenticate
from django.contrib.auth.password_validation import validate_password
from .models import (Branch,User,Teacher,Student,DailyPayment,Attendance,Group,
StudentPaymentHistory, Schedule, Notification,StudentDebt,Salary,Expense,AttendanceReport)

from django.contrib.auth import authenticate
from rest_framework import serializers

class Loginserializers(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')

        if phone_number and password:
            # Telefon raqam orqali autentifikatsiya qilish
            user = authenticate(username=phone_number, password=password)
            
            if user:
                if not user.is_active:
                    raise serializers.ValidationError("Foydalanuvchi hisobi o'chirilgan")
                
                data['user'] = user
                return data

            raise serializers.ValidationError("Telefon raqam yoki parol noto‘g‘ri")
        
        raise serializers.ValidationError("Telefon raqam va parolni kiritish shart")


class RegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(write_only=True)  # Parolni tasdiqlash
    phone_number = serializers.CharField(required=True)  # Telefon raqamini talab qilish

    class Meta:
        model = User
        fields = ['phone_number', 'password', 'password2', 'email', 'first_name', 'last_name', 'user_role']
        extra_kwargs = {
            'password': {'write_only': True}
        }

    def validate(self, data):
        # Parollar mos kelishini tekshirish
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password2": "Parollar mos kelmadi."})

        # Parol uzunligini tekshirish (kamida 4 belgi)
        if len(data['password']) < 4:
            raise serializers.ValidationError({"password": "Parol kamida 4 belgidan iborat bo'lishi kerak."})

        # Telefon raqamini takrorlanmasligini tekshirish
        if User.objects.filter(phone_number=data['phone_number']).exists():
            raise serializers.ValidationError({"phone_number": "Ushbu telefon raqam bilan foydalanuvchi allaqachon mavjud."})

        return data

    def create(self, validated_data):
        validated_data.pop('password2')  # Parol tasdiqlashni olib tashlash

        # `username` ni `phone_number` ga teng qilib saqlash
        user = User.objects.create_user(
            username=validated_data['phone_number'],  
            phone_number=validated_data['phone_number'],  
            email=validated_data.get('email', ''),
            first_name=validated_data.get('first_name', ''),
            last_name=validated_data.get('last_name', ''),
            user_role=validated_data.get('user_role', ''),
            password=validated_data['password']  
        )
        
        return user


 
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

