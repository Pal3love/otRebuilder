#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)

from fontTools.ttLib.tables import _c_m_a_p
from fontTools.ttLib.tables import _n_a_m_e

from otRebuilder.Lib import Constants


class Worker(object):
    def __init__(self, ttfontObj, jobsObj):
        self.font = ttfontObj
        self.jobs = jobsObj


class OS2f2Worker(Worker):

    @staticmethod
    def getUsWeightClass(head):
        if head and (head.macStyle & 1):
            return 700
        else:
            return 400

    @staticmethod
    def getFsSelection(head):
        fsSelection = 0
        if not head:
            return fsSelection
        if (head.macStyle & 1):  # Set bold bit
            fsSelection |= 1<<5
        if (head.macStyle & 1<<1):  # Set italic bit
            fsSelection |= 1
        if not (head.macStyle & 1) and not (head.macStyle & 1<<1):  # Neither bold nor italic
            fsSelection = 1<<6  # Set to regular
        return fsSelection

    @staticmethod
    def recalcXAvgCharWidth(hmtx):
        if not hmtx:
            return 0
        count = 0
        sumWidth = 0
        for glyfName in hmtx.metrics.keys():
            # [0]: advance width; [1]: lsb
            if hmtx.metrics[glyfName][0] == 0:
                continue
            else:            
                sumWidth += hmtx.metrics[glyfName][0]
                count += 1
        return sumWidth // count


