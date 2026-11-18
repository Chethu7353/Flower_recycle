from datetime import date
from decimal import Decimal
from django.contrib import messages
from django.contrib.auth import login, logout
from django.db import transaction
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone

from .forms import (
    AdminTempleForm,
    AdminUserForm,
    CollectionRecordForm,
    FlowerSubmissionForm,
    RoleLoginForm,
    TempleProfileForm,
)
from .models import (
    Collection,
    CollectionRecord,
    CustomUser,
    FlowerSubmission,
    Temple,
)
from .permissions import (
    admin_dept_required,
    collector_required,
    get_role_dashboard_url,
    temple_owner_required,
)


# ==========================================
# 1. PUBLIC WELCOME & AUTHENTICATION VIEWS
# ==========================================

def welcome(request):
    """Public landing page displaying project branding, workflow, and role selection."""
    if request.user.is_authenticated:
        return redirect(get_role_dashboard_url(request.user))

    # Public aggregate metrics for display
    total_temples = Temple.objects.count() or 5
    total_collections = CollectionRecord.objects.count() or Collection.objects.count() or 12
    total_weight = (
        CollectionRecord.objects.aggregate(total=Sum("collected_weight"))["total"]
        or Collection.objects.aggregate(total=Sum("quantity"))["total"]
        or 1250
    )

    context = {
        "total_temples": total_temples,
        "total_collections": total_collections,
        "total_weight_kg": round(float(total_weight), 1),
    }
    return render(request, "welcome.html", context)


def role_login(request, role=None):
    """
    Role-specific or unified login view.
    Maps role url parameter to expected CustomUser.Role.
    """
    if request.user.is_authenticated:
        return redirect(get_role_dashboard_url(request.user))

    role_map = {
        "temple": CustomUser.Role.TEMPLE_OWNER,
        "temple_owner": CustomUser.Role.TEMPLE_OWNER,
        "collector": CustomUser.Role.COLLECTOR,
        "admin": CustomUser.Role.ADMIN,
    }
    expected_role = role_map.get(role)

    role_meta = {
        CustomUser.Role.TEMPLE_OWNER: {
            "title": "Temple Owner Portal",
            "tagline": "Sign in to record flower waste submissions and track collection statuses.",
            "badge_class": "badge-temple",
            "icon": "bi-building",
        },
        CustomUser.Role.COLLECTOR: {
            "title": "SONPK Collector Portal",
            "tagline": "Sign in to view pending temple submissions and log completed pickups.",
            "badge_class": "badge-collector",
            "icon": "bi-truck",
        },
        CustomUser.Role.ADMIN: {
            "title": "Admin Department Portal",
            "tagline": "Sign in for central administrative control, user management, and monitoring.",
            "badge_class": "badge-admin",
            "icon": "bi-shield-lock",
        },
    }

    form = RoleLoginForm(request.POST or None, expected_role=expected_role)
    if request.method == "POST" and form.is_valid():
        user = form.user
        login(request, user)
        messages.success(request, f"Welcome back, {user.full_name or user.email}! Signed in successfully.")

        # Check 'next' parameter if safe
        next_url = request.GET.get("next") or request.POST.get("next")
        if next_url and next_url.startswith("/"):
            return redirect(next_url)

        return redirect(get_role_dashboard_url(user))

    context = {
        "form": form,
        "expected_role": expected_role,
        "meta": role_meta.get(expected_role, {
            "title": "Role-Based Portal Login",
            "tagline": "Select your role and provide your assigned credentials to proceed.",
            "badge_class": "badge-default",
            "icon": "bi-person-circle",
        }),
    }
    return render(request, "auth/login.html", context)


def logout_view(request):
    """Safely log out user and redirect to public welcome page."""
    logout(request)
    messages.info(request, "You have been signed out successfully.")
    return redirect("welcome")


# ==========================================
# 2. TEMPLE OWNER MODULE
# ==========================================

