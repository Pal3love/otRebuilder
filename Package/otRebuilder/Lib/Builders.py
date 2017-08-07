#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)

import re
from fontTools.ttLib import newTable

from otRebuilder.Lib import Constants
from otRebuilder.Lib import Workers


class cffTopDictBuilder(object):

    def __init__(self):
        self.__version = None               # float
        self.__cidRegistry = None           # string
        self.__cidOrdering = None           # string
        self.__cidSupplement = None         # int
        self.__psName = None                # string
        self.__fullName = None              # string
        self.__family = None                # string
        self.__weight = None                # string
        self.__copyright = None             # string
        self.__trademark = None             # string
        self.__isMonospaced = None          # bool
        self.__italicAngle = None           # float
        self.__underlinePosition = None     # float
        self.__underlineThickness = None    # float
        self.__fontBBox = None              # float[]

    def clear(self):
        self.__version = None
        self.__cidRegistry = None
        self.__cidOrdering = None
        self.__cidSupplement = None
        self.__psName = None
        self.__fullName = None
        self.__family = None
        self.__weight = None
        self.__copyright = None
        self.__trademark = None
        self.__isMonospaced = None
        self.__italicAngle = None
        self.__underlinePosition = None
        self.__underlineThickness = None
        self.__fontBBox = None
        return

    def setVersion(self, version):
        if version and (isinstance(version, int) or isinstance(version, float)):
            self.__version = float(abs(version))
            return True
        else:
            return False

    def setROS(self, registry, ordering, supplement):
        if registry and (isinstance(registry, str) or isinstance(registry, unicode)) and \
            ordering and (isinstance(ordering, str) or isinstance(ordering, unicode)) and \
            (isinstance(supplement, float) or isinstance(supplement, int)):
            self.__cidRegistry = self.__toASCII(registry.strip())
            self.__cidOrdering = self.__toASCII(ordering.strip())
            self.__cidSupplement = int(abs(supplement))
            return True
        else:
            return False

    def setPostScriptName(self, psName):
        if psName and (isinstance(psName, str) or isinstance(psName, unicode)):
            psName = re.sub(r"[\(\)\[\]\{\}<>/%]+", r"", psName)
            psName = psName.strip()
            psName = re.sub(r"\s+", r"-", psName)
            if len(psName) > 63:
                print("WARNING: PostScript name is longer than 63 bytes. It will be trimmed.", file = sys.stderr)
                psName = psName[:63]
            self.__psName = self.__toASCII(psName)
            return True
        else:
            return False

    def setFullName(self, fullName):
        if fullName and (isinstance(fullName, str) or isinstance(fullName, unicode)):
            self.__fullName = self.__toASCII(fullName.strip())
            return True
        else:
            return False

    def setFamily(self, family):
        if family and (isinstance(family, str) or isinstance(family, unicode)):
            self.__family = self.__toASCII(family.strip())
            return True
        else:
            return False

    def setWeight(self, weight):
        if weight and (isinstance(weight, str) or isinstance(weight, unicode)):
            self.__weight = self.__toASCII(weight.strip())
            return True
        else:
            return False

    def setCopyright(self, copyright):
        if copyright and (isinstance(copyright, str) or isinstance(copyright, unicode)):
            self.__copyright = self.__toASCII(copyright.strip())
            return True
        else:
            return False

    def setTrademark(self, trademark):
        if trademark and (isinstance(trademark, str) or isinstance(trademark, unicode)):
            self.__trademark = self.__toASCII(trademark.strip())
            return True
        else:
            return False

    def setMonospaced(self, isMonospaced):
        if isinstance(isMonospaced, bool):
            self.__isMonospaced = isMonospaced
            return True
        else:
            return False

    def setItalicAngle(self, italicAngle):
        if italicAngle and (isinstance(italicAngle, int) or isinstance(italicAngle, float)):
            self.__italicAngle = float(italicAngle)
            return True
        else:
            return False

    def setUnderlinePosition(self, underlinePosition):
        if underlinePosition and (isinstance(underlinePosition, int) or isinstance(underlinePosition, float)):
            self.__underlinePosition = float(underlinePosition)
            return True
        else:
            return False

    def setUnderlineThickness(self, underlineThickness):
        if underlineThickness and (isinstance(underlineThickness, int) or isinstance(underlineThickness, float)):
            self.__underlineThickness = float(underlineThickness)
            return True
        else:
            return False

    def setFontBBox(self, xMin, yMin, xMax, yMax):
        if xMin and (isinstance(xMin, int) or isinstance(xMin, float)) and \
            yMin and (isinstance(yMin, int) or isinstance(yMin, float)) and \
            xMax and (isinstance(xMax, int) or isinstance(xMax, float)) and \
            yMax and (isinstance(yMax, int) or isinstance(yMax, float)):
            self.__fontBBox = [float(xMin), float(yMin), float(xMax), float(yMax)]
            return True
        else:
            return False

    def setFontBBoxFromHeadTable(self, headTable):
        if headTable:
            self.setFontBBox(headTable.xMin, headTable.yMin, headTable.xMax, headTable.yMax)
            return True
        else:
            return False

    def clearCFFnameMenu(self, cffTable):
        if cffTable and hasattr(cffTable, "cff") and cffTable.cff:
            cff = cffTable.cff
            if hasattr(cff, "topDictIndex") and len(cff.topDictIndex) > 0:
                cff.topDictIndex[0].FullName = ""
                cff.topDictIndex[0].FamilyName = ""
                cff.topDictIndex[0].Copyright = ""
                cff.topDictIndex[0].Notice = ""
                # cff.topDictIndex[0].Weight = ""
                # cff.topDictIndex[0].version = ""
                # if hasattr(cff.topDictIndex[0], "ROS"):  # CID font
                    # cff.topDictIndex[0].CIDFontVersion = 0.0
            return True
        else:
            return False

    def applyToCFFtable(self, cffTable):
        if cffTable and hasattr(cffTable, "cff") and cffTable.cff:
            oldPSname = None
            cff = cffTable.cff
            if hasattr(cff, "fontNames") and len(cff.fontNames) > 0 and len(cff.fontNames[0]) > 0:
                oldPSname = cff.fontNames[0]
            # ---- CFF PostScript Name and CID Font Name ----
            if self.__psName:
                cff.fontNames = [self.__psName]
            # ---- CFF Top Dict Items ----
            if hasattr(cff, "topDictIndex") and len(cff.topDictIndex) > 0:
                # ---- CID Specific Items ----
                if hasattr(cff.topDictIndex[0], "ROS"):  # CID font
                    if self.__cidRegistry and self.__cidOrdering and (self.__cidSupplement is not None):
                        cff.topDictIndex[0].ROS = (self.__cidRegistry, self.__cidOrdering, self.__cidSupplement)
                    if self.__psName and oldPSname and hasattr(cff.topDictIndex[0], "FDArray"):
                        for fd in cff.topDictIndex[0].FDArray:
                            fd.FontName = fd.FontName.replace(oldPSname, self.__psName)
                    if self.__version is not None:
                        cff.topDictIndex[0].CIDFontVersion = self.__version
                # ---- General CFF Items ----
                if self.__fontBBox:
                    cff.topDictIndex[0].FontBBox = self.__fontBBox
                if self.__fullName:
                    cff.topDictIndex[0].FullName = self.__fullName
                if self.__family:
                    cff.topDictIndex[0].FamilyName = self.__family
                if self.__weight:
                    cff.topDictIndex[0].Weight = self.__weight
                if self.__copyright:
                    cff.topDictIndex[0].Copyright = self.__copyright
                if self.__trademark:
                    cff.topDictIndex[0].Notice = self.__trademark
                if self.__isMonospaced is not None:
                    if self.__isMonospaced:
                        cff.topDictIndex[0].isFixedPitch = 1
                    else:
                        cff.topDictIndex[0].isFixedPitch = 0
                if self.__version is not None:
                    cff.topDictIndex[0].version = str(self.__version)
                if self.__italicAngle is not None:
                    cff.topDictIndex[0].ItalicAngle = self.__italicAngle
                if self.__underlinePosition is not None:
                    cff.topDictIndex[0].UnderlinePosition = self.__underlinePosition
                if self.__underlineThickness is not None:
                    cff.topDictIndex[0].UnderlineThickness = self.__underlineThickness
            return True
        else:
            return False

    def __toASCII(self, anyString):
        if isinstance(anyString, bytes):
            return anyString
        else:
            return anyString.encode("ascii", errors = "ignore")


