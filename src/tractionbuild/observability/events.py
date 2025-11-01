def mk_event(event_type, actor=None, project_id=None, payload=None):
    """Creates a structured event dictionary."""
    return {
        "event_type": event_type,
        "actor": actor,
        "project_id": project_id,
        "payload": payload,
    }

def emit(event):
    """(No-op) Emits an event to a logging or monitoring system."""
    pass
