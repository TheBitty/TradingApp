#!/bin/bash

echo "=== Testing Shared Memory Communication ==="
echo

# Cleanup any existing shared memory
echo "Cleaning up any existing shared memory..."
rm -f /dev/shm/trading_data

# Start C++ producer
echo "Starting C++ producer..."
cd C++/src
./trading_app &
PRODUCER_PID=$!

# Wait a moment for shared memory to be created
sleep 2

# Check if shared memory was created
if [ -f /dev/shm/trading_data ]; then
    echo "✓ Shared memory created successfully"
    ls -la /dev/shm/trading_data
else
    echo "✗ Failed to create shared memory"
    kill $PRODUCER_PID 2>/dev/null
    exit 1
fi

echo
echo "Starting Python consumer for 5 seconds..."
cd ../../Python

# Run Python consumer for 5 seconds
timeout 5s python3 main.py

echo
echo "Stopping C++ producer..."
kill $PRODUCER_PID 2>/dev/null
wait $PRODUCER_PID 2>/dev/null

echo "✓ Test completed"
echo
echo "=== How it works ==="
echo "1. C++ creates POSIX shared memory at /dev/shm/trading_data"
echo "2. C++ writes atomic TradingData structure (24 bytes)"  
echo "3. Python memory-maps same file and reads the structure"
echo "4. Both processes access same physical memory = zero-copy"
echo "5. Atomic operations ensure thread-safety without locks"