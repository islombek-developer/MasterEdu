from django.urls import re_path
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
from django.urls import path,include
from rest_framework.routers import DefaultRouter
from apps.users.views import BranchViewSet,TeacherViewSet,UseradminViewSet
from .login import LoginAPIView,Registerview


router = DefaultRouter()
router.include_root_view = False

schema_view = get_schema_view(
   openapi.Info(
      title="Snippets API",
      default_version='v1',
      description="oqumarkazni avtomatlashtirish",
      terms_of_service="https://www.google.com/policies/terms/",
      contact=openapi.Contact(email="contact@snippets.local"),
      license=openapi.License(name="BSD License"),
   ),
   public=True,
   permission_classes=(permissions.AllowAny,),
)

urlpatterns = [
   
   path('',include(router.urls)),
   path('branchs/', BranchViewSet.as_view({'get': 'list','post':'create'}), name='restaurant-detail'),
   path('branch/<int:id>',BranchViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
   path('teachers/', TeacherViewSet.as_view({'get': 'list','post':'create'}), name='restaurant-detail'),
   path('teacher/<int:id>',TeacherViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),
   path('user-admins/', UseradminViewSet.as_view({'get': 'list','post':'create'}), name='restaurant-detail'),
   path('user-admin/<int:id>',UseradminViewSet.as_view({'get': 'retrieve', 'delete': 'destroy'})),

   path('login/', LoginAPIView.as_view()),
   path('register/', Registerview.as_view()),
   path('swagger.<format>/', schema_view.without_ui(cache_timeout=0), name='schema-json'),
   path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
   path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
]