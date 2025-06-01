#!/usr/bin/env python3
"""
Python consumer for the trading system shared memory.
Reads market data produced by the C++ backend.
"""

import struct
import time
import mmap
import os
from typing import Optional, NamedTuple

class MarketData(NamedTuple):
    """Market data structure matching the C++ SimpleMarketData struct"""
    price: float
    volume: float
    timestamp: int
    symbol: str
    data_ready: bool

class SharedMemoryConsumer:
    """Consumer for reading market data from shared memory"""

    # Struct format: double, double, long, 16 chars, bool + padding
    # 'd' = double (8 bytes), 'q' = long long (8 bytes),
    # '16s' = 16 character string, 'B' = unsigned char (bool)
    # '7x' = 7 bytes padding to align to 8-byte boundary
    STRUCT_FORMAT = 'ddq16sB7x'  # Total: 48 bytes
    STRUCT_SIZE = struct.calcsize(STRUCT_FORMAT)

    def __init__(self, shm_name: str = "/trading_data"):
        self.shm_name = shm_name
        self.shm_fd: Optional[int] = None
        self.memory_map: Optional[mmap.mmap] = None

    def connect(self) -> bool:
        """Connect to the shared memory object created by C++"""
        try:
            # Open the shared memory object (read-only)
            self.shm_fd = os.open(f"/dev/shm{self.shm_name}", os.O_RDONLY)

            # Create memory map
            self.memory_map = mmap.mmap(
                self.shm_fd,
                self.STRUCT_SIZE,
                mmap.MAP_SHARED,
                mmap.PROT_READ
            )

            print(f"Connected to shared memory: {self.shm_name}")
            return True

        except (OSError, FileNotFoundError) as e:
            print(f"Failed to connect to shared memory: {e}")
            print("Make sure the C++ producer is running first!")
            return False

    def read_market_data(self) -> Optional[MarketData]:
        """Read current market data from shared memory"""
        if not self.memory_map:
            return None

        try:
            # Read raw bytes from shared memory
            self.memory_map.seek(0)
            raw_data = self.memory_map.read(self.STRUCT_SIZE)

            # Unpack the binary data
            unpacked = struct.unpack(self.STRUCT_FORMAT, raw_data)

            # Extract and clean up the symbol string
            symbol = unpacked[3].decode('utf-8').rstrip('\x00')

            return MarketData(
                price=unpacked[0],
                volume=unpacked[1],
                timestamp=unpacked[2],
                symbol=symbol,
                data_ready=bool(unpacked[4])
            )

        except Exception as e:
            print(f"Error reading market data: {e}")
            return None

    def monitor_data(self, duration: float = 30.0):
        """Monitor shared memory for new data"""
        start_time = time.time()
        last_timestamp = 0

        print("Monitoring market data...")
        print("Price    | Volume   | Symbol | Timestamp      | Ready")
        print("-" * 55)

        while time.time() - start_time < duration:
            data = self.read_market_data()

            if data and data.timestamp > last_timestamp:
                print(f"{data.price:8.2f} | {data.volume:8.0f} | {data.symbol:6s} | "
                      f"{data.timestamp:13d} | {data.data_ready}")
                last_timestamp = data.timestamp

            time.sleep(0.1)  # Check 10 times per second

    def disconnect(self):
        """Clean up resources"""
        if self.memory_map:
            self.memory_map.close()
            self.memory_map = None

        if self.shm_fd:
            os.close(self.shm_fd)
            self.shm_fd = None

        print("Disconnected from shared memory")

def main():
    consumer = SharedMemoryConsumer()

    try:
        if consumer.connect():
            consumer.monitor_data(30.0)  # Monitor for 30 seconds
        else:
            print("\nTroubleshooting:")
            print("1. Make sure the C++ producer is running")
            print("2. Check if /dev/shm/trading_data exists")
            print("3. Verify file permissions")

    except KeyboardInterrupt:
        print("\nShutdown requested by user")
    finally:
        consumer.disconnect()

if __name__ == "__main__":
    main()