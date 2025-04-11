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

        # for the relaxed case of memory order of read and write, since sw edges for release acquire are already there
        # goes through the reads, see if it has read froms, if it has it gets the closest release fence to the left of
        # the write and adds a sw edge to the closest edge to the right of the read
        for action_group in trace.actions:
            for read in action_group:
                if read.action_type == "atomic read" and read.read_from is not None:
                    for write in trace.actions[read.read_from]:
                        if write.action_type == "atomic write" and write.location == read.location:
                            f_release = closest_fence_leftside.get(write.id)
                            f_acquire = closest_fence_rightside.get(read.id)
                            if f_release is not None and f_acquire is not None:
                                self.add_edge(f_release, f_acquire)

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

        self.add_fences_sw_edges(trace)

        for action_group in trace.actions:
            for action in action_group: 
                # adds to action to the list of actions per location
                self.location_to_actions[action.location].append(action.id)

                # mutexes
                if action.action_type == "lock":
                    if action.location in mutex_last_unlock:
                        self.add_edge(mutex_last_unlock[action.location], action.id)
                elif action.action_type == "unlock":
                    mutex_last_unlock[action.location] = action.id
                # condition variables (notify/wait)
                # treat wait as an unlock: it releases a mutex (given by `value`),
                # so we update mutex_last_unlock to allow a SW edge to the next lock.
                # we don't track which notify triggered it—C++tester ensures correct thread is awakened.
                # for broadcast if more threads are awakened, only one will actually execute, the others only when
                # this chosen one will release the mutex.

                # Under broadcast, only one thread resumes first (as per trace order).
                # That thread unlocks the mutex, allowing the next resumed thread to lock it.
                # Each resumed thread thus gets a SW edge from the previous one via lock/unlock.
                # This creates transitive HB edges from the broadcast thread to all resumed threads,
                # so explicit notify one / notify all edges are unnecessary.
                elif action.action_type == "wait":
                    address = self.format_address_value_location(action.value)
                    mutex_last_unlock[address] = action.id


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
        for group in self.trace.actions:
            for action in group:
                if action.id == action_id:
                    return action

    def detect_data_races(self) -> List[Tuple[ThreadAction, ThreadAction]]:
        dependency_sets = self._compute_dependency_sets()
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

