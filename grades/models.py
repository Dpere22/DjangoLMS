from django.core.exceptions import ValidationError, PermissionDenied
from django.db import models
from django.contrib.auth.models import User, Group
from django.template.defaultfilters import filesizeformat


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
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='author_set')
    grader = models.ForeignKey(User, on_delete=models.SET_NULL, related_name='graded_set', null=True)
    score = models.FloatField(validators=[is_positive], null = True, blank = True)
    file = models.FileField()
    def change_grade(self, user, grade):
        if user == self.grader:
            self.score = grade
        else:
            raise PermissionDenied
    def view_submission(self, user):
        if user == self.grader or user == self.author or user.is_superuser:
            return self.file
        else:
            raise PermissionDenied
