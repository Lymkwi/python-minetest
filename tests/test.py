#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
############################
## Tests ran for Python-MT
##

import libminetest
import libminetest.map
import libminetest.config
from libminetest.schematics import Schematic

import random
import time
import os
import sys

from io import BytesIO

def testMapBlockLoad(map):
    file = libminetest.map.MapVessel(map)
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
    assert(libminetest.utils.readS8(BytesIO(b"\xf8")) == -8)
    print("  -> readS8: OK")
    assert(libminetest.utils.readS16(BytesIO(b"\x9f\xff")) == -24577)
    print("  -> readS16: OK")
    assert(libminetest.utils.readS32(BytesIO(b"\xf0\x00\x00\x00")) == -268435456)
    print("  -> readS32: OK")

    assert(libminetest.utils.readU8(BytesIO(b"\xf8")) == 248)
    print("  -> readU8: OK")
    assert(libminetest.utils.readU16(BytesIO(b"\x9f\xff")) == 40959)
    print("  -> readU16: OK")
    assert(libminetest.utils.readU32(BytesIO(b"\xf0\x00\x00\x00")) == 4026531840)
    print("  -> readU32: OK")

    print(" --> Test successful")


def testGetNode(map):
    db = libminetest.map.MapInterface(map)

    u = random.randint(500, 2000)
    k = random.randint(40,400)

    db.set_maxcachesize(k)
    print("  -> Maximum cache size set to {0} mapblocks".format(k))

    s = time.time()
    for i in range(u):
        pos = libminetest.utils.Pos({'x': random.randint(-300, 300), 'y': random.randint(-300, 300), 'z': random.randint(-300, 300)})
        assert(db.get_node(pos).get_name() != "")

        if len(db.interface.cache) == db.get_maxcachesize():
            endstr = " (MAX)\r"
        else:
            endstr = " \r"

        print("[{0}/{1}] Cache size: {2}".format(i, u, len(db.interface.cache)), end = endstr)

        assert(len(db.interface.cache) <= db.get_maxcachesize())

    print("  -> ~{0:.4f}ms per call to get_node".format((time.time()-s)*1000/u), end = "     \n")
    print(" --> Test successful")

def testSetNode(map):
    db = libminetest.map.MapInterface(map)
    f = open("./dump.bin", "w")
    dummy = libminetest.nodes.Node("default:nyancat")
    s = time.time()
    u = 100

    for y in range(1, u+1):
        db.set_node(libminetest.utils.Pos({'x': 0, 'y': y, 'z': 0}), dummy)

    print("  -> {0} nyan cats placed".format(u))
    print("  -> {0}ms per call to set_node".format((time.time()-s)/u*1000))
    s = time.time()
    db.save()
    print("  -> database saving took {0}s".format(time.time()-s))
    print(" --> Test successful")

def invManip(map):
    db = libminetest.map.MapInterface(map)
    pos = libminetest.utils.Pos({'x': 0, 'y': 0, 'z': 0})
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

def testSchematics(map):
    # Import from file
    schem = libminetest.schematics.Schematic(os.environ["HOME"] + "/.minetest/games/minetest_game/mods/default/schematics/apple_tree_from_sapling.mts")
    print("  -> Schematic : {0}".format(schem))

    # Export to BytesStream & file
    assert(schem.export().read())
    print("  -> Export : OK")
    s = time.time()
    schem.export_to_file("test.mts")
    print("  ~~> File export : {0}s".format(time.time()-s))
    assert(open("test.mts"))

    # Map export
    db = libminetest.map.MapInterface(map)
    s = time.time()
    schem = db.export_schematic(libminetest.utils.Pos(), libminetest.utils.Pos({"x": -100, "y": 10, "z": 100}))
    s = time.time() - s
    assert(schem.export().read())
    print("  -> Schematic exportation : OK")
    print("  ~~> Exportation took {0}s".format(s))
    schem.export_to_file("test.mts")

    # Get node
    node = schem.get_node(libminetest.utils.Pos({"x": 0, "y": 0, "z": 0})).get_name()
    assert(node != "")
    print("  -> Node in (0,0,0) is {0}".format(node))

    # Import
    s = time.time()
    db.import_schematic(libminetest.utils.Pos({"x": 100, "y": 100, "z": 100}), schem)
    print("  -> Importation in map took {0}s".format(time.time() - s))

    print("  -> {0} mapblock(s) to be saved".format(len(db.mod_cache)))
    s = time.time()
    db.save()
    print("  -> Saving took {0}s".format(time.time() - s))
    print(" --> Test successful")

