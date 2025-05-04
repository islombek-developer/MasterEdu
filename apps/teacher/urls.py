from django.urls import path, include
from rest_framework.routers import DefaultRouter
from apps.teacher.v1.views.views import (
    TeacherViewSet, SciencesViewSet, GroupViewSet, ScheduleViewSet,
    LessonMaterialViewSet, CategoryViewSet, QuizViewSet, QuestionViewSet,
    QuizAssignmentViewSet, QuizAttemptViewSet, StudentQuizViewSet
)

router = DefaultRouter()


router.register('teachers', TeacherViewSet, basename='teacher')
router.register('sciences', SciencesViewSet, basename='science')
router.register('groups', GroupViewSet, basename='group')
router.register('schedules', ScheduleViewSet, basename='schedule')
router.register('materials', LessonMaterialViewSet, basename='material')
router.register('categories', CategoryViewSet, basename='category')
router.register('quizzes', QuizViewSet, basename='quiz')
router.register('questions', QuestionViewSet, basename='question')
router.register('assignments', QuizAssignmentViewSet, basename='assignment')
router.register('attempts', QuizAttemptViewSet, basename='attempt')

urlpatterns = [
  
    path('', include(router.urls)),
    

    path('teachers/<int:pk>/groups/', TeacherViewSet.as_view({'get': 'groups'}), name='teacher-groups'),
    path('teachers/<int:pk>/schedule/', TeacherViewSet.as_view({'get': 'schedule'}), name='teacher-schedule'),
    path('teachers/<int:pk>/quizzes/', TeacherViewSet.as_view({'get': 'quizzes'}), name='teacher-quizzes'),
    

    path('groups/<int:pk>/schedules/', GroupViewSet.as_view({'get': 'schedules'}), name='group-schedules'),
    path('groups/<int:pk>/materials/', GroupViewSet.as_view({'get': 'materials'}), name='group-materials'),
    path('groups/<int:pk>/students/', GroupViewSet.as_view({'get': 'students'}), name='group-students'),
    path('groups/<int:pk>/assignments/', GroupViewSet.as_view({'get': 'assignments'}), name='group-assignments'),
    
    path('quizzes/<int:pk>/questions/', QuizViewSet.as_view({'get': 'questions'}), name='quiz-questions'),
    path('quizzes/<int:pk>/assignments/', QuizViewSet.as_view({'get': 'assignments'}), name='quiz-assignments'),
    path('quizzes/<int:pk>/attempts/', QuizViewSet.as_view({'get': 'attempts'}), name='quiz-attempts'),
    

    path('assignments/<int:pk>/attempts/', QuizAssignmentViewSet.as_view({'get': 'attempts'}), name='assignment-attempts'),
    
 
    path('attempts/<int:pk>/submit-answers/', QuizAttemptViewSet.as_view({'post': 'submit_answers'}), name='attempt-submit-answers'),
    path('attempts/<int:pk>/questions/', QuizAttemptViewSet.as_view({'get': 'questions'}), name='attempt-questions'),
    path('attempts/<int:pk>/answers/', QuizAttemptViewSet.as_view({'get': 'answers'}), name='attempt-answers'),
    

    path('student/quizzes/', StudentQuizViewSet.as_view({'get': 'list'}), name='student-quiz-list'),
    path('student/quizzes/<int:pk>/', StudentQuizViewSet.as_view({'get': 'retrieve'}), name='student-quiz-detail'),
    path('student/quizzes/available-quizzes/', StudentQuizViewSet.as_view({'get': 'available_quizzes'}), name='student-available-quizzes'),
]