#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
######################################
## Configuration for Python-Minetest
##
#

import os

#from errors import ConfigurationFormatError

class Configuration:
	def __init__(self, file):
		self.data = dict()
		self.read(file)
		self.file = file

	def __contains__(self, key):
		return key in self.data

	def __getitem__(self, key):
		return self.data.get(key)

	def __delitem__(self, key):
		del self.data[key]

	def __len__(self):
		return len(self.data)

	def __setitem__(self, key, val):
		self.data[key] = val


	def read(self, file=None):
		buffer = open(file or self.file)
		for line in buffer.readlines():
			line = line.strip("\r\n")
			k = line.split("=")

			if len(k) < 2:
				continue

			data = " = ".join(k[1:]).strip()

			if data == "true" or data == "1":
				data = True

			elif data == "false" or data == "0":
				data = False

			self.data[k[0].strip()] = data

	def write(self, file=None):
		try:
			f = open(file or self.file, "w")
		except Exception as err:
			return None

		for key in self.data:
			f.write("{0} = {1}\n".format(key, self.data[key]))

		f.close()
		return True

	@classmethod
	def open_world(cls, dir):
		try:
			open(dir + "/world.mt")
		except Exception as err:
			return None

		return cls(dir + "/world.mt")
