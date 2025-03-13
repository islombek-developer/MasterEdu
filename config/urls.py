
from django.contrib import admin
from django.urls import path,include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include("apps.users.urls")),
    path('api/teacher/', include("apps.teacher.urls")),
    path('api/student/', include("apps.student.urls")),
]