class CmapWorker(Worker):

    @staticmethod
    def isUVS(subtable):
        return subtable.platformID == 0 and subtable.format == 14

    @staticmethod
    def isLastResort(subtable):
        return subtable.platformID == 0 and subtable.format == 13

    @staticmethod
    def isUnicode(subtable):
        return subtable.isUnicode()

    @staticmethod
    def isSymbol(subtable):
        return subtable.isSymbol()

    @staticmethod
    def isMacRoman(subtable):
        return subtable.platformID == 1 and subtable.platEncID == 0 and subtable.language == 0

    @staticmethod
    def getUVS(subtables):
        for subtable in subtables:
            if CmapWorker.isUVS(subtable):
                return subtable
        return None

    @staticmethod
    def getLastResort(subtables):
        for subtable in subtables:
            if CmapWorker.isLastResort(subtable):
                return subtable
        return None

    @staticmethod
    def getSymbol(subtables):
        for subtable in subtables:
            if subtable.isSymbol():
                return subtable
        return None

    @staticmethod
    def getMacRoman(subtables):
        for subtable in subtables:
            if CmapWorker.isMacRoman(subtable):
                return subtable
        return None

    @staticmethod
    def makeTruncatedDict(fullDict):
        truncatedDict = {}
        for code in fullDict.keys():
            if (code < 0xD800) or (code > 0xDFFF and code < 0x10000):
                truncatedDict[code] = fullDict[code]
        return truncatedDict

    # It does not check whether the mappingDict size fits the corresponding subtable format.
    @staticmethod
    def makeSubtable(platformID, platEncID, languageID, tableFormatID, mappingDict):
        newSubtable = _c_m_a_p.CmapSubtable.newSubtable(tableFormatID)
        newSubtable.platformID = platformID
        newSubtable.platEncID = platEncID
        newSubtable.language = languageID
        newSubtable.cmap = mappingDict
        return newSubtable

    # 'unicodeSubtable' means Unicode or Microsoft Unicode
    @staticmethod
    def subtable_buildMacRomanFromUnicode(unicodeSubtable):
        macRomanMappingDict = {}
        unicodeMappingDict = unicodeSubtable.cmap
        for i in range(0, 256):
            # Get the corresponding Unicode value of Macintosh Roman code
            unicodeFromMacRoman = ord(chr(i).decode('mac_roman'))
            if unicodeMappingDict.has_key(unicodeFromMacRoman):
                macRomanMappingDict[i] = unicodeMappingDict[unicodeFromMacRoman]
        # Subtable format for modern MacRoman should be 6 instead of 0.
        return CmapWorker.makeSubtable(1, 0, 0, 6, macRomanMappingDict)

    @staticmethod
    def subtables_buildFmt4sFromMacRoman(macRomanSubtable):
        fmt4Subtables = []
        unicodeMappingDict = {}
        macRomanMappingDict = macRomanSubtable.cmap
        for macCode in macRomanMappingDict.keys():
            uniCode = ord(chr(macCode).decode('mac_roman'))
            unicodeMappingDict[uniCode] = macRomanMappingDict[macCode]
        fmt4Subtables.append(CmapWorker.makeSubtable(3, 1, 0, 4, unicodeMappingDict))  # Microsoft Unicode BMP
        fmt4Subtables.append(CmapWorker.makeSubtable(0, 3, 0, 4, unicodeMappingDict))  # Unicode BMP
        return fmt4Subtables

    @staticmethod
    def subtables_buildFmt4sFromBMP(BMPSubtable):
        fmt4Subtables = []
        mappingDict = BMPSubtable.cmap
        fmt4Subtables.append(CmapWorker.makeSubtable(3, 1, 0, 4, mappingDict))  # Microsoft Unicode BMP
        fmt4Subtables.append(CmapWorker.makeSubtable(0, 3, 0, 4, mappingDict))  # Unicode BMP
        return fmt4Subtables

    @staticmethod
    def subtables_buildFmt12sFromFull(fullSubtable):
        fmt12Subtables = []
        mappingDict = fullSubtable.cmap
        fmt12Subtables.append(CmapWorker.makeSubtable(3, 10, 0, 12, mappingDict))  # Microsoft Unicode full repertoire
        fmt12Subtables.append(CmapWorker.makeSubtable(0, 4, 0, 12, mappingDict))  # Unicode full repertoire
        return fmt12Subtables

    @staticmethod
    def subtables_buildUnicodeAllFromFull(fullSubtable):
        unicodeSubtables = []
        fullDict = fullSubtable.cmap
        truncatedDict = CmapWorker.makeTruncatedDict(fullDict)
        unicodeSubtables.append(CmapWorker.makeSubtable(3, 1, 0, 4, truncatedDict))  # Microsoft Unicode BMP
        unicodeSubtables.append(CmapWorker.makeSubtable(3, 10, 0, 12, fullDict))  # Microsoft Unicode full repertoire
        unicodeSubtables.append(CmapWorker.makeSubtable(0, 3, 0, 4, truncatedDict))  # Unicode BMP
        unicodeSubtables.append(CmapWorker.makeSubtable(0, 4, 0, 12, fullDict))  # Unicode full repertoire
        return unicodeSubtables

    # It almost doesn't make any sense.
    @staticmethod
    def subtables_buildfmt13sFromLastResort(lastSubtable):
        unicodeSubtables = []
        fullDictEx = lastSubtable.cmap
        unicodeSubtables.append(CmapWorker.makeSubtable(3, 10, 0, 13, fullDictEx))  # Microsoft Unicode full repertoire
        unicodeSubtables.append(CmapWorker.makeSubtable(0, 4, 0, 13, fullDictEx))  # Unicode full repertoire
        unicodeSubtables.append(CmapWorker.makeSubtable(0, 6, 0, 13, fullDictEx))  # Unicode full coverage
        return unicodeSubtables


