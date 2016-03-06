#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
############################
## Tests ran for Python-MT
##

import minetest
import random
import time

from io import BytesIO
from schematics import Schematic

def testMapBlockLoad():
	file = minetest.map.MapVessel("./map.sqlite")
	for i in range(-4096, 4096):
		res, code = file.read(i)
		if not res:
			continue
		else:
			mapb = file.load(i)
			print("Read and loaded {0}: {1}".format(i, mapb), end = "    \r")

	print("  -> There are in total {0} mapblocks in the map".format(len(file.get_all_mapblock_ids())), end = (' ' * 20) + '\n')
	print(" --> Test successful")

def testEndians():
	assert(minetest.utils.readS8(BytesIO(b"\xf8")) == -8)
	print("  -> readS8: OK")
	assert(minetest.utils.readS16(BytesIO(b"\x9f\xff")) == -24577)
	print("  -> readS16: OK")
	assert(minetest.utils.readS32(BytesIO(b"\xf0\x00\x00\x00")) == -268435456)
	print("  -> readS32: OK")

	assert(minetest.utils.readU8(BytesIO(b"\xf8")) == 248)
	print("  -> readU8: OK")
	assert(minetest.utils.readU16(BytesIO(b"\x9f\xff")) == 40959)
	print("  -> readU16: OK")
	assert(minetest.utils.readU32(BytesIO(b"\xf0\x00\x00\x00")) == 4026531840)
	print("  -> readU32: OK")

	print(" --> Test successful")


def testGetNode():
	db = minetest.map.MapInterface("./map.sqlite")

	u = random.randint(500, 2000)
	k = random.randint(40,400)

	db.set_maxcachesize(k)
	print("  -> Maximum cache size set to {0} mapblocks".format(k))

	s = time.time()
	for i in range(u):
		pos = minetest.utils.Pos({'x': random.randint(-300, 300), 'y': random.randint(-300, 300), 'z': random.randint(-300, 300)})
		assert(db.get_node(pos).get_name() != "")

		if len(db.interface.cache) == db.get_maxcachesize():
			endstr = " (MAX)\r"
		else:
			endstr = " \r"

		print("[{0}/{1}] Cache size: {2}".format(i, u, len(db.interface.cache)), end = endstr)

		assert(len(db.interface.cache) <= db.get_maxcachesize())

	print("  -> ~{0:.4f}ms per call to get_node".format((time.time()-s)*1000/u), end = "     \n")
	print(" --> Test successful")

def testSetNode():
	db = minetest.map.MapInterface("./map.sqlite")
	f = open("./dump.bin", "w")
	dummy = minetest.nodes.Node("default:nyancat")
	s = time.time()
	u = 100

	for y in range(1, u+1):
		db.set_node(minetest.utils.Pos({'x': 0, 'y': y, 'z': 0}), dummy)

	print("  -> {0} nyan cats placed".format(u))
	print("  -> {0}ms per call to set_node".format((time.time()-s)/u*1000))
	s = time.time()
	db.save()
	print("  -> database saving took {0}s".format(time.time()-s))
	print(" --> Test successful")

def invManip():
	db = minetest.map.MapInterface("./map.sqlite")
	pos = minetest.utils.Pos({'x': 0, 'y': 0, 'z': 0})
	chest = db.get_meta(pos)
	inv = chest.get_inventory()

	print("  -> Testing inventory in node at {0}".format(pos))
	print("  ~~> Node's name is {0}".format(db.get_node(pos).get_name()))
	if inv.is_empty("main"):
		print("  ~~> Inventory is empty")
	else:
		print("  ~~> Inventory is not empty")

	print("  ~~> Size of 'main' list is {0} slots".format(inv.get_size("main")))
	print(" --> Test successful")

def testSchematics():
	# Import from file
	schem = minetest.schematics.Schematic("/home/lymkwi/.minetest/games/minetest_game/mods/default/schematics/apple_tree_from_sapling.mts")
	print("  -> Schematic : {0}".format(schem))

	# Export to BytesStream & file
	assert(schem.export().read())
	print("  -> Export : OK")
	s = time.time()
	schem.export_to_file("test.mts")
	print("  ~~> File export : {0}s".format(time.time()-s))
	assert(open("test.mts"))

	# Map export
	db = minetest.map.MapInterface("./map.sqlite")
	s = time.time()
	schem = db.export_schematic(minetest.utils.Pos(), minetest.utils.Pos({"x": -100, "y": 10, "z": 100}))
	s = time.time() - s
	assert(schem.export().read())
	print("  -> Schematic exportation : OK")
	print("  ~~> Exportation took {0}s".format(s))
	schem.export_to_file("test.mts")

	# Get node
	node = schem.get_node(minetest.utils.Pos({"x": 0, "y": 0, "z": 0})).get_name()
	assert(node != "")
	print("  -> Node in (0,0,0) is {0}".format(node))

	# Import
	s = time.time()
	db.import_schematic(minetest.utils.Pos({"x": 100, "y": 100, "z": 100}), schem)
	print("  -> Importation in map took {0}s".format(time.time() - s))

	print("  -> {0} mapblock(s) to be saved".format(len(db.mod_cache)))
	s = time.time()
	db.save()
	print("  -> Saving took {0}s".format(time.time() - s))
	print(" --> Test successful")

def testMapBlockInit():
	# Open the db
	db = minetest.map.MapInterface("./map.sqlite")

	# Override
	print("  -> Init mapblock at (0,0,0)")
	db.init_mapblock(0, override = True)

	print("  -> Saving..")
	db.save()
	db.unload_mapblock(0)

	# Seek node at (0,0,0)
	print("  -> Assertion about node at (0,0,0)")
	assert(db.get_node(minetest.utils.Pos()).get_name() == "air")
	print("  -> Assertion succeeded")
	print(" --> Test successful")


def main():
	print("=> MapBlockLoad Test")
	s = time.time()
	testMapBlockLoad()
	print("  => Test took {0:.10f}s".format(time.time()-s))

	print("=> Signed Endians")
	s = time.time()
	testEndians()
	print("  => Test took {0:.10f}s".format(time.time()-s))

	print("=> get_node Test")
	s = time.time()
	testGetNode()
	print("  => Test took {0:.10f}s".format(time.time()-s))

	print("=> set_node")
	s = time.time()
	testSetNode()
	print("  => Test took {0:.10f}s".format(time.time()-s))

	print("=> inventory manipulation (WIP)")
	s = time.time()
	invManip()
	print("  => Test took {0:.10f}s".format(time.time()-s))

	print("=> schematic manipulation (WIP)")
	s = time.time()
	testSchematics()
	print("  => Test took {0:.10f}s".format(time.time()-s))"""

	print("=> MapBlock init")
	s = time.time()
	testMapBlockInit()
	print("  => Test took {0:.10f}s".format(time.time()-s))

if __name__ == "__main__":
	main()
