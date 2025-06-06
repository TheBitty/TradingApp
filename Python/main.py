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

class TradingData(NamedTuple):
    """Trading data structure matching the C++ TradingData struct"""
    price: float
    timestamp: int
    volume: int
    valid: bool

class SharedMemoryConsumer:
    """Consumer for reading trading data from shared memory"""

    # Struct format matching C++ TradingData:
    # atomic<double> price (8 bytes), atomic<uint64_t> timestamp (8 bytes),
    # atomic<int32_t> volume (4 bytes), atomic<bool> valid (1 byte) + padding
    STRUCT_FORMAT = 'dQiB3x'  # Total: 24 bytes
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

    def read_trading_data(self) -> Optional[TradingData]:
        """Read current trading data from shared memory"""
        if not self.memory_map:
            return None

        try:
            # Read raw bytes from shared memory
            self.memory_map.seek(0)
            raw_data = self.memory_map.read(self.STRUCT_SIZE)

            # Unpack the binary data
            unpacked = struct.unpack(self.STRUCT_FORMAT, raw_data)

            return TradingData(
                price=unpacked[0],
                timestamp=unpacked[1],
                volume=unpacked[2],
                valid=bool(unpacked[3])
            )

        except Exception as e:
            print(f"Error reading trading data: {e}")
            return None

    def monitor_data(self, duration: float = 30.0):
        """Monitor shared memory for new data"""
        start_time = time.time()
        last_timestamp = 0

        print("Monitoring trading data...")
        print("Price    | Volume   | Timestamp      | Valid")
        print("-" * 45)

        while time.time() - start_time < duration:
            data = self.read_trading_data()

            if data and data.timestamp > last_timestamp:
                print(f"{data.price:8.2f} | {data.volume:8d} | "
                      f"{data.timestamp:13d} | {data.valid}")
                last_timestamp = data.timestamp

            time.sleep(0.001)  # Check 1000 times per second for low latency

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