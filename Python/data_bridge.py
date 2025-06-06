#!/usr/bin/env python3
"""
Data Bridge - Python interface for C++ trading system
Handles shared memory communication and provides API for data access
"""
import mmap
import struct
import os
import json
import pandas as pd
import time
from datetime import datetime
from typing import Dict, List, Optional, Any
import requests
import threading

class TradingDataBridge:
    def __init__(self, shm_name="/trading_data"):
        self.shm_name = shm_name
        self.shm_fd = None
        self.shm_map = None
        self.connected = False
        
    def connect(self) -> bool:
        """Connect to C++ shared memory"""
        try:
            self.shm_fd = os.open(f"/dev/shm{self.shm_name}", os.O_RDWR)
            self.shm_map = mmap.mmap(self.shm_fd, 24, mmap.MAP_SHARED, mmap.PROT_READ | mmap.PROT_WRITE)
            self.connected = True
            print("✓ Connected to C++ shared memory")
            return True
        except Exception as e:
            print(f"Failed to connect to shared memory: {e}")
            return False
    
    def read_data(self) -> Optional[Dict[str, Any]]:
        """Read current trading data from shared memory"""
        if not self.connected:
            return None
        
        try:
            self.shm_map.seek(0)
            data = self.shm_map.read(24)
            price, timestamp, volume, valid = struct.unpack('dQi?3x', data)
            
            return {
                'price': price,
                'timestamp': timestamp,
                'volume': volume,
                'valid': bool(valid),
                'datetime': datetime.fromtimestamp(timestamp) if timestamp > 0 else None,
                'formatted_time': datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S") if timestamp > 0 else "N/A"
            }
        except Exception as e:
            print(f"Error reading shared memory: {e}")
            return None
    
    def write_data(self, price: float, volume: int, timestamp: int = None, valid: bool = True) -> bool:
        """Write trading data to shared memory"""
        if not self.connected:
            return False
        
        try:
            if timestamp is None:
                timestamp = int(time.time())
            
            data = struct.pack('dQi?3x', price, timestamp, volume, valid)
            self.shm_map.seek(0)
            self.shm_map.write(data)
            self.shm_map.flush()
            return True
        except Exception as e:
            print(f"Error writing to shared memory: {e}")
            return False
    
    def close(self):
        """Close shared memory connection"""
        if self.shm_map:
            self.shm_map.close()
        if self.shm_fd:
            os.close(self.shm_fd)
        self.connected = False

class DataManager:
    def __init__(self, data_dir="./market_data"):
        self.data_dir = data_dir
        self.bridge = TradingDataBridge()
        self.bridge.connect()
        
    def get_available_symbols(self) -> Dict[str, List[str]]:
        """Get all available symbols organized by asset type"""
        symbols = {'stocks': [], 'forex': [], 'crypto': []}
        
        for asset_type in symbols.keys():
            asset_dir = os.path.join(self.data_dir, asset_type)
            if os.path.exists(asset_dir):
                for file in os.listdir(asset_dir):
                    if file.endswith('.csv'):
                        symbols[asset_type].append(file[:-4])
        
        return symbols
    
    def load_symbol_data(self, symbol: str, asset_type: str = None) -> Optional[pd.DataFrame]:
        """Load data for a specific symbol"""
        if asset_type:
            file_path = os.path.join(self.data_dir, asset_type, f"{symbol}.csv")
            if os.path.exists(file_path):
                return pd.read_csv(file_path)
        else:
            # Search all asset types
            for atype in ['stocks', 'forex', 'crypto']:
                file_path = os.path.join(self.data_dir, atype, f"{symbol}.csv")
                if os.path.exists(file_path):
                    return pd.read_csv(file_path)
        
        return None
    
    def get_latest_price(self, symbol: str) -> Optional[float]:
        """Get latest price for a symbol from local data"""
        df = self.load_symbol_data(symbol)
        if df is not None and 'price' in df.columns and not df.empty:
            return float(df['price'].iloc[-1])
        return None
    
    def get_price_history(self, symbol: str, limit: int = 100) -> Optional[pd.DataFrame]:
        """Get recent price history for a symbol"""
        df = self.load_symbol_data(symbol)
        if df is not None and not df.empty:
            return df.tail(limit)
        return None
    
    def update_shared_memory(self, symbol: str) -> bool:
        """Update shared memory with latest data for symbol"""
        df = self.load_symbol_data(symbol)
        if df is not None and not df.empty:
            latest = df.iloc[-1]
            return self.bridge.write_data(
                price=float(latest['price']),
                volume=int(latest['volume']),
                timestamp=int(latest['timestamp']),
                valid=True
            )
        return False
    
    def get_shared_memory_data(self) -> Optional[Dict[str, Any]]:
        """Get current data from shared memory"""
        return self.bridge.read_data()
    
    def save_new_data(self, symbol: str, data: List[Dict], asset_type: str = 'stocks'):
        """Save new market data to CSV"""
        if not data:
            return
        
        df = pd.DataFrame(data)
        asset_dir = os.path.join(self.data_dir, asset_type)
        os.makedirs(asset_dir, exist_ok=True)
        
        file_path = os.path.join(asset_dir, f"{symbol}.csv")
        
        # Append to existing file or create new one
        if os.path.exists(file_path):
            df.to_csv(file_path, mode='a', header=False, index=False)
        else:
            df.to_csv(file_path, index=False)
        
        print(f"Saved {len(data)} records for {symbol}")

