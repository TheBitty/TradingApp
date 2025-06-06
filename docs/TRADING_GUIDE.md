# Trading System Guide

## How to Trade with the System

### Overview
This guide explains how to use the trading system for actual trading operations, from basic monitoring to implementing sophisticated trading strategies.

## Getting Started

### 1. Launch the Trading System
```bash
cd C++/src
./trading_app
```

This will:
- Clean up any previous shared memory
- Start market data feeds
- Launch Python bridge automatically
- Begin streaming real-time data

### 2. Monitor Real-Time Data
```bash
# In another terminal
cd Python
python3 main.py
```

You should see current price data being displayed from shared memory.

### 3. Launch Data Viewer (Optional)
```bash
python3 data_viewer.py
```

Provides GUI interface for data visualization and analysis.

## Trading Operations

### Basic Data Access

#### Get Current Market Data
```python
from data_bridge import TradingSystem

system = TradingSystem()
data = system.data_manager.get_shared_memory_data()

if data and data['valid']:
    current_price = data['price']
    volume = data['volume']
    timestamp = data['timestamp']
    print(f"Current AAPL price: ${current_price:.2f}")
```

#### Get Historical Data
```python
# Load historical data for analysis
df = system.data_manager.load_symbol_data("AAPL")

if df is not None:
    print(f"Historical data: {len(df)} records")
    print(f"Price range: ${df['price'].min():.2f} - ${df['price'].max():.2f}")
    print(f"Average volume: {df['volume'].mean():,.0f}")
```

### Strategy Implementation

#### Simple Buy/Sell Strategy
```python
class SimpleStrategy:
    def __init__(self, symbol="AAPL"):
        self.system = TradingSystem()
        self.symbol = symbol
        self.position = 0  # Current position size
        self.entry_price = 0
        
    def check_signals(self):
        """Check for buy/sell signals"""
        data = self.system.data_manager.get_shared_memory_data()
        
        if not data or not data['valid']:
            return
            
        current_price = data['price']
        
        # Simple momentum strategy
        if self.position == 0:  # No position
            # Buy if price moves up
            if self.should_buy(current_price):
                self.buy(current_price, 100)
                
        elif self.position > 0:  # Long position
            # Sell if profit target hit or stop loss
            if self.should_sell(current_price):
                self.sell(current_price, self.position)
    
    def should_buy(self, price):
        """Buy logic - implement your criteria"""
        # Example: Buy if price is above recent average
        df = self.system.data_manager.load_symbol_data(self.symbol)
        if df is not None and len(df) > 20:
            recent_avg = df['price'].tail(20).mean()
            return price > recent_avg * 1.01  # 1% above average
        return False
    
    def should_sell(self, price):
        """Sell logic - implement your criteria"""
        if self.position <= 0:
            return False
            
        # Profit target: 2% gain
        if price >= self.entry_price * 1.02:
            return True
            
        # Stop loss: 1% loss
        if price <= self.entry_price * 0.99:
            return True
            
        return False
    
    def buy(self, price, quantity):
        """Execute buy order"""
        print(f"BUY {quantity} shares at ${price:.2f}")
        self.position += quantity
        self.entry_price = price
        
        # Send signal to C++ system
        self.system.send_signal_to_cpp("BUY", {
            "symbol": self.symbol,
            "price": price,
            "quantity": quantity,
            "timestamp": int(time.time())
        })
    
    def sell(self, price, quantity):
        """Execute sell order"""
        pnl = (price - self.entry_price) * quantity
        print(f"SELL {quantity} shares at ${price:.2f}, P&L: ${pnl:.2f}")
        self.position -= quantity
        
        # Send signal to C++ system
        self.system.send_signal_to_cpp("SELL", {
            "symbol": self.symbol,
            "price": price,
            "quantity": quantity,
            "timestamp": int(time.time())
        })

# Usage
strategy = SimpleStrategy("AAPL")

# Run strategy
import time
while True:
    strategy.check_signals()
    time.sleep(1)  # Check every second
```

