"""Centralized audit-event creation helpers.

Call these helpers from the same database transaction as the state change so
an event is not written when its corresponding operation rolls back.
"""
from apps.annotations.models import AuditEvent


def record_event(*, project, actor, event_type, object_type, object_id, metadata=None):
    """Persist a small, structured event; callers must not pass sensitive payloads."""
    return AuditEvent.objects.create(
        project=project,
        actor=actor,
        event_type=event_type,
        object_type=object_type,
        object_id=str(object_id),
        metadata=metadata or {},
    )
