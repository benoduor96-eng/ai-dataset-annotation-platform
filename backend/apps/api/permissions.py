"""Reusable ownership checks for API objects.

The platform is intentionally single-tenant at the project boundary for now:
a user may only operate on projects they own. Centralising these checks keeps
viewsets from accidentally exposing objects belonging to another account.
"""
from rest_framework.permissions import BasePermission


class IsProjectOwner(BasePermission):
    """Allow access only when the object's project belongs to the requester."""

    message = "You do not have access to this project."

    def has_object_permission(self, request, view, obj):
        project = getattr(obj, "project", None)
        if project is None and hasattr(obj, "dataset"):
            project = getattr(obj.dataset, "project", None)
        if project is None and hasattr(obj, "task"):
            project = getattr(obj.task.dataset, "project", None)
        if project is None and hasattr(obj, "annotation"):
            project = getattr(obj.annotation.task.dataset, "project", None)
        return project is not None and project.owner_id == request.user.id