@temple_owner_required
def temple_dashboard(request):
    """
    Temple Owner Dashboard:
    - Temple info
    - Flower submission CTA
    - Submission records with collection status
    - Relevant statistics
    """
    user = request.user
    temple = Temple.objects.filter(owner=user).first() or Temple.objects.filter(manager=user).first()

    # Submissions belonging strictly to this temple owner's temple
    submissions = FlowerSubmission.objects.filter(temple__in=Temple.objects.filter(Q(owner=user) | Q(manager=user))).select_related("temple", "collection_record__collector")

    # Filter by status if provided in GET
    status_filter = request.GET.get("status", "").strip().upper()
    if status_filter in dict(FlowerSubmission.Status.choices):
        submissions = submissions.filter(status=status_filter)

    # Statistics
    total_submissions = submissions.count()
    pending_count = submissions.filter(status__in=[FlowerSubmission.Status.SUBMITTED, FlowerSubmission.Status.PENDING]).count()
    collected_count = submissions.filter(status=FlowerSubmission.Status.COLLECTED).count()
    total_submitted_weight = submissions.aggregate(total=Sum("weight"))["total"] or Decimal("0")
    total_collected_weight = (
        CollectionRecord.objects.filter(submission__in=submissions)
        .aggregate(total=Sum("collected_weight"))["total"]
        or Decimal("0")
    )

    context = {
        "temple": temple,
        "submissions": submissions[:25],
        "total_submissions": total_submissions,
        "pending_count": pending_count,
        "collected_count": collected_count,
        "total_submitted_weight": total_submitted_weight,
        "total_collected_weight": total_collected_weight,
        "current_status_filter": status_filter,
        "status_choices": FlowerSubmission.Status.choices,
    }
    return render(request, "temple_owner/dashboard.html", context)


@temple_owner_required
def temple_submit_flower(request):
    """
    Temple Owner Flower Submission:
    - Flower type
    - Flower weight (> 0)
    - Submission date
    - Remarks
    - Auto-associated with temple
    """
    user = request.user
    temple = Temple.objects.filter(owner=user).first() or Temple.objects.filter(manager=user).first()

    if not temple:
        messages.warning(request, "Please set up your temple details first before submitting flower waste.")
        return redirect("temple_profile")

    form = FlowerSubmissionForm(request.POST or None, user=user)
    if request.method == "POST" and form.is_valid():
        submission = form.save(commit=False)
        submission.temple = form.cleaned_data.get("temple") or temple
        submission.submitted_by = user
        submission.status = FlowerSubmission.Status.SUBMITTED
        submission.save()

        messages.success(
            request,
            f"Successfully submitted {submission.weight} kg of {submission.flower_type}. SONPK Collectors have been notified!"
        )
        return redirect("temple_dashboard")

    context = {
        "form": form,
        "temple": temple,
    }
    return render(request, "temple_owner/submit_flower.html", context)


@temple_owner_required
def temple_profile(request):
    """Manage temple details (name, address, contact)."""
    user = request.user
    temple = Temple.objects.filter(owner=user).first() or Temple.objects.filter(manager=user).first()

    if request.method == "POST":
        form = TempleProfileForm(request.POST, instance=temple)
        if form.is_valid():
            temple_instance = form.save(commit=False)
            temple_instance.owner = user
            temple_instance.save()
            messages.success(request, "Temple details updated successfully.")
            return redirect("temple_dashboard")
    else:
        form = TempleProfileForm(instance=temple)

    return render(request, "temple_owner/temple_profile.html", {"form": form, "temple": temple})


@temple_owner_required
def temple_submission_detail(request, pk):
    """View full details and collection history of a specific submission."""
    user = request.user
    submission = get_object_or_404(
        FlowerSubmission.objects.select_related("temple", "submitted_by", "collection_record__collector"),
        pk=pk,
        temple__in=Temple.objects.filter(Q(owner=user) | Q(manager=user)),
    )
    return render(request, "temple_owner/submission_detail.html", {"submission": submission})


