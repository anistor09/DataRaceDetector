from trace_structure import ThreadAction, TraceStruct
from typing import List,Optional

def parse_trace(file_name):
    """
    lines: list of strings representing each row (beyond the header).
    Returns: list of Event objects
    """
    execution_trace_list:List[TraceStruct] = []

    with open(file_name, 'r') as file:
        
        while (line := file.readline()):
            line = line.strip()
            words = line.split()
            if len(words) == 3 and words[0] == "Execution" and words[1] == "trace":
                id = 0
                trace_number = int(words[2][:-1])
                
                file.readline()
                file.readline()
                file.readline()
                
                thread_action_trace:List[List[ThreadAction]] = []
                actions_with_same_id:List[ThreadAction] = []
                prev_action_id = 0
                
                while (raw := file.readline()) and not (line := raw.strip()).startswith("HASH"):
                    word_iter = iter(line.split())
                    
                    action_id = int( next(word_iter) ) - 1 #action id skip
                    thread_id:int = int(next(word_iter))
                    action_type: str = next(word_iter) + " " + next(word_iter)
                    
                    if action_type == "atomic notify":
                        action_type+= " " + next(word_iter)

                    memory_order: str = next(word_iter)
                    location: str = next(word_iter)
                    value: str = next(word_iter)
                    
                    read_from: Optional[int] = None
                    next_word = next(word_iter)
                    if next_word != "(":
                        read_from = int(next_word) - 1
                    
                    
                    thread_action:ThreadAction = ThreadAction(id, thread_id, action_type, memory_order, location, value, read_from)
                    id+=1
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
