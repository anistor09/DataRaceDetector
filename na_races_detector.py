from hb_builder import happens_before


def detect_na_races(events, hb_tc):
    """
    Return a list of (e1, e2) pairs that form a non-atomic data race.
    """
    na_races = []
    n = len(events)
    for i in range(n):
        for j in range(i + 1, n):
            e1 = events[i]
            e2 = events[j]
            # Data-race conditions
            same_location = (e1.location == e2.location) and e1.location != ""
            at_least_one_write = (e1.is_write() or e2.is_write())
            # concurrency => not (e1->e2) and not (e2->e1)
            concurrent = (not happens_before(e1, e2, hb_tc)) and \
                         (not happens_before(e2, e1, hb_tc))

            # For NA-race: at least one is non-atomic
            if same_location and at_least_one_write and concurrent:
                if e1.is_non_atomic() or e2.is_non_atomic():
                    na_races.append((e1, e2))
    return na_races
