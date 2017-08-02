#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)

from fontTools.ttLib import newTable
from fontTools.ttLib.tables import O_S_2f_2

from otRebuilder.Lib import Builders
from otRebuilder.Lib import Constants
from otRebuilder.Lib import Workers


class Initializer(Workers.Worker):

    def __init__(self, ttfontObj, jobsObj):
        super(Initializer, self).__init__(ttfontObj, jobsObj)
        if not self.isValidFont():
            print("ERROR: Invalid font file. Please make sure it has all required tables.", file = sys.stderr)
            print("Required tables: " + ", ".join(Constants.REQUIRED_TABLES), file = sys.stderr)
            sys.exit(1)
        else:
            self.initMaxp()
            self.initOS2f2()
            self.initPost()
            self.initName()
            self.removeDSIG()
        return

    # It must be called first!
    def isValidFont(self):
        for tag in Constants.REQUIRED_TABLES:
            if not self.font.has_key(tag):
                return False
        return True

    def isSymbolFont(self):
        for subtable in self.font["cmap"].tables:
            if subtable.isSymbol():
                return True
            else:
                continue
        return False

    def isTrueType(self):
        if self.font.has_key("glyf"):
            return True
        elif self.font.sfntVersion == "true":
            return True
        elif self.font.sfntVersion == "\0\1\0\0":
            return True
        else:
            return False

    def refreshTables(self):
        tags = self.font.keys()
        for tag in tags:
            # Manually load each table into memory
            table = self.font.get(tag)
        return

    # If `maxp` doesn't exist, generate a new one.
    def initMaxp(self):
        if not self.font.has_key("maxp"):
            self.font["maxp"] = self.__createMaxp()
        if self.font["maxp"] is None:
            print("ERROR: Invalid font file. Please make sure it is either TrueType or CFF-based.", file = sys.stderr)
            sys.exit(1)
        return

    # If `OS/2` doesn't exist, generate a new one with Constants.DEFAULT_OS2f2_VERSION.
    def initOS2f2(self):
        if not self.font.has_key("OS/2"):
            self.font["OS/2"] = self.__createOS2f2()
        return

    # If `name` doesn't exist, generate a new one with defaultFontName.
    def initName(self):
        if not self.font.has_key("name"):
            self.font["name"] = self.__createName()
        return

    # If `post` doesn't exist, generate a new one with version 1.0.
    # FontTools heavily relies on `post` to establish a font's data structure, so it would crash
    # if there is no `post` table in the very beginning. Maybe one day fontTools would change its
    # implementation, and at that time this method would actually work.
    def initPost(self):
        if not self.font.has_key("post"):
            self.font["post"] = self.__createPost()
        if self.font.has_key("CFF "):
            self.font["post"].formatType = 3.0
        return

    # After font modification the original signature would become invalid, so it should be removed.
    def removeDSIG(self):
        if self.font.has_key("DSIG"):
            del self.font["DSIG"]
        return

    def removeGasp(self):
        if not self.isTrueType():
            self.jobs.rebuild_gasp = False
            # print("WARNING: Invalid TrueType font. --smoothRendering is now ignored.", file = sys.stderr)
            # return
        if self.font.has_key("gasp"):
            del self.font["gasp"]
        return

    # Hinting-related tables: `cvt `, `fpgm`, `glyf`, `prep`, `hdmx`, `LTSH`, `VDMX`, `gasp`
    def removeHinting(self):
        if not self.isTrueType():
            self.jobs.init_removeHinting = False
            self.jobs.rebuild_gasp = False
            # print("WARNING: Invalid TrueType font. --removeHinting is now ignored.", file = sys.stderr)
            # return
        if self.font.has_key("glyf"):
            glyf = self.font["glyf"]
            for key in glyf.keys():
                glyf[key].removeHinting()
        if self.font.has_key("cvt "):
            del self.font["cvt "]
        if self.font.has_key("fpgm"):
            del self.font["fpgm"]
        if self.font.has_key("prep"):
            del self.font["prep"]
        if self.font.has_key("hdmx"):
            del self.font["hdmx"]
        if self.font.has_key("LTSH"):
            del self.font["LTSH"]
        if self.font.has_key("VDMX"):
            del self.font["VDMX"]
        if self.font.has_key("gasp"):
            del self.font["gasp"]
        return

    # Black & white Bitmap-related tables: `EBDT`, `EBLC`, `EBSC`
    def removeBitmap(self):
        if not self.isTrueType():
            self.jobs.init_removeBitmap = False
            # print("WARNING: Invalid TrueType font. --removeBitmap is now ignored.", file = sys.stderr)
            # return
        if self.font.has_key("EBDT"):
            del self.font["EBDT"]
        if self.font.has_key("EBLC"):
            del self.font["EBLC"]
        if self.font.has_key("EBSC"):
            del self.font["EBSC"]
        return

    def removeGlyphNames(self):
        # `post` always exists.
        if self.isTrueType():
            self.font["post"].formatType = 1.0
        elif self.font.has_key("CFF "):
            self.font["post"].formatType = 3.0
        else:
            pass
        return

    def __createMaxp(self):
        maxp = newTable("maxp")
        if self.font.has_key("CFF "):
            maxp.tableVersion = 0x00005000
            maxp.numGlyphs = len(self.font.getGlyphOrder())
        elif self.font.has_key("glyf"):
            maxp.tableVersion = 0x00010000
            maxp.recalc(self.font)
            # The following are TT instructions metadata.
            maxp.maxZones = 0
            maxp.maxTwilightPoints = 0
            maxp.maxStorage = 0
            maxp.maxFunctionDefs = 0
            maxp.maxInstructionDefs = 0
            maxp.maxStackElements = 0
            maxp.maxSizeOfInstructions = 0
            maxp.maxComponentElements = 0
        else:
            return None
        return maxp

    def __createOS2f2(self):
        OS2f2 = newTable("OS/2")
        OS2f2.version = Constants.DEFAULT_OS2f2_VERSION
        OS2f2.xAvgCharWidth = self.__createOS2f2_recalcXAvgCharWidth()
        OS2f2.usWeightClass = self.__createOS2f2_getUsWeightClass()
        OS2f2.usWidthClass = 5
        OS2f2.fsType = 0
        OS2f2.ySubscriptXSize = 0
        OS2f2.ySubscriptYSize = 0
        OS2f2.ySubscriptXOffset = 0
        OS2f2.ySubscriptYOffset = 0
        OS2f2.ySuperscriptXSize = 0
        OS2f2.ySuperscriptYSize = 0
        OS2f2.ySuperscriptXOffset = 0
        OS2f2.ySuperscriptYOffset = 0
        OS2f2.yStrikeoutSize = 0
        OS2f2.yStrikeoutPosition = 0
        OS2f2.sFamilyClass = 0
        OS2f2.panose = O_S_2f_2.Panose()
        OS2f2.panose.bFamilyType = 2
        OS2f2.panose.bSerifStyle = 0
        OS2f2.panose.bWeight = 5
        OS2f2.panose.bProportion = 0
        OS2f2.panose.bContrast = 0
        OS2f2.panose.bStrokeVariation = 0
        OS2f2.panose.bArmStyle = 0
        OS2f2.panose.bLetterForm = 0
        OS2f2.panose.bMidline = 0
        OS2f2.panose.bXHeight = 0
        OS2f2.recalcUnicodeRanges(self.font)
        OS2f2.achVendID = Constants.DEFAULT_OS2f2_ACHVENDID
        OS2f2.fsSelection = self.__createOS2f2_getFsSelection()
        OS2f2.updateFirstAndLastCharIndex(self.font)
        OS2f2.sTypoAscender = self.font["hhea"].ascent
        OS2f2.sTypoDescender = self.font["hhea"].descent
        OS2f2.sTypoLineGap = self.font["hhea"].lineGap
        OS2f2.usWinAscent = abs(self.font["hhea"].ascent)
        OS2f2.usWinDescent = abs(self.font["hhea"].descent)
        if OS2f2.version > 0:
            OS2f2.ulCodePageRange1 = 1
            OS2f2.ulCodePageRange2 = 0
        if OS2f2.version > 1:
            OS2f2.sxHeight = 0
            OS2f2.sCapHeight = 0
            OS2f2.usDefaultChar = 0
            OS2f2.usBreakChar = 0
            OS2f2.usMaxContext = 0
        if OS2f2.version > 4:
            OS2f2.usLowerOpticalPointSize = 0
            OS2f2.usUpperOpticalPointSize = 0
        return OS2f2

    # For a CFF-based font, we can also generate `name` from `CFF ` table.
    def __createName(self):
        builder = Builders.NameTableBuilder()
        family = subfamily = fullName = psName = uniqueID = copyright = trademark = None
        versionStr = Workers.NameWorker.getVersionString(self.font.get("head"))
        # recordsFromCFF = (family, subfamily, fullName, psName, versionStr, copyright, trademark)
        recordsFromCFF = Workers.NameWorker.getRecordsFromCFF(self.font.get("CFF "))
        if recordsFromCFF:
            if recordsFromCFF[0]:
                family = recordsFromCFF[0]
            if recordsFromCFF[1]:
                subfamily = recordsFromCFF[1]
            if recordsFromCFF[2]:
                fullName = recordsFromCFF[2]
            if recordsFromCFF[3]:
                psName = recordsFromCFF[3]
            if recordsFromCFF[4]:
                versionStr = recordsFromCFF[4]
            if recordsFromCFF[5]:
                copyright = recordsFromCFF[5]
            if recordsFromCFF[6]:
                trademark = recordsFromCFF[6]
        if family is None:
            family = Constants.DEFAULT_FONT_NAME
        if subfamily is None:
            subfamily = Workers.NameWorker.getWinStyle(self.font.get("head"))
        if fullName is None:
            if psName:
                fullName = psName
            else:
                fullName = family + " " + subfamily
        uniqueID = fullName + "; " + versionStr
        if psName is None:
            psName = family.replace(" ", "") + "-" + subfamily.replace(" ", "")
        if copyright:
            builder.addEngName(copyright, 0)  # Copyright, name ID 0
        if trademark:
            builder.addEngName(trademark, 7)  # Trademark, name ID 7
        if subfamily in Constants.LEGACY_WIN_STYLES:
            builder.addEngName(family, 1)  # Font family, name ID 1
            builder.addEngName(subfamily, 2)  # Font subfamily, name ID 2
        elif "Italic" in subfamily:  # Non-legacy italic style
            winLegacyFamily = family + " " + subfamily.replace(" Italic", "")
            builder.addEngName(winLegacyFamily, 1)  # Font family, name ID 1
            builder.addEngName("Italic", 2)  # Font subfamily, name ID 2
            builder.addEngName(family, 16)  # Font preferred family, name ID 16
            builder.addEngName(subfamily, 17)  # Font preferred subfamily, name ID 17
        else:  # Non-legacy regular style
            winLegacyFamily = family + " " + subfamily
            builder.addEngName(winLegacyFamily, 1)  # Font family, name ID 1
            builder.addEngName("Regular", 2)  # Font subfamily, name ID 2
            builder.addEngName(family, 16)  # Font preferred family, name ID 16
            builder.addEngName(subfamily, 17)  # Font preferred subfamily, name ID 17
        builder.addEngName(fullName, 4)  # Font full name, name ID 4
        builder.addPostScriptName(psName)
        builder.addFontUniqueID(uniqueID)
        builder.addVersionString(versionStr)
        return builder.build(self.font["cmap"])

    def __createPost(self):
        post = newTable("post")
        post.formatType = 1.0
        post.italicAngle = 0.0
        post.underlinePosition = Constants.DEFAULT_UNDERLINE_POSITION
        post.underlineThickness = Constants.DEFAULT_UNDERLINE_THICKNESS
        post.isFixedPitch = 0L
        post.minMemType42 = 0
        post.maxMemType42 = 0
        post.minMemType1 = 0
        post.maxMemType1 = 0
        # Get metadata from CFF and change version
        cffT = self.font.get("CFF ")
        if cffT and hasattr(cffT, "cff") and cffT.cff:
            cff = cffT.cff
            post.formatType = 3.0  # CFF-based fonts use version 3.0
            if hasattr(cff, "topDictIndex") and len(cff.topDictIndex) > 0:
                if cff.topDictIndex[0].ItalicAngle != cff.topDictIndex[0].defaults["ItalicAngle"]:
                    post.italicAngle = float(cff.topDictIndex[0].ItalicAngle)
                if cff.topDictIndex[0].isFixedPitch != cff.topDictIndex[0].defaults["isFixedPitch"]:
                    post.isFixedPitch = long(cff.topDictIndex[0].isFixedPitch)
                if cff.topDictIndex[0].UnderlineThickness != cff.topDictIndex[0].defaults["UnderlineThickness"]:
                    post.underlineThickness = int(cff.topDictIndex[0].UnderlineThickness)
                if hasattr(cff.topDictIndex[0], "UnderlinePosition"):
                    post.underlinePosition = int(cff.topDictIndex[0].UnderlinePosition)
        return post

    def __createOS2f2_recalcXAvgCharWidth(self):
        hmtx = self.font["hmtx"]
        count = 0
        sumWidth = 0
        for glyfName in hmtx.metrics.keys():
            sumWidth += hmtx.metrics[glyfName][0]
            count += 1
        return sumWidth // count

    def __createOS2f2_getUsWeightClass(self):
        head = self.font["head"]
        if (head.macStyle & 1):
            return 700
        else:
            return 400

    def __createOS2f2_getFsSelection(self):
        head = self.font["head"]
        fsSelection = 0
        if (head.macStyle & 1):  # Set bold bit
            fsSelection |= 1<<5
        if (head.macStyle & 1<<1):  # Set italic bit
            fsSelection |= 1
        if not (head.macStyle & 1) and not (head.macStyle & 1<<1):  # Neither bold nor italic
            fsSelection = 1<<6  # Set to regular
        return fsSelection

