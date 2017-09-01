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

    def otf2ttf(self, maxErr = 1.0, postFormat = 2.0, reverseDirection = True):
        # maxErr = 1.0, approximation error, measured in units per em (UPM).
        # postFormat = 2.0, default `post` table format.
        # reverseDirection = True, assuming the input contours' direction is correctly set (counter-clockwise), we just flip it to clockwise.
        if self.font.sfntVersion != "OTTO" or not self.font.has_key("CFF ") or not self.font.has_key("post"):
            print("WARNING: Invalid CFF-based font. --otf2ttf is now ignored.", file = sys.stderr)
            self.jobs.convert_otf2ttf = False
            return

        # Convert cubic to quadratic
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

        # Change sfntVersion from CFF to TrueType
        self.font.sfntVersion = "\x00\x01\x00\x00"

        # Recalculate missing properties in `head`, `glyf`, `maxp` upon compile
        self.font.recalcBBoxes = True

        # Clean-ups
        del self.font["CFF "]
        if self.font.has_key("VORG"):
            del self.font["VORG"]
        return

    def changeUPM(self, targetUPM):
        # Calculate scaling factor between old and new UPM
        upmOld = self.font["head"].unitsPerEm
        upmNew = int(targetUPM)
        if upmOld == upmNew:
            return
        elif upmNew < 16 or upmNew > 16384:
            print("WARNING: Invalid UPM value. --UPM is now ignored.", file = sys.stderr)
            return
        elif self.font.has_key("CFF "):
            print("WARNING: CFF-based font detected. Unfortunately it is currently not supported.", file = sys.stderr)
            return
        elif upmNew > 5000:
            print("WARNING: UPM > 5000 will cause problems in Adobe InDesign and Illustrator.", file = sys.stderr)
        else:
            pass
        scaleFactor = upmNew / upmOld  # Get float because __future__.division has been imported

        # Conversion: re-scale all glyphs
        scaledGlyphs = {}
        glyphOrder = self.font.getGlyphOrder()
        glyphSet = self.font.getGlyphSet()
        for glyphName in glyphSet.keys():
            glyph = glyphSet[glyphName]
            ttPen = TTGlyphPen(glyphSet)
            scalePen = TransformPen(ttPen, Scale(scaleFactor, scaleFactor))
            glyph.draw(scalePen)
            # Glyph-specific hinting will be removed upon TTGlyphPen.glyph() call.
            scaledGlyphs[glyphName] = ttPen.glyph()

        # Apply `glyf` table with scaled glyphs
        glyf = newTable("glyf")
        glyf.glyphOrder = glyphOrder
        glyf.glyphs = scaledGlyphs
        self.font["glyf"] = glyf

        # Update tables to apply the new UPM
        self.__applyNewUPM(upmOld, upmNew)

        # Recalculate `head`, `glyf`, `maxp` upon compile
        self.font.recalcBBoxes = True
        return

    # Affected tables: `head`, `hhea`, `hmtx`, `kern`, `maxp`, `post`, `vhea`, `vmtx`, `OS/2`, `BASE`, `GPOS`, `JSTF`
    # ---- TODO: OpenType layout tables: `MATH` ----
    def __applyNewUPM(self, upmOld, upmNew):
        scaleFactor = upmNew / upmOld
        
        # Get font tables
        head = self.font.get("head")
        hhea = self.font.get("hhea")
        hmtx = self.font.get("hmtx")
        kern = self.font.get("kern")
        # `maxp` will be recalculated
        post = self.font.get("post")
        vhea = self.font.get("vhea")
        vmtx = self.font.get("vmtx")
        OS2f2 = self.font.get("OS/2")
        BASE = self.font.get("BASE")
        GPOS = self.font.get("GPOS")
        JSTF = self.font.get("JSTF")
        # MATH = self.font.get("MATH")

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
        # Every otTable is an otBase.BaseTTXConverter object, which must have the 'table' attr.
        if BASE and BASE.table:
            # Both HorizAxis and VertAxis must exist.
            self.__applyNewUPM_handleBASEaxis(BASE.table.HorizAxis, scaleFactor)
            self.__applyNewUPM_handleBASEaxis(BASE.table.VertAxis, scaleFactor)
        if GPOS and GPOS.table:
            if GPOS.table.LookupList:
                self.__applyNewUPM_handleGPOSlookups(GPOS.table.LookupList.Lookup, scaleFactor)
        if JSTF and JSTF.table:
            for record in JSTF.table.JstfScriptRecord:
                if record.JstfScript:
                    if record.JstfScript.DefJstfLangSys:
                        self.__applyNewUPM_handleJstfLangSys(record.JstfScript.DefJstfLangSys, scaleFactor)
                    for sysRecord in record.JstfScript.JstfLangSysRecord:
                        self.__applyNewUPM_handleJstfLangSys(sysRecord.JstfLangSys, scaleFactor)
        return

    def __applyNewUPM_handleBASEaxis(self, axis, scaleFactor):
        if not axis:  # Axis might be None
            return
        for record in axis.BaseScriptList.BaseScriptRecord:
            if record.BaseScript:
                if record.BaseScript.BaseValues:
                    for coord in record.BaseScript.BaseValues.BaseCoord:
                        coord.Coordinate = int(round(coord.Coordinate * scaleFactor))
                if record.BaseScript.DefaultMinMax:
                    if record.BaseScript.DefaultMinMax.MinCoord:  # BaseCoord
                        oldCoordValue = record.BaseScript.DefaultMinMax.MinCoord.Coordinate
                        newCoordValue = int(round(oldCoordValue * scaleFactor))
                        record.BaseScript.DefaultMinMax.MinCoord.Coordinate = newCoordValue
                    if record.BaseScript.DefaultMinMax.MaxCoord:  # BaseCoord
                        oldCoordValue = record.BaseScript.DefaultMinMax.MaxCoord.Coordinate
                        newCoordValue = int(round(oldCoordValue * scaleFactor))
                        record.BaseScript.DefaultMinMax.MaxCoord.Coordinate = newCoordValue
                    for featRecord in record.BaseScript.DefaultMinMax.FeatMinMaxRecord:
                        if featRecord.MinCoord:  # BaseCoord
                            oldCoordValue = featRecord.MinCoord.Coordinate
                            newCoordValue = int(round(oldCoordValue * scaleFactor))
                            featRecord.MinCoord.Coordinate = newCoordValue
                        if featRecord.MaxCoord:  # BaseCoord
                            oldCoordValue = featRecord.MaxCoord.Coordinate
                            newCoordValue = int(round(oldCoordValue * scaleFactor))
                            featRecord.MaxCoord.Coordinate = newCoordValue
        return

    def __applyNewUPM_handleJstfLangSys(self, jstfLangSys, scaleFactor):
        if not jstfLangSys:  # JstfLangSys might be None
            return
        for priority in jstfLangSys.JstfPriority:
            # Other attrs are just references to `GSUB` or `GPOS` table.
            if hasattr(priority, "ShrinkageJstfMax") and priority.ShrinkageJstfMax:
                self.__applyNewUPM_handleGPOSlookups(priority.ShrinkageJstfMax.Lookup, scaleFactor)
            if hasattr(priority, "ExtensionJstfMax") and priority.ExtensionJstfMax:
                self.__applyNewUPM_handleGPOSlookups(priority.ExtensionJstfMax.Lookup, scaleFactor)
        return

    def __applyNewUPM_handleGPOSlookups(self, gsubLookups, scaleFactor):
        if not gsubLookups:
            return
        for lookup in gsubLookups:
            for sub in lookup.SubTable:
                if lookup.LookupType in range(1, 9):
                    self.__applyNewUPM_handleGPOSsubTable(
                        lookup.LookupType,
                        sub,
                        scaleFactor
                        )
                elif lookup.LookupType == 9:  # ExtensionPos, format 1
                    if sub.Format == 1:  # sub.ExtensionLookupType, sub.ExtSubTable
                        self.__applyNewUPM_handleGPOSsubTable(
                            sub.ExtensionLookupType,
                            sub.ExtSubTable,
                            scaleFactor
                            )
                else:
                    pass
        return

    def __applyNewUPM_handleGPOSsubTable(self, lookupType, subTable, scaleFactor):
        if not subTable or not lookupType:
            return
        if lookupType == 1:  # SinglePos, format 1, 2
            # Attr here is 'Format', not 'PosFormat'
            if subTable.Format == 1:  # subTable.Value == ValueRecord
                self.__applyNewUPM_handleValueRecord(subTable.Value, scaleFactor)
            elif subTable.Format == 2:  # subTable.Value == ValueRecord[]
                for valRecord in subTable.Value:
                    self.__applyNewUPM_handleValueRecord(valRecord, scaleFactor)
            else:
                pass
        elif lookupType == 2:  # PairPos, format 1, 2
            if subTable.Format == 1:  # subTable.PairSet[].PairValueRecord[]
                for pair in subTable.PairSet:
                    for pairValRec in pair.PairValueRecord:
                        self.__applyNewUPM_handleValueRecord(pairValRec.Value1, scaleFactor)
                        self.__applyNewUPM_handleValueRecord(pairValRec.Value2, scaleFactor)
            elif subTable.Format == 2:  # subTable.Class1Record[].Class2Record[]
                for cls1Rec in subTable.Class1Record:
                    for cls2Rec in cls1Rec.Class2Record:
                        self.__applyNewUPM_handleValueRecord(cls2Rec.Value1, scaleFactor)
                        self.__applyNewUPM_handleValueRecord(cls2Rec.Value2, scaleFactor)
            else:
                pass
        elif lookupType == 3:  # CursivePos, format 1
            if subTable.Format == 1:  # subTable.EntryExitRecord[]
                for eeRec in subTable.EntryExitRecord:
                    self.__applyNewUPM_handleAnchor(eeRec.EntryAnchor, scaleFactor)
                    self.__applyNewUPM_handleAnchor(eeRec.ExitAnchor, scaleFactor)
        elif lookupType == 4:  # MarkBasePos, format 1
            if subTable.Format == 1:  # subTable.MarkArray, subTable.BaseArray
                for markRec in subTable.MarkArray.MarkRecord:
                    self.__applyNewUPM_handleAnchor(markRec.MarkAnchor, scaleFactor)
                for baseRec in subTable.BaseArray.BaseRecord:
                    for anchor in baseRec.BaseAnchor:
                        self.__applyNewUPM_handleAnchor(anchor, scaleFactor)
        elif lookupType == 5:  # MarkLigPos, format 1
            if subTable.Format == 1:  # subTable.MarkArray, subTable.LigatureArray
                for markRec in subTable.MarkArray.MarkRecord:
                    self.__applyNewUPM_handleAnchor(markRec.MarkAnchor, scaleFactor)
                for ligAttach in subTable.LigatureArray.LigatureAttach:
                    for cmpntRec in ligAttach.ComponentRecord:
                        for anchor in cmpntRec.LigatureAnchor:
                            self.__applyNewUPM_handleAnchor(anchor, scaleFactor)
        elif lookupType == 6:  # MarkMarkPos, format 1
            if subTable.Format == 1:  # subTable.Mark1Array == MarkArray, subTable.Mark2Array
                for markRec in subTable.Mark1Array.MarkRecord:
                    self.__applyNewUPM_handleAnchor(markRec.MarkAnchor, scaleFactor)
                for mark2Rec in subTable.Mark2Array.Mark2Record:
                    for anchor in mark2Rec.Mark2Anchor:
                        self.__applyNewUPM_handleAnchor(anchor, scaleFactor)
        elif lookupType == 7:  # ContextPos, format 1, 2, 3
            pass  # It will eventually reference to another lookup, type 1-6.
        elif lookupType == 8:  # ChainContextPos, format 1, 2, 3
            pass  # It will eventually reference to another lookup, type 1-6.
        else:
            pass
        return

    def __applyNewUPM_handleAnchor(self, anchor, scaleFactor):
        if not anchor:
            return
        if hasattr(anchor, "XCoordinate") and anchor.XCoordinate:
            anchor.XCoordinate = int(round(anchor.XCoordinate * scaleFactor))
        if hasattr(anchor, "YCoordinate") and anchor.YCoordinate:
            anchor.YCoordinate = int(round(anchor.YCoordinate * scaleFactor))
        return

    # The ValueRecord here is otBase.ValueRecord class, not the one presented in otData.
    def __applyNewUPM_handleValueRecord(self, valueRecord, scaleFactor):
        if not valueRecord:
            return
        if hasattr(valueRecord, "XPlacement") and valueRecord.XPlacement:
            valueRecord.XPlacement = int(round(valueRecord.XPlacement * scaleFactor))
        if hasattr(valueRecord, "YPlacement") and valueRecord.YPlacement:
            valueRecord.YPlacement = int(round(valueRecord.YPlacement * scaleFactor))
        if hasattr(valueRecord, "XAdvance") and valueRecord.XAdvance:
            valueRecord.XAdvance = int(round(valueRecord.XAdvance * scaleFactor))
        if hasattr(valueRecord, "YAdvance") and valueRecord.YAdvance:
            valueRecord.YAdvance = int(round(valueRecord.YAdvance * scaleFactor))
        return

