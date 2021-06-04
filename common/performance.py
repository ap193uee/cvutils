#!/usr/bin/env python3

class Multicore(object):
    """ To convert a single core function into multicore function using the
    python's multiprocessing module.
    """
    def __init__(self, func):
        from multiprocessing import Pool, cpu_count
        from collections import deque
        from time import sleep

        self.processn = cpu_count()
        self.pool = Pool(processes=self.processn)
        self.pending = deque()
        self.func = func
        self.wait = sleep

    def run(self, *args):
        out = None
        if len(self.pending) > 0:
            if len(self.pending) == self.processn:
                while not self.pending[0].ready():
                    self.wait(0.01)
                out = self.pending.popleft().get()
        if len(self.pending) < self.processn:
            task = self.pool.apply_async(self.func, (args))
            self.pending.append(task)
        return out
