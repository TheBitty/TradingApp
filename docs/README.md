# Trading System Documentation

## Overview

This is a high-performance trading application demonstrating ultra-low latency inter-process communication (IPC) between C++ and Python components using POSIX shared memory. The system has been optimized to eliminate duplicate code and provides a streamlined architecture for real-time trading operations.

## Quick Start

### Running the System

1. **Single Command Launch**: The C++ application automatically launches the Python process
   ```bash
   cd C++/src
   ./trading_app
   ```

2. **What Happens**: 
   - Shared memory is automatically cleaned up from previous sessions
   - C++ producer starts generating market data
   - Python consumer is automatically launched and connects
   - Real-time data flows between processes

3. **Shutdown**: Press `Ctrl+C` to cleanly shutdown both processes

## Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   C++ Producer  │◄──►│  Shared Memory   │◄──►│ Python Consumer │
│  (Market Data)  │    │   (/dev/shm)     │    │   (Strategies)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
        │                       │                       │
        ▼                       ▼                       ▼
   Market APIs            TradingData              Trading Logic
   Data Storage           (24 bytes)               Data Processing
```

## Components

### C++ Core (`/C++/src/`)

#### Main Application (`simple_main.cpp`)
- **Purpose**: Main entry point that orchestrates the entire system
- **Features**:
  - Automatic shared memory cleanup on startup
  - Python process management (fork/exec)
  - Signal handling for clean shutdown
  - Real-time market data simulation
  - Process monitoring and restart capabilities

#### Shared Memory System (`include/shared_code.h`)
- **Purpose**: Ultra-low latency IPC using POSIX shared memory
- **Key Features**:
  - Template-based SharedMemory class
  - Atomic operations for thread safety
  - Zero-copy data access
  - Memory cleanup utilities

#### Data Structures (`include/trading_system.h`)
- **TradingData**: Core structure for shared memory
  ```cpp
  struct TradingData {
      std::atomic<double> price{0.0};      // Current price
      std::atomic<uint64_t> timestamp{0};  // Unix timestamp
      std::atomic<int32_t> volume{0};      // Trading volume
      std::atomic<bool> valid{false};      // Data validity flag
  };
  ```

### Python Components (`/Python/`)

#### Consolidated Data Bridge (`data_bridge.py`)
- **TradingDataBridge**: Main interface for shared memory access
- **DataManager**: File-based data storage and retrieval
- **TradingSystem**: High-level trading system interface
- **PythonAPIClient**: Alternative data sources

#### Simple Consumer (`main.py`)
- **Purpose**: Lightweight shared memory reader
- **Usage**: Quick testing and monitoring

#### Data Viewer (`data_viewer.py`)
- **Purpose**: GUI application for data visualization
- **Features**: 
  - Real-time shared memory monitoring
  - CSV data analysis and charting
  - Market data browsing

## Build Instructions

### Prerequisites
```bash
# Required packages
sudo apt-get install build-essential libcurl4-openssl-dev python3 python3-pip

# Python dependencies
pip3 install pandas matplotlib requests
```

### Building
```bash
cd C++/src
g++ -o trading_app simple_main.cpp -lrt -pthread -std=c++17
```

### Testing
```bash
# Test the integrated system
./trading_app

# In another terminal, verify Python connection
cd ../../Python
python3 main.py
```

## Performance Specifications

- **Latency**: < 100 nanoseconds for shared memory access
- **Throughput**: > 1M messages/second
- **Memory**: 24 bytes per market data point
- **Zero-copy**: Direct memory access between processes

## Data Flow

### C++ → Python (Real-time)
1. C++ writes TradingData to shared memory using atomic operations
2. Python reads TradingData directly from shared memory
3. No serialization/deserialization overhead
4. Microsecond-level latency

### Data Persistence
- CSV files stored in `market_data/` directory
- Organized by asset type: `stocks/`, `forex/`, `crypto/`
- Historical data available for backtesting

## API Reference

### C++ SharedMemory API
```cpp
// Create shared memory
SharedMemory<TradingData> shm("/trading_data", true);
auto data = shm.get();

// Write data (atomic)
data->price.store(150.25);
data->timestamp.store(1643723400);
data->valid.store(true);

// Cleanup
destroy_memory_block("/trading_data");
```

### Python TradingDataBridge API
```python
from data_bridge import TradingDataBridge

# Connect to shared memory
bridge = TradingDataBridge()
bridge.connect()

