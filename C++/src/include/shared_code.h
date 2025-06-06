#ifndef SHARED_MEM_H
#define SHARED_MEM_H

#include <sys/mman.h>    // shm_open, mmap, munmap
#include <sys/stat.h>    // mode constants
#include <fcntl.h>       // O_* constants
#include <unistd.h>      // ftruncate, close
#include <string>
#include <stdexcept>
#include <cstring>
#include <iostream>
#include <type_traits>
#include <errno.h>
#include <atomic>        // For atomic operations needed in trading
#include "trading_system.h"

// Low-level functions for shared memory operations - IMPLEMENTATIONS
inline char* create_memory_block(const char* filename, int size) {
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

inline char* attach_memory_block(const char* filename, int size) {
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

inline bool detach_from_memory_block(char* block, int size) {
    return munmap(block, size) != -1;
}

inline bool destroy_memory_block(const char* filename) {
    return shm_unlink(filename) != -1;
}


template<typename T>
class SharedMemory {
private:
    char* raw_memory_;
    const char* filename_;
    bool owner_;
    static_assert(std::is_trivially_copyable_v<T>,
                  "Type must be trivially copyable for shared memory");

public:
    explicit SharedMemory(const char* filename, bool create_new = true);
    ~SharedMemory();

    T* get() { return reinterpret_cast<T*>(raw_memory_); }
    const T* get() const { return reinterpret_cast<const T*>(raw_memory_); }
    T& operator*() { return *get(); }
    const T& operator*() const { return *get(); }
    T* operator->() { return get(); }
    const T* operator->() const { return get(); }
    
    bool is_valid() const { return raw_memory_ != nullptr; }
};

template<typename T>
SharedMemory<T>::SharedMemory(const char* filename, bool create_new)
    : raw_memory_(nullptr), filename_(filename), owner_(create_new) {

    if (create_new) {
        raw_memory_ = create_memory_block(filename, sizeof(T));
        new(raw_memory_) T{};
    } else {
        raw_memory_ = attach_memory_block(filename, sizeof(T));
    }
}

template<typename T>
SharedMemory<T>::~SharedMemory() {
    if (raw_memory_) {
        detach_from_memory_block(raw_memory_, sizeof(T));
        if (owner_) {
            destroy_memory_block(filename_);
        }
    }
}

#endif // SHARED_MEM_H
