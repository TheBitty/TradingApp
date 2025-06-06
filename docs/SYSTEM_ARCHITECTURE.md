# System Architecture

## Overview

The trading system is designed as a high-performance, low-latency application with clear separation between data acquisition (C++) and strategy execution (Python). The architecture prioritizes speed, reliability, and maintainability.

## Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        Trading System                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────┐    ┌──────────────────┐    ┌─────────────┐ │
│  │   C++ Producer  │◄──►│  Shared Memory   │◄──►│   Python    │ │
│  │   (Market Data) │    │   (/dev/shm)     │    │  Consumer   │ │
│  │                 │    │                  │    │ (Strategy)  │ │
│  │  ┌─────────────┐│    │ ┌──────────────┐ │    │             │ │
│  │  │Market APIs  ││    │ │ TradingData  │ │    │┌───────────┐│ │
│  │  │- YFinance   ││    │ │  Structure   │ │    ││Strategies ││ │
│  │  │- Tiingo     ││    │ │(24 bytes)    │ │    ││- Moving   ││ │
│  │  │- Finnhub    ││    │ │              │ │    ││  Average  ││ │
│  │  └─────────────┘│    │ └──────────────┘ │    ││- RSI      ││ │
│  │                 │    │                  │    ││- Custom   ││ │
│  │  ┌─────────────┐│    │                  │    │└───────────┘│ │
│  │  │Local Storage││    │                  │    │             │ │
│  │  │- CSV Files  ││    │                  │    │┌───────────┐│ │
│  │  │- Historical ││    │                  │    ││Data Bridge││ │
│  │  │  Data       ││    │                  │    ││- File I/O ││ │
│  │  └─────────────┘│    │                  │    ││- API      ││ │
│  └─────────────────┘    └──────────────────┘    │└───────────┘│ │
│                                                  └─────────────┘ │
│                                                                 │
├─────────────────────────────────────────────────────────────────┤
│                       External Interfaces                      │
│                                                                 │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐        │
│  │   Market    │    │    GUI      │    │   Brokers   │        │
│  │   Data      │    │   Viewer    │    │   (Future)  │        │
│  │  Providers  │    │  (tkinter)  │    │             │        │
│  └─────────────┘    └─────────────┘    └─────────────┘        │
└─────────────────────────────────────────────────────────────────┘
```

## Component Architecture

### C++ Core System

#### Process Management
```cpp
┌─────────────────────────────────────────┐
│              main()                     │
├─────────────────────────────────────────┤
│  1. Signal handlers (SIGINT, SIGTERM)  │
│  2. Shared memory cleanup              │
│  3. TradingData shared memory creation  │
│  4. Python process fork/exec           │
│  5. Market data simulation loop        │
│  6. Graceful shutdown handling         │
└─────────────────────────────────────────┘
```

#### Shared Memory Layer
```cpp
┌─────────────────────────────────────────┐
│          SharedMemory<T>                │
├─────────────────────────────────────────┤
│  Template Class:                       │
│  - Type-safe memory mapping            │
│  - POSIX shm_open/mmap interface       │
│  - Automatic cleanup on destruction    │
│  - Lock-free atomic operations         │
│                                         │
│  Memory Layout:                         │
│  ┌─────────────────────────────────────┐ │
│  │ TradingData (24 bytes aligned)     │ │
│  │ ┌─────────┬─────────┬─────┬─────┐ │ │
│  │ │ price   │timestamp│vol  │valid│ │ │
│  │ │(8 bytes)│(8 bytes)│(4b) │(4b) │ │ │
│  │ └─────────┴─────────┴─────┴─────┘ │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### Data Structures
```cpp
┌─────────────────────────────────────────┐
│           TradingData                   │
├─────────────────────────────────────────┤
│  Fields:                               │
│  - atomic<double> price                │
│  - atomic<uint64_t> timestamp          │
│  - atomic<int32_t> volume              │
│  - atomic<bool> valid                  │
│                                         │
│  Properties:                           │
│  - Lock-free operations                │
│  - Cross-platform compatibility        │
│  - Cache-line aligned                  │
│  - Memory barrier guarantees           │
└─────────────────────────────────────────┘
```

