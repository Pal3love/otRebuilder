#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)

from fontTools.ttLib import newTable
from fontTools.ttLib.tables import O_S_2f_2
from fontTools.ttLib.standardGlyphOrder import standardGlyphOrder

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
            self.initOS2f2()
            self.initName()
            self.initPost()
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

    def isVariableFont(self):
        if self.font.has_key("CFF2"):
            return True
        elif self.font.has_key("gvar"):
            return True
        else:
            return False

    def refreshTables(self):
        tags = self.font.keys()
        for tag in tags:
            # Manually load each table into memory
            table = self.font.get(tag)
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
        if self.font.has_key("gasp"):
            del self.font["gasp"]
        return

    # Hinting-related tables: `cvt `, `fpgm`, `glyf`, `prep`, `hdmx`, `LTSH`, `VDMX`, `gasp`
    def removeHinting(self):
        if not self.isTrueType():
            self.jobs.init_removeHinting = False
            self.jobs.rebuild_gasp = False
            self.jobs.rebuild_prep = False
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
        if self.font.has_key("EBDT"):
            del self.font["EBDT"]
        if self.font.has_key("EBLC"):
            del self.font["EBLC"]
        if self.font.has_key("EBSC"):
            del self.font["EBSC"]
        return

    def removeGlyphNames(self):
        # `post` always exists.
        self.font["post"].formatType = 3.0
        return

    def __createOS2f2(self):
        OS2f2 = newTable("OS/2")
        OS2f2.version = Constants.DEFAULT_OS2f2_VERSION
        OS2f2.xAvgCharWidth = Workers.OS2f2Worker.recalcXAvgCharWidth(self.font["hmtx"])
        OS2f2.usWeightClass = Workers.OS2f2Worker.getUsWeightClass(self.font["head"])
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
        OS2f2.fsSelection = Workers.OS2f2Worker.getFsSelection(self.font["head"])
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
            OS2f2.usBreakChar = 0x20  # "space"
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
        # Add Mac family & subfamily first because on Mac there are no historical issues for them.
        builder.addMacNameEx(family.decode(), 1, 0)
        builder.addMacNameEx(subfamily.decode(), 2, 0)
        # Add Win family & subfamily then.
        if subfamily in Constants.LEGACY_WIN_STYLES:
            builder.addWinNameEx(family.decode(), 1, 0x0409)
            builder.addWinNameEx(subfamily.decode(), 2, 0x0409)
        else:
            builder.addWinNameEx(family.decode(), 16, 0x0409)
            builder.addWinNameEx(subfamily.decode(), 17, 0x0409)
            if "Italic" in subfamily:  # Non-legacy italic style
                winLegacyFamily = family + " " + subfamily.replace(" Italic", "")
                builder.addWinNameEx(winLegacyFamily.decode(), 1, 0x0409)
                builder.addWinNameEx(u"Italic", 2, 0x0409)
            else:  # Non-legacy regular style, such as "Light"
                winLegacyFamily = family + " " + subfamily
                builder.addWinNameEx(winLegacyFamily.decode(), 1, 0x0409)
                builder.addWinNameEx(u"Regular", 2, 0x0409)
        builder.addEngName(fullName, 4)
        builder.addMacCompatibleFullEx(fullName, 0)
        builder.addPostScriptName(psName)
        builder.addFontUniqueID(uniqueID)
        builder.addVersionString(versionStr)
        return builder.build(self.font["cmap"])

    def __createPost(self):
        post = newTable("post")
        post.formatType = 3.0
        post.italicAngle = 0.0
        post.underlinePosition = Constants.DEFAULT_UNDERLINE_POSITION
        post.underlineThickness = Constants.DEFAULT_UNDERLINE_THICKNESS
        post.isFixedPitch = 0L
        post.minMemType42 = 0
        post.maxMemType42 = 0
        post.minMemType1 = 0
        post.maxMemType1 = 0
        post.glyphOrder = None
        # Get metadata from CFF and change version
        cffT = self.font.get("CFF ")
        if cffT and hasattr(cffT, "cff") and cffT.cff:
            cff = cffT.cff
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

