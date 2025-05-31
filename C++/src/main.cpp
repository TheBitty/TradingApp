#include <atomic>

#include <sys.mman.h> // for shm_open(creating a shared memory object) 
#include <unistd.h> // For ftruncate(Setting the size of the shared memory object) on POSIX systems 
#include "~TradingApp/C++/src/SharedMem.h" // shared code 
#include <sys.stat.h> // for mode constants
#include <iostream>
#include <cstring>
#include <chrono>
#include <thread>
struct SimpleDataStruct{
  double Price;
  double volume;
  long timestamp;
  char symbol[16];
  //32 Bytes!
  volatile bool data_ready; //flag for python

};

void MemoryObject(){ // creates a simple shared memory object for now 
  const char* shm_name = "/simplebuffer"; // we will test a char buffer first....
  int size = sizeof(SimpleDataStruct);

  //int shm_open(const char *name, int oflag, mode_t mode);
}

int main(){ MemoryObject(); return 0; };
