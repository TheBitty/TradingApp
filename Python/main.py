# most of this code will relie on the struct to ensure the data is packed and unpacked in a consisitant format....(WHICH IS KEY)
# as python has very limited ways to handle the memory opperations we do in our c++ backend!
import struct 
import time 
from multiprocessing import shared_memory #for shared_memory
import numpy as np # for math

def read_from_shared_memory(): # this function assumes the C++ backend has created the memory block....
    try:
        existing_shm = shm.SharedMemory(name = "/simplebuffer")
        raw_memory = 
    else:
      print("C++ backend is not started or an error has occured in the creation of the memory block")

    if _name_ == "_main_":
        data = read_from_shared_memory()
        if data = 1:
            print("C++ BACKEND DATA:")
