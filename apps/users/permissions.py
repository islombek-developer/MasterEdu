from rest_framework import permissions
from django.db.models import Q
from apps.users.models import User, Branch, Notification
from django.utils import timezone

class IsAuthenticated(permissions.BasePermission):
    """Faqat tizimga kirgan foydalanuvchilar uchun"""
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated)

class IsOwner(permissions.BasePermission):
    """Platforma egasi uchun ruxsat"""
    message = "Faqat platforma egasi bu amalni bajara oladi."
    
    def has_permission(self, request, view):
        return request.user.user_role == 'owner'

class IsBranchAdmin(permissions.BasePermission):
    """Filial admini uchun ruxsat"""
    message = "Faqat filial admini bu amalni bajara oladi."
    
    def has_permission(self, request, view):
        # Admin bo'lishi va kamida 1 ta filialga tegishli bo'lishi kerak
        return (request.user.user_role == 'admin' and 
                request.user.branch.exists())

class IsTeacher(permissions.BasePermission):
    """O'qituvchi uchun ruxsat"""
    message = "Faqat o'qituvchi bu amalni bajara oladi."
    
    def has_permission(self, request, view):
        return request.user.user_role == 'teacher'

class CanCreateBranch(permissions.BasePermission):
    """Filial yaratish uchun ruxsat"""
    message = "Siz yangi filial yarata olmaysiz."
    
    def has_permission(self, request, view):
        return request.user.can_create_branch()

class CanManageBranch(permissions.BasePermission):
    """Filialni boshqarish uchun ruxsat"""
    message = "Siz faqat o'z filialingizni boshqara olasiz."
    
    def has_object_permission(self, request, view, obj):
        if request.user.user_role == 'owner':
            return True
        elif request.user.user_role == 'admin':
            return obj in request.user.branch.all()
        return False

class CanCreateTeacher(permissions.BasePermission):
    """O'qituvchi yaratish uchun ruxsat"""
    message = "Siz yangi o'qituvchi yarata olmaysiz."
    
    def has_permission(self, request, view):
        return request.user.can_create_teacher()

class CanManageUser(permissions.BasePermission):
    """Foydalanuvchini boshqarish uchun ruxsat"""
    message = "Siz bu foydalanuvchini boshqara olmaysiz."
    
    def has_permission(self, request, view):
        # Ro'yxatni ko'rish uchun ruxsat
        if view.action in ['list', 'retrieve']:
            return True
        return request.user.can_manage_user(User())
    
    def has_object_permission(self, request, view, obj):
        return request.user.can_manage_user(obj)

class CanManageGroup(permissions.BasePermission):
    """Guruhni boshqarish uchun ruxsat"""
    message = "Siz bu guruhni boshqara olmaysiz."
    
    def has_permission(self, request, view):
        return request.user.user_role in ['owner', 'admin', 'teacher']
    
    def has_object_permission(self, request, view, obj):
        if request.user.user_role == 'owner':
            return True
        elif request.user.user_role == 'admin':
            return obj.branch in request.user.branch.all()
        elif request.user.user_role == 'teacher':
            return obj.teacher.user == request.user
        return False

class CanManagePayment(permissions.BasePermission):
    """To'lovlarni boshqarish uchun ruxsat"""
    message = "Siz to'lovlarni boshqara olmaysiz."
    
    def has_permission(self, request, view):
        return request.user.user_role in ['owner', 'admin']
    
    def has_object_permission(self, request, view, obj):
        if request.user.user_role == 'owner':
            return True
        elif request.user.user_role == 'admin':
            # To'lov filialga tegishli bo'lishi kerak
            return obj.branch in request.user.branch.all()
        return False

class CanViewStudent(permissions.BasePermission):
    """O'quvchi ma'lumotlarini ko'rish uchun ruxsat"""
    message = "Siz o'quvchi ma'lumotlarini ko'ra olmaysiz."
    
    def has_permission(self, request, view):
        return request.user.user_role in ['owner', 'admin', 'teacher', 'parent']
    
    def has_object_permission(self, request, view, obj):
        if request.user.user_role == 'owner':
            return True
        elif request.user.user_role == 'admin':
            return obj.branch.filter(id__in=request.user.branch.values_list('id', flat=True)).exists()
        elif request.user.user_role == 'teacher':
            # O'qituvchi o'z guruhidagi o'quvchilarni ko'ra oladi
            return obj.student_groups.filter(group__teacher__user=request.user).exists()
        elif request.user.user_role == 'parent':
            # Ota-ona faqat o'z farzandlarini ko'ra oladi
            return obj.parent == request.user
        return False

