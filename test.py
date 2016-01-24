#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
##########################
##

import minetest
import random
from utils import readS8, readS16
from io import BytesIO

file = minetest.MapVessel("./map.sqlite")
#i = 2+12*4096+(-9)*4096*4096
#i = 0

def testSignedEndians():
    print(readS16(BytesIO(b"\x9f\xff")))

def testMapBlockLoad():
    for i in range(-4096, 4096):
        res, code = file.read(i)
        if not res:
            continue
        else:
            print("Read {0}: {1}".format(i, (res, code)))

            mapb = file.load(i)
            print("Loaded {0}: {1}".format(i, mapb))


    print(len(file.cache))

if __name__ == "__main__":
    testMapBlockLoad()
    #testSignedEndians()
