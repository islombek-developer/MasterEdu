from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Branch, Notification, Status


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ('username', 'full_name', 'phone_number', 'user_role', 'status', 'is_active')
    list_filter = ('user_role', 'status', 'is_active')
    search_fields = ('username', 'first_name', 'last_name', 'phone_number')
    readonly_fields = ('last_login', 'date_joined')
    filter_horizontal = ('groups', 'user_permissions', 'branch')
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal Info', {
            'fields': (
                'first_name', 'last_name', 'email', 'image', 'phone_number', 'address',
                'jobs', 'telegram_chat_id'
            )
        }),
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Role & Branches', {'fields': ('user_role', 'branch', 'created_by', 'managed_by')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )


@admin.register(Branch)
class BranchAdmin(admin.ModelAdmin):
    list_display = ('name', 'phone_number', 'status', 'created_at')
    search_fields = ('name', 'address', 'phone_number')
    list_filter = ('status', 'created_at')


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ('title', 'user', 'is_read', 'created_at', 'created_by')
    search_fields = ('title', 'message', 'user__username', 'created_by__username')
    list_filter = ('is_read', 'created_at')