def testMapBlockInit(map):
    # Open the db
    db = libminetest.map.MapInterface(map)

    # Override
    print("  -> Init mapblock at (0,0,0)")
    db.init_mapblock(0, override = True)

    print("  -> Saving..")
    db.save()
    db.unload_mapblock(0)

    # Seek node at (0,0,0)
    print("  -> Assertion about node at (0,0,0)")
    assert(db.get_node(libminetest.utils.Pos()).get_name() == "air")
    print("  -> Assertion succeeded")
    print(" --> Test successful")


def testConfiguration():
    # Open the file
    dir = os.environ["HOME"] + "/.minetest/worlds/world"
    print("  -> Testing world configuration first")
    print("  ~~> Trying to open {0}(/world.mt)".format(dir))
    conf = libminetest.config.Configuration.open_world(dir)
    if not conf:
        print("=> No conf found")
        return

    print("  ~~> The world's backend is {0}".format(conf["backend"]))
    print("  ~~> There are {0} configuration keys in the file".format(len(conf)))
    if "load_mod_mesecon" in conf and conf["load_mod_mesecon"]:
        print("  ~~> You have mesecon installed and set to be loaded")
    else:
        print("  ~~> You do not have mesecon installed, or it is disabled")

    print("  -> Testing libminetest.conf second")
    conf = libminetest.config.Configuration(os.environ["HOME"] + "/.minetest/minetest.conf")
    if not conf:
        print("  ~~> File not opened")
        return

    print("  ~~> The admin's name is {0}".format(conf["name"] or "unknown"))
    print("  ~~> The last server you joined was at {0}:{1}".format(conf["address"], conf["port"] or '?????'))
    print("  ~~> The last selected world is located at {0}".format(conf["selected_world_path"]))

    print("  -> Checking write abilities.. ")
    fixed_map_seed = random.randint(0, 100000000)
    conf["fixed_map_seed"] = fixed_map_seed
    print("  ~~> Fixed map seed to {0}".format(fixed_map_seed))

    assert(conf.write())
    print("  ~~> Configuration written")

    conf = None
    print("  ~~> Object thrown away")
    newconf = libminetest.config.Configuration(os.environ["HOME"] + "/.minetest/minetest.conf")
    print("  ~~> Checking fixed_map_seed...")
    print("  ~~> fixed_map_seed = {0}".format(newconf["fixed_map_seed"]))
    assert(newconf["fixed_map_seed"] == fixed_map_seed)
    print("  ~~> Assertion passed")
    newconf = None

    print("  ~~> Checking item removal")
    conf = libminetest.config.Configuration(os.environ["HOME"] + "/.minetest/minetest.conf")
    name = conf["name"]
    del conf["name"]
    conf.write()
    conf = libminetest.config.Configuration(os.environ["HOME"] + "/.minetest/minetest.conf")
    assert(not conf["name"])
    print("  ~~> Item 'name' removed correctly")
    conf = None

    print("  ~~> Checking item insertion")
    conf = libminetest.config.Configuration(os.environ["HOME"] + "/.minetest/minetest.conf")
    conf["name"] = name
    conf.write()
    conf = None
    print("  ~~> Name inserted back")
    conf = libminetest.config.Configuration(os.environ["HOME"] + "/.minetest/minetest.conf")
    print("  ~~> Name is '{}'".format(conf["name"]))
    assert(conf["name"] == name)
    print("  ~~> Assertion passed")
    conf = None

    print(" --> Test successful")


def main(map):
    print("=> Tests will begin now")
    time.sleep(3)

    print("=> MapBlockLoad Test")
    s = time.time()
    testMapBlockLoad(map)
    print("  => Test took {0:.10f}s".format(time.time()-s))

    print("=> Signed Endians")
    s = time.time()
    testEndians()
    print("  => Test took {0:.10f}s".format(time.time()-s))

    print("=> get_node Test")
    s = time.time()
    testGetNode(map)
    print("  => Test took {0:.10f}s".format(time.time()-s))

    print("=> set_node")
    s = time.time()
    testSetNode(map)
    print("  => Test took {0:.10f}s".format(time.time()-s))

    print("=> inventory manipulation (WIP)")
    s = time.time()
    invManip(map)
    print("  => Test took {0:.10f}s".format(time.time()-s))

    print("=> schematic manipulation")
    s = time.time()
    testSchematics(map)
    print("  => Test took {0:.10f}s".format(time.time()-s))

    print("=> MapBlock init")
    s = time.time()
    testMapBlockInit(map)
    print("  => Test took {0:.10f}s".format(time.time()-s))

    print("=> Configuration Test (WIP)")
    s = time.time()
    testConfiguration()
    print("  => Test took {0:.10f}s".format(time.time()-s))


if __name__ == "__main__":
    if not len(sys.argv) >= 2:
        print("Please give the path to a map file")
    else:
        main(sys.argv[1])