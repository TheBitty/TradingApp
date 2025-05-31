# most of this code will rely on the struct to ensure the data is packed and unpacked in a consisitant format....(WHICH IS KEY)
# as python has very limited ways to handle the memory opperations we do in our c++ backend!

import struct 
import time 
from multiprocessing import shared_memory #for shared_memory
import numpy as np # for math

def read_from_shared_memory(): # this function assumes the C++ backend has created the memory block....
    try:
        existing_shm = shm.SharedMemory(name="simplebuffer") # this opens a system file created by the backend
        raw_data = existing_shm.buf[:struct.calcsize('ddl16s?')]         
        price, volume, timestamp, symbol_bytes, data_ready = 
        struct.unpack('ddl16s?', raw_data)
        
        stock_symbol = symbol_bytes.decode("utf-8").rstrip("\x00")
        
        # we need to fix the error handling 
        print("C++ backend is not started or an error has occured in the 
      creation of the memory block")

def write_to_shared_memory():
    

def menu:
    print("OPTION LIST:")



if _name_ == "_main_":
        data = read_from_shared_memory()
        if data: #if we are going to code it this way we need the readfromem function to have a 0 check for data....(so I think)
            print("C++ BACKEND DATA:")

