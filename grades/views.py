from django.contrib.auth import authenticate, login, logout
from django.core.exceptions import ValidationError, PermissionDenied
from django.db.models import Count, Q
from django.http import Http404, HttpResponse, HttpResponseBadRequest
from django.shortcuts import render, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.utils.http import url_has_allowed_host_and_scheme

from . import models

@login_required
def index(request):
    assignments = models.Assignment.objects.all()
    return render(request, 'index.html', {"assignments": assignments})

@login_required
def assignment(request, assignment_id):
    try:
        curr_user = request.user
        curr_assignment = models.Assignment.objects.get(pk=assignment_id)
        if is_student(curr_user):
            submission = get_submission(curr_assignment, curr_user)
            has_submission, past_due, graded, score, percent = get_submission_stuff(curr_assignment, submission)
            if request.method == "POST":
                if not past_due:
                    error = submit_assignment(request, curr_assignment, submission, request.user)
                    if error is None:
                        return redirect(f'/{assignment_id}/')
                    else:
                        return render(request, 'assignment.html',
                          {"assignment": curr_assignment,
                           "assignment_id": assignment_id,
                           "submission": submission,
                           "is_student": True,
                           "is_ta": False,
                           "past_due": past_due,
                           "has_submission": has_submission,
                           "graded": graded,
                           "score": score,
                           "percent": percent,
                           "error": error})
                else:
                    return HttpResponseBadRequest
            else:
                return render(request, 'assignment.html',
                          {"assignment": curr_assignment,
                           "assignment_id": assignment_id,
                           "submission": submission,
                           "is_student": True,
                           "is_ta": False,
                           "past_due": past_due,
                           "has_submission": has_submission,
                           "graded": graded,
                           "score": score,
                           "percent": percent})
        elif is_ta(curr_user):
            num_students = models.Group.objects.get(name="Students").user_set.count()
            num_submissions = curr_assignment.submission_set.count()
            is_superuser = curr_user.is_superuser
            if is_superuser:
                num_grader_submissions = models.Submission.objects.filter(assignment_id=assignment_id).count()
            else:
                num_grader_submissions = curr_user.graded_set.filter(
                    assignment_id=assignment_id).count()
            return render(request, 'assignment.html',
                          {"assignment": curr_assignment,
                           "num_students": num_students,
                           "num_submissions": num_submissions,
                           "num_grader_submissions": num_grader_submissions,
                           "assignment_id": assignment_id,
                           "is_student": False,
                           "is_ta": True,
                           "is_superuser": is_superuser,})
    except models.Assignment.DoesNotExist:
        raise Http404("Assignment does not exist")

def pick_grader(assign):
    grader = models.Group.objects.get(name="Teaching Assistants").user_set.annotate(total_assigned = Count("graded_set", filter=Q(graded_set__assignment = assign))).order_by("total_assigned").first()
    return grader


def get_submission_stuff(curr_assignment, submission):
    current_time = timezone.now()
    past_due, has_submission, graded = False, False, False
    score, percent = 0, 0
    if current_time > curr_assignment.deadline:  ##i.e. it's late
        past_due = True
    if submission is not None:
        has_submission = True
        if submission.score is not None:
            graded = True
            score = submission.score
            percent = submission.score / curr_assignment.points * 100
    return has_submission, past_due, graded, score, percent


def get_submission(curr_assignment, curr_user):
    try:
        submission = models.Submission.objects.get(assignment=curr_assignment, author=curr_user)
    except models.Submission.DoesNotExist:
        submission = None
    return submission

def is_student(user):
    return user.groups.filter(name="Students").exists() or user.is_anonymous
def is_ta(user):
    return user.groups.filter(name="Teaching Assistants").exists() or user.is_superuser


def submit_assignment(request, curr_assignment, submission, author):
    file = request.FILES['file']
    max_size = 64 * 1024 * 1024
    if file.size > max_size:
        return "file size too large"
    if not is_pdf(file):
        return "File type not supported"
    if submission is None:
        grader = pick_grader(curr_assignment)
        new_sub = models.Submission.objects.create(assignment=curr_assignment, author=author, grader=grader, score = None, file = file)
        new_sub.full_clean()
        new_sub.save()
    else:
        submission.file = file
        submission.full_clean()
        submission.save()
    return None


