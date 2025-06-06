from ...utils.HelperFunctions import *
from PyQt5 import QtGui, QtCore, QtWidgets
from enum import Enum
import yaml
import os
import numpy as np


class FlatlandFootprint():
    def __init__(self):
        self.layers = []
        self.collision = True
        self.density = 1.0

    def __eq__(self, other):
        if not isinstance(other, FlatlandFootprint):
            return NotImplemented

        return (self.layers == other.layers
                and self.collision == other.collision
                and np.allclose(self.density, other.density))

    @staticmethod
    def fromDict(d: dict):
        fp = FlatlandFootprint()
        # fill inherited class fields
        if d["type"] == "polygon":
            fp = PolygonFlatlandFootprint.fromDict(d)
        elif d["type"] == "circle":
            fp = CircleFlatlandFootprint.fromDict(d)
        else:
            raise Exception("unknown footprint type.")

        # fill base class fields
        if "layers" in d:
            fp.layers = d["layers"]
        if "collision" in d:
            fp.collision = d["collision"]
        if "density" in d:
            fp.density = float(d["density"])

        return fp

    def toDict(self):
        d = {}
        d["layers"] = self.layers
        d["collision"] = self.collision
        d["density"] = self.density
        return d


class CircleFlatlandFootprint(FlatlandFootprint):
    def __init__(self):
        super().__init__()
        self.center = [0.0, 0.0]
        self.radius = 0.5

    def __eq__(self, other):
        if not isinstance(other, CircleFlatlandFootprint):
            return NotImplemented

        return (super().__eq__(other)
                and np.allclose(self.center, other.center)
                and np.allclose(self.radius, other.radius))

    @staticmethod
    def fromDict(d: dict):
        fp = CircleFlatlandFootprint()
        if "center" in d:
            fp.center = [float(val) for val in d["center"]]
        if "radius" in d:
            fp.radius = float(d["radius"])
        return fp

    def toDict(self):
        d = super().toDict()
        d["center"] = self.center
        d["radius"] = self.radius
        d["type"] = "circle"
        return d


class PolygonFlatlandFootprint(FlatlandFootprint):
    def __init__(self):
        super().__init__()
        self.points = []

    def __eq__(self, other):
        if not isinstance(other, PolygonFlatlandFootprint):
            return NotImplemented

        if len(self.points) != len(other.points):
            return False

        return (super().__eq__(other)
                and np.allclose(self.points, other.points))

    @staticmethod
    def fromDict(d: dict):
        fp = PolygonFlatlandFootprint()
        if "points" in d:
            fp.points = [[float(point[0]), float(point[1])] for point in d["points"]]
        return fp

    def toDict(self):
        d = super().toDict()
        d["points"] = self.points
        d["type"] = "polygon"
        return d


class FlatlandObject():
    def __init__(self, name: str = ""):
        self.name = name
        self.pos = np.zeros(2)
        self.angle = 0.0

    @staticmethod
    def fromDict(d: dict):
        o = FlatlandObject()
        o.loadFromDict(d)
        return o

    def loadFromDict(self, d: dict):
        self.name = d["name"]
        self.pos = np.array([float(val) for val in d["pos"]])
        self.angle = float(d["angle"])

    def toDict(self):
        d = {}
        d["name"] = self.name
        d["pos"] = [float(val) for val in self.pos]
        d["angle"] = round(normalize_angle(self.angle), 3)
        return d
