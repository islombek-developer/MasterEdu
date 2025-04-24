from rest_framework import serializers
from apps.users.models import Branch, User, Notification
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

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

    def get_has_subscription(self, obj):
        return obj.has_active_subscription()

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