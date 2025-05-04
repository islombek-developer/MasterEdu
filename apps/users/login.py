from rest_framework import serializers, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from django.db import IntegrityError

User = get_user_model()


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    password2 = serializers.CharField(write_only=True)
    
    class Meta:
        model = User
        fields = ['phone_number', 'first_name', 'last_name', 'password', 'password2', 'user_role']
        
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({'password': 'Passwords must match.'})
        
        if User.objects.filter(phone_number=data['phone_number']).exists():
            raise serializers.ValidationError({'phone_number': 'User with this phone number already exists.'})
        
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        validated_data['username'] = validated_data['phone_number']
        
        try:
            user = User.objects.create_user(**validated_data)
            return user
        except IntegrityError:
            raise serializers.ValidationError({'error': 'Something went wrong during registration'})


class RegisterView(generics.CreateAPIView):
    serializer_class = RegisterSerializer
    
    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        tokens = user.token()
        
        return Response({
            'message': 'User registered successfully',
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'full_name': user.full_name(),
                'user_role': user.user_role,
            },
            'tokens': tokens
        }, status=status.HTTP_201_CREATED)


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField(max_length=13)
    password = serializers.CharField(max_length=128, write_only=True)
    
    def validate(self, data):
        phone_number = data.get('phone_number')
        password = data.get('password')
        
        if phone_number and password:
            try:
                user = User.objects.get(phone_number=phone_number)
                user = authenticate(username=user.username, password=password)
                
                if not user:
                    raise serializers.ValidationError('Unable to log in with provided credentials.')
                
            except User.DoesNotExist:
                raise serializers.ValidationError('No user found with this phone number.')
        else:
            raise serializers.ValidationError('Must include "phone_number" and "password".')
        
        data['user'] = user
        return data


class LoginView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data['user']
        tokens = user.token()
        
        return Response({
            'message': 'Login successful',
            'user': {
                'id': user.id,
                'phone_number': user.phone_number,
                'full_name': user.full_name(),
                'user_role': user.user_role,
            },
            'tokens': tokens
        }, status=status.HTTP_200_OK)