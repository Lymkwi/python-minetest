#!/usr/bin/env python3
# -*- encoding: utf8 -*-
###########################
## Metadata for Python-MT
##
##
#

from inventory import InvRef
from utils import Pos


class NodeMetaRef:
    def __init__(self, spos = None, meta = None, inv = None):
        self.data = meta or dict()
        self.pos = spos or Pos()
        self.inv = inv or InvRef()

    def get_raw(self, key):
        return self.data.get(key)

    def set_raw(self, key, val):
        self.data[key] = val

    def get_string(self, key):
        # Gather the integers into a string
        data = self.data.get(key)
        if not data:
            return None

        res = ""
        for c in data:
            if c >= 256 or c < 0:
                return data # IT IS A NUMBER AAAAAH

            res += chr(c)
        return res

    def set_string(self, key, val):
        self.data[key] = [ord(b) for b in val]

    def get_int(self, key):
        return int(self.data.get(key))

    def set_int(self, key, val):
        self.data[key] = int(val)

    def get_float(self, key):
        return float(self.data.get(key))

    def set_float(self, key, val):
        self.data[key] = float(val)

    def get_inventory(self):
        return self.inv

    def to_table(self):
        return self.meta

    def from_table(self, tab = {}):
        self.meta = tab