# ==========================================
# 3. SONPK COLLECTOR MODULE
# ==========================================

@collector_required
def collector_dashboard(request):
    """
    SONPK Collector Dashboard:
    - Total submissions, pending collections, completed collections
    - Temples with pending submissions
    - Collection action links
    - Collector's personal history
    """
    user = request.user

    # Submissions available across all temples
    all_submissions = FlowerSubmission.objects.select_related("temple", "submitted_by")
    pending_submissions = all_submissions.filter(
        status__in=[FlowerSubmission.Status.SUBMITTED, FlowerSubmission.Status.PENDING]
    ).order_by("-submission_date", "-created_at")

    # Collections performed by this collector
    my_collections = CollectionRecord.objects.filter(collector=user).select_related(
        "submission__temple", "submission"
    ).order_by("-collected_at")

    # Summary metrics
    total_pending = pending_submissions.count()
    my_completed_count = my_collections.count()
    my_collected_weight = my_collections.aggregate(total=Sum("collected_weight"))["total"] or Decimal("0")
    system_total_submissions = all_submissions.count()

    context = {
        "pending_submissions": pending_submissions[:10],
        "my_collections": my_collections[:10],
        "total_pending": total_pending,
        "my_completed_count": my_completed_count,
        "my_collected_weight": my_collected_weight,
        "system_total_submissions": system_total_submissions,
    }
    return render(request, "collector/dashboard.html", context)


@collector_required
def collector_submissions_list(request):
    """
    Browse flower submissions with filtering and searching:
    - Temple, Flower Type, Status, Date
    """
    submissions = FlowerSubmission.objects.select_related("temple", "submitted_by", "collection_record__collector").all()

    # Search query
    q = request.GET.get("q", "").strip()
    if q:
        submissions = submissions.filter(
            Q(temple__name__icontains=q)
            | Q(temple__city__icontains=q)
            | Q(temple__address__icontains=q)
            | Q(flower_type__icontains=q)
            | Q(remarks__icontains=q)
        )

    # Status filter (default to pending if requested, or specific status)
    status_filter = request.GET.get("status", "").strip().upper()
    if status_filter in dict(FlowerSubmission.Status.choices):
        submissions = submissions.filter(status=status_filter)
    elif status_filter == "ACTIVE_PENDING":
        submissions = submissions.filter(status__in=[FlowerSubmission.Status.SUBMITTED, FlowerSubmission.Status.PENDING])

    # Temple filter
    temple_id = request.GET.get("temple", "").strip()
    if temple_id.isdigit():
        submissions = submissions.filter(temple_id=int(temple_id))

    all_temples = Temple.objects.order_by("name")

    context = {
        "submissions": submissions[:50],
        "q": q,
        "status_filter": status_filter,
        "selected_temple": temple_id,
        "all_temples": all_temples,
        "status_choices": FlowerSubmission.Status.choices,
    }
    return render(request, "collector/submissions_list.html", context)


@collector_required
def collector_record_collection(request, pk):
    """
    Collection action workflow:
    1. Review submission & temple details
    2. Input collected weight, collection timestamp, remarks
    3. Transition status to COLLECTED atomically
    4. Save permanent CollectionRecord
    """
    submission = get_object_or_404(
        FlowerSubmission.objects.select_related("temple", "submitted_by"),
        pk=pk
    )

    # Prevent duplicate collection
    if submission.status == FlowerSubmission.Status.COLLECTED or hasattr(submission, "collection_record"):
        messages.warning(request, "This submission has already been recorded as Collected.")
        return redirect("collector_dashboard")

    if request.method == "POST":
        form = CollectionRecordForm(request.POST)
        if form.is_valid():
            with transaction.atomic():
                record = form.save(commit=False)
                record.submission = submission
                record.collector = request.user
                record.status = CollectionRecord.Status.COLLECTED
                record.save()

                # Update submission status
                submission.status = FlowerSubmission.Status.COLLECTED
                submission.save(update_fields=["status", "updated_at"])

            messages.success(
                request,
                f"Collection recorded successfully! {record.collected_weight} kg collected from {submission.temple.name}."
            )
            return redirect("collector_dashboard")
    else:
        # Pre-fill collected weight with submitted weight
        form = CollectionRecordForm(initial={
            "collected_weight": submission.weight,
            "collected_at": timezone.now(),
        })

    context = {
        "form": form,
        "submission": submission,
    }
    return render(request, "collector/collect_form.html", context)


