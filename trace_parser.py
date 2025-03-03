from event import Event


def parse_trace(lines):
    """
    lines: list of strings representing each row (beyond the header).
    Returns: list of Event objects
    """
    events = []
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#') or line.startswith('-'):
            continue

        parts = line.split()
        # EID T ActionType MO Location Value
        eid = int(parts[0])
        thread_id = int(parts[1])
        action_type = parts[2] + (" " + parts[3] if len(parts) > 3 else "")
        mem_order = parts[4] if len(parts) > 4 else ""
        location = parts[5] if len(parts) > 5 else ""
        value = parts[6] if len(parts) > 6 else ""

        # We might have to adjust index slicing if the columns vary
        evt = Event(eid, thread_id, action_type, mem_order, location, value)
        events.append(evt)

    # Sort by EID just in case
    events.sort(key=lambda e: e.eid)
    return events
