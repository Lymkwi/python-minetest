#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
############################
## Tests ran for Python-MT
##

import minetest
import random
from utils import readS8, readS16, Pos
from io import BytesIO

def testSignedEndians():
    print(readS16(BytesIO(b"\x9f\xff")))

def testMapBlockLoad():
    file = minetest.map.MapVessel("./map.sqlite")
    #i = 2+12*4096+(-9)*4096*4096
    #i = 0
    for i in range(-4096, 4096):
        res, code = file.read(i)
        if not res:
            continue
        else:
            print("Read {0}: {1}".format(i, (res, code)))

            mapb = file.load(i)
            print("Loaded {0}: {1}".format(i, mapb))


    print(len(file.cache))

def testGetNode():
    db = minetest.MapInterface("./map.sqlite")
    for _ in range(1000):
        pos = Pos({'x': random.randint(-300, 300), 'y': random.randint(-300, 300), 'z': random.randint(-300, 300)})

        print("{0}: {1}".format(pos, db.get_node(pos).get_name()))
        print("Cache: {0}".format(len(db.interface.cache)))

if __name__ == "__main__":
    testMapBlockLoad()
    testSignedEndians()
    testGetNode()
