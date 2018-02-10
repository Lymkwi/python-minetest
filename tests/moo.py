import libminetest.map

def main(map):
	vessel = libminetest.map.MapVessel(map)
	minpos = None
	maxpos = None
	for block in vessel.get_all_mapblock_ids():
		print(block)
		pos = libminetest.utils.getIntegerAsBlock(block)
		if minpos is None:
			minpos = pos
		if maxpos is None:
			maxpos = pos
		minpos = libminetest.utils.Pos(min(pos.x,minpos.x),min(pos.y,minpos.y),min(pos.z,minpos.z))
		maxpos = libminetest.utils.Pos(max(pos.x,maxpos.x),max(pos.y,maxpos.y),max(pos.z,maxpos.z))
		#print(vessel.load(block))
	print(minpos)
	print(maxpos)

	dimens = len(vessel.get_all_mapblock_ids())
	print("There are {0} blocks currently generated and stored".format(dimens))
	vessel.close()

if __name__ == "__main__":
	main("/home/limefox/.minetest/worlds/Creative/map.sqlite")
