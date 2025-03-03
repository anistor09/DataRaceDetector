from collections import defaultdict, deque


def build_hb_edges(events):
    """
    Returns a dict: hb_edges[eid] = set of EIDs that happen
    immediately after e1 in the partial order.
    (We do a simple approach: same-thread ordering + start/finish constraints.)
    """
    hb_edges = defaultdict(set)

    # Group events by thread
    thread_map = defaultdict(list)
    for e in events:
        thread_map[e.thread_id].append(e)

    # Sort within each thread by EID (we assume they're mostly sorted, but just to be sure)
    for tid, ev_list in thread_map.items():
        ev_list.sort(key=lambda x: x.eid)
        # For consecutive events in same thread, e_i -> e_(i+1)
        for i in range(len(ev_list) - 1):
            e1 = ev_list[i]
            e2 = ev_list[i + 1]
            hb_edges[e1.eid].add(e2.eid)

    # We can add more logic for "thread start" or "thread finish" if needed
    # In your trace, "thread start" is typically the first event of that thread.
    # "thread finish" is typically the last event.
    # But we won't add special edges for them unless we have cross-thread constraints.

    return dict(hb_edges)


def build_transitive_closure(hb_edges):
    """
    Compute the transitive closure: for each e, find all events reachable from e.
    Return a dict: hb_tc[e] = set of all e' where e -> e' in the transitive sense.
    """
    hb_tc = {}
    for start in hb_edges.keys():
        visited = set()
        stack = list(hb_edges[start])
        while stack:
            nxt = stack.pop()
            if nxt not in visited:
                visited.add(nxt)
                stack.extend(hb_edges.get(nxt, []))
        hb_tc[start] = visited
    return hb_tc


def happens_before(e1, e2, hb_tc):
    """Return True if e1 -> e2 (transitively) using hb_tc dict."""
    return e2.eid in hb_tc.get(e1.eid, set())
