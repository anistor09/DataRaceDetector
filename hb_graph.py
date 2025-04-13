from collections import defaultdict
from typing import List,Dict,Optional,Tuple
from collections import deque
from trace_structure import ThreadAction, TraceStruct
import time
from typing import List, Set



class HBGraph:

    def add_fences_sw_edges(self, trace):
        closest_fence_leftside = {}
        prefix_fence_for_thread = defaultdict(lambda: None)

        # for each atomic write find the closest release fence to the left
        for action_group in trace.actions:
            for action in action_group:
                tid = action.thread_id
                if action.action_type == "fence" and action.memory_order in ("acq_rel", "release", "seq_cst"):
                    prefix_fence_for_thread[tid] = action.id
                elif action.action_type == "atomic write":
                    closest_fence_leftside[action.id] = prefix_fence_for_thread[tid]

        closest_fence_rightside = {}
        prefix_fence_for_thread = defaultdict(lambda: None)

        # for each atomic read find the closest acquire fence to the right
        for action_group in reversed(trace.actions):
            for action in reversed(action_group):
                tid = action.thread_id
                if action.action_type == "fence" and action.memory_order in ("acq_rel", "acquire", "seq_cst"):
                    prefix_fence_for_thread[tid] = action.id
                elif action.action_type == "atomic read":
                    closest_fence_rightside[action.id] = prefix_fence_for_thread[tid]

        # For each atomic read:
        # - Check if it has a read-from relationship (it reads a value written by some write).
        # - Look up the closest release-side fence before the write (in its thread).
        # - Look up the closest acquire-side fence after the read (in its thread).
        # Then add the appropriate edges based on C++11 synchronization rules:
        # - Fence-to-Fence: release fence → acquire fence
        # - Fence-to-Read: release fence → acquire read
        # - Write-to-Fence: release write → acquire fence
        for action_group in trace.actions:
            for read in action_group:
                if read.action_type == "atomic read" and read.read_from is not None:
                    for write in trace.actions[read.read_from]:
                        if write.action_type == "atomic write" and write.location == read.location:
                            f_release = closest_fence_leftside.get(write.id)
                            f_acquire = closest_fence_rightside.get(read.id)
                            # Fence-fence synchronization
                            if f_release is not None and f_acquire is not None:
                                self.add_edge(f_release, f_acquire, edge_type="sw")
                            # Fence-atomic synchronization
                            # the read has to be acquire, write can be any memory order, f_release is before write in thread A
                            if f_release is not None and read.memory_order in ("acquire", "seq_cst"):
                                self.add_edge(f_release, read.id, edge_type="sw")
                            # Atomic-fence synchronization
                            # the write has to be release, atomic read before fence in thread B, read has any memory order
                            if f_acquire is not None and write.memory_order in ("release", "seq_cst"):
                                self.add_edge(write.id, f_acquire, edge_type="sw")

    def __init__(self, trace:TraceStruct):
        # unique thread id trace size
        self.size: int = trace.actions[-1][-1].id + 1
        # the graph
        self.edges:List[List[int]] = [[] for _ in range(self.size)]
        # the tracer
        self.trace:TraceStruct = trace
        # memory location to actions
        self.location_to_actions: Dict[str , List[int]] = defaultdict(lambda: [])
        self.simple_action_list: List[ThreadAction] = []
        # last unlocked mutex for sw between unlock -> lock for a mutex location
        mutex_last_unlock: Dict[str, int] = {}

        last_thread_create: Optional[int] = None
        thread_to_last_action:Dict[int,int] = {}

        # The next 3 data structures are used only for plotting purposes
        self.sw_edges: Set[Tuple[int, int]] = set()
        self.po_edges: Set[Tuple[int, int]] = set()
        self.action_types: Dict[int, str] = {}

        self.add_fences_sw_edges(trace)

        for action_group in trace.actions:
            for action in action_group: 
                # adds to action to the list of actions per location
                self.location_to_actions[action.location].append(action.id)
                self.simple_action_list.append(action)
                self.action_types[action.id] = action.action_type

                # mutexes
                # Create a SW edge from the last unlock on the same mutex to the current lock.
                if action.action_type == "lock":
                    if action.location in mutex_last_unlock:
                        self.add_edge(mutex_last_unlock[action.location], action.id, edge_type="sw")
                elif action.action_type == "unlock":
                    mutex_last_unlock[action.location] = action.id
                # Condition variable wait
                # Treat 'wait' as an implicit unlock of the associated mutex (stored in `value`).
                # This allows a SW edge from the wait to the next lock on the same mutex.
                #
                # Note: We do NOT explicitly add notify edges.
                # C++Tester guarantees the correct thread resumes from notify_one or notify_all.
                #
                # In broadcast cases (notify_all), only one thread proceeds first.
                # When it unlocks the mutex, the next awakened thread can lock it, and so on.
                # This builds transitive HB edges across resumed threads naturally through lock/unlock edges.
                # so explicit notify one / notify all edges are unnecessary.
                elif action.action_type == "wait":
                    address = self.format_address_value_location(action.value)
                    mutex_last_unlock[address] = action.id

                # write release -> rf -> read acquire
                # goes through action_group to find a possible sw parent
                if action.memory_order == "acquire" and action.read_from:
                    for possible_parent in trace.actions[action.read_from]:
                        if possible_parent.memory_order == "release" and possible_parent.value == action.value and possible_parent.location == action.location:
                            self.add_edge(possible_parent.id, action.id, edge_type="sw")

                if action.action_type == "thread start" or action.action_type == "pthread start":
                    # if it's thread 1 since it does not have a thread that started it
                    if not last_thread_create:
                        thread_to_last_action[action.thread_id] = action.id
                        # first thread
                        continue
                    # po edge between parent and child thread
                    self.add_edge(last_thread_create, action.id, edge_type="po")
                    thread_to_last_action[action.thread_id] = action.id
                    # thread was just created
                    continue
                
                if action.action_type == "pthread join" or action.action_type == "thread join":
                    end_thread = int(action.value, 16)
                    self.add_edge(thread_to_last_action[end_thread], action.id, edge_type="po")

                if action.action_type == "pthread create" or action.action_type == "thread create":
                    last_thread_create = action.id

                # po edge from same thread to same thread
                self.add_edge(thread_to_last_action[action.thread_id], action.id, edge_type="po")
                # mark action as last processed action in thread
                thread_to_last_action[action.thread_id] = action.id
        

    # def add_edge(self, parent, node):
    #     self.edges[parent].append(node)

    def add_edge(self, parent, node, edge_type: Optional[str] = None):
        self.edges[parent].append(node)
        if edge_type == "sw":
            self.sw_edges.add((parent, node))
        elif edge_type == "po":
            self.po_edges.add((parent, node))

    def format_address_value_location(self, hex_value):
        formatted = f"{int(hex_value, 16):016X}"
        return formatted

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

        result.append("  SW Edges:")
        for (src, dst) in sorted(self.sw_edges):
            result.append(f"    {src} -> {dst}")

        result.append("  PO Edges:")
        for (src, dst) in sorted(self.po_edges):
            result.append(f"    {src} -> {dst}")

        result.append("  Action ID -> (TID, Type, Location):")
        for action_id in sorted(self.action_types.keys()):
            action = self._get_action_by_id(action_id)
            thread_id = action.thread_id
            action_type = self.action_types[action_id]
            location = action.location
            result.append(f"    {action_id} -> (T{thread_id}, {action_type}, loc: {location})")
        
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

    def _compute_happens_before(self) -> List[set]:
        n = len(self.edges)
        happensBefore = [set() for _ in range(n)]
        in_degree = [0] * n

        # Compute in-degrees
        for u in range(n):
            for v in self.edges[u]:
                in_degree[v] += 1

        # Initialize queue with nodes that have in-degree 0
        queue = deque([i for i in range(n) if in_degree[i] == 0])

        while queue:
            node = queue.popleft()

            for neighbor in self.edges[node]:
                # Add current node to happens-before of the neighbor
                happensBefore[neighbor].add(node)
                # Add everything that happened before current node
                happensBefore[neighbor].update(happensBefore[node])

                # Decrease in-degree and enqueue if it's 0
                in_degree[neighbor] -= 1
                if in_degree[neighbor] == 0:
                    queue.append(neighbor)

        return happensBefore

    def _get_action_by_id(self, action_id: int) -> ThreadAction:
        return self.simple_action_list[action_id]
    
    def detect_data_races(self) -> List[Tuple[ThreadAction, ThreadAction]]:
        dependency_sets = self._compute_dependency_sets()
        races = []

        for location, action_ids in self.location_to_actions.items():
            for i in range(len(action_ids)):
                id1 = action_ids[i]
                a1 = self._get_action_by_id(id1)
                if a1.action_type == "nonatomic write":
                    for j in range(0, len(action_ids)):
                        id2 = action_ids[j]
                        a2 = self._get_action_by_id(id2)
                        if not (j <= i and a2.action_type == "nonatomic write"):
                            if id2 not in dependency_sets[id1] and id1 not in dependency_sets[id2]:
                                races.append((a1, a2))
        return races

    def _compute_dependency_sets(self) -> List[set]:
        use_happens_before = True
        if use_happens_before:
            return self._compute_happens_before()
        else:
            return self._compute_reachability()

    def comparison_hb_reachable(self) -> bool:
        start = time.time()
        reachable = self._compute_reachability()
        end = time.time()
        time_non_eff = end - start
        print(f"Non-efficient version took {time_non_eff:.6f} seconds")

        start = time.time()
        happens_before_eff = self._compute_happens_before()
        end = time.time()
        time_eff = end - start
        print(f"Efficient version took {time_eff:.6f} seconds")
        n = len(self.edges)

        # Let s see if the HB and HB from reachable are identic
        happens_before_from_reachable: List[Set[int]] = [set() for _ in range(n)]
        for j in range(n):
            for i in reachable[j]:
                happens_before_from_reachable[i].add(j)

        if happens_before_eff == happens_before_from_reachable:
            return True
        else:
            print("HB from reachable:")
            print(happens_before_from_reachable)
            print("HB normal computation:")
            print(happens_before_eff)
            return False

