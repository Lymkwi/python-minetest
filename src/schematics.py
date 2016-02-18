#!/usr/bin/env python3
# -*- encoding: utf8 -*-
###########################
## Schematics for Python-MT
##
##
#

from nodes import Node
from utils import readU16, readU8, readU32, writeU16, writeU8, writeU32

import zlib
from io import BytesIO

# See :
# https://github.com/minetest/minetest/blob/master/src/mg_schematic.cpp#L339
# https://github.com/minetest/minetest/blob/master/src/mapnode.cpp#L548
# https://github.com/minetest/minetest/blob/master/src/mg_schematic.cpp#L260

# Quick spec for ver4
"""
u32 signature (= b"MTSM")
u16 version?
u16 size_x
u16 size_y
u16 size_z

foreach size_y:
	u8 slice_prob

u16 num_names
foreach num_names:
	u16 name_len
	u8[name_len] name

zlib encrypted mapnode bulk data (see src/mapnode.cpp)
foreach size_x * size_y * size_z:
	u16 param0

foreach size_x * size_y * size_z:
	u8 param1

foreach size_x * size_y * size_z:
	u8 param2
"""

# Definitions

class Schematic:
	def __init__(self, filename = None):
		self.filename = filename
		self.loaded = False
		self._init_data()
		if self.filename:
			self.load_from_file(filename)

	def _init_data(self):
		self.version = -1
		self.size = {}
		self.y_slice_probs = {}
		self.nodes = []
		self.data = {}

	def load(self, data):
		self._init_data()
		self.loaded = False

		try:
			assert(data.read(4) == b"MTSM")
		except AssertionError:
			print("ERROR: {0} couldn't load schematic from data : invalid signature".format(self))
			return

		self.version = readU16(data)
		self.size = {"x": readU16(data), "y": readU16(data), "z": readU16(data)}

		for i in range(self.size["y"]):
			p = readU8(data)
			if p < 127:
				self.y_slice_probs[i] = p

		for _ in range(readU16(data)):
			nodename = ""
			for _ in range(readU16(data)):
				nodename += chr(readU8(data))
			self.nodes.append(nodename)


		bulk = BytesIO(zlib.decompress(data.read()))
		nodecount = self.size["x"] * self.size["y"] * self.size["z"]
		self.data = {}
		for i in range(nodecount):
			self.data[i] = Node(self.nodes[readU16(bulk)])

		for i in range(nodecount):
			self.data[i].set_param1(readU8(bulk))

		for i in range(nodecount):
			self.data[i].set_param2(readU8(bulk))

		self.loaded = True

	def export(self):
		if not self.loaded:
			return

		data = BytesIO(b"")

		data.write(b"MTSM")
		writeU16(data, self.version)

		writeU8(data, self.size["x"])
		writeU8(data, self.size["y"])
		writeU8(data, self.size["z"])

		for u in range(self.size["y"]):
			p = self.y_slice_probs.get(u) or 127
			writeU8(data, p)

		writeU16(data, len(self.nodes))
		for node in self.nodes:
			writeU16(data, len(node))
			for c in node:
				writeU8(data, ord(c))

		bulk = BytesIO(b"")
		nodecount = self.size["x"] * self.size["y"] * self.size["z"]
		for i in range(nodecount):
			writeU16(bulk, self.nodes.index(self.data[i].get_name()))

		for i in range(nodecount):
			writeU8(bulk, self.data[i].get_param1())

		for i in range(nodecount):
			writeU8(bulk, self.data[i].get_param2())

		bulk.seek(0)
		data.write(zlib.compress(bulk.read()))
		data.seek(0)

		return data

	def load_from_file(self, filename):
		try:
			ifile = open(filename, "rb")
		except Exception as err:
			print("ERROR: {0} couldn't open file {1} : {2}".format(self, filename, err))
			return

		self.load(ifile)

	def export_to_file(self, filename):
		try:
			ofile = open(filename, "wb")
		except Exception as err:
			print("ERROR: {0} couldn't open file {1} : {2}".format(self, filename, err))
			return

		ofile.write(self.export().read())

	def serialize_schematic(self, schemtab):
		self._init_data()

		self.version = 4
		self.size = schemtab["size"]

		if schemtab.get("y_slice_probs"):
			for prob in schemtab["y_slice_probs"]:
				self.y_slice_probs[prob[0]] = prob[1]

		for index in schemtab["data"]:
			entry = schemtab["data"][index]

			if not entry["name"] in self.nodes:
				self.nodes.append(entry["name"])

			self.data[index] = Node(entry["name"], param1 = entry["prob"], param2 = entry.get("param2") or 0)
			if not entry.get("force_place"):
				self.data[index].set_param1(int(entry["prob"] / 2))

		self.loaded = True

	def get_node(self, pos):
		if not self.loaded:
			return

		if pos.x > self.size["x"] or pos.y > self.size["y"] or pos.z > self.size["z"]:
			return

		abspos = pos.x + (pos.y * self.size["x"]) + (pos.z * self.size["y"] * self.size["x"])
		return self.data[abspos]
