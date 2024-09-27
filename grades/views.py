from . import models
from django.shortcuts import render

# Create your views here.

def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, 'index.html', {"assignments":assignments})

def assignment(request, assignment_id):
    return render(request, 'assignment.html')

def submissions(request, assignment_id):
    return render(request, 'submissions.html')

def profile(request):
    return render(request, 'profile.html')

def login_form(request):
    return render(request, 'login.html')
