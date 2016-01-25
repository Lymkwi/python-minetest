#!/usr/bin/env python3
# -*- encoding: utf8 -*-
###########################
## Nodes for Python-MT
##
##
#

from utils import Pos

class NodeTimerRef:
    def __init__(self, pos = Pos(), timeout = 0.0, elapsed = 0.0):
        self.pos = pos
        self.timeout = timeout
        self.elapsed = elapsed
        self.active = False

    def set(self, timeout, elapsed):
        self.timeout, self.elapsed = timeout, elapsed

    def start(self, timeout):
        self.set(timeout, 0)
        self.active = True

    def stop(self):
        self.active = False

    def get_timeout(self):
        return self.timeout

    def get_elapsed(self):
        return self.elapsed

    def is_started(self):
        return self.active

class Node:
    def __init__(self, pos, itemstring, param1 = 0, param2 = 0):
        self.pos = pos
        self.itemstring = itemstring
        self.param1, self.param2 = param1, param2

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return self.itemstring

    def get_name(self):
        return self.itemstring
