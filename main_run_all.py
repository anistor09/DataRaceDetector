import os
import sys
from io import StringIO

from hb_graph import HBGraph
from parser_2 import parse_trace


def process_trace_file(trace_path):
    output = StringIO()
    try:
        execution_trace_list = parse_trace(trace_path)

        for trace in execution_trace_list:
            hb_graph = HBGraph(trace)
            # Testing purposes
            # if hb_graph.comparison_hb_reachable():
            #     output.write("HB and Reachable are the same ✅\n")
            # else:
            #     output.write("HB and Reachable are not the same ❌\n")
            data_races = hb_graph.detect_data_races()
            for el1, el2 in data_races:
                output.write("Data race detected between\n")
                output.write(f"{el1}\n")
                output.write(f"{el2}\n\n")
            if not data_races:
                output.write("No data races found in this program")
    except Exception as e:
        output.write(f"Error processing {trace_path}: {e}\n")

    return output.getvalue()


def main():
    benchmark_dir = "benchmark"

    for root, dirs, files in os.walk(benchmark_dir):
        for file in files:
            if file.endswith(".txt"):
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}")
                result = process_trace_file(file_path)
                output_path = os.path.splitext(file_path)[0] + "_algorithm_output.txt"
                with open(output_path, "w") as f:
                    f.write(result)


if __name__ == "__main__":
    main()