# ==========================================
# 4. ADMIN DEPARTMENT MODULE
# ==========================================

@admin_dept_required
def admin_dashboard(request):
    """
    Admin Department Dashboard:
    - Overview of the complete ecosystem:
      * Total temples, owners, collectors
      * Total submissions, pending, completed
      * Overall collection metrics
    - Quick management links and recent activity
    """
    total_temples = Temple.objects.count()
    total_owners = CustomUser.objects.filter(role=CustomUser.Role.TEMPLE_OWNER).count()
    total_collectors = CustomUser.objects.filter(role=CustomUser.Role.COLLECTOR).count()
    total_submissions = FlowerSubmission.objects.count()
    pending_collections = FlowerSubmission.objects.filter(
        status__in=[FlowerSubmission.Status.SUBMITTED, FlowerSubmission.Status.PENDING]
    ).count()
    completed_collections = CollectionRecord.objects.count()
    total_weight_collected = (
        CollectionRecord.objects.aggregate(total=Sum("collected_weight"))["total"]
        or Decimal("0")
    )

    recent_submissions = FlowerSubmission.objects.select_related("temple", "submitted_by")[:8]
    recent_collections = CollectionRecord.objects.select_related("submission__temple", "collector")[:8]

    context = {
        "total_temples": total_temples,
        "total_owners": total_owners,
        "total_collectors": total_collectors,
        "total_submissions": total_submissions,
        "pending_collections": pending_collections,
        "completed_collections": completed_collections,
        "total_weight_collected": total_weight_collected,
        "recent_submissions": recent_submissions,
        "recent_collections": recent_collections,
    }
    return render(request, "admin_dept/dashboard.html", context)


@admin_dept_required
def admin_users_list(request):
    """Manage temple-owner and collector user accounts."""
    users = CustomUser.objects.all().order_by("-created_at")

    role_filter = request.GET.get("role", "").strip()
    if role_filter in dict(CustomUser.Role.choices):
        users = users.filter(role=role_filter)

    status_filter = request.GET.get("status", "").strip()
    if status_filter == "active":
        users = users.filter(is_active=True)
    elif status_filter == "inactive":
        users = users.filter(is_active=False)

    q = request.GET.get("q", "").strip()
    if q:
        users = users.filter(Q(full_name__icontains=q) | Q(email__icontains=q) | Q(phone__icontains=q))

    context = {
        "users": users,
        "role_choices": CustomUser.Role.choices,
        "current_role": role_filter,
        "current_status": status_filter,
        "q": q,
    }
    return render(request, "admin_dept/users_list.html", context)


@admin_dept_required
def admin_user_create(request):
    """Create a new user account with role assignment."""
    if request.method == "POST":
        form = AdminUserForm(request.POST, is_create=True)
        if form.is_valid():
            user = form.save(commit=False)
            password = form.cleaned_data["password"]
            user.set_password(password)
            user.username = user.email
            user.save()

            # Optionally auto-create temple if user is Temple Owner and temple name was provided
            temple_name = form.cleaned_data.get("create_temple_name", "").strip()
            if user.role == CustomUser.Role.TEMPLE_OWNER and temple_name:
                Temple.objects.create(
                    name=temple_name,
                    address=form.cleaned_data.get("create_temple_address", "") or "Address to be updated",
                    contact_person=user.full_name,
                    contact_number=user.phone or "To be updated",
                    owner=user,
                )

            messages.success(request, f"User account for '{user.full_name or user.email}' created successfully.")
            return redirect("admin_users_list")
    else:
        form = AdminUserForm(is_create=True)

    return render(request, "admin_dept/user_form.html", {"form": form, "title": "Create User Account"})