# Built on HashSet, a data structure without repetitions.
# Identical name records added would be ignored.
class NameTableBuilder(object):

    def __init__(self):
        self.__macExs = set()
        self.__winSymExs = set()
        self.__winBMPExs = set()
        self.__winFulExs = set()
        self.__winLgcExs = set()
        self.__miscExs = set()
        self.__pscidffustr = None  # Unicode string

    def clear(self):
        self.__macExs.clear()
        self.__winSymExs.clear()
        self.__winBMPExs.clear()
        self.__winFulExs.clear()
        self.__winLgcExs.clear()
        self.__miscExs.clear()
        self.__pscidffustr = None
        return

    # Add name records with language English US
    # string could be either ascii string or uString
    def addEngName(self, string, nameID):
        uString = self.__getUstring(string)
        # English US always succeeds
        self.addMacNameEx(uString, nameID, 0)
        self.addWinNameEx(uString, nameID, 0x0409)
        return

    def addName(self, uString, nameID, langTag):
        macNamRec = Workers.NameWorker.makeMacName(uString, nameID, langTag)
        symNamRecs = Workers.NameWorker.makeWinNames(uString, nameID, 0, langTag)
        bmpNamRecs = Workers.NameWorker.makeWinNames(uString, nameID, 1, langTag)
        fulNamRecs = Workers.NameWorker.makeWinNames(uString, nameID, 10, langTag)
        if macNamRec and symNamRecs and bmpNamRecs and fulNamRecs:
            self.__macExs.add(NameRecordEx(macNamRec))
            for namRec in symNamRecs:
                self.__winSymExs.add(NameRecordEx(namRec))
            for namRec in bmpNamRecs:
                self.__winBMPExs.add(NameRecordEx(namRec))
            for namRec in fulNamRecs:
                self.__winFulExs.add(NameRecordEx(namRec))
            return True
        else:
            return False

    def addNameEx(self, uString, nameID, platformID, platEncID, langID):
        namRec = Workers.NameWorker.makeName(uString, nameID, platformID, platEncID, langID)
        if platformID == 1:
            self.__macExs.add(NameRecordEx(namRec))
        elif platformID == 3:
            if platEncID == 0:
                self.__winSymExs.add(NameRecordEx(namRec))
            elif platEncID == 1:
                self.__winBMPExs.add(NameRecordEx(namRec))
            elif platEncID == 10:
                self.__winFulExs.add(NameRecordEx(namRec))
            else:
                self.__winLgcExs.add(NameRecordEx(namRec))
        else:
            self.__miscExs.add(NameRecordEx(namRec))
        return

    def addNameFromNameRecord(self, nameRecord):
        self.addNameEx(nameRecord.toUnicode(), 
            nameRecord.nameID, nameRecord.platformID, 
            nameRecord.platEncID, nameRecord.langID
            )
        return

    def addMacName(self, uString, nameID, langTag):
        namRec = Workers.NameWorker.makeMacName(uString, nameID, langTag)
        if namRec:
            self.__macExs.add(NameRecordEx(namRec))
            return True
        else:
            return False

    def addMacNameEx(self, uString, nameID, macLngID):
        namRec = Workers.NameWorker.makeMacNameEx(uString, nameID, macLngID)
        if namRec:
            self.__macExs.add(NameRecordEx(namRec))
            return True
        else:
            return False

    def addWinNames(self, uString, nameID, langTag):
        symNamRecs = Workers.NameWorker.makeWinNames(uString, nameID, 0, langTag)
        bmpNamRecs = Workers.NameWorker.makeWinNames(uString, nameID, 1, langTag)
        fulNamRecs = Workers.NameWorker.makeWinNames(uString, nameID, 10, langTag)
        if symNamRecs and bmpNamRecs and fulNamRecs:
            for namRec in symNamRecs:
                self.__winSymExs.add(NameRecordEx(namRec))
            for namRec in bmpNamRecs:
                self.__winBMPExs.add(NameRecordEx(namRec))
            for namRec in fulNamRecs:
                self.__winFulExs.add(NameRecordEx(namRec))
            return True
        else:
            return False

    def addWinNameEx(self, uString, nameID, winLngID):
        self.__winSymExs.add(NameRecordEx(
            Workers.NameWorker.makeWinNameEx(uString, nameID, 0, winLngID)
            ))
        self.__winBMPExs.add(NameRecordEx(
            Workers.NameWorker.makeWinNameEx(uString, nameID, 1, winLngID)
            ))
        self.__winFulExs.add(NameRecordEx(
            Workers.NameWorker.makeWinNameEx(uString, nameID, 10, winLngID)
            ))
        return

    # Name ID 2, English US
    def addStylelink(self, stylelinkCode):
        if stylelinkCode == Constants.STYLELINK_BOLD:
            self.addEngName("Bold", 2)
        elif stylelinkCode == Constants.STYLELINK_ITALIC:
            self.addEngName("Italic", 2)
        elif stylelinkCode == Constants.STYLELINK_BOLDITALIC:
            self.addEngName("Bold Italic", 2)
        else:
            self.addEngName("Regular", 2)
        return

    # Name ID 3, English US
    def addFontUniqueID(self, string):
        self.addEngName(string, 3)
        return

    # Name ID 5, English US
    # Format: "Version x.yz"
    # To customize format and presision, use the method below.
    def addVersion(self, version):
        if isinstance(version, int) or isinstance(version, float):
            self.addVersionString("Version " + "%.2f" % abs(version))
        return
        
    # Name ID 5, English US
    def addVersionString(self, string):
        if string.find(".") == -1:
            string += ".00"
        self.addEngName(string, 5)
        return

    # Name ID 5, English US
    def addVersionStringFromCFFtable(self, cffTable):
        if cffTable and hasattr(cffTable, "cff") and cffTable.cff:
            cff = cffTable.cff
            if hasattr(cff, "topDictIndex") and len(cff.topDictIndex) > 0:
                if hasattr(cff.topDictIndex[0], "version") and len(cff.topDictIndex[0].version) > 0:
                    self.addVersionString("Version " + cff.topDictIndex[0].version.strip())
                elif hasattr(cff.topDictIndex[0], "CIDFontVersion") and cff.topDictIndex[0].CIDFontVersion > 0.0:
                    self.addVersionString("Version " + str(cff.topDictIndex[0].CIDFontVersion))
                else:
                    pass
        return

    # Name ID 6, English US
    def addPostScriptName(self, string):
        string = re.sub(r"[\(\)\[\]\{\}<>/%]+", r"", string)
        string = re.sub(r"\s+", r"-", string)
        self.addEngName(string, 6)
        return

    # Name ID 6, English US
    def addPostScriptNameFromNameTable(self, nameTable):
        if nameTable and hasattr(nameTable, "names") and isinstance(nameTable.names, list):
            for namRec in nameTable.names:
                if namRec.nameID == 6 and namRec.langID in [0x0, 0x0409]:
                    self.addPostScriptName(namRec.toUnicode())
                    return
        return

    # Name ID 6, English US
    def addPostScriptNameFromCFFtable(self, cffTable):
        if cffTable and hasattr(cffTable, "cff") and cffTable.cff:
            cff = cffTable.cff
            if hasattr(cff, "fontNames") and len(cff.fontNames) > 0 and len(cff.fontNames[0]) > 0:
                try:
                    self.addPostScriptName(cff.fontNames[0].decode())
                except UnicodeDecodeError:
                    print("WARNING: Corrupted PostScript Name in table `CFF `.", file = sys.stderr)
                    self.addPostScriptName(cff.fontNames[0].decode(errors = "ignore"))
        return

    # Name ID 18, Macintosh only
    def addMacCompatibleFull(self, uString, langTag):
        return self.addMacName(uString, 18, langTag)

    # Name ID 18, Macintosh only
    def addMacCompatibleFullEx(self, uString, macLngID):
        return self.addMacNameEx(uString, 18, macLngID)

    # Name ID 20, Macintosh only
    # Add PostScript CID Findfont name record for Macintosh
    def addPSCIDFFName(self, string):
        string = re.sub(r"[\(\)\[\]\{\}<>/%]+", r"", string)
        string = re.sub(r"\s+", r"-", string)
        self.__pscidffustr = self.__getUstring(string)
        return

    # Name ID 20, Macintosh only
    # Get PostScript CID Findfont name record from the given `name` table
    def addPSCIDFFNameFromNameTable(self, nameTable):
        if nameTable and hasattr(nameTable, "names") and isinstance(nameTable.names, list):
            for namRec in nameTable.names:
                if namRec.nameID == 20:             
                    self.addPSCIDFFName(namRec.string.decode(errors = "ignore"))
                    return
        return

    # It must be called right before building the `name` table!
    def convertWinLegacy(self):
        for ex in self.__winLgcExs:
            namRec = ex.getNameRecord()
            macRec = Workers.NameWorker.winName2Mac(namRec)
            self.addNameFromNameRecord(macRec)
            self.addWinNameEx(namRec.toUnicode(), namRec.nameID, namRec.langID)
        return

    # It must be called right before building the `name` table!
    def clearMiscellaneousRecords(self):
        self.__miscExs.clear()
        return

    # Build `name` table with `cmap` consistency
    def build(self, cmapTable):
        self.__genPSCIDFFmacExs()
        self.__truncateLimitedExs()
        self.__removeUnsupportedChars()
        nameTable = newTable("name")
        nameTable.names = []
        needMac = False
        needWinSym = False
        needWinBMP = False
        needWinFul = False
        needWinLgc = False
        for subtable in cmapTable.tables:
            if subtable.platformID == 0 or subtable.platformID == 1:
                needMac = True
            elif subtable.platformID == 3:
                if subtable.platEncID == 0:
                    needWinSym = True
                elif subtable.platEncID == 1:
                    needWinBMP = True
                elif subtable.platEncID == 10:
                    needWinFul = True
                else:
                    needWinLgc = True
            else:
                continue
        if needMac:
            for ex in self.__macExs:
                nameTable.names.append(ex.getNameRecord())
        if needWinSym:
            for ex in self.__winSymExs:
                nameTable.names.append(ex.getNameRecord())
        if needWinBMP:
            for ex in self.__winBMPExs:
                nameTable.names.append(ex.getNameRecord())
        if needWinFul:
            for ex in self.__winFulExs:
                nameTable.names.append(ex.getNameRecord())
        if needWinLgc:
            for ex in self.__winLgcExs:
                nameTable.names.append(ex.getNameRecord())
        for ex in self.__miscExs:
            nameTable.names.append(ex.getNameRecord())
        return nameTable

    # Get Python Unicode string from either bytes or uString.
    def __getUstring(self, string):
        if isinstance(string, bytes):
            return string.decode(errors = "ignore")
        else:
            return string

    # It must be called right before building the `name` table!
    def __genPSCIDFFmacExs(self):
        if not self.__pscidffustr:
            return
        macPltEncIDs = set()
        for macEx in self.__macExs:
            macPltEncIDs.add(macEx.getPlatEncID())
        for macPltEncID in macPltEncIDs:
            self.addNameEx(self.__pscidffustr, 20, 1, macPltEncID, 65535)
        return

    # This is rather undocumented in the spec: string length of nameID 1 must be less than 32, 
    # otherwise the font will not load in Windows.
    def __truncateLimitedExs(self):
        exSetArray = [self.__macExs, self.__winSymExs, self.__winBMPExs, self.__winFulExs, self.__winLgcExs, self.__miscExs]
        for exSet in exSetArray:
            for ex in exSet:
                string = ex.getString()
                if ex.getNameID() == 1 and len(string) > 31:
                    print("WARNING: Legacy family name is longer than 31 characters. It will be truncated.", file = sys.stderr)
                    print("Legacy family name: " + string, file = sys.stderr)
                    ex.setString(string[:31])
                elif ex.getNameID() == 6 and len(string) > 63:
                    print("WARNING: PostScript name is longer than 63 bytes. It will be truncated.", file = sys.stderr)
                    print("PostScript name: " + string, file = sys.stderr)
                    ex.setString(string[:63])
                else:
                    continue
        return

    # It must be called right before building the `name` table!
    def __removeUnsupportedChars(self):
        for ex in self.__macExs:
            macRec = ex.getNameRecord()
            # Iteratively remove all unsupported chars cause UnicodeEncodeError.
            while True:
                try:
                    nativeStr = macRec.toBytes()
                    break
                except UnicodeEncodeError as uExp:
                    tempUstr = macRec.string[:uExp.start]
                    if uExp.end < len(macRec.string):
                        tempUstr += macRec.string[uExp.end:]
                    macRec.string = tempUstr
                    continue
            ex.setString(nativeStr)
        return


