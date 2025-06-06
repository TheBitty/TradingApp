# API Reference

## C++ API

### SharedMemory Class

#### Constructor
```cpp
SharedMemory<T>(const char* filename, bool create = false)
```
- **filename**: Name of shared memory object (e.g., "/trading_data")
- **create**: Whether to create new memory block (true) or attach to existing (false)

#### Methods

##### get()
```cpp
T* get()
```
Returns pointer to shared memory data structure.

##### Example Usage
```cpp
SharedMemory<TradingData> shm("/trading_data", true);
auto data = shm.get();
data->price.store(150.25);
```

### TradingData Structure

```cpp
struct TradingData {
    std::atomic<double> price{0.0};      // Current market price
    std::atomic<uint64_t> timestamp{0};  // Unix timestamp in seconds
    std::atomic<int32_t> volume{0};      // Trading volume
    std::atomic<bool> valid{false};      // Data validity flag
};
```

#### Thread Safety
All fields use atomic operations for lock-free access across processes.

#### Memory Layout
- Total size: 24 bytes (aligned)
- All operations are atomic and wait-free

### Utility Functions

#### create_memory_block()
```cpp
char* create_memory_block(const char* filename, int size)
```
Creates new shared memory block.

#### attach_memory_block()
```cpp
char* attach_memory_block(const char* filename, int size)
```
Attaches to existing shared memory block.

#### destroy_memory_block()
```cpp
bool destroy_memory_block(const char* filename)
```
Destroys shared memory block.

## Python API

### TradingDataBridge Class

#### Constructor
```python
TradingDataBridge(shm_name="/trading_data")
```
- **shm_name**: Name of shared memory object to connect to

#### Methods

##### connect()
```python
def connect() -> bool
```
Connects to C++ shared memory. Returns True on success.

```python
bridge = TradingDataBridge()
if bridge.connect():
    print("Connected to shared memory")
```

##### read_data()
```python
def read_data() -> Optional[Dict[str, Any]]
```
Reads current trading data from shared memory.

**Returns:**
```python
{
    'price': float,           # Current price
    'timestamp': int,         # Unix timestamp
    'volume': int,            # Trading volume
    'valid': bool,            # Data validity
    'datetime': datetime,     # Converted datetime object
    'formatted_time': str     # Human-readable time
}
```

**Example:**
```python
data = bridge.read_data()
if data and data['valid']:
    print(f"AAPL: ${data['price']:.2f} at {data['formatted_time']}")
```

##### write_data()
```python
def write_data(price: float, volume: int, timestamp: int = None, valid: bool = True) -> bool
```
Writes trading data to shared memory.

**Parameters:**
- **price**: Market price to write
- **volume**: Trading volume
- **timestamp**: Unix timestamp (current time if None)
- **valid**: Data validity flag

**Example:**
```python
success = bridge.write_data(
    price=150.25,
    volume=1000000,
    valid=True
)
```

##### close()
```python
def close()
```
Closes shared memory connection and cleans up resources.

### DataManager Class

#### Constructor
```python
DataManager(data_dir="./market_data")
```
- **data_dir**: Directory containing market data CSV files

#### Methods

##### get_available_symbols()
```python
def get_available_symbols() -> Dict[str, List[str]]
```
Returns dictionary of available symbols organized by asset type.

**Returns:**
```python
{
    'stocks': ['AAPL', 'TSLA', 'MSFT'],
    'forex': ['EURUSD', 'GBPUSD'],
    'crypto': ['BTC', 'ETH']
}
```

##### load_symbol_data()
```python
def load_symbol_data(symbol: str, asset_type: str = None) -> Optional[pd.DataFrame]
```
Loads CSV data for specific symbol.

**Parameters:**
- **symbol**: Symbol to load (e.g., "AAPL")
- **asset_type**: Asset type ("stocks", "forex", "crypto") or None to search all

**Returns:** Pandas DataFrame with price/volume/timestamp data

##### get_latest_price()
```python
def get_latest_price(symbol: str) -> Optional[float]
```
Returns most recent price for symbol from local data.

##### update_shared_memory()
```python
def update_shared_memory(symbol: str) -> bool
```
Updates shared memory with latest data for symbol.

##### save_new_data()
```python
def save_new_data(symbol: str, data: List[Dict], asset_type: str = 'stocks')
```
Saves new market data to CSV files.

**Parameters:**
- **symbol**: Symbol to save
- **data**: List of dictionaries with price/volume/timestamp
- **asset_type**: Directory to save in

### TradingSystem Class

#### Constructor
```python
TradingSystem(data_dir="./market_data")
```
High-level interface combining all trading system components.

#### Methods

##### start_monitoring()
```python
def start_monitoring(symbols: List[str], interval: int = 60)
```
Starts background monitoring of symbols with automatic shared memory updates.

**Parameters:**
- **symbols**: List of symbols to monitor
- **interval**: Update interval in seconds

##### stop_monitoring()
```python
def stop_monitoring()
```
Stops background monitoring.

##### fetch_and_store()
```python
def fetch_and_store(symbol: str, days: int = 30, asset_type: str = 'stocks') -> bool
```
Fetches fresh data from external APIs and stores locally.

