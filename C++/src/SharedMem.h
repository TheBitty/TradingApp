#ifndef SHARED_MEM_H
#define SHARED_MEM_H

#include <sys/mman.h>    // shm_open, mmap, munmap
#include <sys/stat.h>    // mode constants
#include <fcntl.h>       // O_* constants
#include <unistd.h>      // ftruncate, close
#include <string>
#include <stdexcept>
#include <cstring>

char * attached_memory_block(char* filename, int size); //filename is a shared file with our memory address of py
                                                        //size is going to be a templete i.e the size of a address buffer?
bool detach_from_memory_block(char *block);
bool destory_memory_block(char *filename);

struct SimpleMarketData{
  double price;
  double volume;
  long timestamp;
  char symbol[16];
  volatile bool data_ready; // check if data is ready to be shared with python
                            // this is to be changed of course with the introduction of my python math...
     SimpleMarketData() : price(0.0), volume(0.0), timestamp(0), data_ready(false) {
        memset(symbol, 0, sizeof(symbol));
    }};

#endif // SHARED_MEM_H                                            
                                                      
