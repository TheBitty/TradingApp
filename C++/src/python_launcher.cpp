#include <iostream>
#include <chrono>
#include <thread>
#include <signal.h>
#include <atomic>
#include <cstring>

#include "include/shared_code.h"
#include "include/python_launcher.h"

// Simple market data structure matching your existing code
struct SimpleMarketData {
    double price;
    double volume;
    long timestamp;
    char symbol[16];
    volatile bool data_ready;

    SimpleMarketData() : price(0.0), volume(0.0), timestamp(0), data_ready(false) {
        memset(symbol, 0, sizeof(symbol));
    }
};

// Global shutdown flag
std::atomic<bool> running{true};

void signal_handler(int signal) {
    std::cout << "\nReceived signal " << signal << ", shutting down..." << std::endl;
    running = false;
}

class TradingSystem {
private:
    type_shared_memory<SimpleMarketData> shared_data_;
    std::unique_ptr<trading::PythonLauncher> python_launcher_;

public:
    TradingSystem()
        : shared_data_("/trading_data", true)  // Create shared memory
        , python_launcher_(trading::create_trading_python_launcher("main.py"))
    {
        // Set up Python process callbacks
        python_launcher_->set_started_callback([](pid_t pid, int code) {
            std::cout << "✓ Python consumer started successfully (PID: " << pid << ")" << std::endl;
        });

        python_launcher_->set_crashed_callback([](pid_t pid, int code) {
            std::cerr << "✗ Python consumer crashed (PID: " << pid << ", exit code: " << code << ")" << std::endl;
        });

        python_launcher_->set_terminated_callback([](pid_t pid, int code) {
            std::cout << "✓ Python consumer terminated gracefully (PID: " << pid << ")" << std::endl;
        });
    }

    bool initialize() {
        std::cout << "Initializing trading system..." << std::endl;

        // Initialize shared memory with default values
        auto* data = shared_data_.get();
        *data = SimpleMarketData{}; // Zero-initialize

        // Start Python consumer
        if (!python_launcher_->start()) {
            std::cerr << "Failed to start Python consumer" << std::endl;
            return false;
        }

        // Give Python time to connect to shared memory
        std::this_thread::sleep_for(std::chrono::milliseconds(1000));

        std::cout << "Trading system initialized successfully" << std::endl;
        return true;
    }

    void run_market_simulation() {
        std::cout << "Starting market data simulation..." << std::endl;
        std::cout << "Press Ctrl+C to stop" << std::endl;
        std::cout << std::string(60, '-') << std::endl;

        int tick = 0;
        auto simulation_start = std::chrono::steady_clock::now();

        while (running) {
            // Update Python process state
            python_launcher_->update();

            // Check if Python process is still running
            if (!python_launcher_->is_running()) {
                std::cerr << "Python consumer is not running, stopping simulation" << std::endl;
                break;
            }

            // Generate realistic market data
            auto* data = shared_data_.get();

            // Simulate price movement with some volatility
            double base_price = 150.0;
            double volatility = 2.0 * sin(tick * 0.1) + 0.5 * sin(tick * 0.3);
            data->price = base_price + volatility;

            data->volume = 1000.0 + (tick % 50) * 100.0;
            data->timestamp = std::chrono::duration_cast<std::chrono::microseconds>(
                std::chrono::system_clock::now().time_since_epoch()).count();
            strcpy(data->symbol, "AAPL");
            data->data_ready = true;  // Signal to Python that new data is available

            // Log every 5th tick to avoid spam
            if (tick % 5 == 0) {
                auto uptime = python_launcher_->get_uptime();
                auto uptime_sec = std::chrono::duration_cast<std::chrono::seconds>(uptime).count();

                std::cout << "Tick " << std::setw(4) << tick
                          << " | Price: $" << std::fixed << std::setprecision(2) << data->price
                          << " | Volume: " << std::setw(6) << static_cast<int>(data->volume)
                          << " | Python uptime: " << uptime_sec << "s" << std::endl;
            }

            tick++;
            std::this_thread::sleep_for(std::chrono::milliseconds(500));
        }

        auto simulation_end = std::chrono::steady_clock::now();
        auto total_time = std::chrono::duration_cast<std::chrono::seconds>(
            simulation_end - simulation_start).count();

        std::cout << std::string(60, '-') << std::endl;
        std::cout << "Market simulation completed:" << std::endl;
        std::cout << "  Total ticks: " << tick << std::endl;
        std::cout << "  Total time: " << total_time << " seconds" << std::endl;
        std::cout << "  Average rate: " << (tick / std::max(1L, total_time)) << " ticks/second" << std::endl;
    }

    void shutdown() {
        std::cout << "Shutting down trading system..." << std::endl;

        // Clear the data_ready flag to signal Python to stop
        if (auto* data = shared_data_.get()) {
            data->data_ready = false;
        }

        // Give Python a moment to see the shutdown signal
        std::this_thread::sleep_for(std::chrono::milliseconds(500));

        // Stop Python process
        if (python_launcher_) {
            python_launcher_->stop(true);
        }

        std::cout << "Trading system shut down complete" << std::endl;
    }
};

int main(int argc, char** argv) {
    // Set up signal handling for clean shutdown
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);

    std::cout << "=== High-Performance Trading System ===" << std::endl;
    std::cout << "C++ Producer with Python Consumer via Shared Memory" << std::endl;
    std::cout << std::endl;

    try {
        TradingSystem system;

        if (system.initialize()) {
            system.run_market_simulation();
        } else {
            std::cerr << "Failed to initialize trading system" << std::endl;
            return 1;
        }

        system.shutdown();

    } catch (const std::exception& e) {
        std::cerr << "Fatal error: " << e.what() << std::endl;
        return 1;
    }

    std::cout << "Program exited successfully" << std::endl;
    return 0;
}