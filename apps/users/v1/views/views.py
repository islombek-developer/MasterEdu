from rest_framework import viewsets, permissions, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q
from django.shortcuts import get_object_or_404
from django.utils import timezone
from apps.users.permissions import IsOwnerOrAdmin

from apps.users.models import Branch, User, Notification
from apps.users.v1.serializers.serializers import (
    BranchSerializer, 
    UserSerializer, 
    NotificationSerializer,
    CustomTokenObtainPairSerializer,
    ChangePasswordSerializer
)

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == 200:
            user = User.objects.get(username=request.data['username'])
            response.data['user'] = UserSerializer(user).data
        return response



class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsOwnerOrAdmin]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address', 'phone_number', 'email']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['name']
    
    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return Branch.objects.none()
            
        queryset = Branch.objects.all()
        
        if user.user_role == 'owner':
            return queryset
        elif user.user_role == 'admin':
            return queryset.filter(id__in=user.branch.values_list('id', flat=True))
        elif user.user_role in ['teacher', 'student']:
            return queryset.filter(id__in=user.branch.values_list('id', flat=True))
        return queryset.none()

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=['get'])
    def subscription_status(self, request, pk=None):
        branch = self.get_object()
        data = {
            'has_active_subscription': branch.has_active_subscription(),
            'is_trial': branch.is_on_trial()
        }
        
        current_subscription = branch.get_current_subscription()
        if current_subscription:
            data['subscription'] = {
                'id': current_subscription.id,
                'start_date': current_subscription.start_date,
                'end_date': current_subscription.end_date,
                'payment_status': current_subscription.payment_status,
                'plan_name': current_subscription.plan.name if current_subscription.plan else None
            }
        
        return Response(data)

    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        branch = self.get_object()
        branch.is_active = True
        branch.save()
        return Response({'status': 'branch activated'})

    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        branch = self.get_object()
        branch.is_active = False
        branch.save()
        return Response({'status': 'branch deactivated'})

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['user_role', 'status', 'branch']  
    search_fields = ['username', 'first_name', 'last_name', 'phone_number', 'email', 'address']
    ordering_fields = ['username', 'date_joined', 'first_name', 'last_name']
    ordering = ['-date_joined']

    def get_queryset(self):
        user = self.request.user
        if not user.is_authenticated:
            return User.objects.none()
            
        queryset = User.objects.all()
        
        if user.user_role == 'owner':
            return queryset
        elif user.user_role == 'admin':
            return queryset.filter(
                Q(branch__in=user.branch.all()) | 
                Q(created_by=user)
            ).distinct()
        elif user.user_role == 'teacher':
            from apps.teacher.models import Teacher
            teacher = get_object_or_404(Teacher, user=user)
            return queryset.filter(
                Q(id=user.id) | 
                Q(id__in=teacher.get_students().values_list('id', flat=True))
            )
        return queryset.filter(id=user.id)
    
    def get_permissions(self):
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsOwnerOrAdmin()]
        return [permissions.IsAuthenticated()]
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    def perform_update(self, serializer):
        serializer.save(updated_by=self.request.user, updated_at=timezone.now())
    
    @action(detail=False, methods=['get'])
    def me(self, request):
        serializer = self.get_serializer(request.user) 
        return Response(serializer.data)

    
    @action(detail=False, methods=['put', 'patch'])
    def update_me(self, request):
        user = request.user
        serializer = self.get_serializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def teachers(self, request):
        user = request.user
        if user.user_role in ['owner', 'admin']:
            queryset = self.filter_queryset(self.get_queryset().filter(user_role='teacher'))
            
            if user.user_role == 'admin':
                queryset = queryset.filter(branch__in=user.branch.all())
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=False, methods=['get'])
    def students(self, request):
        user = request.user
        if user.user_role in ['owner', 'admin', 'teacher']:
            queryset = self.filter_queryset(self.get_queryset().filter(user_role='student'))
            
            if user.user_role == 'admin':
                queryset = queryset.filter(branch__in=user.branch.all())
            elif user.user_role == 'teacher':
                from apps.teacher.models import Teacher
                teacher = get_object_or_404(Teacher, user=user)
                queryset = queryset.filter(id__in=teacher.get_students().values_list('id', flat=True))
            
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            
            serializer = self.get_serializer(queryset, many=True)
            return Response(serializer.data)
        return Response({"detail": "Permission denied"}, status=status.HTTP_403_FORBIDDEN)
    
    @action(detail=True, methods=['post'])
    def change_password(self, request, pk=None):
        user = self.get_object()
        if not request.user.can_manage_user(user) and request.user.id != user.id:
            return Response({"detail": "You don't have permission"}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ChangePasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        user.set_password(serializer.validated_data['password'])
        user.save()
        return Response({"detail": "Password changed successfully"})
    
    @action(detail=True, methods=['post'])
    def activate(self, request, pk=None):
        user = self.get_object()
        if not request.user.can_manage_user(user):
            return Response({"detail": "You don't have permission"}, status=status.HTTP_403_FORBIDDEN)
        
        user.is_active = True
        user.save()
        return Response({'status': 'user activated'})
    
    @action(detail=True, methods=['post'])
    def deactivate(self, request, pk=None):
        user = self.get_object()
        if not request.user.can_manage_user(user):
            return Response({"detail": "You don't have permission"}, status=status.HTTP_403_FORBIDDEN)
        
        user.is_active = False
        user.save()
        return Response({'status': 'user deactivated'})

    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        if notification.user != request.user:
            return Response({"detail": "Not your notification"}, status=status.HTTP_403_FORBIDDEN)
            
        notification.is_read = True
        notification.read_at = timezone.now()
        notification.save()
        return Response({"status": "notification marked as read"})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        updated = self.get_queryset().filter(is_read=False).update(
            is_read=True,
            read_at=timezone.now()
        )
        return Response({"status": f"{updated} notifications marked as read"})
    
    @action(detail=False, methods=['get'])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})

class NotificationViewSet(viewsets.ModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter]
    filterset_fields = ['is_read', 'related_to', 'notification_type']
    ordering_fields = ['created_at', 'is_read']
    ordering = ['-created_at']
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def mark_as_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"status": "notification marked as read"})
    
    @action(detail=False, methods=['post'])
    def mark_all_as_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({"status": "all notifications marked as read"})