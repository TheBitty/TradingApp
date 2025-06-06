# Trading Application Project Memory

## Project Overview
A high-performance trading system demonstrating ultra-low latency inter-process communication (IPC) between C++ and Python components using POSIX shared memory.

## Architecture Summary
```
C++ Producer (market data) <---> Shared Memory (/dev/shm) <---> Python Consumer (trading strategies)
```

## Key Components

### C++ Core (`/C++/src/`)
- **`include/shared_code.h`**: Template-based SharedMemory class with atomic operations
- **`include/trading_system.h`**: Trading-specific data structures
- **`main.cpp`**: Main application with shared memory producer implementation
- **`simple_main.cpp`**: Simplified version for testing
- **`api.cpp`**: API implementation for external interfaces
- **Market Data**: CSV files in `market_data/` (stocks: AAPL, TSLA; crypto: BTC)

### Python Components (`/Python/`)
- **`main.py`**: SharedMemoryConsumer class for reading C++ shared memory
- **`data_bridge.py`**: Bridge utilities for data translation
- **`data_viewer.py`**: Visualization and monitoring tools

### Shared Memory Structure
```cpp
struct TradingData {
    std::atomic<double> price;      // 8 bytes
    std::atomic<uint64_t> timestamp; // 8 bytes
    std::atomic<int32_t> volume;    // 4 bytes
    std::atomic<bool> valid;        // 1 byte + 3 padding
}; // Total: 24 bytes
```

## Build Commands
```bash
# C++ build
cd C++/src
g++ -o trading_app main.cpp -lrt -pthread -std=c++17

# Run system
./run_system.sh  # Automated startup script
```

## Testing
- **`test_system.py`**: Python system tests
- **`test_shared_memory.sh`**: Shell script for shared memory validation
- **`demo.py`**: Interactive demonstration

## Performance Goals
- **Latency**: < 100 nanoseconds for shared memory access
- **Throughput**: > 1M messages/second
- **Zero-copy**: Direct memory access between processes

## Common Operations

### Check shared memory status
```bash
ls -la /dev/shm/trading_data
```

### Clean up shared memory
```bash
rm -f /dev/shm/trading_data
```

### Monitor system
```bash
# C++ side
./trading_app

# Python side (in separate terminal)
cd Python && python3 main.py
```

## Debug Tips
1. Use `strace` to monitor system calls: `strace -e trace=mmap,shm_open ./trading_app`
2. Check memory layout: `hexdump -C /dev/shm/trading_data`
3. Verify struct sizes match between C++ and Python (24 bytes)

## Next Steps
- [ ] Add ring buffer for multiple data points
- [ ] Implement order management system
- [ ] Add real-time performance monitoring
- [ ] Create WebSocket API for web clients

## Notes
- Uses POSIX shared memory (`/dev/shm/`) for ultra-low latency
- All operations are lock-free using atomic types
- Python uses 1ms polling by default (adjustable for higher frequency)
- Remember to handle cleanup properly to avoid memory leaks
