#!/usr/bin/env python3
"""
Simple Python consumer using consolidated data_bridge module
"""

from data_bridge import TradingSystem

def main():
    """Simple consumer example"""
    system = TradingSystem()
    
    print("Starting simple monitoring...")
    try:
        data = system.data_manager.get_shared_memory_data()
        if data:
            print(f"Current data: Price=${data['price']:.2f}, Volume={data['volume']}, Valid={data['valid']}")
        else:
            print("No data available in shared memory")
            print("Make sure the C++ producer is running!")
    except KeyboardInterrupt:
        print("\nShutdown requested")

if __name__ == "__main__":
    main()