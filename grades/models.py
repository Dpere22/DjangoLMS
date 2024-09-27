from django.core.exceptions import ValidationError
from django.db import models
from django.contrib.auth.models import User, Group

def is_positive(n):
    if n >= 0:
        return True
    else:
        raise ValidationError('Number must be positive')

class Assignment(models.Model):
    title = models.CharField(max_length=100, unique=True)
    description = models.TextField(null = True, blank = True)
    deadline = models.DateTimeField(null = True, blank = True) # An assignment may not have a due date.
    weight = models.IntegerField(default = 100)
    points = models.IntegerField(default=100)

class Submission(models.Model):
    assignment = models.ForeignKey(Assignment, on_delete=models.CASCADE)
    author = models.ForeignKey(User, on_delete=models.RESTRICT)
    grader = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='graded_set', null=True)
    score = models.FloatField(validators=[is_positive], null = True, blank = True)
    file = models.FileField()


# Create your models here.
