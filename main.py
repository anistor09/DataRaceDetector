import sys

from hb_graph import HBGraph
from parser_2 import parse_trace
import sys
sys.setrecursionlimit(1000000)


def main():
    trace_name = "trace.txt"
    # 1) Parse input
    execution_trace_list = parse_trace(trace_name)
    for trace in execution_trace_list:
        hb_graph = HBGraph(trace)
        print(hb_graph)
        data_races = hb_graph.detect_data_races()
        if not data_races:
            print("No data races found in this program")
        for data_race in data_races:
            el1 = data_race[0]
            el2 = data_race[1]
            print("Data race detected between")
            print(el1)
            print(el2)
            print()
        return

if __name__ == "__main__":
    main()
