#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
######################################
## Configuration for Python-Minetest
##
#

import os

#from errors import ConfigurationFormatError

class Configuration:
    def __init__(self, file):
        self.data = dict()
        self.lines = []
        self.read(file)
        self.file = file

    def __contains__(self, key):
        return key in self.data

    def __getitem__(self, key):
        return self.data.get(key)

    def __delitem__(self, key):
        del self.data[key]

    def __len__(self):
        return len(self.data)

    def __setitem__(self, key, val):
        self.data[key] = val


    def read(self, file=None):
        try:
            buffer = open(file or self.file)
        except Exception:
            return

        i = -1
        for line in buffer.readlines():
            i += 1
            line = line.strip("\r\n")

            if len(line) == 0:
                self.lines.append((0,))
                continue

            elif line[0] == '#':
                self.lines.append((1, line[1:]))
                continue

            k = line.split("=")
            data = " = ".join(k[1:]).strip()

            if data == "true" or data == "1":
                data = True

            elif data == "false" or data == "0":
                data = False

            elif data.isdigit():
                data = int(data)

            elif data.isdecimal():
                data = float(data)

            self.data[k[0].strip()] = data
            self.lines.append((2, k[0].strip()))

    def write(self, file=None):
        try:
            f = open(file or self.file, "w")
        except Exception as err:
            return None

        #for key in self.data:
        #    f.write("{0} = {1}\n".format(key, self.data[key]))
        for t in self.lines:
            #t = self.lines[i]

            if t[0] == 0:
                f.write('\n')
                continue

            elif t[0] == 1:
                f.write("#{}\n".format(t[1]))
                continue

            elif t[0] == 2:
                if not self.data.get(t[1]):
                    del self.lines[self.lines.index(t)]
                    continue

                f.write("{0} = {1}\n".format(t[1], self.data[t[1]]))
                continue

        for key in self.data:
            if (2, key) in self.lines:
                continue

            f.write("{0} = {1}\n".format(key, self.data[key]))
            self.lines.append((2,key))

        f.close()
        return True


    @classmethod
    def open_world(cls, dir):
        try:
            open(dir + "/world.mt")
        except Exception as err:
            return None

        return cls(dir + "/world.mt")
