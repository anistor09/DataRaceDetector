# NA-Race Detector

## Overview
This project detects **non-atomic data races (NA-races)** in execution traces of **C++ concurrent programs**. It processes an input trace, builds a **happens-before (HB) relation** using **thread start/finish and sequential execution**, and identifies data races where **at least one access is non-atomic**.

## How It Works
1. **Reads** an execution trace from the console **(all lines at once)**.
2. **Parses** only the first five columns:  
   - **Event ID (EID)**  
   - **Thread ID (T)**  
   - **Action Type** (`thread start`, `non-atomic write`, `atomic read`, etc.)  
   - **Memory Order (MO)** (`non-atomic`, `relaxed`, `seq_cst`, etc.)  
   - **Memory Location** (`&g_counter`, `&g_atomicCounter`, etc.)  
   - Everything after the **memory location is ignored**.
3. **Builds a happens-before (HB) relation**:
   - Orders events **within the same thread**.
   - Orders **thread start** → first event and **last event** → **thread finish**.
4. **Computes HB transitive closure** to determine **concurrent** events.
5. **Detects NA-races** by checking:
   - **Same memory location**
   - **At least one write**
   - **At least one non-atomic**
   - **No happens-before relation** (concurrent accesses)
6. **Outputs the detected NA-races** or confirms none were found.

## Input Format
Each execution trace line should follow this format:


- **EID**: Unique Event ID
- **T**: Thread ID
- **Action Type**: Memory action (`read`, `write`, `atomic write`, etc.)
- **MO (Memory Order)**: `non-atomic`, `relaxed`, `seq_cst`
- **Location**: The shared variable (`&g_counter`)
- **Everything after the memory location is ignored**.

## How to Use
1. Run the script:
2. **Enter trace data line by line**, then **press Ctrl+D** (Linux/macOS) or **Ctrl+Z + Enter** (Windows).
3. The program will **analyze the trace** and output **detected non-atomic data races**.

