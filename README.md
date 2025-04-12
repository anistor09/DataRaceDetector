# NA-Race Detector

## 🧠 Overview

This project detects **non-atomic data races (NA-races)** in execution traces of **C++ concurrent programs**. It parses a trace of program execution, builds a **happens-before (HB) graph** using synchronization events and program order, and identifies potential data races where **at least one access is non-atomic**.

---

## 🚀 How It Works

1. **Parse Execution Trace**  
   Reads the execution trace (e.g., `signal_wait.txt`) and converts it into structured trace events.

2. **Build Happens-Before (HB) Graph**  
   Constructs a graph capturing the HB relations between events, based on:
   - Program order (sequential execution within a thread)
   - Synchronization primitives (e.g., `signal/wait`)

3. **Detect NA-Races**  
   Identifies pairs of conflicting memory accesses (i.e., accesses to the same variable where at least one is a write) that are not ordered by the HB relation — and where **at least one is non-atomic**.

## 📌 Usage

1. Place your execution trace file in the `benchmark/` directory.

2. Run the main script:

```bash
python main.py
```

3. Output will list all detected non-atomic data races, or indicate that none were found.

---

## 🧪 Example Output

```
Data race detected between
[Thread 1] Write x at Line 42 (non-atomic)
[Thread 2] Read x at Line 37 (atomic)
```

Or:

```
No data races found in this program
```

---