### Python Bridge System

#### Module Architecture
```python
┌─────────────────────────────────────────┐
│            data_bridge.py               │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │      TradingDataBridge              │ │
│  │  - Shared memory connection        │ │
│  │  - Binary data parsing             │ │
│  │  - Read/write operations           │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │        DataManager                  │ │
│  │  - CSV file management             │ │
│  │  - Symbol discovery                │ │
│  │  - Historical data access          │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │       TradingSystem                 │ │
│  │  - High-level trading interface    │ │
│  │  - Strategy framework              │ │
│  │  - Portfolio management            │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### Data Flow Architecture
```python
┌─────────────────────────────────────────┐
│              Data Flow                  │
├─────────────────────────────────────────┤
│                                         │
│  C++ → Shared Memory → Python           │
│   ↓        ↓              ↓             │
│  Market    TradingData    Strategy       │
│  Data      Structure      Logic         │
│   ↓        ↓              ↓             │
│  APIs   ┌─────────┐    ┌─────────┐      │
│  Feed   │ price   │    │Indicators│      │
│  ────→  │timestamp│ ──→│Signals   │      │
│         │ volume  │    │Orders    │      │
│         │ valid   │    └─────────┘      │
│         └─────────┘                     │
│                                         │
│  Python → Shared Memory → C++           │
│   ↓           ↓              ↓          │
│  Trading   Signal Data   Order          │
│  Signals   Structure     Management     │
└─────────────────────────────────────────┘
```

## Inter-Process Communication

### Shared Memory Protocol

#### Memory Layout
```
/dev/shm/trading_data (24 bytes total)
┌─────────────────────────────────────────┐
│ Offset │  Size  │    Type    │   Field  │
├─────────────────────────────────────────┤
│   0-7  │ 8 bytes│atomic<dbl> │  price   │
│  8-15  │ 8 bytes│atomic<u64> │timestamp │
│ 16-19  │ 4 bytes│atomic<i32> │ volume   │
│  20    │ 1 byte │atomic<bool>│  valid   │
│ 21-23  │ 3 bytes│  padding   │ alignment│
└─────────────────────────────────────────┘
```

#### Access Patterns
```cpp
// C++ Producer (Write)
data->price.store(new_price, std::memory_order_release);
data->timestamp.store(timestamp, std::memory_order_release);  
data->volume.store(volume, std::memory_order_release);
data->valid.store(true, std::memory_order_release);

// Python Consumer (Read)
struct.unpack('dQi?3x', raw_bytes)
```

#### Synchronization Model
```
┌─────────────────────────────────────────┐
│          Lock-Free Protocol             │
├─────────────────────────────────────────┤
│                                         │
│  C++ Writer           Python Reader     │
│      ↓                     ↑            │
│  1. Write price           1. Check valid │
│  2. Write timestamp       2. Read data   │
│  3. Write volume          3. Process     │
│  4. Set valid=true        4. Repeat      │
│      ↓                     ↑            │
│  Memory barriers ensure ordering        │
│                                         │
│  No locks, no waiting, minimal latency │
└─────────────────────────────────────────┘
```

## Process Lifecycle

### Startup Sequence
```
1. C++ Main Process
   ├── Install signal handlers
   ├── Clean previous shared memory
   ├── Create new shared memory segment
   ├── Initialize TradingData structure
   ├── Fork Python process
   │   └── exec Python data_bridge.py
   ├── Wait for Python connection
   └── Start market data loop

2. Python Bridge Process  
   ├── Import required modules
   ├── Connect to shared memory
   ├── Initialize data structures
   ├── Start monitoring loop
   └── Begin strategy execution
```

### Shutdown Sequence
```
1. Signal Reception (SIGINT/SIGTERM)
   └── C++ Main Process
       ├── Set running=false
       ├── Stop market data loop
       ├── Send SIGTERM to Python
       ├── Wait for Python exit
       ├── Close shared memory
       └── Cleanup resources

2. Python Process
   ├── Receive SIGTERM
   ├── Stop monitoring loops
   ├── Close shared memory connection
   ├── Save any persistent data
   └── Exit gracefully
