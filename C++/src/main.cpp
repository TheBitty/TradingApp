#include <atomic>
#include <sys/mman.h> // for shm_open(creating a shared memory object)
#include <unistd.h> // For ftruncate(Setting the size of the shared memory object) on POSIX systems
#include <sys/stat.h> // for mode constants
#include <iostream>
#include <cstring>
#include <thread>
#include <chrono>
#include "include/shared_code.h"

char* create_memory_block(const char* filename, int size) {
    std::cout << "Creating memory block " << filename << std::endl;
  
    const int shm_fd = shm_open(filename, O_CREAT | O_EXCL | O_RDWR, 0666);
    if (shm_fd == -1) {
        if (errno == EEXIST) {
            throw std::runtime_error("Shared memory already exists - use attach mode");
        } else {
            throw std::runtime_error("Failed to create shared memory: " + std::string(strerror(errno)));
        }
    }

    if (ftruncate(shm_fd, size) == -1) {
        close(shm_fd);
        shm_unlink(filename);
        throw std::runtime_error("Failed to set shared memory size");
    }

    auto memory = static_cast<char*>(
        mmap(nullptr, size, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0)
    );
    close(shm_fd);

    if (memory == MAP_FAILED) {
        shm_unlink(filename);
        throw std::runtime_error("Failed to map shared memory");
    }

    return memory;
} 

char* attach_memory_block(const char* filename, int size) {
    int shm_fd = shm_open(filename, O_RDWR, 0);
    if (shm_fd == -1) {
        throw std::runtime_error("Failed to open existing shared memory");
    }

    auto memory = static_cast<char*>(
        mmap(nullptr, size, PROT_READ | PROT_WRITE, MAP_SHARED, shm_fd, 0)
    );
    close(shm_fd);

    if (memory == MAP_FAILED) {
        throw std::runtime_error("Failed to map existing shared memory");
    }

    return memory;
}

bool detach_from_memory_block(char* block, int size) {
    return munmap(block, size) != -1;
}

bool destroy_memory_block(const char* filename) {
    return shm_unlink(filename) != -1;
}


int main(int argc, char** argv) {
    try {
        SharedMemory<TradingData> trading_shm("/trading_data", true);
        
        auto data = trading_shm.get();
        data->price.store(100.50);
        data->volume.store(1000);
        data->timestamp.store(1234567890);
        data->valid.store(true);
        
        std::cout << "Created shared memory with price: " << data->price.load() << std::endl;
        std::cout << "Press Ctrl+C to exit..." << std::endl;
        
        // Keep updating data to demonstrate real-time sharing
        while (true) {
            data->price.store(data->price.load() + 0.01);
            data->timestamp.store(data->timestamp.load() + 1);
            std::this_thread::sleep_for(std::chrono::milliseconds(100));
        }
        
    } catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    
    return 0;
}
