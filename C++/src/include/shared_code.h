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

// Low-level functions for shared memory operations - DECLARATIONS ONLY
char* create_memory_block(const char* filename, int size);
char* attach_memory_block(const char* filename, int size);
bool detach_from_memory_block(char* block, int size);
bool destroy_memory_block(const char* filename);

struct TradingData {
    std::atomic<double> price{0.0};
    std::atomic<uint64_t> timestamp{0};
    std::atomic<int32_t> volume{0};
    std::atomic<bool> valid{false};
};

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