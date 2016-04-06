#!/usr/bin/env python3
# -*- encoding: utf8 -*-
###########################
## Maps for Python-MT
##
##
#

import sqlite3 as _sql
import zlib
from io import BytesIO
import math
import logging

from .errors import MapError, IgnoreContentReplacementError, EmptyMapVesselError, UnknownMetadataTypeIDError, InvalidParamLengthError, OutOfBordersCoordinates
from .utils import *
from .metadata import NodeMetaRef
from .inventory import getSerializedInventory, deserializeInventory, InvRef
from .nodes import NodeTimerRef, Node
from .schematics import Schematic
from .logger import logger

logger.debug("Map Loaded")

# Bitmask constants
IS_UNDERGROUND = 1
DAY_NIGHT_DIFFERS = 2
LIGHTING_EXPIRED = 4
GENERATED = 8

class MapBlock:
	def __init__(self, data = None, abspos = 0):
		self.abspos = abspos
		self.mapblockpos = posFromInt(self.abspos, 4096)
		logger.debug("MapBlock object initiated at {0}".format(self.mapblockpos))
		if data:
			self.explode(data)
		else:
			self.nodes = dict()
			self.version = 25
			self.mapblocksize = 16 # Normally
			self.bitmask = GENERATED & LIGHTING_EXPIRED
			self.content_width = 2
			self.param_width = 2
			self.node_meta = dict()
			self.static_object_version = 0 #u8
			self.static_object_count = 0 #u16
			self.static_objects = [] #u8, s32, s32, s32, u16, u8
			self.timestamp = 0 #u32
			self.name_id_mapping_version = 0 #u8
			self.num_name_id_mappings = 0 #u16
			self.name_id_mappings = dict() #u16, u8[u16]
			self.single_timer_data_length = 10 #u8
			self.timer_counts = 0 #u16
			self.node_timers = dict() #u16, s32, s32

			for x in range(4096):
				# Bypass position verification
				self.nodes[x] = Node("air")

			self.name_id_mappings = self.create_name_id_mappings()
			self.num_name_id_mappings = len(self.name_id_mappings)

	def create_name_id_mappings(self):
		names = []
		for node in self.nodes.values():
			if not node.itemstring in names:
				names.append(node.itemstring)

		return names

	def implode(self):
		data = BytesIO(b"")
		writeU8(data, self.version)
		writeU8(data, self.bitmask)
		writeU8(data, self.content_width)
		writeU8(data, self.param_width)

		# Node params
		node_data = {"param0": [], "param1": [], "param2": []}
		self.name_id_mappings = self.create_name_id_mappings()
		self.num_name_id_mappings = len(self.name_id_mappings)

		for node in self.nodes.values():
			node_data["param0"].append(self.name_id_mappings.index(node.itemstring))
			node_data["param1"].append(node.param1)
			node_data["param2"].append(node.param2)

		c_width_data = BytesIO(b"")
		for b in node_data["param0"]:
			writeU16(c_width_data, b)

		for b in node_data["param1"]:
			writeU8(c_width_data, b)

		for b in node_data["param2"]:
			writeU8(c_width_data, b)

		data.write(zlib.compress(c_width_data.getvalue()))

		# Metadata
		# Meta version
		meta_data = BytesIO(b"")
		writeU8(meta_data, 1)
		writeU16(meta_data, len(self.node_meta))
		for meta_key in self.node_meta.keys():

			meta = self.node_meta[meta_key]
			writeU16(meta_data, meta.pos.getAsInt())
			writeU32(meta_data, len(meta.data.keys()))

			for meta_key in list(meta.data.keys()):
				writeU16(meta_data, len(meta_key))

				for b in meta_key:
					writeU8(meta_data, ord(b))

				writeU32(meta_data, len(meta.data[meta_key]))
				for b in meta.data[meta_key]:
					writeU8(meta_data, b)

			for c in meta.get_inventory().to_string():
				meta_data.write(c.encode("utf8"))

		data.write(zlib.compress(meta_data.getvalue()))

		# Static object version
		writeU8(data, 0)
		writeU16(data, self.static_object_count)

		for obj in self.static_objects:
			writeU8(data, obj["type"])
			writeU32(data, obj["pos"].x * 1000) # Should be S32 but it has the same result
			writeU32(data, obj["pos"].y * 1000)
			writeU32(data, obj["pos"].z * 1000)
			writeU16(data, len(obj["data"]))
			for b in obj["data"]:
				writeU8(data, ord(b))

		# Last time it was modified
		writeU32(data, self.timestamp)

		# ID mappings starts here
		writeU8(data, self.name_id_mapping_version)
		self.num_name_id_mappings = len(self.name_id_mappings)
		writeU16(data, self.num_name_id_mappings)
		for i in range(self.num_name_id_mappings):
			writeU16(data, i)
			writeU16(data, len(self.name_id_mappings[i]))
			for b in self.name_id_mappings[i]:
				writeU8(data, ord(b))

		# Node timers
		writeU8(data, self.single_timer_data_length) # Always 2+4+4=10
		writeU16(data, len(self.node_timers))
		for timer in self.node_timers.values():
			writeU16(data, timer.pos.getAsInt())
			writeU32(data, int(timer.timeout * 1000))
			writeU32(data, int(timer.elapsed * 1000))

		# EOF.
		return data.getvalue()

	def check_pos(self, mapblockpos):
		if mapblockpos < 0 or mapblockpos >= 4096:
			raise OutOfBordersCoordinates("Invalid position : " + str(mapblockpos))

	def get_node(self, mapblockpos):
		self.check_pos(mapblockpos)

		return self.nodes[mapblockpos]

	def set_node(self, mapblockpos, node):
		self.check_pos(mapblockpos)

		if self.node_meta.get(mapblockpos):
			del self.node_meta[mapblockpos]
		if self.node_timers.get(mapblockpos):
			del self.node_timers[mapblockpos]

		self.nodes[mapblockpos] = node

		return True

	def add_node(self, mapblockpos, node):
		self.set_node(self, mapblockpos, node)

	def explode(self, bytelist):
		data = BytesIO(bytelist)

		self.mapblocksize = 16 # Normally
		self.version = readU8(data)
		self.bitmask = readU8(data)
		self.content_width = readU8(data)
		self.param_width = readU8(data)

		self.nodes = dict()
		node_data = dict()

		k = b""
		while True:
			oldklen = len(k)
			k += data.read(1)

			try:
				c_width_data = BytesIO(zlib.decompress(k))
			except zlib.error as err:
				if len(k) > oldklen:
					continue
			else:
				break

		node_data["param0"] = []
		for _ in range(4096):
			if self.content_width == 1:
				b = readU8(c_width_data)
			else:
				b = readU16(c_width_data)

			node_data["param0"].append(int(b))

		node_data["param1"] = [ int(b) for b in c_width_data.read(4096) ]
		node_data["param2"] = [ int(b) for b in c_width_data.read(4096) ]

		try:
			assert(len(node_data["param0"]) == 4096)
			assert(len(node_data["param1"]) == 4096)
			assert(len(node_data["param2"]) == 4096)
		except AssertionError:
			raise InvalidParamLengthError()

		k = b""
		while True:
			oldklen = len(k)
			k += data.read(1)

			try:
				node_meta_list = BytesIO(zlib.decompress(k))
			except zlib.error as err:
				if len(k) > oldklen:
					continue
			else:
				break

		self.node_meta = dict()
		if self.version <= 22:
			self.meta_version = readU16(node_meta_list)
			metadata_count = readU16(node_meta_list)

			for i in range(metadata_count):
				pos = posFromInt(readU16(node_meta_list), self.mapblocksize).getAsTuple()
				self.node_meta[pos] = NodeMetaRef(pos)

				type_id = readU16(node_meta_list)
				c_size = readU16(node_meta_list)
				meta = [readU8(node_meta_list) for _ in range(c_size)]

				if type_id == 1:
					# It is "generic" metadata

					# serialized inventory
					self.node_meta[pos].get_inventory().from_list(getSerializedInventory(node_meta_list))

					# u8[u32 len] text
					self.node_meta[pos].set_raw("text", "".join([ readU8(node_meta_list) for _ in range(readU32(node_meta_list))]))

					# u8[u16 len] owner
					self.node_meta[pos].set_raw("owner", "".join([ readU8(node_meta_list) for _ in range(readU16(node_meta_list))]))

					# u8[u16 len] infotext
					self.node_meta[pos].set_raw("infotext", "".join([ readU8(node_meta_list) for _ in range(readU16(node_meta_list))]))

					# u8[u16 len] inventory_drawspec
					self.node_meta[pos].set_raw("formspec", "".join([ readU8(node_meta_list) for _ in range(readU16(node_meta_list))]))

					# u8 allow_text_input
					self.node_meta[pos].set_raw("allow_text_input", readU8(node_meta_list))

					# u8 removeal_disabled
					self.node_meta[pos].set_raw("removal_disabled", readU8(node_meta_list))

					# u8 enforce_owner
					self.node_meta[pos].set_raw("enforce_owner", readU8(node_meta_list))

					# u32 num_vars
					num_vars = readU32(node_meta_list)

					for _ in range(num_vars):
						# u8 [u16 len] name
						name = [readU8(node_meta_list) for _ in range(readU16(node_meta_list))]

						# u8 [u32 len] value
						value = [readU8(node_meta_list) for _ in range(readU32(node_meta_list))]

						self.node_meta[pos].set_raw(name, value)

				elif type_id == 14:
					# Sign metadata
					# u8 [u16 text_len] text
					self.node_meta[pos].set_raw("text", "".join([ readU8(node_meta_list) for _ in range(readU16(node_meta_list)) ]))

				elif type_id == 15 or type_id == 16:
					# Chest metadata
					# Also, Furnace metadata
					# Which doesn't seem to be documented
					# So let's assume they're like chests
					# (which will probably fail)

					# serialized inventory
					self.node_meta[pos].get_inventory().from_string(getSerializedInventory(node_meta_list))


				elif type_id == 17:
					# Locked Chest metadata

					# u8 [u16 len] owner
					self.node_meta[pos].set_raw("owner", "".join([ readU8(node_meta_list) for _ in range(readU16(node_meta_list)) ]))

					# serialized inventory
					self.node_meta[pos].get_inventory().from_string(getSerializedInventory(node_meta_list))

				else:
					raise UnknownMetadataTypeIDError("Unknown metadata type ID: {0}".format(type_id))

		else:
			self.meta_version = readU8(node_meta_list)
			if self.meta_version == 0:# and self.bitmask & GENERATED == 0:
				# Mapblock was probably not generated
				# It is CONTENT_IGNORE
				# Or there are no metadata
				# GET THE HELL OUT OF HERE!
				pass

			else:
				metadata_count = readU16(node_meta_list)

				for _ in range(metadata_count):
					posObj = posFromInt(readU16(node_meta_list), self.mapblocksize)
					pos = posObj.getAsInt()
					self.node_meta[pos] = NodeMetaRef(posObj)

					num_vars = readU32(node_meta_list)
					for _ in range(num_vars):
						key_len = readU16(node_meta_list)
						key = "".join([chr(readU8(node_meta_list)) for _ in range(key_len)])

						val_len = readU32(node_meta_list)
						val = [readU8(node_meta_list) for _ in range(val_len)]
						self.node_meta[pos].set_raw(key, val)

					self.node_meta[pos].get_inventory().from_string(getSerializedInventory(node_meta_list))

		# We skip node_timers for now, not used in v23, v24 never released, and v25 has them later

		# u8 static_object_version
		self.static_object_version = readU8(data)

		# u16 static_object_count
		self.static_object_count = readU16(data)

		self.static_objects = []
		for _ in range(self.static_object_count):
			# u8 type
			otype = readU8(data)

			# s32 pos_x_nodes
			pos_x_nodes = readS32(data) / 10000

			# s32 pos_y_nodes
			pos_y_nodes = readS32(data) / 10000

			# s32 pos_z_nodes
			pos_z_nodes = readS32(data) / 10000


			# u8 [u16 data_size] data
			odata = [ readU8(data) for _ in range(readU16(data)) ]

			self.static_objects.append({
				"type": otype,
				"pos": Pos(pos_x_nodes + self.mapblockpos.x,pos_y_nodes + self.mapblockpos.y, pos_z_nodes + self.mapblockpos.z),
				"data": str(odata),
			})

		# u32 timestamp
		self.timestamp = readU32(data)

		# u8 name_id_mapping_version
		self.name_id_mapping_version = readU8(data)

		# u16 num_name_id_mappings
		self.num_name_id_mappings = readU16(data)

		self.name_id_mappings = dict()
		for _ in range(self.num_name_id_mappings):
			# u16 id, u8 [u16 name_len] name
			id = readU16(data)
			name = "".join([ chr(readU8(data)) for _ in range(readU16(data)) ])
			self.name_id_mappings[id] = name

		if self.version == 25:
			# u8 single_timer_data_length
			self.single_timer_data_length = readU8(data)

			# u16 num_of_timers
			self.timer_counts = readU16(data)

			self.node_timers = dict()
			for _ in range(self.timer_counts):
				pos = posFromInt(readU16(data), 16).getAsTuple()
				timeout = readS32(data) / 1000
				elapsed = readS32(data) / 1000
				self.node_timers[pos] = NodeTimerRef(Pos(0, 0, 0).fromTuple(pos), timeout, elapsed)

		for id in range(4096):
			itemstring = self.name_id_mappings[node_data["param0"][id]]
			param1 = node_data["param1"][id]
			param2 = node_data["param2"][id]
			pos = posFromInt(id, self.mapblocksize)
			pos.x += self.mapblockpos.x
			pos.z += self.mapblockpos.z
			pos.y += self.mapblockpos.y
			self.nodes[id] = Node(itemstring, param1 = param1, param2 = param2, pos = pos)

		# EOF!
		self.loaded = True

	def get_meta(self, abspos):
		self.check_pos(abspos)

		return self.node_meta.get(abspos) or NodeMetaRef()


