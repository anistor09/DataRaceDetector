from collections import defaultdict
from typing import List,Dict,Optional,Tuple
from dataclasses import dataclass
from trace_structure import ThreadAction, TraceStruct

class HBGraph:
    
    def __init__(self, trace:TraceStruct):
        # unique thread id trace size
        self.size: int = trace.actions[-1][-1].id + 1
        # the graph
        self.edges:List[List[int]] = [[] for _ in range(self.size)]
        # the tracer
        self.trace:TraceStruct = trace
        # memory location to actions
        self.location_to_actions: Dict[str , List[int]] = defaultdict(lambda: [])
        # last unlocked mutex for sw between unlock -> lock for a mutex location
        mutex_last_unlock: Dict[str, int] = {}

        last_thread_create: Optional[int] = None
        thread_to_last_action:Dict[int,int] = {}

        for action_group in trace.actions:
            for action in action_group: 
                # adds to action to the list of actions per location
                self.location_to_actions[action.location].append(action.id)

                if action.action_type == "lock":
                    if action.location in mutex_last_unlock:
                        self.add_edge(mutex_last_unlock[action.location], action.id)
                elif action.action_type == "unlock":
                    mutex_last_unlock[action.location] = action.id

                # goes through action_group to find a possible sw parent
                if action.memory_order == "acquire" and action.read_from:
                    for possible_parent in trace.actions[action.read_from]:
                        if possible_parent.memory_order == "release" and possible_parent.value == action.value and possible_parent.location == action.location:
                            self.add_edge(possible_parent.id, action.id)

                if action.action_type == "thread start":
                    # if it's thread 1 since it does not have a thread that started it
                    if not last_thread_create:
                        thread_to_last_action[action.thread_id] = action.id
                        # first thread
                        continue
                    # po edge between parent and child thread
                    self.add_edge(last_thread_create, action.id)
                    thread_to_last_action[action.thread_id] = action.id
                    # thread was just created
                    continue
                
                if action.action_type == "pthread join":
                    end_thread = int(action.value, 16)
                    self.add_edge(thread_to_last_action[end_thread], action.id)

                if action.action_type == "pthread create":
                    last_thread_create = action.id

                # po edge from same thread to same thread
                self.add_edge(thread_to_last_action[action.thread_id], action.id)
                # mark action as last processed action in thread
                thread_to_last_action[action.thread_id] = action.id
        

    def add_edge(self, parent, node):
        self.edges[parent].append(node)

    def __str__(self):
        result = ["HBGraph:"]
        result.append("  Edges:")
        for src, targets in enumerate(self.edges):
            if targets:
                targets_str = ", ".join(map(str, targets))
                result.append(f"    {src} -> [{targets_str}]")
        
        result.append("  Location to Actions:")
        for loc, ids in self.location_to_actions.items():
            ids_str = ", ".join(map(str, ids))
            result.append(f"    {loc}: [{ids_str}]")
        
        return "\n".join(result)
    
    def _compute_reachability(self) -> List[set]:
        n = len(self.edges)
        reachable = [set() for _ in range(n)]

        def dfs(start, node):
            for neighbor in self.edges[node]:
                if neighbor not in reachable[start]:
                    reachable[start].add(neighbor)
                    dfs(start, neighbor)

        for i in range(n):
            dfs(i, i)

        return reachable

    def _get_action_by_id(self, action_id: int) -> ThreadAction:
        for group in self.trace.actions:
            for action in group:
                if action.id == action_id:
                    return action

    def detect_data_races(self) -> List[Tuple[ThreadAction, ThreadAction]]:
        reachable = self._compute_reachability()
        races = []

        for location, action_ids in self.location_to_actions.items():
            for i in range(len(action_ids)):
                for j in range(i + 1, len(action_ids)):
                    id1, id2 = action_ids[i], action_ids[j]
                    a1 = self._get_action_by_id(id1)
                    a2 = self._get_action_by_id(id2)

                    if a1.thread_id == a2.thread_id:
                        continue
                    if "nonatomic write" not in a1.action_type and "nonatomic write" not in a2.action_type:
                        continue
                    if id2 not in reachable[id1] and id1 not in reachable[id2]:
                        races.append((a1, a2))
        return races