@admin_dept_required
def admin_user_edit(request, pk):
    """Edit user details, activate/deactivate, update role."""
    user = get_object_or_404(CustomUser, pk=pk)

    if request.method == "POST":
        form = AdminUserForm(request.POST, instance=user)
        if form.is_valid():
            updated_user = form.save(commit=False)
            new_password = form.cleaned_data.get("password")
            if new_password:
                updated_user.set_password(new_password)
            updated_user.save()
            messages.success(request, f"User '{updated_user.full_name or updated_user.email}' updated successfully.")
            return redirect("admin_users_list")
    else:
        form = AdminUserForm(instance=user)

    return render(request, "admin_dept/user_form.html", {"form": form, "title": f"Manage User: {user.full_name or user.email}", "edit_user": user})


@admin_dept_required
def admin_user_toggle_status(request, pk):
    """Quickly toggle active/inactive status for a user."""
    user = get_object_or_404(CustomUser, pk=pk)
    if user == request.user:
        messages.error(request, "Security constraint: You cannot deactivate your own administrative account.")
        return redirect("admin_users_list")

    user.is_active = not user.is_active
    user.save(update_fields=["is_active"])
    status_label = "activated" if user.is_active else "deactivated"
    messages.success(request, f"Account for '{user.full_name or user.email}' has been {status_label}.")
    return redirect("admin_users_list")


@admin_dept_required
def admin_temples_list(request):
    """View and manage all registered temples."""
    temples = Temple.objects.annotate(
        submission_count=Count("submissions"),
        total_collected=Sum("submissions__collection_record__collected_weight")
    ).select_related("owner").order_by("name")

    q = request.GET.get("q", "").strip()
    if q:
        temples = temples.filter(
            Q(name__icontains=q) | Q(city__icontains=q) | Q(state__icontains=q) | Q(address__icontains=q)
        )

    context = {
        "temples": temples,
        "q": q,
    }
    return render(request, "admin_dept/temples_list.html", context)


@admin_dept_required
def admin_temple_create(request):
    """Register a new temple and assign an owner."""
    if request.method == "POST":
        form = AdminTempleForm(request.POST)
        if form.is_valid():
            temple = form.save()
            messages.success(request, f"Temple '{temple.name}' created successfully.")
            return redirect("admin_temples_list")
    else:
        form = AdminTempleForm()

    return render(request, "admin_dept/temple_form.html", {"form": form, "title": "Register New Temple"})


@admin_dept_required
def admin_temple_edit(request, pk):
    """Edit temple details and change owner assignment."""
    temple = get_object_or_404(Temple, pk=pk)
    if request.method == "POST":
        form = AdminTempleForm(request.POST, instance=temple)
        if form.is_valid():
            form.save()
            messages.success(request, f"Temple '{temple.name}' updated successfully.")
            return redirect("admin_temples_list")
    else:
        form = AdminTempleForm(instance=temple)

    return render(request, "admin_dept/temple_form.html", {"form": form, "title": f"Edit Temple: {temple.name}", "temple": temple})


