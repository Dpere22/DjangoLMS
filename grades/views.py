from django.contrib.auth.models import User
from django.core.exceptions import ValidationError
from django.http import Http404, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404

from . import models


def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, 'index.html', {"assignments": assignments})


def assignment(request, assignment_id):
    try:
        alice = get_object_or_404(User, username="a")
        curr_assignment = models.Assignment.objects.get(pk=assignment_id)
        try:
            submission = models.Submission.objects.get(assignment=curr_assignment, author=alice)
        except models.Submission.DoesNotExist:
            submission = None
        if request.method == "POST":
            submit_assignment(request, curr_assignment, submission, alice)
            return redirect(f'/{assignment_id}/')
        num_students = models.Group.objects.get(name="Students").user_set.count()
        num_submissions = curr_assignment.submission_set.count()
        num_grader_submissions = models.User.objects.get(username="g").graded_set.filter(
            assignment_id=assignment_id).count()
        return render(request, 'assignment.html',
                      {"assignment": curr_assignment,
                       "num_students": num_students,
                       "num_submissions": num_submissions,
                       "num_grader_submissions": num_grader_submissions,
                       "assignment_id": assignment_id,
                       "submission": submission})
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist")


def submit_assignment(request, curr_assignment, submission, author):
    grader = get_object_or_404(User, username="g")
    file = request.FILES['file']
    if submission is None:
        new_sub = models.Submission.objects.create(assignment=curr_assignment, author=author, grader=grader, score = None, file = file)
        new_sub.full_clean()
        new_sub.save()
    else:
        submission.file = file
        submission.full_clean()
        submission.save()


def submissions(request, assignment_id):
    curr_assignment = models.Assignment.objects.get(pk=assignment_id)
    grader_submissions = models.User.objects.get(username="g").graded_set.filter(assignment_id=assignment_id)
    errors = {}
    other_errors = []
    has_errors = False
    if request.method == "POST":
        errors, other_errors, has_errors = try_grade(request.POST, curr_assignment.points)
        if not has_errors:
            return redirect(f"/{assignment_id}/submissions")
    organized = create_zip(grader_submissions, errors)
    return render(request, 'submissions.html', {"assignment": curr_assignment, "organized": organized,
                                                "assignment_id": assignment_id, "other_errors": other_errors})


def create_zip(subs, errors):
    error_list = []
    for sub in subs:
        if sub.id not in errors:
            error_list.append([])
        else:
            error_list.append(errors[sub.id])
    return zip(subs, error_list)


def try_grade(post, max_points):
    submission_objects = []
    other_errors = []
    error_fields = {}
    has_errors = False
    for key in post:
        if "grade-" not in key:
            continue
        sub_id = int(key.replace("grade-", ""))
        error_fields[sub_id] = []
        try:
            submission = models.Submission.objects.get(pk=sub_id)
            score = post[key]
            if score != "":
                num_score = float(score)
                if 0.0 <= num_score <= float(max_points):
                    submission.score = num_score
                else:
                    has_errors = True
                    error_fields[sub_id].append("Score out of range")
            else:
                submission.score = None
            submission.full_clean()
            submission_objects.append(submission)
        except models.Submission.DoesNotExist:
            error_fields[sub_id].append("Submission does not exist")
            has_errors = True
        except (ValueError, KeyError):
            error_fields[sub_id].append("Please enter an valid number")
            has_errors = True
        except ValidationError:
            other_errors.append("Validation Error")
            has_errors = True
    models.Submission.objects.bulk_update(submission_objects, ['score'])
    return error_fields, other_errors, has_errors

def profile(request):
    assignments = models.Assignment.objects.all()
    assignments_info = []
    for inner_assignment in assignments:
        grade_set = models.User.objects.get(username="g").graded_set.filter(assignment=inner_assignment)
        num_to_grade = grade_set.count()
        graded = grade_set.filter(score__isnull=False).count()
        assignments_info.append([inner_assignment.title, num_to_grade, graded])
    return render(request, 'profile.html', {'assignments_info': assignments_info})


def login_form(request):
    return render(request, 'login.html')

def show_upload(request, filename):
    submission = models.Submission.objects.get(file=filename)
    return HttpResponse(submission.file.open())