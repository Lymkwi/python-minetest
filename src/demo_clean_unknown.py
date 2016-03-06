#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
############################
## Demo of Python-Minetest :
## Erease all unknown nodes from a map.sqlite file
##
## args :
## ./demo_clean_unknowns.py <path to sqlite file> <path to list of known nodes>
##
#

import minetest
import time

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
    ids = u.get_all_mapblock_ids()
    nids = len(ids)
    print("{0} mapblocks to inspect".format(nids))

    s = time.time()
    eta = 0

    for index in range(len(ids)):
        i = ids[index]
        k = u.load(i)
        absi = minetest.utils.posFromInt(i, 4096)
        pct = index/nids * 100
        if index % 10 == 0:
            eta = ((time.time() - s) / (index+1)) * (nids - index)
            etastring = "[ETA {0}:{1:2d}]".format(int(eta/60), int(eta%60))

        print("[{0:3.2f}%]{1} Checking mapblock {2} ({3})".format(pct, etastring, i, absi), end = "     \r")
        unknowns = []
        for id in k.name_id_mappings:
            node = k.name_id_mappings[id]
            if node != "air":
                if not node in nodes:
                    unknowns.append(node)

        if len(unknowns) > 0:
            for x in range(16):
                for y in range(16):
                    for z in range(16):
                        noderef = k.get_node(x + y * 16 + z * 16 * 16)
                        if noderef.get_name() in unknowns:
                            k.remove_node(x + y * 16 + z * 16 * 16)

            print("\n[{0:3.2f}%] {1} nodes removed".format(pct, len(unknowns)))
            print("[{0:3.2f}%] Saving mapblock {1}".format(pct, absi))
            u.store(i, k.implode())
            u.write(i)

        u.uncache(i)

    u.commit()

if __name__ == "__main__":
    removeUnknowns()