#### Moving Average Crossover Strategy
```python
import pandas as pd

class MovingAverageCrossover:
    def __init__(self, symbol="AAPL", short_window=5, long_window=20):
        self.system = TradingSystem()
        self.symbol = symbol
        self.short_window = short_window
        self.long_window = long_window
        self.position = 0
        
    def calculate_signals(self):
        """Calculate moving average crossover signals"""
        df = self.system.data_manager.load_symbol_data(self.symbol)
        
        if df is None or len(df) < self.long_window:
            return None
            
        # Calculate moving averages
        df['MA_short'] = df['price'].rolling(window=self.short_window).mean()
        df['MA_long'] = df['price'].rolling(window=self.long_window).mean()
        
        # Generate signals
        df['signal'] = 0
        df['signal'][self.short_window:] = np.where(
            df['MA_short'][self.short_window:] > df['MA_long'][self.short_window:], 1, 0
        )
        
        # Signal changes
        df['positions'] = df['signal'].diff()
        
        return df
    
    def execute_strategy(self):
        """Execute the moving average crossover strategy"""
        df = self.calculate_signals()
        
        if df is None:
            return
            
        # Get latest signal
        latest_signal = df['positions'].iloc[-1]
        current_price = df['price'].iloc[-1]
        
        if latest_signal == 1 and self.position == 0:  # Buy signal
            self.buy(current_price, 100)
        elif latest_signal == -1 and self.position > 0:  # Sell signal
            self.sell(current_price, self.position)
    
    def buy(self, price, quantity):
        print(f"MA Crossover BUY: {quantity} shares at ${price:.2f}")
        self.position += quantity
        
    def sell(self, price, quantity):
        print(f"MA Crossover SELL: {quantity} shares at ${price:.2f}")
        self.position -= quantity
```

### Market Data Management

#### Adding New Symbols
1. **Create CSV file** in appropriate directory:
   ```bash
   # For stocks
   touch C++/src/market_data/stocks/NVDA.csv
   
   # For crypto
   touch C++/src/market_data/crypto/ETH.csv
   ```

2. **CSV Format**:
   ```csv
   timestamp,symbol,price,volume,open,high,low,close,source
   1643723400,NVDA,280.50,2000000,279.00,281.00,278.50,280.50,Manual
   ```

3. **Update Strategy**:
   ```python
   # Add to monitoring list
   system.start_monitoring(["AAPL", "TSLA", "NVDA"], interval=30)
   ```

#### Fetch Fresh Market Data
```python
# Fetch from external APIs
success = system.fetch_and_store("AAPL", days=7, asset_type="stocks")
if success:
    print("Fresh data downloaded and stored")

# For crypto
success = system.fetch_and_store("BTC", days=7, asset_type="crypto")
```

### Risk Management

#### Position Sizing
```python
class RiskManager:
    def __init__(self, max_position_size=1000, max_risk_per_trade=0.02):
        self.max_position_size = max_position_size
        self.max_risk_per_trade = max_risk_per_trade  # 2% max risk
        
    def calculate_position_size(self, entry_price, stop_loss_price, account_value):
        """Calculate position size based on risk management"""
        risk_per_share = abs(entry_price - stop_loss_price)
        max_risk_amount = account_value * self.max_risk_per_trade
        
        if risk_per_share == 0:
            return 0
            
        position_size = int(max_risk_amount / risk_per_share)
        return min(position_size, self.max_position_size)

# Usage
risk_manager = RiskManager()
position_size = risk_manager.calculate_position_size(
    entry_price=150.00,
    stop_loss_price=147.00,  # 2% stop loss
    account_value=100000     # $100k account
)
print(f"Suggested position size: {position_size} shares")
```

