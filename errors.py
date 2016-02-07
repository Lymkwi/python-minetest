#!/usr/bin/env python3
# -*- encoding: utf8 -*-
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
    pass

class EmptyMapVesselError(MinetestException):
    __cause__ = "Tried to use empty mapfile vessel"

class UnknownMetadataTypeIDError(MapError):
    pass

class InvalidParamLengthError(MapError):
    pass

class EmptyMapBlockError(MapError):
    pass

class IgnoreContentReplacementError(MapError):
    pass

##=========================================##
# 2. Containers Errors
class ContainerError(MinetestException):
    __cause__ = "Error in container"

class OutOfBordersCoordinates(ContainerError):
    __cause__ = "Coordinates out of borders"

##=========================================##
# 3. Inventory Errors

class InventoryError(MinetestException):
    __cause__ = "Inventory Error"

class InventoryDeserializationError(InventoryError):
    pass
