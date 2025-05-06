from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.student.v1.views.views import (
    StudentViewSet, StudentGroupViewSet, AttendanceViewSet, StudentProgressViewSet
)

router = DefaultRouter()
router.register('students', StudentViewSet)
router.register('enrollments', StudentGroupViewSet)
router.register('attendance', AttendanceViewSet)
router.register('progress', StudentProgressViewSet)

urlpatterns = [
    path('', include(router.urls)),
]