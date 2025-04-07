import sys

#from hb_builder import build_hb_graph
#from na_races_detector import detect_na_races
from hb_graph import HBGraph
from trace_parser import parse_trace


def main():
    trace_name = "trace_outputNicu.txt"
    # 1) Parse input
    execution_trace_list = parse_trace(trace_name)

    for trace in execution_trace_list:
        hb_graph = HBGraph(trace)
        print(hb_graph)
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
