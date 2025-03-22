import multiprocessing as mp

class Semaphore:
    def __init__(self, value=1):
        self.sem = mp.Semaphore(value)

    def acquire(self):
        self.sem.acquire()

    def release(self):
        self.sem.release()