class NameWorker(Worker):

    @staticmethod
    def getWinStyle(headTable):
        if headTable:
            if (headTable.macStyle & 1) and (headTable.macStyle & 1<<1):  # Bold Italic
                return "Bold Italic"
            elif (headTable.macStyle & 1):  # Bold
                return "Bold"
            elif (headTable.macStyle & 1<<1):  # Italic
                return "Italic"
            else:
                return "Regular"
        else:
            return "Regular"

    @staticmethod
    def getVersionString(headTable):
        if not headTable or not headTable.fontRevision:
            return "Version " + "%.2f" % abs(Constants.DEFAULT_FONT_REVISION)
        else:
            return "Version " + "%.2f" % headTable.fontRevision

    @staticmethod
    def getRecordsFromCFF(cffTable):
        if cffTable and hasattr(cffTable, "cff") and cffTable.cff:
            cff = cffTable.cff
            family = subfamily = fullName = psName = versionStr = copyright = trademark = None
            if hasattr(cff, "fontNames") and len(cff.fontNames) > 0 and len(cff.fontNames[0]) > 0:
                psName = cff.fontNames[0]
            if hasattr(cff, "topDictIndex") and len(cff.topDictIndex) > 0:
                if hasattr(cff.topDictIndex[0], "version") and len(cff.topDictIndex[0].version) > 0:
                    versionStr = "Version " + cff.topDictIndex[0].version.strip()
                elif hasattr(cff.topDictIndex[0], "CIDFontVersion") and cff.topDictIndex[0].CIDFontVersion > 0.0:
                    versionStr = "Version " + str(cff.topDictIndex[0].CIDFontVersion)
                else:
                    pass
                if hasattr(cff.topDictIndex[0], "Notice") and len(cff.topDictIndex[0].Notice) > 0:
                    trademark = cff.topDictIndex[0].Notice.strip()
                if hasattr(cff.topDictIndex[0], "Copyright") and len(cff.topDictIndex[0].Copyright) > 0:
                    copyright = cff.topDictIndex[0].Copyright.strip()
                if hasattr(cff.topDictIndex[0], "FullName") and len(cff.topDictIndex[0].FullName) > 0:
                    fullName = cff.topDictIndex[0].FullName.strip()
                if hasattr(cff.topDictIndex[0], "FamilyName") and len(cff.topDictIndex[0].FamilyName) > 0:
                    family = cff.topDictIndex[0].FamilyName.strip()
                if hasattr(cff.topDictIndex[0], "Weight") and len(cff.topDictIndex[0].Weight) > 0:
                    subfamily = cff.topDictIndex[0].Weight.strip().title()
                if cff.topDictIndex[0].ItalicAngle != cff.topDictIndex[0].defaults["ItalicAngle"]:
                    if subfamily is None or subfamily in Constants.REGULAR_STYLES:
                        subfamily = "Italic"
                    else:
                        subfamily += " Italic"
            records = [family, subfamily, fullName, psName, versionStr, copyright, trademark]
            return tuple(records)
        else:
            return None

    # Even though winNameRecord.string is Unicode-based, it's encoded with utf_16_be, and must be decoded first.
    # According to the _n_a_m_e module, all NameRecord strings are recommended to be Python Unicode format, 
    # and it will be local-encoded upon compile.

    @staticmethod
    def isPureUnicode(nameRecord):
        return nameRecord.platformID == 0

    @staticmethod
    def isMacintosh(nameRecord):
        return nameRecord.platformID == 1

    @staticmethod
    def isWindows(nameRecord):
        return nameRecord.platformID == 3

    @staticmethod
    def isWindowsLegacy(nameRecord):
        return nameRecord.platformID == 3 and nameRecord.platEncID in range(2, 7)

    @staticmethod
    def isWindowsSymbol(nameRecord):
        return nameRecord.platformID == 3 and nameRecord.platEncID == 0

    @staticmethod
    def isWindowsBMP(nameRecord):
        return nameRecord.platformID == 3 and nameRecord.platEncID == 1

    @staticmethod
    def isWindowsFull(nameRecord):
        return nameRecord.platformID == 3 and nameRecord.platEncID == 10

    @staticmethod
    def isWinPltEncIDUnicode(winPltEncID):
        return winPltEncID in [0, 1, 10]

    @staticmethod
    def getName(nameRecords, nameID, platformID, platEncID, langID):
        for name in nameRecords:
            if name.nameID == nameID and name.platformID == platformID and \
                name.platEncID == platEncID and name.langID == langID:
                return name
        return None

    # In nameRecords search for the given nameRecord.
    # If found, return that reference, or return None if not found.
    @staticmethod
    def findName(nameRecords, nameRecord):
        return NameWorker.getName(nameRecords, nameRecord.nameID, 
            nameRecord.platformID, nameRecord.platEncID, nameRecord.langID
            )

    @staticmethod
    def makeName(uString, nameID, platformID, platEncID, langID):
        return _n_a_m_e.makeName(uString, nameID, platformID, platEncID, langID)

    @staticmethod
    def makeMacName(uString, nameID, langTag):
        if Constants.LANGTAG_TO_MAC_LANGCODE.has_key(langTag):
            macLngID = Constants.LANGTAG_TO_MAC_LANGCODE[langTag]
            macPltEncID = Constants.MAC_LANGCODE_TO_PLATENCID[macLngID]
            return NameWorker.makeName(uString, nameID, 1, macPltEncID, macLngID)
        else:
            return None

    @staticmethod
    def makeMacNameEx(uString, nameID, macLngID):
        if Constants.MAC_LANGCODE_TO_PLATENCID.has_key(macLngID):
            macPltEncID = Constants.MAC_LANGCODE_TO_PLATENCID[macLngID]
            return NameWorker.makeName(uString, nameID, 1, macPltEncID, macLngID)
        else:
            return None

    # winPltEncID except 0(symbol), 1(BMP) and 10(full repertoire) are currently deprecated.
    @staticmethod
    def makeWinNames(uString, nameID, winPltEncID, langTag):
        winNamRecs = []
        if Constants.LANGTAG_TO_MAC_LANGCODE.has_key(langTag):
            macLngID = Constants.LANGTAG_TO_MAC_LANGCODE[langTag]
            for winLngID in Constants.MAC_LANGCODE_TO_WIN[macLngID]:
                winNamRecs.append(NameWorker.makeName(uString, nameID, 
                    3, winPltEncID, winLngID
                    ))
            return winNamRecs
        else:
            return None

    # winPltEncID except 0(symbol), 1(BMP) and 10(full repertoire) are currently deprecated.
    @staticmethod
    def makeWinNameEx(uString, nameID, winPltEncID, winLngID):
        return NameWorker.makeName(uString, nameID, 3, winPltEncID, winLngID)

    @staticmethod
    def winName2Mac(winNameRecord):
        if Constants.WIN_LANGCODE_TO_MAC.has_key(winNameRecord.langID):
            macLngID = Constants.WIN_LANGCODE_TO_MAC[winNameRecord.langID]
            # There must be the corresponding macPltEncID if macLngID exists!
            macPltEncID = Constants.MAC_LANGCODE_TO_PLATENCID[macLngID]
            return NameWorker.makeName(winNameRecord.toUnicode(), 
                winNameRecord.nameID, 1, macPltEncID, macLngID
                )
        else:
            return None

    # winPltEncID except 0(symbol), 1(BMP) and 10(full repertoire) are currently deprecated.
    @staticmethod
    def macName2Win(macNameRecord, winPltEncID, winLngID):
        return NameWorker.makeName(macNameRecord.toUnicode(), 
            macNameRecord.nameID, 3, winPltEncID, winLngID
            )

    # winPltEncID except 0(symbol), 1(BMP) and 10(full repertoire) are currently deprecated.
    @staticmethod
    def macName2WinAll(macNameRecord, winPltEncID):
        winNamRecs = []
        if Constants.MAC_LANGCODE_TO_WIN.has_key(macNameRecord.langID):
            for winLngID in Constants.MAC_LANGCODE_TO_WIN[macNameRecord.langID]:
                winNamRecs.append(NameWorker.makeName(macNameRecord.toUnicode(), 
                    macNameRecord.nameID, 3, winPltEncID, winLngID
                    ))
            return winNamRecs
        else:
            return None

