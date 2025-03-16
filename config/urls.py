
from django.contrib import admin
from django.urls import path,include
from django.conf.urls.i18n import set_language

urlpatterns = [
    path('admin/', admin.site.urls),
    path('i18n/set_language/', set_language, name='set_language'), 
    path('api/', include("apps.users.urls")),
    path('api/teacher/', include("apps.teacher.urls")),
    path('api/student/', include("apps.student.urls")),
]