@login_required
def submissions(request, assignment_id):
    if not is_ta(request.user):
        raise PermissionDenied
    curr_assignment = models.Assignment.objects.get(pk=assignment_id)
    curr_user = request.user
    if not curr_user.is_superuser:
        grader_submissions = curr_user.graded_set.filter(assignment_id=assignment_id)
    else:
        grader_submissions = models.Submission.objects.filter(assignment_id=assignment_id)
    errors = {}
    other_errors = []
    if request.method == "POST":
        errors, other_errors, has_errors = try_grade(request.user, request.POST, curr_assignment.points)
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


def try_grade(user, post, max_points):
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
                    submission.change_grade(user, num_score)
                else:
                    has_errors = True
                    error_fields[sub_id].append("Score out of range")
            else:
                submission.change_grade(user, None)
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

@login_required
def profile(request):
    assignments = models.Assignment.objects.all()
    assignments_info = []
    user = request.user
    is_s = is_student(user)
    is_t = is_ta(user)
    if is_t:
        for inner_assignment in assignments:
            grade_set = user.graded_set.filter(assignment=inner_assignment)
            num_to_grade = grade_set.count()
            graded = grade_set.filter(score__isnull=False).count()
            assignments_info.append([inner_assignment.title, num_to_grade, graded])
        return render(request, 'profile.html', {'assignments_info': assignments_info,
                                                'user': request.user, 'is_student': is_s})
    elif is_s:
        current_time = timezone.now()
        total_possible_points = 0
        total_points = 0
        for inner_assignment in assignments:
            grade_set = user.author_set.filter(assignment=inner_assignment)
            if current_time > inner_assignment.deadline:
                if  grade_set.count() > 0:
                    score = grade_set[0].score
                    if score is not None: ##assignment graded
                        total_points += score
                        total_possible_points += inner_assignment.points
                else: ##assignment missing
                    total_points += 0
                    total_possible_points += inner_assignment.points
            assignments_info.append([inner_assignment.title, get_student_score_percent(grade_set, inner_assignment), inner_assignment.weight])
        final_percent = round(total_points / total_possible_points * 100, 2)
        return render(request, 'profile.html', {'assignments_info': assignments_info,
                                                'user': request.user, 'is_student': is_s, 'final_percent': final_percent})

def get_student_score_percent(grade_set, assign):
    current_time = timezone.now()
    if grade_set.count() == 0:
        if current_time > assign.deadline:
            return "Missing"
        else:
            return "Not Due"
    else:
        score = grade_set[0].score
        if score is None:
            return "Ungraded"
        else:
            return str(score/assign.points * 100) + "%"


def login_form(request):
    next_page = request.GET.get('next')
    if next_page is None:
        next_page = '/profile/'
    if request.method == "POST":
        next_url = request.POST.get('next', '/profile/')
        if not url_has_allowed_host_and_scheme(next_url, None):
            next_url = '/'
        username = request.POST.get("username", "")
        password = request.POST.get("password", "")
        user = authenticate(request, username=username, password=password)
        if user is not None:
            login(request, user)
            return redirect(next_url)
        else:
            error = 'Username and password do not match'
            return render(request, 'login.html', {"next_page": next_page, "error": error})
    return render(request, 'login.html',{"next_page": next_page})


def is_pdf(file):
    if not next(file.chunks()).startswith(b'%PDF-') or not file.name.lower().endswith('.pdf'):
        return False
    return True


@login_required
def show_upload(request, filename):
    submission = models.Submission.objects.get(file=filename)
    file = submission.view_submission(request.user)
    if is_pdf(file):
        response = HttpResponse(file.open(), content_type="application/pdf")
        response['Content-Disposition'] = 'attachment; filename="%s"' % filename
        return response
    else:
        raise Http404


def logout_form(request):
    logout(request)
    return redirect("/profile/login/")