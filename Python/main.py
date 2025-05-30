//master file ik we should use mutiple files but umm noo 

from multiprocessing import shared_memory #for shared_memory

import numpy as np 

shm = shared_memory.SharedMemory(create=True, size=a.nbytes)

def GetSharedMemFromC(): #do we have to pass the memory address of our c++ mem?
    print ("waiiting for file to open")
