#include <iostream>
#include <thread>
#include <chrono>
#include <signal.h>
#include <atomic>
#include <sys/wait.h>
#include <unistd.h>
#include <random>
#include <iomanip>
#include "include/shared_code.h"

std::atomic<bool> running{true};
pid_t python_pid = 0;

void cleanup_shared_memory() {
    std::cout << "Cleaning up previous shared memory..." << std::endl;
    if (destroy_memory_block("/trading_data")) {
        std::cout << "Previous shared memory cleared" << std::endl;
    }
}

void signal_handler(int signal) {
    std::cout << "\nReceived signal " << signal << ", shutting down..." << std::endl;
    running = false;
    
    if (python_pid > 0) {
        std::cout << "Terminating Python process..." << std::endl;
        kill(python_pid, SIGTERM);
        int status;
        waitpid(python_pid, &status, 0);
    }
}

pid_t launch_python_process() {
    pid_t pid = fork();
    
    if (pid == 0) {
        execl("/usr/bin/python3", "python3", "../../Python/data_bridge.py", nullptr);
        perror("Failed to launch Python process");
        exit(1);
    } else if (pid > 0) {
        std::cout << "Launched Python process with PID: " << pid << std::endl;
        return pid;
    } else {
        perror("Failed to fork Python process");
        return -1;
    }
}

int main(int argc, char** argv) {
    signal(SIGINT, signal_handler);
    signal(SIGTERM, signal_handler);
    
    try {
        cleanup_shared_memory();
        
        SharedMemory<TradingData> trading_shm("/trading_data", true);        
        auto shared_data = trading_shm.get();
        
        python_pid = launch_python_process();
        if (python_pid == -1) {
            std::cerr << "Failed to launch Python process, continuing without it..." << std::endl;
        }
        
        std::cout << "\n=== Trading System Ready ===" << std::endl;
        std::cout << "✓ Shared memory initialized" << std::endl;
        std::cout << "✓ Python bridge process launched" << std::endl;
        std::cout << "✓ Simulating real market data" << std::endl;
        
        std::random_device rd;
        std::mt19937 gen(rd());
        std::uniform_real_distribution<> price_dist(-2.0, 2.0);
        std::uniform_int_distribution<> volume_dist(500000, 2000000);
        
        double base_price = 150.0; // Starting price for AAPL
        int tick = 0;
        
        std::cout << "\nPress Ctrl+C to exit..." << std::endl;
        std::cout << "\nStreaming market data updates:\n" << std::endl;
        
        while (running) {
            double price_change = price_dist(gen);
            double current_price = base_price + price_change;
            int current_volume = volume_dist(gen);
            auto timestamp = std::chrono::duration_cast<std::chrono::seconds>(
                std::chrono::system_clock::now().time_since_epoch()).count();
            
            shared_data->price.store(current_price);
            shared_data->volume.store(current_volume);
            shared_data->timestamp.store(timestamp);
            shared_data->valid.store(true);
            
            if (tick % 10 == 0) {
                std::cout << "Tick " << tick 
                          << " | AAPL: $" << std::fixed << std::setprecision(2) << current_price
                          << " | Volume: " << current_volume
                          << " | Time: " << timestamp << std::endl;
            }
            
            base_price += (price_dist(gen) * 0.1); // Slow price drift
            if (base_price < 100) base_price = 100;
            if (base_price > 200) base_price = 200;
            
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
            tick++;
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}