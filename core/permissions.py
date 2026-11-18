from functools import wraps
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.shortcuts import redirect
from rest_framework import permissions

from .models import CustomUser


# ==========================================
# View Decorators for Web Interface
# ==========================================

def get_role_dashboard_url(user):
    """Return the correct home dashboard URL for a given user."""
    if not user.is_authenticated:
        return "login"
    if user.role == CustomUser.Role.ADMIN or user.is_superuser or user.is_staff:
        return "admin_dashboard"
    if user.role == CustomUser.Role.COLLECTOR:
        return "collector_dashboard"
    if user.role == CustomUser.Role.TEMPLE_OWNER:
        return "temple_dashboard"
    return "home"


def temple_owner_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access the Temple Owner portal.")
            return redirect(f"/login/temple/?next={request.path}")
        if request.user.role != CustomUser.Role.TEMPLE_OWNER and not request.user.is_superuser:
            messages.error(request, "Access Denied: Only Temple Owners can access this page.")
            return redirect(get_role_dashboard_url(request.user))
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def collector_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access the SONPK Collector portal.")
            return redirect(f"/login/collector/?next={request.path}")
        if request.user.role != CustomUser.Role.COLLECTOR and not request.user.is_superuser:
            messages.error(request, "Access Denied: Only authorized SONPK Collectors can access this page.")
            return redirect(get_role_dashboard_url(request.user))
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def admin_dept_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not request.user.is_authenticated:
            messages.warning(request, "Please log in to access the Admin Department portal.")
            return redirect(f"/login/admin/?next={request.path}")
        if not (request.user.role == CustomUser.Role.ADMIN or request.user.is_superuser or request.user.is_staff):
            messages.error(request, "Access Denied: Administrator privileges are required to access this page.")
            return redirect(get_role_dashboard_url(request.user))
        return view_func(request, *args, **kwargs)
    return _wrapped_view


# ==========================================
# Django REST Framework Permissions
# ==========================================

class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated and (request.user.role == CustomUser.Role.ADMIN or request.user.is_superuser))


class IsTempleOwner(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == CustomUser.Role.TEMPLE_OWNER or request.user.is_superuser))


class IsCollector(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == CustomUser.Role.COLLECTOR or request.user.is_superuser))


class IsAdminDept(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and (request.user.role == CustomUser.Role.ADMIN or request.user.is_superuser or request.user.is_staff))
