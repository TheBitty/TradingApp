#include <syslog.h>
#include <iostream>

void log_shm_error(const char* shm_name, ) {
      syslog(LOG_ERR, "%s failed for '%s': %s (errno: %d)", 
           operation, shm_name, strerror(error_code), error_code);   
      
      std::cerr << "ERROR: " << operation << "failed for " << shm_name
        << "' - " << strerror(error_code) << " (errno: " << error_code << ")" << std::endl;

  if(shm_fd == -1){
        log_shm_error("shm_open", shm_name, errno);
    throw std::runtime_error("shm_open failed to create memory object");
  }
}