"""
	MapVessel
"""
class MapVessel:
	def __init__(self, mapfile, backend = "sqlite3"):
		self.mapfile = mapfile
		self.open(mapfile, backend)

	def __str__(self):
		return "mapfile vessel for {0}".format(self.mapfile)

	def get_all_mapblock_ids(self):
		try:
			self.cur.execute("SELECT \"pos\" from \"blocks\"")
		except _sql.OperationalError as err:
			raise MapError("Error retrieving all mapblock pos : {0}".format(err))

		return [id[0] for id in self.cur.fetchall()]

	def open(self, mapfile, backend = "sqlite3"):
		try:
			self.conn = _sql.connect(mapfile)
			self.cur = self.conn.cursor()
		except _sql.OperationalError as err:
			raise MapError("Error opening database : {0}".format(err))

	def close(self):
		self.conn.close()
		self.mapblocks = None
		self.mapfile = None
		self.cache = dict()

	def read(self, blockID):
		try:
			self.cur.execute("SELECT * from blocks where pos = {0}".format(blockID))
		except _sql.OperationalError as err:
			raise MapError(err)

		data = self.cur.fetchall()
		if len(data) == 1:
			logger.debug("Binary blob for mapblock {0} read".format(blockID))
			return data[0][1]

	def load(self, blockID):
		data = self.read(blockID)
		if not data:
			logger.debug("Mapblock {0} not found".format(blockID))
			return

		logger.debug("Building mapblock {0} from binary blob".format(blockID))
		return MapBlock(data, abspos = blockID)

	def write(self, blockID, data):
		try:
			self.cur.execute("REPLACE INTO `blocks` (`pos`, `data`) VALUES ({0}, ?)".format(blockID), [data])

		except _sql.OperationalError as err:
			raise MapError(err)
		logger.debug("Binary blob for mapblock {0} written".format(blockID))

	def commit(self):
		logger.debug("Committing on database")
		self.conn.commit()

	def remove(self, blockID):
		try:
			self.cur.execute("DELETE FROM `blocks` WHERE `pos` = ?", [blockID])
		except _sql.OperationalError as err:
			raise MapError(err)

	def empty_map(self):
		"""
		Delete the entire map's mapblocks
		Note : Removal of mapblocks in the database after the last commit is reversible until the next call to commit()
		"""

		logger.warning("WARNING: Emptying the entire map of its mapblocks")
		try:
			self.cur.execute("DELETE from `blocks` where pos or pos == 0")
		except _sql.OperationalError as err:
			raise MapError("Error while removing all mapblock : {0}".format(err))