# A name record class enhanced for HashSet.
class NameRecordEx(object):

    def __init__(self, nameRecord = None):
        if nameRecord:
            self.__string = nameRecord.string
            self.__nameID = nameRecord.nameID
            self.__platformID = nameRecord.platformID
            self.__platEncID = nameRecord.platEncID
            self.__langID = nameRecord.langID
        else:
            self.clear()

    # Without string comparation, Exs with identical metadata can be overwritten.
    def __hash__(self):
        return self.__nameID + \
            self.__platformID + \
            self.__platEncID + \
            self.__langID # + \
            # hash(self.__string)

    def __eq__(self, another):
        return type(self) == type(another) and \
            self.__nameID == another.getNameID() and \
            self.__platformID == another.getPlatformID() and \
            self.__platEncID == another.getPlatEncID() and \
            self.__langID == another.getLangID() # and \
            # self.__string == another.getString()

    def isEmpty(self):
        return not self.__string and \
            not self.__nameID and \
            not self.__platformID and \
            not self.__platEncID and \
            not self.__langID

    def clear(self):
        self.__string = None
        self.__nameID = None
        self.__platformID = None
        self.__platEncID = None
        self.__langID = None
        return

    def setString(self, string):
        self.__string = string
        return

    def setNameID(self, nameID):
        self.__nameID = nameID
        return

    def setPlatformID(self, platformID):
        self.__platformID = platformID
        return

    def setPlatEncID(self, platEncID):
        self.__platEncID = platEncID
        return

    def setLangID(self, langID):
        self.__langID = langID
        return

    def setEx(self, string, nameID, platformID, platEncID, langID):
        self.__string = string
        self.__nameID = nameID
        self.__platformID = platformID
        self.__platEncID = platEncID
        self.__langID = langID
        return

    def setFromNameRecord(self, nameRecord):
        self.__string = nameRecord.string
        self.__nameID = nameRecord.nameID
        self.__platformID = nameRecord.platformID
        self.__platEncID = nameRecord.platEncID
        self.__langID = nameRecord.langID
        return

    def getString(self):
        return self.__string

    def getNameID(self):
        return self.__nameID

    def getPlatformID(self):
        return self.__platformID

    def getPlatEncID(self):
        return self.__platEncID

    def getLangID(self):
        return self.__langID

    def getNameRecord(self):
        if self.isEmpty():
            return None
        else:
            return Workers.NameWorker.makeName(self.__string, 
                self.__nameID, self.__platformID, 
                self.__platEncID, self.__langID
                )