```

### Error Handling
```
┌─────────────────────────────────────────┐
│            Error Recovery               │
├─────────────────────────────────────────┤
│                                         │
│  C++ Errors:                           │
│  - Shared memory creation failure      │
│  - Python process launch failure       │
│  - Market data API errors             │
│                                         │
│  Recovery Actions:                      │
│  - Retry with exponential backoff      │
│  - Continue with simulation mode       │
│  - Log errors for debugging           │
│                                         │
│  Python Errors:                        │
│  - Shared memory connection failure    │
│  - Data parsing errors                │
│  - Strategy execution exceptions       │
│                                         │
│  Recovery Actions:                      │
│  - Reconnection attempts               │
│  - Graceful degradation                │
│  - Error notification to C++          │
└─────────────────────────────────────────┘
```

## Performance Architecture

### Latency Optimization

#### Memory Access Patterns
```
┌─────────────────────────────────────────┐
│         Latency Breakdown               │
├─────────────────────────────────────────┤
│                                         │
│  Operation                 │ Latency    │
│  ──────────────────────────┼───────────  │
│  Shared memory read        │ < 100ns    │
│  Shared memory write       │ < 100ns    │
│  Python struct unpack     │ < 1μs      │
│  Strategy calculation      │ < 10μs     │
│  Total round-trip          │ < 20μs     │
│                                         │
│  Optimizations:                        │
│  - Lock-free atomic ops               │
│  - Memory-mapped I/O                  │
│  - Cache-friendly data layout         │
│  - Minimal memory allocations         │
└─────────────────────────────────────────┘
```

#### CPU and Memory Layout
```
┌─────────────────────────────────────────┐
│           CPU Architecture              │
├─────────────────────────────────────────┤
│                                         │
│  Core 0          Core 1                │
│  ┌─────────┐    ┌─────────┐            │
│  │ C++ App │    │Python   │            │
│  │Producer │    │Consumer │            │
│  └─────────┘    └─────────┘            │
│       │              │                 │
│       └──────┬───────┘                 │
│              │                         │
│         ┌─────────┐                    │
│         │ Shared  │                    │
│         │ Memory  │                    │
│         │24 bytes │                    │
│         └─────────┘                    │
│                                         │
│  Cache Lines: 64 bytes                 │
│  TradingData: 24 bytes (fits in 1)     │
│  Alignment: 8-byte boundaries          │
└─────────────────────────────────────────┘
```

### Scalability Architecture

#### Multi-Symbol Support
```
┌─────────────────────────────────────────┐
│        Multi-Symbol Design             │
├─────────────────────────────────────────┤
│                                         │
│  Current: Single Symbol                │
│  /dev/shm/trading_data (24 bytes)      │
│                                         │
│  Future: Multiple Symbols              │
│  /dev/shm/trading_data_AAPL            │
│  /dev/shm/trading_data_TSLA            │
│  /dev/shm/trading_data_MSFT            │
│                                         │
│  Or Ring Buffer Design:                │
│  /dev/shm/trading_ring (4KB)           │
│  ┌─────────────────────────────────────┐ │
│  │Header│Symbol1│Symbol2│...│SymbolN │ │
│  │(64b) │(24b)  │(24b)  │   │(24b)   │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

