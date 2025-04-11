from trace_structure import ThreadAction, TraceStruct
from typing import List, Optional


def parse_trace(file_name):
    """
    Parses a trace file and returns a list of TraceStruct objects.
    """
    execution_trace_list: List[TraceStruct] = []

    with open(file_name, 'r') as file:

        while (line := file.readline()):
            line = line.strip()
            words = line.split()
            if len(words) == 3 and words[0] == "Execution" and words[1] == "trace":
                id = 0
                trace_number = int(words[2][:-1])

                # Skip the next three header lines
                file.readline()
                file.readline()
                file.readline()

                thread_action_trace: List[List[ThreadAction]] = []
                actions_with_same_id: List[ThreadAction] = []
                prev_action_id = 0

                while (raw := file.readline()) and not (line := raw.strip()).startswith("HASH"):
                    word_iter = iter(line.split())

                    # action id skip
                    action_id = int(next(word_iter)) - 1
                    thread_id: int = int(next(word_iter))

                    # Parse action type flexibly:
                    first = next(word_iter)
                    second = next(word_iter)
                    if first == "atomic" and second == "notify":
                        third = next(word_iter)
                        action_type = f"{first} {second} {third}"
                    elif first == "notify" and second == "one":
                        action_type = f"{first} {second}"
                    else:
                        combined = f"{first} {second}"
                        known_two_word_actions = {
                            "atomic read", "atomic write",
                            "pthread create", "pthread join",
                            "thread start", "thread sleep",
                            "nonatomic write", "thread finish", "notify all",
                            "atomic rmw",
                        }
                        if combined in known_two_word_actions:
                            action_type = combined
                        else:
                            # It's a single-word action (e.g., "lock" or "unlock")
                            action_type = first
                            # Put 'second' token back into the iterator
                            word_iter = iter([second] + list(word_iter))

                    # the remaining tokens:
                    memory_order: str = next(word_iter)
                    location: str = next(word_iter)
                    value: str = next(word_iter)

                    read_from: Optional[int] = None
                    next_word = next(word_iter)

                    if action_type == "atomic rmw":
                        next_word = next(word_iter)
                        token = next_word.rstrip(",)")
                        if token.isdigit():
                            read_from = int(token) - 1
                        else:
                            read_from = None 

                    elif next_word != "(":
                        # Remove trailing commas or parentheses from token.
                        token = next_word.rstrip(",)")
                        if token.isdigit():
                            read_from = int(token) - 1
                        else:
                            read_from = None  # If it isn't a valid number, ignore RF.
                    
                    if read_from == -1:
                        read_from = 0

                    thread_action = ThreadAction(id, thread_id, action_type, memory_order, location, value, read_from)
                    id += 1
                    if action_id == prev_action_id:
                        actions_with_same_id.append(thread_action)
                    else:
                        thread_action_trace.append(actions_with_same_id)
                        actions_with_same_id = [thread_action]

                    prev_action_id = action_id

                thread_action_trace.append(actions_with_same_id)

                traceStruct = TraceStruct(trace_number, thread_action_trace)
                execution_trace_list.append(traceStruct)

    return execution_trace_list