class StackCache:
	def __init__(self):
		self.data = []

	def __contains__(self, val):
		return val in self.data

	def __delitem__(self, key):
		self.remove(key)

	def __getitem__(self, key):
		return self.data[key]

	def __iter__(self):
		return self.data.__iter__()

	def __len__(self):
		return len(self.data)

	def __str__(self):
		return str(self.data)

	def add(self, elem):
		while elem in self.data:
			self.data.remove(elem)
		self.data.append(elem)

	def remove(self, elem):
		while elem in self.data:
			self.data.remove(elem)

	def flush(self, elem):
		self.data = []

class MapInterface:
	def __init__(self, datafile, backend = "sqlite3"):
		self.datafile = datafile
		self.container = MapVessel(datafile, backend)
		self.max_cache_size = 100
		self.mapblocks = dict()
		self.cache_history = StackCache()
		self.mod_cache = StackCache()


	# Cache stuff
	def flag_mod(self, mapblockid):
		self.mod_cache.add(mapblockid)

	def unflag_mod(self, mapblockid):
		self.mod_cache.remove(mapblockid)

	def set_maxcachesize(self, size):
		if type(size) != type(0):
			raise TypeError("Invalid type for size: {0}".format(type(size)))

		self.max_cache_size = size
		logger.debug("MapVessel's maximum cache size set to {0}".format(size))
		self.check_cache()

	def get_maxcachesize(self):
		return self.max_cache_size

	def check_cache(self):
		while len(self.mapblocks) > self.max_cache_size:
			logger.debug("Removing mapblock {0} from cache to create space".format(self.cache_history[0]))
			self.unload_mapblock(self.cache_history[0])

	def flush_cache(self):
		self.save()
		while len(self.cache_history) > 0:
			logger.debug("Removing mapblock {id} for cache flush".format(id=self.cache_history[0]))
			self.unload_mapblock(self.cache_history[0])

	# Mapblock loading/unloading
	def load_mapblock(self, blockID):
		logger.debug("Loaded mapblock at {id}".format(id=blockID))
		data = self.container.load(blockID)
		if not data:
			logger.debug("Mapblock is None")
			return False

		self.mapblocks[blockID] = data
		self.cache_history.add(blockID)
		self.check_cache()
		return True

	def unload_mapblock(self, blockID):
		if blockID in self.mod_cache:
			logger.debug("Unloading and saving mapblock at pos {0}".format(blockID))
			self.save_mapblock(blockID)

		self.cache_history.remove(blockID)
		del self.mapblocks[blockID]

	def save_mapblock(self, blockID):
		if not self.mapblocks.get(blockID):
			return False

		logger.debug("Saving block at pos {0} {1}".format(blockID, posFromInt(blockID, 4096)))
		self.container.write(blockID, self.mapblocks[blockID].implode())

		self.mod_cache.remove(blockID)

		return True

	def init_mapblock(self, mapblockpos):
		logger.debug("Init mapblock at {0}".format(str(mapblockpos)))
		self.mapblocks[mapblockpos] = MapBlock(abspos = mapblockpos)
		self.mod_cache.add(mapblockpos)
		self.cache_history.add(mapblockpos)
		self.check_cache()

	# Node interface stuff
	def check_for_pos(self, mapblockpos):
		if not self.mapblocks.get(mapblockpos):
			return self.load_mapblock(mapblockpos)

		return True

	def get_node(self, pos):
		mapblock = determineMapBlock(pos)
		mapblockpos = getMapBlockPos(mapblock)
		if not self.check_for_pos(mapblockpos):
			return Node("ignore", pos = pos)

		return self.mapblocks[mapblockpos].get_node(Pos(pos.x % 16, pos.y % 16, pos.z % 16).getAsInt())

	def set_node(self, pos, node):
		mapblock = determineMapBlock(pos)
		mapblockpos = getMapBlockPos(mapblock)
		if not self.check_for_pos(mapblockpos):
			raise IgnoreContentReplacementError("Pos: {0}".format(pos))

		node.pos = pos
		self.flag_mod(mapblockpos)

		return self.mapblocks[mapblockpos].set_node(Pos(pos.x % 16, pos.y % 16, pos.z % 16).getAsInt(), node)

	def remove_node(self, pos):
		return self.set_node(self, pos, Node("air"))

	def get_meta(self, pos):
		mapblock = determineMapBlock(pos)
		mapblockpos = getMapBlockPos(mapblock)
		self.flag_mod(mapblockpos) # Just in case, we don't know if metadata will be modified
		if not self.check_for_pos(mapblockpos):
			return NodeMetaRef()

		return self.mapblocks[mapblockpos].get_meta(pos.getAsInt())

	# The schematics stuff
	def export_schematic(self, startpos, endpos, forceplace = True):

		# Get the corners first
		minpos = Pos(min(startpos.x, endpos.x), min(startpos.y, endpos.y), min(startpos.z, endpos.z))
		maxpos = Pos(max(startpos.x, endpos.x), max(startpos.y, endpos.y), max(startpos.z, endpos.z))

		schem = {}
		schem["size"] = {"x": maxpos.x - minpos.x, "y": maxpos.y - minpos.y, "z": maxpos.z - minpos.y}
		schem["data"] = {}
		for x in range(schem["size"]["x"]):
			for y in range(schem["size"]["y"]):
				for z in range(schem["size"]["z"]):
					schem["data"][x + (y * schem["size"]["x"]) + (z * schem["size"]["y"] * schem["size"]["x"])] = {
						"name": self.get_node(Pos(minpos.x + x, minpos.y + y, minpos.z + z)).get_name(),
						"prob": 255,
						"force_place": forceplace
					}

		sch = Schematic()
		sch.serialize_schematic(schem)

		return sch

	def import_schematic(self, pos, schematic, stage_save=0):
		k = schematic.size["x"] * schematic.size["y"] * schematic.size["z"]
		tenth = 0
		for y in range(schematic.size["y"]):
			for x in range(schematic.size["x"]):
				for z in range(schematic.size["z"]):
					v = Vector()
					rpos = Pos(x, y, z)
					pct = (1 + z + (x * schematic.size["z"]) + (y * schematic.size["z"] * schematic.size["x"])) / k * 100
					node = schematic.get_node(rpos)
					vpos = v.add(pos, rpos)
					pctstr = "[{0:3.5f}%] Placing nodes..".format(pct)

					while True:
						try:
							self.set_node(vpos, node)
							break
						except IgnoreContentReplacementError:
							self.init_mapblock(getMapBlockPos(determineMapBlock(v.add(pos, rpos))))
							continue
						logger.debug(pctstr)
						if stage_save and int(pct/stage_save) != tenth:
							tenth = int(pct/stage_save)
							logger.debug("Saving partial import at {0:3.5f}%..".format(pct))
							logger.debug("{0} mapblocks to save".format(len(self.mod_cache)))
							self.save()

	# Method to save
	def save(self):
		logger.debug("Saving..")
		while len(self.mod_cache) > 0:
			logger.debug("{0} mapblocks left to save".format(len(self.mod_cache)))
			u = self.mod_cache[0]
			self.save_mapblock(u)
			self.unload_mapblock(u)

		self.container.commit()