##### get_portfolio_summary()
```python
def get_portfolio_summary() -> Dict[str, Any]
```
Returns comprehensive summary of all available data and current system state.

**Returns:**
```python
{
    'total_symbols': int,
    'by_asset_type': {'stocks': int, 'forex': int, 'crypto': int},
    'symbols': {asset_type: [symbol_list]},
    'shared_memory': {current_shared_memory_data}
}
```

##### send_signal_to_cpp()
```python
def send_signal_to_cpp(signal_type: str, data: Dict[str, Any])
```
Sends trading signals back to C++ system via shared memory.

**Signal Types:**
- **"price_update"**: Update shared memory with new price data

## Data Formats

### CSV File Format
Market data CSV files should have the following columns:
```csv
timestamp,symbol,price,volume,open,high,low,close,source
1643723400,AAPL,150.25,1000000,149.50,151.00,149.00,150.25,YFinance
```

**Required Columns:**
- **timestamp**: Unix timestamp (seconds)
- **price**: Current/close price
- **volume**: Trading volume

**Optional Columns:**
- **open**, **high**, **low**, **close**: OHLC data
- **source**: Data provider name
- **symbol**: Asset symbol

### Shared Memory Data Structure
```python
# Python struct format for shared memory
STRUCT_FORMAT = 'dQi?3x'  # 24 bytes total

# Breakdown:
# d  = double (8 bytes) - price
# Q  = uint64 (8 bytes) - timestamp  
# i  = int32 (4 bytes)  - volume
# ?  = bool (1 byte)    - valid
# 3x = padding (3 bytes) - alignment
```

## Error Handling

### C++ Exceptions
```cpp
try {
    SharedMemory<TradingData> shm("/trading_data", true);
    // ... operations
} catch (const std::exception& e) {
    std::cerr << "Error: " << e.what() << std::endl;
}
```

### Python Exception Handling
```python
try:
    bridge = TradingDataBridge()
    if not bridge.connect():
        raise ConnectionError("Failed to connect to shared memory")
        
    data = bridge.read_data()
    if not data:
        raise ValueError("No data available")
        
except Exception as e:
    print(f"Error: {e}")
finally:
    bridge.close()
```

### Common Error Codes

#### Shared Memory Errors
- **ENOENT**: Shared memory object doesn't exist
- **EACCES**: Permission denied
- **EEXIST**: Memory object already exists (when creating)

#### Resolution
```bash
# Check if shared memory exists
ls -la /dev/shm/trading_data

# Clean up orphaned shared memory
rm -f /dev/shm/trading_data

# Fix permissions
sudo chmod 666 /dev/shm/trading_data
```

## Performance Guidelines

### Best Practices

#### C++ Side
```cpp
// Use atomic operations for all shared data
data->price.store(new_price, std::memory_order_release);
auto current_price = data->price.load(std::memory_order_acquire);

// Minimize shared memory writes
if (new_price != last_price) {
    data->price.store(new_price);
    last_price = new_price;
}
```

#### Python Side
```python
# Cache bridge connection
class TradingStrategy:
    def __init__(self):
        self.bridge = TradingDataBridge()
        self.bridge.connect()
    
    def get_current_price(self):
        # Reuse connection for best performance
        return self.bridge.read_data()
```

### Memory Access Patterns
- **Read frequency**: Up to 1000 Hz without performance impact
- **Write frequency**: Limited by data source frequency
- **Latency**: < 100 nanoseconds for local shared memory access

### Optimization Tips
1. **Batch operations**: Group multiple writes when possible
2. **Cache validation**: Check `valid` flag before processing data
3. **Memory barriers**: Use appropriate memory ordering
4. **Process affinity**: Pin processes to specific CPU cores for consistent latency

## Integration Examples

### Strategy Implementation
```python
class MovingAverageStrategy:
    def __init__(self, window=20):
        self.trading_system = TradingSystem()
        self.window = window
        self.prices = []
    
    def on_price_update(self):
        data = self.trading_system.data_manager.get_shared_memory_data()
        if data and data['valid']:
            self.prices.append(data['price'])
            
            if len(self.prices) > self.window:
                self.prices.pop(0)
                
            if len(self.prices) == self.window:
                ma = sum(self.prices) / self.window
                current_price = self.prices[-1]
                
                if current_price > ma * 1.02:  # 2% above MA
                    self.send_buy_signal(current_price)
    
    def send_buy_signal(self, price):
        self.trading_system.send_signal_to_cpp("BUY", {
            "price": price,
            "quantity": 100,
            "timestamp": int(time.time())
        })
```

### Real-time Monitoring
```python
import time
from data_bridge import TradingSystem

def monitor_prices():
    system = TradingSystem()
    
    while True:
        data = system.data_manager.get_shared_memory_data()
        if data and data['valid']:
            print(f"Price: ${data['price']:.2f}, "
                  f"Volume: {data['volume']:,}, "
                  f"Time: {data['formatted_time']}")
        
        time.sleep(0.1)  # 10 Hz monitoring

if __name__ == "__main__":
    monitor_prices()
```