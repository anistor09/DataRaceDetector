import sys

# from hb_builder import build_hb_graph
# from na_races_detector import detect_na_races
from hb_graph import HBGraph
# from trace_parser import parse_trace
from parser_2 import parse_trace
import sys
sys.setrecursionlimit(1000000)


def main():
    # trace_name = "trace_outputNicu.txt"
    trace_name = "benchmark/c11tester/iris/trace_output_test2.txt"
    # 1) Parse input
    execution_trace_list = parse_trace(trace_name)
    for trace in execution_trace_list:
        hb_graph = HBGraph(trace)
        # print(hb_graph)
        if hb_graph.comparison_hb_reachable():
            print("HB and Reachable are the same ✅")
        else:
            print("HB and Reachable are not the same ❌")
        data_races = hb_graph.detect_data_races()
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
