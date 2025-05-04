
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .login import RegisterView,LoginView
from apps.users.v1.views.views import (
    CustomTokenObtainPairView,
    BranchViewSet,
    UserViewSet,
    NotificationViewSet
)

router = DefaultRouter()
router.register('branches', BranchViewSet, basename='branch')
router.register('users', UserViewSet, basename='user')
router.register('notifications', NotificationViewSet, basename='notification')

urlpatterns = [
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    path('', include(router.urls)),
    
    path('users/me/', UserViewSet.as_view({'get': 'me'}), name='user-me'),
    path('users/me/update/', UserViewSet.as_view({'put': 'update_me', 'patch': 'update_me'}), name='user-me-update'),
    path('users/teachers/', UserViewSet.as_view({'get': 'teachers'}), name='user-teachers'),
    path('users/students/', UserViewSet.as_view({'get': 'students'}), name='user-students'),

    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),

]

extra_urlpatterns = [
    path('branches/<int:pk>/activate/', BranchViewSet.as_view({'post': 'activate'}), name='branch-activate'),
    path('branches/<int:pk>/deactivate/', BranchViewSet.as_view({'post': 'deactivate'}), name='branch-deactivate'),
    path('branches/<int:pk>/subscription-status/', BranchViewSet.as_view({'get': 'subscription_status'}), name='branch-subscription-status'),
    
    path('users/<int:pk>/change-password/', UserViewSet.as_view({'post': 'change_password'}), name='user-change-password'),
    path('users/<int:pk>/activate/', UserViewSet.as_view({'post': 'activate'}), name='user-activate'),
    path('users/<int:pk>/deactivate/', UserViewSet.as_view({'post': 'deactivate'}), name='user-deactivate'),
    
    path('notifications/mark-all-as-read/', NotificationViewSet.as_view({'post': 'mark_all_as_read'}), name='notification-mark-all-read'),
    path('notifications/unread-count/', NotificationViewSet.as_view({'get': 'unread_count'}), name='notification-unread-count'),
]

urlpatterns += extra_urlpatterns