#### Portfolio Tracking
```python
class Portfolio:
    def __init__(self):
        self.positions = {}  # symbol: quantity
        self.trades = []     # Trade history
        
    def add_trade(self, symbol, quantity, price, side):
        """Record a trade"""
        trade = {
            'timestamp': time.time(),
            'symbol': symbol,
            'quantity': quantity,
            'price': price,
            'side': side,  # 'BUY' or 'SELL'
            'value': quantity * price
        }
        self.trades.append(trade)
        
        # Update position
        if side == 'BUY':
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity
        else:  # SELL
            self.positions[symbol] = self.positions.get(symbol, 0) - quantity
    
    def get_portfolio_value(self, trading_system):
        """Calculate current portfolio value"""
        total_value = 0
        
        for symbol, quantity in self.positions.items():
            if quantity == 0:
                continue
                
            # Get current price from shared memory or historical data
            data = trading_system.data_manager.get_shared_memory_data()
            if data and data['valid']:
                current_price = data['price']
            else:
                # Fallback to historical data
                df = trading_system.data_manager.load_symbol_data(symbol)
                if df is not None and not df.empty:
                    current_price = df['price'].iloc[-1]
                else:
                    continue
                    
            total_value += quantity * current_price
            
        return total_value
    
    def get_pnl(self):
        """Calculate profit and loss"""
        total_pnl = 0
        
        # Group trades by symbol for P&L calculation
        symbol_trades = {}
        for trade in self.trades:
            symbol = trade['symbol']
            if symbol not in symbol_trades:
                symbol_trades[symbol] = []
            symbol_trades[symbol].append(trade)
        
        # Calculate P&L for each symbol
        for symbol, trades in symbol_trades.items():
            position = 0
            total_cost = 0
            realized_pnl = 0
            
            for trade in trades:
                if trade['side'] == 'BUY':
                    position += trade['quantity']
                    total_cost += trade['value']
                else:  # SELL
                    if position > 0:
                        avg_cost = total_cost / position
                        sell_quantity = min(trade['quantity'], position)
                        realized_pnl += sell_quantity * (trade['price'] - avg_cost)
                        position -= sell_quantity
                        total_cost -= sell_quantity * avg_cost
            
            total_pnl += realized_pnl
            
        return total_pnl
```

### Advanced Trading Features

#### Technical Indicators
```python
def calculate_rsi(prices, window=14):
    """Calculate Relative Strength Index"""
    delta = prices.diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_bollinger_bands(prices, window=20, std_dev=2):
    """Calculate Bollinger Bands"""
    sma = prices.rolling(window=window).mean()
    std = prices.rolling(window=window).std()
    upper_band = sma + (std * std_dev)
    lower_band = sma - (std * std_dev)
    return upper_band, sma, lower_band

# Usage in strategy
df = system.data_manager.load_symbol_data("AAPL")
df['RSI'] = calculate_rsi(df['price'])
df['BB_upper'], df['BB_middle'], df['BB_lower'] = calculate_bollinger_bands(df['price'])

# Generate signals based on indicators
oversold = df['RSI'] < 30
overbought = df['RSI'] > 70
price_below_lower_bb = df['price'] < df['BB_lower']
```

#### Backtesting Framework
```python
class Backtester:
    def __init__(self, strategy, initial_capital=100000):
        self.strategy = strategy
        self.initial_capital = initial_capital
        self.capital = initial_capital
        self.positions = {}
        self.trades = []
        
    def run_backtest(self, symbol, start_date=None, end_date=None):
        """Run backtest on historical data"""
        df = self.strategy.system.data_manager.load_symbol_data(symbol)
        
        if df is None:
            print(f"No data available for {symbol}")
            return
        
        # Filter by date range if specified
        if start_date or end_date:
            df['datetime'] = pd.to_datetime(df['timestamp'], unit='s')
            if start_date:
                df = df[df['datetime'] >= start_date]
            if end_date:
                df = df[df['datetime'] <= end_date]
        
        # Run strategy on each data point
        for index, row in df.iterrows():
            # Simulate real-time data
            signals = self.strategy.generate_signals(row)
            
            for signal in signals:
                self.execute_trade(signal, row['price'], row['timestamp'])
        
        # Calculate final results
        return self.calculate_performance()
    
    def execute_trade(self, signal, price, timestamp):
        """Execute trade during backtest"""
        symbol = signal['symbol']
        side = signal['side']  # 'BUY' or 'SELL'
        quantity = signal['quantity']
        
        if side == 'BUY' and self.capital >= price * quantity:
            self.capital -= price * quantity
            self.positions[symbol] = self.positions.get(symbol, 0) + quantity
            self.trades.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price
            })
            
        elif side == 'SELL' and self.positions.get(symbol, 0) >= quantity:
            self.capital += price * quantity
            self.positions[symbol] -= quantity
            self.trades.append({
                'timestamp': timestamp,
                'symbol': symbol,
                'side': side,
                'quantity': quantity,
                'price': price
            })
    
    def calculate_performance(self):
        """Calculate backtest performance metrics"""
        if not self.trades:
            return {}
        
        total_return = (self.capital - self.initial_capital) / self.initial_capital
        num_trades = len(self.trades)
        
        # Calculate win rate
        winning_trades = 0
        for i in range(0, len(self.trades), 2):  # Pairs of buy/sell
            if i + 1 < len(self.trades):
                buy_trade = self.trades[i]
                sell_trade = self.trades[i + 1]
                if sell_trade['price'] > buy_trade['price']:
                    winning_trades += 1
        
        win_rate = winning_trades / (num_trades / 2) if num_trades > 0 else 0
        
        return {
            'total_return': total_return,
            'final_capital': self.capital,
            'num_trades': num_trades,
            'win_rate': win_rate,
            'trades': self.trades
        }
```

