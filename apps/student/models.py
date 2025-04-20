from django.db import models
from django.utils import timezone
from apps.users.models import User, Status

class Student(models.Model):
    user = models.OneToOneField('users.User', on_delete=models.CASCADE)
    home_phone = models.CharField(max_length=14, null=True, blank=True)
    parent_name = models.CharField(max_length=200, blank=True, null=True)
    parent_phone = models.CharField(max_length=13, blank=True, null=True)
    date_of_birth = models.DateField(null=True, blank=True)
    status = models.CharField(choices=Status.choices, max_length=15, default=Status.ACTIVE)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    @property
    def branch(self):
        return self.user.branch.first()
        
    def get_full_name(self):
        return f"{self.user.first_name} {self.user.last_name}"

    def __str__(self):
        return self.get_full_name()

class StudentGroup(models.Model):
    student = models.ForeignKey(Student, on_delete=models.CASCADE, related_name='enrollments')
    group = models.ForeignKey('teacher.Group', on_delete=models.CASCADE, related_name='enrollments')
    joined_date = models.DateField(default=timezone.now)
    status = models.CharField(choices=Status.choices, max_length=15, default=Status.ACTIVE)
    notes = models.TextField(blank=True, null=True)
    
    class Meta:
        unique_together = ['student', 'group']
    
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.group.title}"

class AttendanceStatus(models.TextChoices):
    PRESENT = 'present', 'Present'
    ABSENT = 'absent', 'Absent'
    LATE = 'late', 'Late'
    EXCUSED = 'excused', 'Excused'

class Attendance(models.Model):
    student_group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, related_name='attendances')
    date = models.DateField(default=timezone.localdate)
    status = models.CharField(choices=AttendanceStatus.choices, max_length=10, default=AttendanceStatus.ABSENT)
    note = models.TextField(blank=True, null=True)
    marked_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='marked_attendances')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['student_group', 'date']
        
    def __str__(self):
        return f"{self.student_group.student.get_full_name()} - {self.date} - {self.get_status_display()}"

class StudentProgress(models.Model):
    student_group = models.ForeignKey(StudentGroup, on_delete=models.CASCADE, related_name='progress_records')
    date = models.DateField(default=timezone.localdate)
    grade = models.PositiveIntegerField(default=0)  
    comments = models.TextField(blank=True, null=True)
    created_by = models.ForeignKey('users.User', on_delete=models.CASCADE, related_name='recorded_progress')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.student_group.student.get_full_name()} - {self.date} - {self.grade}%"

