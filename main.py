import sys

from hb_builder import build_hb_edges, build_transitive_closure
from na_races_detector import detect_na_races
from trace_parser import parse_trace


def main():
    print("Enter the execution trace (Ctrl+D to finish input):")

    # Read all lines from input at once
    raw_lines = []
    for line in sys.stdin:
        raw_lines.append(line.strip())

    # 1) Parse input
    events = parse_trace(raw_lines)

    # 2) Build happens-before dependencies
    hb_edges = build_hb_edges(events)

    # 3) Compute transitive closure of HB relation
    hb_tc = build_transitive_closure(hb_edges)

    # 4) Detect NA-races
    races = detect_na_races(events, hb_tc)

    # 5) Print results
    if races:
        print("\nNon-atomic Data Races Found:")
        for (e1, e2) in races:
            print(f"  E{e1.eid} (Thread {e1.thread_id}, {e1.op_type}) "
                  f" and E{e2.eid} (Thread {e2.thread_id}, {e2.op_type}) "
                  f" on location {e1.location}")
    else:
        print("\nNo non-atomic data races found.")


if __name__ == "__main__":
    main()
