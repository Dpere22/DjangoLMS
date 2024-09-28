from django.http import Http404

from . import models
from django.shortcuts import render

def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, 'index.html', {"assignments":assignments})

def assignment(request, assignment_id):
    try:
        curr_assignment = models.Assignment.objects.get(pk=assignment_id)
        num_students = models.Group.objects.get(name="Students").user_set.count()
        num_submissions = curr_assignment.submission_set.count()
        num_grader_submissions = models.User.objects.get(username="g").graded_set.filter(assignment_id=assignment_id).count()
        return render(request, 'assignment.html',
                      {"assignment": curr_assignment,
                       "num_students": num_students,
                       "num_submissions": num_submissions,
                       "num_grader_submissions": num_grader_submissions,
                       "assignment_id": assignment_id})
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist")


def submissions(request, assignment_id):
    curr_assignment = models.Assignment.objects.get(pk=assignment_id)
    grader_submissions = models.User.objects.get(username="g").graded_set.filter(assignment_id=assignment_id)
    ordered = grader_submissions.order_by("author")
    return render(request, 'submissions.html', {"assignment": curr_assignment, "grader_submissions": grader_submissions,
                                                "assignment_id": assignment_id})

def profile(request):
    assignments = models.Assignment.objects.all()
    assignments_info = []
    for inner_assignment in assignments:
        grade_set = models.User.objects.get(username="g").graded_set.filter(assignment = inner_assignment)
        num_to_grade = grade_set.count()
        graded = grade_set.filter(score__isnull=False).count()
        assignments_info.append([inner_assignment.title, num_to_grade, graded])
    return render(request, 'profile.html', {'assignments_info':assignments_info})

def login_form(request):
    return render(request, 'login.html')
