#!/usr/bin/env python3.4
# -*- encoding: utf-8 -*-
############################
## Tests ran for Python-MT
##

import minetest
import random
from utils import readS8, readS16, Pos
from io import BytesIO
from schematics import Schematic

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
		print("Cache size: {0}".format(len(db.interface.cache)), end = "  \r")
		assert(len(db.interface.cache) <= db.get_maxcachesize())

def testSetNode():
	db = minetest.MapInterface("./map.sqlite")
	f = open("./dump.bin", "w")
	dummy = minetest.Node("default:nyancat")

	for y in range(1, 10):
		db.set_node(Pos({'x': 0, 'y': y, 'z': 0}), dummy)

	db.save()

def invManip():
	db = minetest.MapInterface("./map.sqlite")
	chest = db.get_meta(Pos({'x': 0, 'y': 0, 'z': 0}))
	#print(chest)
	inv = chest.get_inventory()
	#print(inv)
	#print(chest.get_string("formspec"))
	#chest.set_string("formspec", chest.get_string("formspec") + "button[0,0;1,0.5;moo;Moo]")
	#print(chest.get_string("formspec"))
	print(inv.is_empty("main"))
	print(inv.get_size("main"))

	db.save()

def testSchematics():
	# Import from file
	schem = Schematic("/home/lymkwi/.minetest/games/minetest_game/mods/default/schematics/apple_tree_from_sapling.mts")

	# Export to BytesStream & file
	print(schem.export().read())
	schem.export_to_file("test.mts")

	# Map export
	db = minetest.MapInterface("./map.sqlite")
	schem = db.export_schematic(Pos(), Pos({"x": -100, "y": 10, "z": 100}))
	schem.export_to_file("test.mts")

	# Get node
	print(schem.get_node(Pos({"x": 1, "y": 1, "z": 0})))

def removeUnknowns():
    import sys

    if len(sys.argv) < 2:
        print("I need a map.sqlite file!")
        return
    elif len(sys.argv) < 3:
        print("I need a known nodes file!")
        return

    try:
        knodes = open(sys.argv[2])
    except Exception as err:
        print("Couldn't open know nodes file {0} : {1}".format(sys.argv[1], err))
        return

    print("Know nodes file opened")
    nodes = [node[:-1] for node in knodes.readlines()] # Remove the \n
    print("{0} nodes known".format(len(nodes)))

    u = minetest.map.MapVessel(sys.argv[1])
    ma = 4096 + 4096 * 4096# + 4096 * 4096 * 4096
    for i in range(-ma, ma):
        k = u.load(i)
        absi = minetest.utils.posFromInt(i, 4096)
        print("Testing mapblock {0} ({1})   ".format(i, absi), end = '\r')
        if k:
            print("Checking mapblock {0} ({1})".format(i, absi), end = "     \r")
            unknowns = []
            for id in k.name_id_mappings:
                node = k.name_id_mappings[id]
                if node != "air":
                    if not node in nodes:
                        print("Unknown node in {0} : {1}".format(i, node))
                        unknowns.append(node)

            if len(unknowns) > 0:
                for x in range(16):
                    for y in range(16):
                        for z in range(16):
                            noderef = k.get_node(x + y * 16 + z * 16 * 16)
                            if noderef.get_name() in unknowns:
                                print("Removed node in {0} : {1}".format(noderef.get_pos(), noderef.get_name()))
                                k.remove_node(x + y * 16 + z * 16 * 16)

                print("Saving mapblock {0}".format(absi))
                u.store(i, k.implode())
                u.write(i)

            u.uncache(i)
    u.commit()



if __name__ == "__main__":
	#findTheShelves()
	print("=> MapBlockLoad")
	#testMapBlockLoad()
	removeUnknowns()
	"""print("=> signed endians")
	testSignedEndians()
	print("=> get_node")
	testGetNode()
	print("=> set_node")
	testSetNode()
	print("=> inventory manipulation (WIP)")
	invManip()
	print("=> schematic manipulation (WIP)")
	testSchematics()"""