## Integration with External Systems

### Real Brokers (Paper Trading Example)
```python
class PaperTradingBroker:
    """Simulated broker for paper trading"""
    
    def __init__(self, initial_balance=100000):
        self.balance = initial_balance
        self.positions = {}
        self.orders = []
        
    def place_order(self, symbol, side, quantity, order_type="MARKET", price=None):
        """Place a trading order"""
        order_id = len(self.orders) + 1
        
        order = {
            'id': order_id,
            'symbol': symbol,
            'side': side,
            'quantity': quantity,
            'type': order_type,
            'price': price,
            'status': 'PENDING',
            'timestamp': time.time()
        }
        
        self.orders.append(order)
        
        # For market orders, execute immediately
        if order_type == "MARKET":
            self.execute_order(order_id)
            
        return order_id
    
    def execute_order(self, order_id):
        """Execute a pending order"""
        order = next((o for o in self.orders if o['id'] == order_id), None)
        if not order:
            return False
            
        # Get current market price (from shared memory)
        trading_system = TradingSystem()
        data = trading_system.data_manager.get_shared_memory_data()
        
        if not data or not data['valid']:
            return False
            
        execution_price = data['price']
        symbol = order['symbol']
        side = order['side']
        quantity = order['quantity']
        
        if side == 'BUY':
            cost = execution_price * quantity
            if cost <= self.balance:
                self.balance -= cost
                self.positions[symbol] = self.positions.get(symbol, 0) + quantity
                order['status'] = 'FILLED'
                order['execution_price'] = execution_price
                return True
        else:  # SELL
            if self.positions.get(symbol, 0) >= quantity:
                self.balance += execution_price * quantity
                self.positions[symbol] -= quantity
                order['status'] = 'FILLED'
                order['execution_price'] = execution_price
                return True
                
        order['status'] = 'REJECTED'
        return False
    
    def get_account_info(self):
        """Get current account information"""
        return {
            'balance': self.balance,
            'positions': self.positions,
            'orders': self.orders
        }

# Usage with trading strategy
broker = PaperTradingBroker()

class IntegratedStrategy:
    def __init__(self, broker):
        self.broker = broker
        self.system = TradingSystem()
        
    def run(self):
        while True:
            data = self.system.data_manager.get_shared_memory_data()
            
            if data and data['valid']:
                signals = self.generate_signals(data)
                
                for signal in signals:
                    order_id = self.broker.place_order(
                        symbol=signal['symbol'],
                        side=signal['side'],
                        quantity=signal['quantity']
                    )
                    print(f"Placed order {order_id}")
            
            time.sleep(1)

strategy = IntegratedStrategy(broker)
# strategy.run()  # Uncomment to run
```

## Best Practices

### Trading Guidelines
1. **Always test strategies** with paper trading first
2. **Implement proper risk management** (position sizing, stop losses)
3. **Monitor system latency** for high-frequency strategies  
4. **Keep detailed logs** of all trades and system events
5. **Regularly backup** trading data and configurations

### Performance Optimization
1. **Use shared memory efficiently** - minimize unnecessary reads/writes
2. **Cache frequently accessed data** to reduce I/O operations
3. **Implement proper error handling** for network and data issues
4. **Monitor memory usage** to prevent system overload

### Security Considerations
1. **Never store API keys** in source code
2. **Use environment variables** for sensitive configuration
3. **Validate all external data** before processing
4. **Implement proper logging** without exposing sensitive information

This guide provides the foundation for building sophisticated trading strategies on top of the high-performance shared memory system.