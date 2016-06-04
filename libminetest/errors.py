#!/usr/bin/env python3
# -*- encoding: utf-8 -*-
###########################
## Rrrors for Python-MT
##
##
#


class MinetestException(Exception):
    pass

##=========================================##
# 1. Map errors

class MapError(MinetestException):
    "Generic map exception"
    pass

class EmptyMapVesselError(MinetestException):
    "Exception raised when one tries using a MapVessel without loading any database in first"
    __cause__ = "Tried to use empty mapfile vessel"

class UnknownMetadataTypeIDError(MapError):
    "Exception raised when the deserialization process finds an unknown type of metadata"
    pass

class InvalidParamLengthError(MapError):
    "Exception raised when either the serialization or the deserialization process is started upon a mapblock with an invalid paramlength field"
    pass

class EmptyMapBlockError(MapError):
    """Exception raised when one tries to use a MapBlock with no data in.
       Note: This exception will probably be removed since empty MapBlocks are not really a thing any more"""
    pass

class IgnoreContentReplacementError(MapError):
    "Exception raised when one tries to place a node where the land was not generated. You can use MapInterface.init_mapblock to initialize an empty one"
    pass

##=========================================##
# 2. Containers Errors
class ContainerError(MinetestException):
    "Generic container exception"
    __cause__ = "Error in container"

class OutOfBordersCoordinates(ContainerError):
    "Exception raised when one tries to place/get a node out of the borders of a container, it being a MapBlock, or a MapInterface"
    __cause__ = "Coordinates out of borders"

##=========================================##
# 3. Inventory Errors

class InventoryError(MinetestException):
    "Generic inventory exception"
    __cause__ = "Inventory Error"

class InventoryDeserializationError(InventoryError):
    "Exception raised when one tries to deserialize an invalid inventory string representation"
    pass

##=========================================##
# 4. Schematic Errors

class SchematicError(MinetestException):
    "Generic schematic exception"
    __cause__ = "Error with schematic"

class InvalidSchematicSignature(SchematicError):
    "Exception raised when an invalid signature is detected upon reading a Schematic file"
    pass
