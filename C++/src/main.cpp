#include <sys.mman.h> // for shm_open(creating a shared memory object) 
#include <unistd.h> // For ftruncate(Setting the size of the shared memory object) on POSIX systems 
#include "~TradingApp/C++/src/SharedMem.h" // shared code 
#include <sys.stat.h> // for mode constants
#include <iostream>
#include <cstring>
#include <chrono>
#include <thread>
#include <stdexcept>  // for std::runtime_error
#include <cstring>    // for strerror
#include <errno.h>    // for errno

struct SimpleDataStruct{
  double Price;
  double volume;
  long timestamp;
  char symbol[16];
  //32 Bytes!
  volatile bool data_ready; //flag for python

}; // with the bool flag we might be at 41....c++ will pad 7 extra making it 48

void MemoryObject(){ // creates a simple shared memory object for now 
  const char* shm_name = "/simplebuffer"; // we will test a char buffer first....
  int size = sizeof(SimpleDataStruct);

  int shm_fd = shm_open(shm_name, O_CREAT |O_RDWR, 0666);
  if(shm_fd == -1) {
    std::cerr << "ERROR!: shm_fd failed to create memory object" << shm_name 
      << "' - " << strerror(errno) << " (errno: " << errno << ")" << std::endl;
    
    throw std::runtime_error("shm_open failed to create memory object terminamting program..."); 
  }  
}

int main(){ MemoryObject(); return 0; };
