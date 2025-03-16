from django.db import models
from apps.users.models import Student,Group


class Question(models.Model):
    group = models.ForeignKey(Group, on_delete=models.CASCADE, related_name="questions")  
    title = models.TextField() 
    has_options = models.BooleanField(default=True)  

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = "Savol"
        verbose_name_plural = "Savollar"


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="answers")
    title = models.TextField() 
    answer_text = models.CharField(max_length=255)  
    is_correct = models.BooleanField(default=False) 
    bnswer_text = models.CharField(max_length=255)  
    bis_correct = models.BooleanField(default=False) 
    cnswer_text = models.CharField(max_length=255)  
    cis_correct = models.BooleanField(default=False) 
    dnswer_text = models.CharField(max_length=255)  
    dis_correct = models.BooleanField(default=False) 
    def __str__(self):
        return self.answer_text

    class Meta:
        verbose_name = "Javob varianti"
        verbose_name_plural = "Javob variantlari"


class WrittenAnswer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, related_name="written_answers")
    title = models.TextField() 
    answer_text = models.TextField()  
    def __str__(self):
        return f"{self.student_name} - {self.question.title[:30]}..."

    class Meta:
        verbose_name = "Yozma javob"
        verbose_name_plural = "Yozma javoblar"