class PythonAPIClient:
    """Python API client for fetching data (complementing C++ providers)"""
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({'User-Agent': 'TradingApp/1.0'})
    
    def get_yahoo_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Fetch data from Yahoo Finance (Python implementation)"""
        try:
            import yfinance as yf
            ticker = yf.Ticker(symbol)
            hist = ticker.history(period=f"{days}d")
            
            data = []
            for date, row in hist.iterrows():
                data.append({
                    'timestamp': int(date.timestamp()),
                    'symbol': symbol,
                    'open': float(row['Open']),
                    'high': float(row['High']),
                    'low': float(row['Low']),
                    'close': float(row['Close']),
                    'volume': float(row['Volume']),
                    'price': float(row['Close']),
                    'source': 'YFinance-Python'
                })
            
            return data
        except Exception as e:
            print(f"Error fetching Yahoo data: {e}")
            return []
    
    def get_crypto_data(self, symbol: str, days: int = 30) -> List[Dict]:
        """Fetch crypto data from free API"""
        try:
            # Using CoinGecko free API
            crypto_id = symbol.lower().replace('btc', 'bitcoin').replace('eth', 'ethereum')
            url = f"https://api.coingecko.com/api/v3/coins/{crypto_id}/market_chart"
            params = {'vs_currency': 'usd', 'days': days}
            
            response = self.session.get(url, params=params)
            if response.status_code == 200:
                data = response.json()
                prices = data.get('prices', [])
                volumes = data.get('total_volumes', [])
                
                result = []
                for i, (timestamp, price) in enumerate(prices):
                    volume = volumes[i][1] if i < len(volumes) else 0
                    result.append({
                        'timestamp': int(timestamp / 1000),  # Convert to seconds
                        'symbol': symbol,
                        'open': price,  # Simplified - real OHLC would need different API
                        'high': price,
                        'low': price,
                        'close': price,
                        'volume': volume,
                        'price': price,
                        'source': 'CoinGecko-Python'
                    })
                
                return result
        except Exception as e:
            print(f"Error fetching crypto data: {e}")
            return []

class TradingSystem:
    """Main Python trading system interface"""
    
    def __init__(self, data_dir="./market_data"):
        self.data_manager = DataManager(data_dir)
        self.api_client = PythonAPIClient()
        self.monitoring = False
        self.monitor_thread = None
    
    def start_monitoring(self, symbols: List[str], interval: int = 60):
        """Start monitoring symbols and updating shared memory"""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_symbols = symbols
        self.monitor_interval = interval
        
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        print(f"Started monitoring {len(symbols)} symbols")
    
    def stop_monitoring(self):
        """Stop monitoring"""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join()
        print("Stopped monitoring")
    
    def _monitor_loop(self):
        """Main monitoring loop"""
        while self.monitoring:
            for symbol in self.monitor_symbols:
                try:
                    # Update shared memory with latest local data
                    self.data_manager.update_shared_memory(symbol)
                    
                    # Optionally fetch fresh data
                    if symbol.upper() in ['BTC', 'ETH', 'BTCUSD', 'ETHUSD']:
                        fresh_data = self.api_client.get_crypto_data(symbol, 1)
                        if fresh_data:
                            self.data_manager.save_new_data(symbol, fresh_data, 'crypto')
                    
                    time.sleep(1)  # Small delay between symbols
                except Exception as e:
                    print(f"Error monitoring {symbol}: {e}")
            
            time.sleep(self.monitor_interval)
    
    def fetch_and_store(self, symbol: str, days: int = 30, asset_type: str = 'stocks'):
        """Fetch data and store locally"""
        if asset_type == 'crypto':
            data = self.api_client.get_crypto_data(symbol, days)
        else:
            data = self.api_client.get_yahoo_data(symbol, days)
        
        if data:
            self.data_manager.save_new_data(symbol, data, asset_type)
            return True
        return False
    
    def get_portfolio_summary(self) -> Dict[str, Any]:
        """Get summary of all available data"""
        symbols = self.data_manager.get_available_symbols()
        summary = {
            'total_symbols': sum(len(symbols[key]) for key in symbols),
            'by_asset_type': {key: len(value) for key, value in symbols.items()},
            'symbols': symbols,
            'shared_memory': self.data_manager.get_shared_memory_data()
        }
        return summary
    
    def send_signal_to_cpp(self, signal_type: str, data: Dict[str, Any]):
        """Send trading signal back to C++ system"""
        # For now, we'll update shared memory with signal data
        if signal_type == "price_update":
            self.data_manager.bridge.write_data(
                price=data.get('price', 0.0),
                volume=data.get('volume', 0),
                timestamp=data.get('timestamp', int(time.time())),
                valid=True
            )
        print(f"Sent signal to C++: {signal_type}")

# Example usage functions
def main():
    """Example usage of the trading system"""
    system = TradingSystem()
    
    # Get portfolio summary
    summary = system.get_portfolio_summary()
    print("Portfolio Summary:")
    print(json.dumps(summary, indent=2, default=str))
    
    # Fetch some fresh data
    print("\nFetching fresh data...")
    system.fetch_and_store("AAPL", 7, "stocks")
    system.fetch_and_store("BTC", 7, "crypto")
    
    # Start monitoring
    system.start_monitoring(["AAPL", "BTC"], interval=30)
    
    try:
        # Run for a bit
        time.sleep(60)
    except KeyboardInterrupt:
        pass
    finally:
        system.stop_monitoring()

if __name__ == "__main__":
    main()