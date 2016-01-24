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

from errors import MapError, EmptyMapVesselError, UnknownMetadataTypeIDError, InvalidParamLengthError
from utils import readU8, readU16, readU32, readS32, Pos, posFromInt
from metadata import NodeMetaRef
from inventory import getSerializedInventory
from nodes import NodeTimerRef

# Bitmask constants
IS_UNDERGROUND = 1
DAY_NIGHT_DIFFERS = 2
LIGHTING_EXPIRED = 4
GENERATED = 8

class MapBlock:
    def __init__(self, data = None):
        if data:
            self.explode(data)
        else:
            self.version = 0
            self.bitmask = b"08"
            self.content_width = 2
            self.param_width = 2
            self.node_data = dict()
            self.node_meta = dict()
            self.node_timers = dict()
            self.static_object_version = 0 #u8
            self.static_object_count = 0 #u16
            self.static_objects = [] #u8, s32, s32, s32, u16, u8
            self.timestamp = 0 #u32
            self.name_id_mapping_version = 0 #u8
            self.num_name_id_mappings = 0 #u16
            self.name_id_mappings = dict() #u16, u8[u16]
            self.single_timer_data_length = 10 #u8
            self.timer_counts = 0 #u16
            self.timers = dict() #u16, s32, s32

    def explode(self, bytelist):
        data = BytesIO(bytelist)

        self.mapblocksize = 16 # Normally
        self.version = readU8(data)
        self.bitmask = readU8(data)
        self.content_width = readU8(data)
        self.param_width = readU8(data)

        self.node_data = dict()

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

        self.node_data["param0"] = [ int(b) for b in c_width_data.read(4096 * self.content_width) ]
        self.node_data["param1"] = [ int(b) for b in c_width_data.read(4096) ]
        self.node_data["param2"] = [ int(b) for b in c_width_data.read(4096) ]

        try:
            assert(len(self.node_data["param0"]) == 4096 * self.content_width)
            assert(len(self.node_data["param1"]) == 4096)
            assert(len(self.node_data["param2"]) == 4096)
        except AssertError:
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
            self.metadata_count = readU16(node_meta_list)

            for i in range(self.metadata_count):
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
                    self.node_meta[pos].get_inventory().from_list(getSerializedInventory(node_meta_list))


                elif type_id == 17:
                    # Locked Chest metadata

                    # u8 [u16 len] owner
                    self.node_meta[pos].set_raw("owner", "".join([ readU8(node_meta_list) for _ in range(readU16(node_meta_list)) ]))

                    # serialized inventory
                    self.node_meta[pos].get_inventory().from_list(getSerializedInventory(node_meta_list))

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
                self.metadata_count = readU16(node_meta_list)

                for _ in range(self.metadata_count):
                    pos = posFromInt(readU16(node_meta_list), self.mapblocksize).getAsTuple()
                    self.node_meta[pos] = NodeMetaRef(pos)

                    num_vars = readU32(node_meta_list)
                    for _ in range(num_vars):
                        key_len = readU16(node_meta_list)
                        key = "".join([chr(readU8(node_meta_list)) for _ in range(key_len)])

                        val_len = readU32(node_meta_list)
                        val = [readU8(node_meta_list) for _ in range(val_len)]
                        self.node_meta[pos].set_raw(key, val)

                    self.node_meta[pos].get_inventory().from_list(getSerializedInventory(node_meta_list))

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
                "pos": Pos({'x': pos_x_nodes, 'y': pos_y_nodes, 'z': pos_z_nodes}),
                "data": odata,
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
            name = [ readU8(data) for _ in range(readU16(data)) ]
            self.name_id_mappings[id] = name

        if self.version == 25:
            # u8 single_timer_data_length
            self.single_timer_data_length = readU8(data)

            # u16 num_of_timers
            self.timer_counts = readU16(data)

            self.timers = dict()
            for _ in range(self.timer_counts):
                pos = posFromInt(readU16(data), 16).getAsTuple()
                timeout = readS32(data) / 1000
                elapsed = readS32(data) / 1000
                self.timers[pos] = NodeTimerRef(pos, timeout, elapsed)

        # EOF!

class MapVessel:
    def __init__(self, mapfile, backend = "sqlite3"):
        self.mapfile = mapfile
        self.cache = dict()
        self.open(mapfile, backend)

    def __str__(self):
        if self.isEmpty():
            return "empty mapfile vessel"
        else:
            return "mapfile vessel for {0}".format(self.mapfile)

    def isEmpty(self):
        return self.mapfile == None

    def open(self, mapfile, backend = "sqlite3"):
        try:
            self.conn = _sql.connect(mapfile)
            self.cur = self.conn.cursor()
        except _sql.OperationalError as err:
            raise MapError("Error opening database : {0}".format(err))

    def close(self):
        self.conn.close()
        self.cache = None
        self.mapfile = None

    def read(self, blockID):
        if self.isEmpty():
            raise EmptyMapVesselError()

        if self.cache.get(blockID):
            return False, "dejavu"

        try:
            self.cur.execute("SELECT * from blocks where pos = {0}".format(blockID))
        except _sql.OperationalError as err:
            raise MapError(err)

        data = self.cur.fetchall()
        if len(data) == 1:
            self.cache[blockID] = data[0][1]
            return True, "ok"
        else:
            return False, "notfound"

    def uncache(self, blockID):
        if self.isEmpty():
            raise EmptyMapVesselError()

        self.cache[blockID] = None
        del self.cache[blockID]
        return True, "ok"

    def write(self, blockID):
        if self.isEmpty():
            raise EmptyMapVesselError()

        if not self.cache.get(blockID):
            return False, "notread"

        try:
            self.cur.execute("REPLACE INTO 'blocks' ('pos', 'data') VALUES ({0}, ?)".format(blockID),
                [self.cache[blockID]])
        except _sql.OperationalError as err:
            raise MapError(err)

    def load(self, blockID):
        if self.isEmpty():
            raise EmptyMapVesselError()

        if not self.cache.get(blockID):
            return False, "notread"

        return MapBlock(self.cache[blockID])
