#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
############################
## Demo of Python-Minetest :
## Exports/Imports a schematic to a map
##
## args :
## ./demo_schematic_manipulation.py <import|export> <path to sqlite file> <path to schematic file>
##
#

import minetest

pos_import = minetest.utils.Pos({"x": 300, "y": 100, "z": 300})
pos1_export = minetest.utils.Pos({"x": -10, "y": -10, "z": -10})
pos2_export = minetest.utils.Pos({"x": 10, "y": 10, "z": 10})

minetest.logger.init_logging(debug=True)

if __name__ == "__main__":
	import sys

	if len(sys.argv) < 4:
		if len(sys.argv) == 2 and sys.argv[1] == "help":
			print("./demo_schematic_manipulation.py <import|export> <path to sqlite file> <path to schematic file>")
		else:
			print("See demo_schematic_manipulation.py help for help")
		sys.exit(0)

	mode, dbfile, schfile = sys.argv[1:4]

	try:
		open(dbfile)
	except Exception as err:
		print("Couldn't open db file {0} : {1}".format(dbfile, err))
		sys.exit(0)

	db = minetest.map.MapInterface(dbfile)

	if mode.lower() == "import":
		db.set_maxcachesize(40)
		print("Reading schematic...")
		schem = minetest.schematics.Schematic(schfile)
		if not schem:
			print("No schematic imported. Aborted.")

		print("Importing schematic..")
		db.import_schematic(pos_import, schem, stage_save=True)
		print("Saving...")
		db.save()
		print("Done")

	elif mode.lower() == "export":
		print("Exporting schematic..")
		db.export_schematic(pos1_export, pos2_export).export_to_file(schfile)
		print("Done")

	else:
		print("Unknown mode {0}".format(mode))
		sys.exit(9)
