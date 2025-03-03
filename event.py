class Event:
    def __init__(self, eid, thread_id, op_type, mem_order, location, value):
        self.eid = eid
        self.thread_id = thread_id
        self.op_type = op_type  # e.g., 'thread start', 'non-atomic write', 'atomic write'
        self.mem_order = mem_order  # e.g., 'non-atomic', 'relaxed', 'seq_cst'
        self.location = location
        self.value = value

    def is_write(self):
        # If the action type says it's a write, we consider it a write
        return 'write' in self.op_type

    def is_read(self):
        return 'read' in self.op_type

    def is_non_atomic(self):
        return (self.mem_order == 'non-atomic')
