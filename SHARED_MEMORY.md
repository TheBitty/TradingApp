# Shared Memory Implementation for Trading App

## Overview
This implementation provides ultra-low latency shared memory communication between C++ and Python components, optimized for nanosecond trading requirements.

## Architecture

### C++ Side (`/C++/src/include/shared_code.h`)
- **SharedMemory<T>**: Template class for type-safe shared memory
- **TradingData**: Atomic data structure for market data
- **POSIX shared memory**: Uses `shm_open()`, `mmap()` for maximum performance

### Python Side (`/Python/main.py`)
- **SharedMemoryConsumer**: Reads data from C++ shared memory
- **TradingData**: Python NamedTuple matching C++ structure
- **1ms polling**: High-frequency monitoring (adjustable to microseconds)

## Usage

### C++ Producer
```cpp
#include "include/shared_code.h"

// Create shared memory segment
SharedMemory<TradingData> trading_shm("/trading_data", true);

// Write atomic data
auto data = trading_shm.get();
data->price.store(100.50);
data->volume.store(1000);
data->timestamp.store(current_nanoseconds());
data->valid.store(true);
```

### Python Consumer
```python
from main import SharedMemoryConsumer

consumer = SharedMemoryConsumer("/trading_data")
if consumer.connect():
    data = consumer.read_trading_data()
    print(f"Price: {data.price}, Volume: {data.volume}")
```

## Performance Characteristics

### Latency
- **Memory access**: ~10-50 nanoseconds (L1 cache hit)
- **Atomic operations**: ~1-10 nanoseconds per read/write
- **No system calls**: After setup, zero kernel overhead
- **Lock-free**: All operations are atomic, no mutexes

### Memory Layout
```
TradingData structure (24 bytes total):
├── price     (8 bytes) - atomic<double>
├── timestamp (8 bytes) - atomic<uint64_t> 
├── volume    (4 bytes) - atomic<int32_t>
├── valid     (1 byte)  - atomic<bool>
└── padding   (3 bytes) - alignment
```

## Key Features

### Atomic Operations
All data fields use `std::atomic` to prevent race conditions:
- **price.store()/load()**: Lock-free price updates
- **timestamp.store()/load()**: Nanosecond timing
- **volume.store()/load()**: Trade volume
- **valid.store()/load()**: Data validity flag

### Memory Mapping
- **POSIX shared memory**: `/dev/shm` filesystem for speed
- **Memory-mapped files**: Direct memory access, no copies
- **PAGE_SIZE aligned**: Optimal for CPU cache lines

## Build & Run

### Compile C++
```bash
cd C++/src
g++ -o trading_app main.cpp -lrt -pthread
./trading_app
```

### Run Python Consumer
```bash
cd Python
python3 main.py
```

## Error Handling

### C++ Errors
- **EEXIST**: Shared memory already exists (use attach mode)
- **EACCES**: Permission denied (check file permissions)
- **ENOMEM**: Insufficient memory

### Python Errors
- **FileNotFoundError**: C++ producer not running
- **PermissionError**: Access rights issue
- **struct.error**: Data format mismatch

## Optimization Tips

### For Nanosecond Trading
1. **CPU Affinity**: Pin processes to specific CPU cores
2. **Memory Locking**: Use `mlock()` to prevent swapping
3. **Huge Pages**: Configure system for 2MB pages
4. **NUMA Awareness**: Place memory on same NUMA node
5. **Real-time Priority**: Use `SCHED_FIFO` scheduling

### Code Example - Ultra Low Latency
```cpp
// Pin to CPU core 0
cpu_set_t cpuset;
CPU_ZERO(&cpuset);
CPU_SET(0, &cpuset);
sched_setaffinity(0, sizeof(cpuset), &cpuset);

// Lock memory to prevent swapping
mlockall(MCL_CURRENT | MCL_FUTURE);

// Set real-time priority
struct sched_param sp;
sp.sched_priority = 99;
sched_setscheduler(0, SCHED_FIFO, &sp);
```

## Future Enhancements
- Ring buffers for multiple data points
- Memory barriers for ordering guarantees
- RDMA support for networked shared memory
- Hardware timestamping integration