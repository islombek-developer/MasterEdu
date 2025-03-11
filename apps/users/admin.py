from django.contrib import admin
from .models import Branch,User,Teacher,Student,DailyPayment,Attendance,Group

class TeacherAdmin(admin.ModelAdmin):
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if not request.user.is_superuser and request.user.user_role == 'admin':
            form.base_fields['branch'].queryset = Branch.objects.filter(id=request.user.branch.id)
        return form
    
    def save_model(self, request, obj, form, change):
        if not change:  
            if not request.user.is_superuser and request.user.user_role == 'admin':
                if obj.user:
                    obj.user.managed_by = request.user
                    obj.user.branch = request.user.branch
                    obj.user.save()
                obj.branch = request.user.branch
        super().save_model(request, obj, form, change)

admin.site.register(Teacher, TeacherAdmin)
admin.site.register(Branch)
admin.site.register(Group)
admin.site.register(Student)
admin.site.register(DailyPayment)
admin.site.register(Attendance)
admin.site.register(User)
