from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status,viewsets,validators,permissions
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Branch, User, Teacher
from .serializers import BranchSerializer,Teacherseritalizer,Userserializers
from rest_framework.decorators import action
from .permissions import IsOwner,IsOwnerOrAdmin


class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsOwnerOrAdmin]
    lookup_field = 'id'
    
    def get_queryset(self):
        user = self.request.user
        if user.user_role == 'owner':
            return Branch.objects.all()
        elif user.user_role == 'admin':
            return Branch.objects.filter(id__in=user.branch.values_list('id', flat=True))
        return Branch.objects.none()
    
    def perform_create(self, serializer):
        branch = serializer.save()
        if self.request.user.user_role == 'admin' and not self.request.user.branch:
            self.request.user.branch = branch
            self.request.user.save()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if request.user.user_role == 'admin' and request.user.branch != instance:
            return Response(
                {"detail": "You don't have permission to update this branch."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if request.user.user_role == 'admin' and request.user.branch != instance:
            return Response(
                {"detail": "You don't have permission to delete this branch."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)

class TeacherViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(user_role='teacher')
    serializer_class = Teacherseritalizer
    permission_classes = [IsOwnerOrAdmin]
    
    def get_queryset(self):
        user = self.request.user
        if user.user_role == 'owner':
            return Teacher.objects.all()
        elif user.user_role == 'admin':
            return Teacher.objects.filter(user__branch__in=user.branch.all())
        return Teacher.objects.none()
    
    def perform_create(self, serializer):
        user_data = serializer.validated_data
        user_data['user_role'] = 'teacher'
        
        created_teacher = serializer.save(
            created_by=self.request.user,
            managed_by=self.request.user
        )
        
        if self.request.user.user_role == 'admin' and self.request.user.branch:
            created_teacher.branch = self.request.user.branch
            created_teacher.save()
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if request.user.user_role == 'admin' and instance.branch != request.user.branch:
            return Response(
                {"detail": "You don't have permission to update this teacher."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        
        if request.user.user_role == 'admin' and instance.branch != request.user.branch:
            return Response(
                {"detail": "You don't have permission to delete this teacher."}, 
                status=status.HTTP_403_FORBIDDEN
            )
            
        return super().destroy(request, *args, **kwargs)


class UseradminViewSet(viewsets.ModelViewSet):
    queryset = User.objects.filter(user_role='admin')
    serializer_class = Userserializers
    permission_classes = [IsOwner]
    
    def perform_create(self, serializer):
        user_data = serializer.validated_data
        user_data['user_role'] = 'admin'
        
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def assign_to_branch(self, request, pk=None):
        admin = self.get_object()
        branch_id = request.data.get('branch_id')
        
        branch = get_object_or_404(Branch, pk=branch_id)
        
        if request.user.user_role == 'owner':
            admin.branch = branch
            admin.save()
            return Response({'status': 'admin assigned to branch'})
        return Response({'error': 'You cannot assign admin to branch'}, status=status.HTTP_403_FORBIDDEN)