#### Strategy Isolation
```
┌─────────────────────────────────────────┐
│         Strategy Architecture           │
├─────────────────────────────────────────┤
│                                         │
│  Python Process                        │
│  ┌─────────────────────────────────────┐ │
│  │         Main Thread                 │ │
│  │  ┌─────────────────────────────────┐│ │
│  │  │      Data Bridge                ││ │
│  │  │   (Shared Memory I/O)           ││ │
│  │  └─────────────────────────────────┘│ │
│  │                                     │ │
│  │  ┌─────────────────────────────────┐│ │
│  │  │     Strategy Thread 1          ││ │
│  │  │   (Moving Average)              ││ │
│  │  └─────────────────────────────────┘│ │
│  │                                     │ │
│  │  ┌─────────────────────────────────┐│ │
│  │  │     Strategy Thread 2          ││ │
│  │  │   (RSI Strategy)                ││ │
│  │  └─────────────────────────────────┘│ │
│  │                                     │ │
│  │  ┌─────────────────────────────────┐│ │
│  │  │     Portfolio Manager          ││ │
│  │  │   (Risk Management)             ││ │
│  │  └─────────────────────────────────┘│ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Data Architecture

### Storage Layer
```
┌─────────────────────────────────────────┐
│           Data Storage                  │
├─────────────────────────────────────────┤
│                                         │
│  File System Layout:                   │
│  market_data/                          │
│  ├── stocks/                           │
│  │   ├── AAPL.csv                      │
│  │   ├── TSLA.csv                      │
│  │   └── MSFT.csv                      │
│  ├── forex/                            │
│  │   ├── EURUSD.csv                    │
│  │   └── GBPUSD.csv                    │
│  └── crypto/                           │
│      ├── BTC.csv                       │
│      └── ETH.csv                       │
│                                         │
│  CSV Format:                           │
│  timestamp,symbol,price,volume,open... │
│  1643723400,AAPL,150.25,1000000,...    │
│                                         │
│  Access Patterns:                      │
│  - Sequential reads for backtesting    │
│  - Append-only writes for new data     │
│  - Memory-mapped for large files       │
└─────────────────────────────────────────┘
```

### Memory Hierarchy
```
┌─────────────────────────────────────────┐
│         Memory Hierarchy                │
├─────────────────────────────────────────┤
│                                         │
│  L1 Cache (32KB)                       │
│  ┌─────────────────────────────────────┐ │
│  │     TradingData (24 bytes)          │ │
│  │     Frequently accessed             │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  L2 Cache (256KB)                      │
│  ┌─────────────────────────────────────┐ │
│  │     Strategy variables              │ │
│  │     Recent price history            │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  RAM (Multiple GB)                     │
│  ┌─────────────────────────────────────┐ │
│  │     Historical datasets             │ │
│  │     Strategy state                  │ │
│  │     Application code                │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  Disk Storage                          │
│  ┌─────────────────────────────────────┐ │
│  │     CSV files                       │ │
│  │     Configuration                   │ │
│  │     Logs                            │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

## Security Architecture

### Process Isolation
```
┌─────────────────────────────────────────┐
│        Security Boundaries             │
├─────────────────────────────────────────┤
│                                         │
│  User Space                            │
│  ┌─────────────────────────────────────┐ │
│  │  C++ Process (PID 1001)             │ │
│  │  ├── Memory: Private heap/stack     │ │
│  │  ├── Files: Read-only access        │ │
│  │  └── Network: Market data APIs      │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │  Python Process (PID 1002)          │ │
│  │  ├── Memory: Private heap/stack     │ │
│  │  ├── Files: CSV read/write          │ │
│  │  └── Network: Strategy APIs         │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  Shared Resources                      │
│  ┌─────────────────────────────────────┐ │
│  │  /dev/shm/trading_data              │ │
│  │  ├── Permissions: 0666              │ │
│  │  ├── Size: 24 bytes                 │ │
│  │  └── Access: Both processes         │ │
│  └─────────────────────────────────────┘ │
└─────────────────────────────────────────┘
```

### Data Validation
```
┌─────────────────────────────────────────┐
│         Data Validation                 │
├─────────────────────────────────────────┤
│                                         │
│  Input Validation:                     │
│  ┌─────────────────────────────────────┐ │
│  │  C++ Side:                          │ │
│  │  - Price range validation          │ │
│  │  - Timestamp sanity checks         │ │
│  │  - Volume boundary checks          │ │
│  │  - API response validation         │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  ┌─────────────────────────────────────┐ │
│  │  Python Side:                       │ │
│  │  - Shared memory data validation   │ │
│  │  - CSV format verification         │ │
│  │  - Strategy parameter bounds       │ │
│  │  - Portfolio constraint checks     │ │
│  └─────────────────────────────────────┘ │
│                                         │
│  Security Measures:                    │
│  - No external code execution         │
│  - Bounded memory access              │
│  - Input sanitization                 │
│  - Audit logging                      │
└─────────────────────────────────────────┘
```

This architecture provides a robust, scalable foundation for high-frequency trading while maintaining clear separation of concerns and optimizing for performance at every level.