# Read current data
data = bridge.read_data()
print(f"Price: ${data['price']:.2f}")

# Write data
bridge.write_data(price=150.25, volume=1000000)

# Cleanup
bridge.close()
```

### High-Level Python API
```python
from data_bridge import TradingSystem

# Initialize system
system = TradingSystem()

# Get portfolio summary
summary = system.get_portfolio_summary()

# Start monitoring
system.start_monitoring(["AAPL", "TSLA"], interval=30)

# Fetch fresh data
system.fetch_and_store("AAPL", days=7, asset_type="stocks")
```

## Memory Management

### Shared Memory Layout
```
/dev/shm/trading_data (24 bytes):
Offset 0-7:   price (double, atomic)
Offset 8-15:  timestamp (uint64_t, atomic)  
Offset 16-19: volume (int32_t, atomic)
Offset 20:    valid (bool, atomic)
Offset 21-23: padding (alignment)
```

### Cleanup Procedures
```bash
# Manual cleanup
rm -f /dev/shm/trading_data

# Check shared memory usage
ls -la /dev/shm/

# Monitor memory usage
ipcs -m
```

## Trading Operations

### Adding New Symbols
1. **Market Data**: Add CSV files to appropriate `market_data/` subdirectory
2. **Symbol List**: Update symbol lists in Python configuration
3. **Data Sources**: Configure new API providers if needed

### Strategy Implementation
```python
# Implement custom trading strategy
class MyStrategy:
    def __init__(self, trading_system):
        self.system = trading_system
    
    def on_market_data(self, data):
        # Your trading logic here
        if data['price'] > threshold:
            # Send signal to C++
            self.system.send_signal_to_cpp("BUY", {
                "symbol": "AAPL",
                "quantity": 100,
                "price": data['price']
            })
```

### Data Analysis
```python
# Load and analyze historical data
from data_bridge import DataManager

manager = DataManager()
df = manager.load_symbol_data("AAPL")

# Statistical analysis
print(f"Average price: ${df['price'].mean():.2f}")
print(f"Price volatility: {df['price'].std():.2f}")

# Technical indicators
df['sma_20'] = df['price'].rolling(20).mean()
df['volatility'] = df['price'].rolling(20).std()
```

## Configuration

### Environment Variables
```bash
export TRADING_DATA_DIR="/path/to/market_data"
export SHARED_MEMORY_SIZE=24
export UPDATE_INTERVAL=100  # milliseconds
```

### File Locations
- **C++ Executable**: `C++/src/trading_app`
- **Python Bridge**: `Python/data_bridge.py`
- **Market Data**: `C++/src/market_data/`
- **Documentation**: `docs/`

## Troubleshooting

### Common Issues

#### Shared Memory Access Denied
```bash
# Fix permissions
sudo chmod 666 /dev/shm/trading_data
```

#### Python Process Not Starting
- Check Python path in `simple_main.cpp:38`
- Verify Python dependencies are installed
- Check file permissions

#### No Market Data
- Verify CSV files exist in `market_data/` directory
- Check data format (price, volume, timestamp columns required)
- Ensure valid file permissions

### Debug Commands
```bash
# Check shared memory
hexdump -C /dev/shm/trading_data

# Monitor system calls
strace -e trace=mmap,shm_open ./trading_app

# Process monitoring
ps aux | grep trading
```

## Performance Tuning

### Memory Optimization
- Use memory-mapped files for large datasets
- Implement ring buffers for historical data
- Optimize struct packing and alignment

### CPU Optimization
- Pin processes to specific CPU cores
- Use NUMA-aware memory allocation
- Implement lockless data structures

### Network Optimization
- Use kernel bypass networking (DPDK)
- Implement multicast market data feeds
- Optimize TCP settings for low latency

## Security Considerations

- Shared memory permissions (0666 for read/write access)
- Process isolation and sandboxing
- Input validation for all external data
- Secure API key management
- Network security for market data feeds

## Future Enhancements

### Planned Features
- [ ] Ring buffer for multiple data points
- [ ] Order management system integration
- [ ] Real-time performance monitoring
- [ ] WebSocket API for web clients
- [ ] Machine learning strategy framework
- [ ] Risk management system

### Scalability Improvements
- [ ] Multi-symbol shared memory regions
- [ ] Distributed processing with message queues
- [ ] Cloud deployment support
- [ ] Real-time analytics dashboard

## Support

For issues and feature requests, refer to the main README.md in the project root or create an issue in the project repository.