class CanSendNotification(permissions.BasePermission):
    """Xabar yuborish uchun ruxsat"""
    message = "Siz xabar yubora olmaysiz."
    
    def has_permission(self, request, view):
        return request.user.user_role in ['owner', 'admin', 'teacher']
    
    def has_object_permission(self, request, view, obj):
        # Faqat xabar yuboruvchisi yoki admin/owner uni tahrirlashi mumkin
        return (obj.created_by == request.user or 
                request.user.user_role in ['owner', 'admin'])

class HasActiveSubscription(permissions.BasePermission):
    """Faol obunaga ega bo'lishni tekshirish"""
    message = "Filialda faol obuna mavjud emas yoki muddati tugagan."
    
    def has_permission(self, request, view):
        if request.user.user_role == 'owner':
            return True
        
        if request.user.user_role in ['admin', 'teacher', 'student']:
            branches = request.user.branch.all()
            return any(branch.has_active_subscription() for branch in branches)
        
        return True
    
class IsOwnerOrAdmin(permissions.BasePermission):

    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return request.user.is_authenticated
        
 
        return request.user.is_authenticated and request.user.user_role in ['owner', 'admin']
    
    def has_object_permission(self, request, view, obj):
        if request.user.user_role == 'owner':
            return True
        elif request.user.user_role == 'admin':
            if isinstance(obj, Branch):
                return request.user.branch.filter(id=obj.id).exists()
            elif isinstance(obj, User):
                return request.user.can_manage_user(obj)
            return True
        return False
    
from rest_framework import permissions


class IsAdmin(permissions.BasePermission):
    """
    Permission to allow only users with admin role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_role == 'admin'


class IsTeacher(permissions.BasePermission):
    """
    Permission to allow only users with teacher role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_role == 'teacher'
    
    def has_object_permission(self, request, view, obj):
        # For group, quiz, and other objects that have a teacher field
        if hasattr(obj, 'teacher'):
            return obj.teacher.user == request.user
        return False


class IsOwnerTeacher(permissions.BasePermission):
    """
    Permission to allow only the teacher who owns the specific resource.
    """
    def has_object_permission(self, request, view, obj):
        # For group-related resources
        if hasattr(obj, 'group') and hasattr(obj.group, 'teacher'):
            return obj.group.teacher.user == request.user
            
        # For quiz-related resources
        if hasattr(obj, 'quiz') and hasattr(obj.quiz, 'teacher'):
            return obj.quiz.teacher.user == request.user
            
        # Direct teacher ownership
        if hasattr(obj, 'teacher'):
            return obj.teacher.user == request.user
            
        # For user-based ownership
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        return False


class IsStudent(permissions.BasePermission):
    """
    Permission to allow only users with student role.
    """
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.user_role == 'student'
    
    def has_object_permission(self, request, view, obj):
        # Access to their own quiz attempts
        if hasattr(obj, 'student'):
            return obj.student.user == request.user
        return False


class IsAdminOrTeacher(permissions.BasePermission):
    """
    Permission to allow users with either admin or teacher role.
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        return request.user.user_role in ['admin', 'teacher']
    
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.user_role == 'admin':
            return True
            
        # For teacher, check ownership
        if request.user.user_role == 'teacher':
            # For group resources
            if hasattr(obj, 'teacher'):
                return obj.teacher.user == request.user
                
            # For resources related to a group
            if hasattr(obj, 'group') and hasattr(obj.group, 'teacher'):
                return obj.group.teacher.user == request.user
        
        return False


class IsAdminOrOwner(permissions.BasePermission):
    """
    Permission to allow admin or the owner of a resource.
    """
    def has_object_permission(self, request, view, obj):
        # Admin can access anything
        if request.user.is_authenticated and request.user.user_role == 'admin':
            return True
            
        # Check if user is the owner
        if hasattr(obj, 'user'):
            return obj.user == request.user
            
        # For student resources
        if hasattr(obj, 'student') and hasattr(obj.student, 'user'):
            return obj.student.user == request.user
            
        # For teacher resources
        if hasattr(obj, 'teacher') and hasattr(obj.teacher, 'user'):
            return obj.teacher.user == request.user
            
        return False