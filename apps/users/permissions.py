from rest_framework import permissions
from .models import User,Branch

class IsOwnerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_role in ['owner', 'admin']
    def has_object_permission(self, request, view, obj):
        user = request.user
        
        # Owner can access everything
        if user.user_role == 'owner':
            return True
            
        # Admin can only access their own branch or users in their branch
        if user.user_role == 'admin':
            if isinstance(obj, Branch):
                return obj.id == user.branch.id if user.branch else False
            elif isinstance(obj, User):
                return obj.branch == user.branch if user.branch else False
            
        return False
class IsOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_role == 'owner'
