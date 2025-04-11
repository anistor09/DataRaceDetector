import os
from io import StringIO

from hb_graph import HBGraph
from parser_2 import parse_trace


def process_trace_file(trace_path):
    output = StringIO()
    try:
        execution_trace_list = parse_trace(trace_path)

        for trace in execution_trace_list:
            hb_graph = HBGraph(trace)
            if hb_graph.comparison_hb_reachable():
                output.write("HB and Reachable are the same ✅\n")
            else:
                output.write("HB and Reachable are not the same ❌\n")
            data_races = hb_graph.detect_data_races()
            for el1, el2 in data_races:
                output.write("Data race detected between\n")
                output.write(f"{el1}\n")
                output.write(f"{el2}\n\n")
    except Exception as e:
        output.write(f"Error processing {trace_path}: {e}\n")

    return output.getvalue()


def main():
    benchmark_dir = "benchmark"
    output_base_dir = "output"
    os.makedirs(output_base_dir, exist_ok=True)

    for root, _, files in os.walk(benchmark_dir):
        for file in files:
            if file.endswith(".txt") and "output" not in root:
                file_path = os.path.join(root, file)
                print(f"Processing {file_path}")
                result = process_trace_file(file_path)

                # Compute relative path from benchmark dir
                relative_dir = os.path.relpath(root, benchmark_dir)
                output_dir = os.path.join(output_base_dir, relative_dir)
                os.makedirs(output_dir, exist_ok=True)

                output_filename = os.path.splitext(file)[0] + "_algorithm_output.txt"
                output_path = os.path.join(output_dir, output_filename)

                with open(output_path, "w") as f:
                    f.write(result)


if __name__ == "__main__":
    main()
