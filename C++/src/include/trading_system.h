#ifndef TRADING_SYSTEM_H
#define TRADING_SYSTEM_H

#include <atomic>
#include <cstdint>

// Essential trading data structure for shared memory communication
struct TradingData {
    std::atomic<double> price{0.0};
    std::atomic<uint64_t> timestamp{0};
    std::atomic<int32_t> volume{0};
    std::atomic<bool> valid{false};
};

#endif // TRADING_SYSTEM_H