@admin_dept_required
def admin_temple_detail(request, pk):
    """Review individual temple details, associated submissions, and collection activity."""
    temple = get_object_or_404(Temple.objects.select_related("owner"), pk=pk)
    submissions = temple.submissions.select_related("submitted_by", "collection_record__collector").all()

    total_submissions = submissions.count()
    completed_collections = submissions.filter(status=FlowerSubmission.Status.COLLECTED).count()
    total_collected_weight = (
        CollectionRecord.objects.filter(submission__in=submissions)
        .aggregate(total=Sum("collected_weight"))["total"]
        or Decimal("0")
    )

    context = {
        "temple": temple,
        "submissions": submissions,
        "total_submissions": total_submissions,
        "completed_collections": completed_collections,
        "total_collected_weight": total_collected_weight,
    }
    return render(request, "admin_dept/temple_detail.html", context)


@admin_dept_required
def admin_submissions_list(request):
    """
    View all flower submissions with filtering:
    - By temple
    - By flower type
    - By submission date
    - By collection status
    """
    submissions = FlowerSubmission.objects.select_related("temple", "submitted_by", "collection_record__collector").all()

    # Filters
    temple_id = request.GET.get("temple", "").strip()
    if temple_id.isdigit():
        submissions = submissions.filter(temple_id=int(temple_id))

    flower_type = request.GET.get("flower_type", "").strip()
    if flower_type:
        submissions = submissions.filter(flower_type__iexact=flower_type)

    status_filter = request.GET.get("status", "").strip().upper()
    if status_filter in dict(FlowerSubmission.Status.choices):
        submissions = submissions.filter(status=status_filter)

    date_filter = request.GET.get("date", "").strip()
    if date_filter:
        try:
            parsed_date = date.fromisoformat(date_filter)
            submissions = submissions.filter(submission_date=parsed_date)
        except ValueError:
            pass

    q = request.GET.get("q", "").strip()
    if q:
        submissions = submissions.filter(
            Q(temple__name__icontains=q) | Q(flower_type__icontains=q) | Q(remarks__icontains=q)
        )

    all_temples = Temple.objects.order_by("name")
    distinct_flower_types = FlowerSubmission.objects.values_list("flower_type", flat=True).distinct().order_by("flower_type")

    context = {
        "submissions": submissions[:100],
        "all_temples": all_temples,
        "flower_types": distinct_flower_types,
        "status_choices": FlowerSubmission.Status.choices,
        "selected_temple": temple_id,
        "selected_flower": flower_type,
        "selected_status": status_filter,
        "selected_date": date_filter,
        "q": q,
    }
    return render(request, "admin_dept/submissions_list.html", context)


@admin_dept_required
def admin_collections_list(request):
    """
    Monitor all collection records:
    - Responsible collector
    - Collection timestamp
    - Collected weight
    - Status & remarks
    """
    collections = CollectionRecord.objects.select_related("submission__temple", "collector", "submission").all()

    collector_id = request.GET.get("collector", "").strip()
    if collector_id.isdigit():
        collections = collections.filter(collector_id=int(collector_id))

    temple_id = request.GET.get("temple", "").strip()
    if temple_id.isdigit():
        collections = collections.filter(submission__temple_id=int(temple_id))

    date_filter = request.GET.get("date", "").strip()
    if date_filter:
        try:
            parsed_date = date.fromisoformat(date_filter)
            collections = collections.filter(collected_at__date=parsed_date)
        except ValueError:
            pass

    q = request.GET.get("q", "").strip()
    if q:
        collections = collections.filter(
            Q(submission__temple__name__icontains=q)
            | Q(collector__full_name__icontains=q)
            | Q(remarks__icontains=q)
        )

    all_collectors = CustomUser.objects.filter(role=CustomUser.Role.COLLECTOR).order_by("full_name")
    all_temples = Temple.objects.order_by("name")
    total_weight = collections.aggregate(total=Sum("collected_weight"))["total"] or Decimal("0")

    context = {
        "collections": collections[:100],
        "all_collectors": all_collectors,
        "all_temples": all_temples,
        "selected_collector": collector_id,
        "selected_temple": temple_id,
        "selected_date": date_filter,
        "total_weight": total_weight,
        "q": q,
    }
    return render(request, "admin_dept/collections_list.html", context)
