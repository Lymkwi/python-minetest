#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
############################
## Tests ran for Python-MT
##

import minetest
import random
from utils import readS8, readS16, Pos
from io import BytesIO


def findTheShelves():
	from PIL import Image
	file = minetest.MapInterface("/home/lymkwi/.minetest/worlds/NodesJustWannaHaveFun/map.sqlite")
	file.setMaxCacheSize(450)
	mapy = {}
	size = 16 # In mapblocks
	hsize = int(size/2)
	alphas, noairs = {}, {}
	for x in range(-hsize, hsize):
		for z in range(-hsize, hsize):
			for y in range(0, 16):
				posx, posy, posz = x*16, y*16, z*16

				for intx in range(0, 16):
					for intz in range(0, 16):
						alpha, noair = 0, 0
						for inty in range(0, 16):
							node = file.get_node(Pos({'x': posx+intx, 'y': posy+inty, 'z': posz+intz}))
							print("[{0}] {1}".format(node.pos, node.get_name()), end = (' ' * 20) + '\r')
							if node.get_name() != "air":
								noair += 1
								if node.get_name() == "ignore":
									alpha += 1

						coords = ((posx + intx) * 4096 * (posz + intz))
						alphas[coords] = (alphas.get(coords) or 256) - alpha
						noairs[coords] = (noairs.get(coords) or 0) + noair

#	mapy = [(alpha,) * 3 + (noair,) ]
	for alpha, noair in zip(alphas.keys(), noairs.keys()):
		mapy[alpha] = (alphas[alpha],) * 3 + (noairs[noair],)

	buildPic(mapy, size).save("map.jpg")


def buildPic(mapy, size):
	im = Image.new("RGBA", (size*16, size*16))
	hsize = int(size*8)
	for x in range(-hsize, hsize):
		for z in range(-hsize, hsize):
			im.putpixel((z+hsize, x+hsize), mapy[x * z*4096])

	im.show()
	return im

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

def testSetNode():
	db = minetest.MapInterface("./map.sqlite")
	db.force_save_on_unload = True
	f = open("./dump.bin", "w")
	dummy = minetest.Node(Pos(), "default:nyancat", 0, 0)
	print(db.get_node(Pos()))
	print(db.set_node(Pos(), dummy))

	for y in range(0, 256):
		db.set_node(Pos({'x': 0, 'y': y, 'z': 0}), dummy)

	db.save()

if __name__ == "__main__":
    #findTheShelves()
    #testMapBlockLoad()
    #testSignedEndians()
    #testGetNode()
    testSetNode()