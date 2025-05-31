#ifndef SHARED_MEM_H
#define SHARED_MEM_H

#include <sys/mman.h>    // shm_open, mmap, munmap
#include <sys/stat.h>    // mode constants
#include <fcntl.h>       // O_* constants
#include <unistd.h>      // ftruncate, close
#include <string>
#include <stdexcept>
#include <cstring>

// Low-level functions for shared memory operations
char* attached_memory_block(const char* filename, int size);
bool detach_from_memory_block(char* block, int size);
bool destroy_memory_block(const char* filename);

template<typename T>
class type_shared_memory{
  
};
