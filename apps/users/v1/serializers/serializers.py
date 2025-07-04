from rest_framework import serializers
from apps.users.models import Branch, User, Notification
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError as DjangoValidationError

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        user = self.user
        data.update({
            'id': user.id,
            'username': user.username,
            'first_name': user.first_name,
            'last_name': user.last_name,
            'user_role': user.user_role,
            'branch_ids': list(user.branch.values_list('id', flat=True)),
            'phone_number': user.phone_number,
            'image': user.image.url if user.image else None,
        })
        return data

class BranchSerializer(serializers.ModelSerializer):
    has_subscription = serializers.SerializerMethodField()
    
    class Meta:
        model = Branch
        fields = '__all__'
        extra_kwargs = {
            'created_by': {'read_only': True}  
        }

    def get_has_subscription(self, obj):
        return obj.has_active_subscription()

    def create(self, validated_data):
        validated_data.pop('created_by', None)
        branch = Branch.objects.create(**validated_data)
        
        if self.context.get('request'):
            branch.created_by = self.context['request'].user
            branch.save()
        
        return branch

class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False)
    branch_names = serializers.SerializerMethodField()
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ('id', 'username', 'password', 'email', 'first_name', 'last_name', 
                  'full_name', 'phone_number', 'address', 'image', 'user_role', 
                  'branch', 'branch_names', 'status', 'date_joined')
        extra_kwargs = {
            'branch': {'required': False},
            'username': {'required': False},
        }
    
    def get_branch_names(self, obj):
        return [branch.name for branch in obj.branch.all()]
    
    def get_full_name(self, obj):
        return f'{obj.first_name} {obj.last_name}'

    def validate_status(self, value):
        if value not in ['active', 'inactive', 'archived']:
            raise serializers.ValidationError("Status must be 'active', 'inactive', or 'archived'")
        return value
    
    def create(self, validated_data):
        password = validated_data.pop('password', None)
        branches = validated_data.pop('branch', [])
        

        if not validated_data.get('username') and validated_data.get('phone_number'):
            validated_data['username'] = validated_data['phone_number']
            
        user = User.objects.create(**validated_data)
        
        if password:
            user.set_password(password)
            user.save()
            
        user.branch.set(branches)
        return user
    
    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        branches = validated_data.pop('branch', None)
        
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        
        if password:
            instance.set_password(password)
        
        if branches is not None:
            instance.branch.set(branches)
        
        instance.save()
        return instance

class NotificationSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = Notification
        fields = ['id', 'title', 'message', 'is_read', 'related_to', 'related_id', 
                  'created_at', 'created_by', 'created_by_name']
        read_only_fields = ['created_at', 'created_by']
    
    def get_created_by_name(self, obj):
        return f"{obj.created_by.first_name} {obj.created_by.last_name}"
    

class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=False, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True)
    confirm_password = serializers.CharField(required=True, write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        new_password = attrs.get('new_password')
        confirm_password = attrs.get('confirm_password')

  
        if new_password != confirm_password:
            raise serializers.ValidationError(
                {"new_password": "Password fields didn't match."}
            )

        if 'user' in self.context and self.context['user'] != user:
            return attrs

        old_password = attrs.get('old_password')
        if not user.check_password(old_password):
            raise serializers.ValidationError(
                {"old_password": "Old password is not correct"}
            )

        return attrs

    def validate_new_password(self, value):
        try:
            validate_password(value)
        except DjangoValidationError as e:
            raise serializers.ValidationError(list(e.messages))
        return value

    def save(self, **kwargs):
        user = self.context.get('user', self.context['request'].user)
        user.set_password(self.validated_data['new_password'])
        user.save()
        return user