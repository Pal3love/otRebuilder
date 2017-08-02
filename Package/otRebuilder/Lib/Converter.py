#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)

from fontTools.ttLib import newTable
from fontTools.pens.ttGlyphPen import TTGlyphPen
from cu2qu.pens import Cu2QuPen

from otRebuilder.Lib import Workers


class Converter(Workers.Worker):

    def __init__(self, ttfontObj, jobsObj):
        super(Converter, self).__init__(ttfontObj, jobsObj)

    def otf2ttf(self, maxErr = 1.0, postFormat = 2.0, reverseDirection = True):
        # Arguments:
        # maxErr = 1.0, approximation error, measured in units per em (UPM).
        # postFormat = 2.0, default `post` table format.
        # reverseDirection = True, assuming the input contours' direction is correctly set (counter-clockwise), we just flip it to clockwise.
        if self.font.sfntVersion != "OTTO" or not self.font.has_key("CFF ") or not self.font.has_key("post"):
            print("WARNING: Invalid CFF-based font. --otf2ttf is now ignored.", file = sys.stderr)
            self.jobs.convert_otf2ttf = False
            return
        # Conversion process
        quadGlyphs = {}
        glyphOrder = self.font.getGlyphOrder()
        glyphSet = self.font.getGlyphSet()
        for glyphName in glyphSet.keys():
            glyph = glyphSet[glyphName]
            ttPen = TTGlyphPen(glyphSet)
            cu2quPen = Cu2QuPen(ttPen, maxErr, reverseDirection)
            glyph.draw(cu2quPen)
            quadGlyphs[glyphName] = ttPen.glyph()
        # Create quadratic `glyf` table
        glyf = newTable("glyf")
        glyf.glyphOrder = glyphOrder
        glyf.glyphs = quadGlyphs
        self.font["glyf"] = glyf
        # Create partial `maxp` table
        maxp = newTable("maxp")
        maxp.tableVersion = 0x00010000
        maxp.maxZones = 1
        maxp.maxTwilightPoints = 0
        maxp.maxStorage = 0
        maxp.maxFunctionDefs = 0
        maxp.maxInstructionDefs = 0
        maxp.maxStackElements = 0
        maxp.maxSizeOfInstructions = 0
        maxp.maxComponentElements = max(
            len(g.components if hasattr(g, "components") else [])
            for g in glyf.glyphs.values())
        self.font["maxp"] = maxp
        # Modify `post` table
        post = self.font["post"]
        post.formatType = postFormat
        post.extraNames = []
        post.mapping = {}
        post.glyphOrder = glyphOrder
        # Create an empty `loca` table, which will be automatically generated upon compile
        self.font["loca"] = newTable("loca")
        # Change sfntVersion from CFF to TrueType
        self.font.sfntVersion = "\x00\x01\x00\x00"
        # Recalculate missing properties in `glyf`, `maxp` and `head` upon compile
        self.font.recalcBBoxes = True
        # Clean-ups
        del self.font["CFF "]
        if self.font.has_key("VORG"):
            del self.font["VORG"]
        return

