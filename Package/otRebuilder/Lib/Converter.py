#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)

from fontTools.ttLib import newTable
from fontTools.misc.transform import Scale
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.pens.transformPen import TransformPen
from fontTools.ttLib.tables.ttProgram import Program
from cu2qu.pens import Cu2QuPen

from otRebuilder.Lib import Workers


class Converter(Workers.Worker):

    def __init__(self, ttfontObj, jobsObj):
        super(Converter, self).__init__(ttfontObj, jobsObj)

    def otf2ttf(self, maxErr = 1.0, postFormat = 2.0, reverseDirection = True, targetUPM = 2048):
        # Arguments:
        # maxErr = 1.0, approximation error, measured in units per em (UPM).
        # postFormat = 2.0, default `post` table format.
        # reverseDirection = True, assuming the input contours' direction is correctly set (counter-clockwise), we just flip it to clockwise.
        # targetUPM = 2048, default UPM for the new generated TrueType font. For TrueType format it should be the power of 2, from 16 to 16384.
        if self.font.sfntVersion != "OTTO" or not self.font.has_key("CFF ") or not self.font.has_key("post"):
            print("WARNING: Invalid CFF-based font. --otf2ttf is now ignored.", file = sys.stderr)
            self.jobs.convert_otf2ttf = False
            return

        # Calculate scaling factor between the old and new UPM
        upmOld = self.font["head"].unitsPerEm
        upmNew = int(targetUPM)
        if upmNew < 16 or upmNew > 16384:
            print("WARNING: Invalid UPM value. Default value (2048) would be applied.", file = sys.stderr)
            upmNew = 2048
        scaleFactor = upmNew / upmOld  # Get float because __future__.division has been imported

        # Conversion: cubic to quadratic
        quadGlyphs = {}
        glyphOrder = self.font.getGlyphOrder()
        glyphSet = self.font.getGlyphSet()
        for glyphName in glyphSet.keys():
            glyph = glyphSet[glyphName]
            ttPen = TTGlyphPen(glyphSet)
            cu2quPen = Cu2QuPen(ttPen, maxErr, reverseDirection)
            scalePen = TransformPen(cu2quPen, Scale(scaleFactor, scaleFactor))
            glyph.draw(scalePen)
            quadGlyphs[glyphName] = ttPen.glyph()

        # Create quadratic `glyf` table
        glyf = newTable("glyf")
        glyf.glyphOrder = glyphOrder
        glyf.glyphs = quadGlyphs
        self.font["glyf"] = glyf

        # Create global instruction table `prep` with basic rendering settings
        hintProg = Program()
        hintProg.fromBytecode([184, 1, 255, 133, 184, 0, 4, 141])
        prep = newTable("prep")
        prep.program = hintProg
        self.font["prep"] = prep

        # Create `gasp` table
        gasp = newTable("gasp")
        gasp.version = 1
        gasp.gaspRange = {65535: 10}
        self.font["gasp"] = gasp

        # Create partial TrueType `maxp` table (v1.0)
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

        # Create an empty `loca` table, which will be automatically generated upon compile
        self.font["loca"] = newTable("loca")

        # Modify `post` table
        post = self.font["post"]
        post.formatType = postFormat
        post.extraNames = []
        post.mapping = {}
        post.glyphOrder = glyphOrder

        # Update tables to apply the new UPM
        self.__applyNewUPM(upmOld, upmNew)

        # Change sfntVersion from CFF to TrueType
        self.font.sfntVersion = "\x00\x01\x00\x00"

        # Recalculate missing properties in `head`, `glyf`, `maxp` upon compile
        self.font.recalcBBoxes = True

        # Clean-ups
        del self.font["CFF "]
        if self.font.has_key("VORG"):
            del self.font["VORG"]
        return

    # Affected tables: `head`, `hhea`, `hmtx`, `kern`, `maxp`, `post`, `vhea`, `vmtx`, `OS/2`, `BASE`
    # ---- TODO: OpenType layout tables: `GPOS`, `JSTF`, `MATH` ----
    def __applyNewUPM(self, upmOld, upmNew):
        scaleFactor = upmNew / upmOld
        
        # Get font tables
        head = self.font.get("head")
        hhea = self.font.get("hhea")
        hmtx = self.font.get("hmtx")
        kern = self.font.get("kern")
        # `maxp` will be regenerated and recalculated
        post = self.font.get("post")
        vhea = self.font.get("vhea")
        vmtx = self.font.get("vmtx")
        OS2f2 = self.font.get("OS/2")
        BASE = self.font.get("BASE")

        # Deal with tables
        if head:
            head.unitsPerEm = upmNew
            head.xMin = int(round(head.xMin * scaleFactor))
            head.yMin = int(round(head.yMin * scaleFactor))
            head.xMax = int(round(head.xMax * scaleFactor))
            head.yMax = int(round(head.yMax * scaleFactor))
        if kern:
            for subtable in kern.kernTables:
                for pair in subtable.kernTable.keys():
                    subtable.kernTable[pair] = int(round(subtable.kernTable[pair] * scaleFactor))
        if hhea:
            hhea.ascent = int(round(hhea.ascent * scaleFactor))
            hhea.descent = int(round(hhea.descent * scaleFactor))
            hhea.lineGap = int(round(hhea.lineGap * scaleFactor))
            hhea.advanceWidthMax = int(round(hhea.advanceWidthMax * scaleFactor))
            hhea.minLeftSideBearing = int(round(hhea.minLeftSideBearing * scaleFactor))
            hhea.minRightSideBearing = int(round(hhea.minRightSideBearing * scaleFactor))
            hhea.xMaxExtent = int(round(hhea.xMaxExtent * scaleFactor))
            # caretSlopeRise and caretSlopeRun are used to get the cursor slope.
            # The slope doesn't change no matter what the scale factor changes.
            hhea.caretOffset = int(round(hhea.caretOffset * scaleFactor))
        if vhea:
            vhea.ascent = int(round(vhea.ascent * scaleFactor))
            vhea.descent = int(round(vhea.descent * scaleFactor))
            vhea.lineGap = int(round(vhea.lineGap * scaleFactor))
            vhea.advanceHeightMax = int(round(vhea.advanceHeightMax * scaleFactor))
            vhea.minTopSideBearing = int(round(vhea.minTopSideBearing * scaleFactor))
            vhea.minBottomSideBearing = int(round(vhea.minBottomSideBearing * scaleFactor))
            vhea.yMaxExtent = int(round(vhea.yMaxExtent * scaleFactor))
            # caretSlopeRise and caretSlopeRun are used to get the cursor slope.
            # The slope doesn't change no matter what the scale factor changes.
            vhea.caretOffset = int(round(vhea.caretOffset * scaleFactor))
        if hmtx:
            for glyfName in hmtx.metrics.keys():
                # Type tuple; [0]: advance width; [1]: lsb
                tempVal0 = int(round(hmtx.metrics[glyfName][0] * scaleFactor))
                tempVal1 = int(round(hmtx.metrics[glyfName][1] * scaleFactor))
                hmtx.metrics[glyfName] = (tempVal0, tempVal1)
        if vmtx:
            for glyfName in vmtx.metrics.keys():
                # Type tuple; [0]: advance width; [1]: lsb
                tempVal0 = int(round(vmtx.metrics[glyfName][0] * scaleFactor))
                tempVal1 = int(round(vmtx.metrics[glyfName][1] * scaleFactor))
                vmtx.metrics[glyfName] = (tempVal0, tempVal1)
        if post:
            post.underlinePosition = int(round(post.underlinePosition * scaleFactor))
            post.underlineThickness = int(round(post.underlineThickness * scaleFactor))
        if OS2f2:
            OS2f2.xAvgCharWidth = int(round(OS2f2.xAvgCharWidth * scaleFactor))
            OS2f2.ySubscriptXSize = int(round(OS2f2.ySubscriptXSize * scaleFactor))
            OS2f2.ySubscriptYSize = int(round(OS2f2.ySubscriptYSize * scaleFactor))
            OS2f2.ySubscriptXOffset = int(round(OS2f2.ySubscriptXOffset * scaleFactor))
            OS2f2.ySubscriptYOffset = int(round(OS2f2.ySubscriptYOffset * scaleFactor))
            OS2f2.ySuperscriptXSize = int(round(OS2f2.ySuperscriptXSize * scaleFactor))
            OS2f2.ySuperscriptYSize = int(round(OS2f2.ySuperscriptYSize * scaleFactor))
            OS2f2.ySuperscriptXOffset = int(round(OS2f2.ySuperscriptXOffset * scaleFactor))
            OS2f2.ySuperscriptYOffset = int(round(OS2f2.ySuperscriptYOffset * scaleFactor))
            OS2f2.yStrikeoutSize = int(round(OS2f2.yStrikeoutSize * scaleFactor))
            OS2f2.yStrikeoutPosition = int(round(OS2f2.yStrikeoutPosition * scaleFactor))
            OS2f2.sTypoAscender = int(round(OS2f2.sTypoAscender * scaleFactor))
            OS2f2.sTypoDescender = int(round(OS2f2.sTypoDescender * scaleFactor))
            OS2f2.sTypoLineGap = int(round(OS2f2.sTypoLineGap * scaleFactor))
            OS2f2.usWinAscent = int(round(OS2f2.usWinAscent * scaleFactor))
            OS2f2.usWinDescent = int(round(OS2f2.usWinDescent * scaleFactor))
            if OS2f2.version > 1:
                OS2f2.sxHeight = int(round(OS2f2.sxHeight * scaleFactor))
                OS2f2.sCapHeight = int(round(OS2f2.sCapHeight * scaleFactor))

        # Deal with OpenType layout tables
        if BASE and hasattr(BASE, "table") and BASE.table:
            if hasattr(BASE.table, "HorizAxis"):
                self.__applyNewUPM_handleOTaxis(BASE.table.HorizAxis, scaleFactor)
            if hasattr(BASE.table, "VertAxis"):
                self.__applyNewUPM_handleOTaxis(BASE.table.VertAxis, scaleFactor)
        return

    def __applyNewUPM_handleOTaxis(self, otAxis, scaleFactor):
        if not otAxis or \
            not hasattr(otAxis, "BaseScriptList") or \
            not hasattr(otAxis.BaseScriptList, "BaseScriptRecord") or \
            not otAxis.BaseScriptList.BaseScriptRecord:
            return
        for record in otAxis.BaseScriptList.BaseScriptRecord:
            if hasattr(record, "BaseScript") and record.BaseScript:
                if hasattr(record.BaseScript, "DefaultMinMax") and record.BaseScript.DefaultMinMax:
                    # -- TODO: Learn the data structure here, which in most case is None --
                    pass
                if hasattr(record.BaseScript, "BaseValues") and \
                    hasattr(record.BaseScript.BaseValues, "BaseCoord") and \
                    record.BaseScript.BaseValues.BaseCoord:
                    for coord in record.BaseScript.BaseValues.BaseCoord:
                        if isinstance(coord.Coordinate, int) or isinstance(coord.Coordinate, float):
                            coord.Coordinate = int(round(coord.Coordinate * scaleFactor))
        return

