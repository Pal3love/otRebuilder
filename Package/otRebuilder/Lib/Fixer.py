#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)

from otRebuilder.Lib import Builders
from otRebuilder.Lib import Constants
from otRebuilder.Lib import Workers


class Fixer(Workers.Worker):

    def __init__(self, ttfontObj, jobsObj):
        super(Fixer, self).__init__(ttfontObj, jobsObj)

    # Convert Apple TrueType font to MS-Adobe OpenType font
    def fixHeader(self):
        if self.font.sfntVersion == "true":
            self.font.sfntVersion = "\x00\x01\x00\x00"
        return

    def fixHead(self):
        head = self.font.get("head")
        head.tableVersion = 1.0
        head.magicNumber = 0x5F0F3CF5
        if self.jobs.init_removeHinting:
            head.flags &= 0b101011110001011
        else:
            head.flags &= 0b111011110011111
        head.macStyle &= 0b1100011
        return

    def fixHhea(self):
        hhea = self.font.get("hhea")
        hhea.tableVersion = 0x10000
        hhea.reserved0 = 0
        hhea.reserved1 = 0
        hhea.reserved2 = 0
        hhea.reserved3 = 0
        hhea.metricDataFormat = 0
        return

    def fixMaxp(self):
        maxp = self.font.get("maxp")
        if self.font.has_key("glyf"):
            if maxp.tableVersion != 0x00010000:
                maxp.tableVersion = 0x00010000
                # Add necessary attributes for TrueType `maxp`.
                maxp.maxZones = 1
                maxp.maxTwilightPoints = 0
                maxp.maxStorage = 0
                maxp.maxFunctionDefs = 0
                maxp.maxInstructionDefs = 0
                maxp.maxStackElements = 0
                maxp.maxSizeOfInstructions = 0
                maxp.maxComponentElements = max(
                    len(g.components if hasattr(g, "components") else [])
                    for g in self.font.get("glyf").glyphs.values())
                # Add remaining necessary attrs by recalculating BBoxs.
                self.font.recalcBBoxes = True
        else:
            maxp.tableVersion = 0x00005000
        return

    def fixPost(self):
        post = self.font.get("post")
        if self.font.has_key("CFF "):
            post.formatType = 3.0
        return

    # We don't have to worry about unused attributes because the compiler compiles only necessary ones.
    def fixOS2f2(self):
        OS2f2 = self.font.get("OS/2")
        if OS2f2.usWeightClass > 1000 or OS2f2.usWeightClass < 1:
            OS2f2.usWeightClass = Workers.OS2f2Worker.getUsWeightClass(self.font["head"])
        if OS2f2.usWidthClass > 9 or OS2f2.usWidthClass < 1:
            OS2f2.usWidthClass = 5  # Medium width
        OS2f2.fsType &= 0b1110
        if self.jobs.general_recalc:
            OS2f2.recalcUnicodeRanges(self.font)
            if OS2f2.panose.bFamilyType == 2 and OS2f2.panose.bProportion == 9:  # monospaced font
                OS2f2.xAvgCharWidth = Workers.OS2f2Worker.recalcXAvgCharWidth(self.font["hmtx"], True)
            else:
                OS2f2.xAvgCharWidth = Workers.OS2f2Worker.recalcXAvgCharWidth(self.font["hmtx"], False)
        if OS2f2.version < 4:
            OS2f2.fsSelection &= 0b1100001
        else:
            OS2f2.fsSelection &= 0b1111100001
        return

    def fixFromCFF(self):
        head = self.font.get("head")
        post = self.font.get("post")
        cffT = self.font.get("CFF ")
        cff = None
        if hasattr(cffT, "cff") and cffT.cff:
            cff = cffT.cff
        else:
            return
        if hasattr(cff, "topDictIndex") and len(cff.topDictIndex) > 0:
            if cff.topDictIndex[0].FontBBox != cff.topDictIndex[0].defaults["FontBBox"]:
                head.xMin = int(cff.topDictIndex[0].FontBBox[0])
                head.yMin = int(cff.topDictIndex[0].FontBBox[1])
                head.xMax = int(cff.topDictIndex[0].FontBBox[2])
                head.yMax = int(cff.topDictIndex[0].FontBBox[3])
            if cff.topDictIndex[0].ItalicAngle != cff.topDictIndex[0].defaults["ItalicAngle"]:
                post.italicAngle = cff.topDictIndex[0].ItalicAngle
            if cff.topDictIndex[0].isFixedPitch != cff.topDictIndex[0].defaults["isFixedPitch"]:
                post.isFixedPitch = cff.topDictIndex[0].isFixedPitch
            if cff.topDictIndex[0].UnderlineThickness != cff.topDictIndex[0].defaults["UnderlineThickness"]:
                post.underlineThickness = int(cff.topDictIndex[0].UnderlineThickness)
            if hasattr(cff.topDictIndex[0], "UnderlinePosition"):  # It doesn't have default value.
                post.underlinePosition = int(cff.topDictIndex[0].UnderlinePosition)
        return

    def fixCmap(self):
        cmap = self.font.get("cmap")
        cmap.tableVersion = 0
        sourceSub, unsupported = self.__fixCmap_categorize(cmap)
        self.__fixCmap_helper(sourceSub)
        newSub = self.__fixCmap_buildNew(sourceSub)
        newSub.extend(unsupported)
        cmap.tables = newSub
        return

    def fixName(self):
        builder = Builders.NameTableBuilder()
        name = self.font.get("name")
        cmap = self.font.get("cmap")
        cffT = self.font.get("CFF ")
        macNamRecs = []
        winNamRecs = []
        unsupported = []
        # Only supported name records listed in Constants.py will be processed.
        supportedMacLangs = Constants.MAC_LANGCODE_TO_WIN.keys()
        supportedWinLangs = Constants.WIN_LANGCODE_TO_MAC.keys()
        # Add PostScript Name and PostScript CID Findfont name from the source name table.
        if cffT:
            builder.addPostScriptNameFromCFFtable(cffT)
        else:
            builder.addPostScriptNameFromNameTable(name)
        builder.addPSCIDFFNameFromNameTable(name)
        for namRec in name.names:
            # Decode everything, including MS Unicode (utf_16_be), to Python Unicode first.
            try:
                namRec.string = namRec.toUnicode()
            except UnicodeDecodeError:
                unsupported.append(namRec)
                continue
            if namRec.nameID in [6, 20]:
                continue  # Those items have been already added
            elif Workers.NameWorker.isMacintosh(namRec):
                if namRec.langID in supportedMacLangs:
                    macNamRecs.append(namRec)
                    builder.addNameFromNameRecord(namRec)
                else:
                    unsupported.append(namRec)
            elif Workers.NameWorker.isWindows(namRec):
                if namRec.langID in supportedWinLangs:
                    winNamRecs.append(namRec)
                    builder.addNameFromNameRecord(namRec)
                else:
                    unsupported.append(namRec)
            else:
                unsupported.append(namRec)
        # The following order must be Win->Mac then Mac->Win!
        # Convert Win names into Mac
        for namRec in winNamRecs:
            if namRec.nameID in [16, 17]:
                continue  # Macintosh platform doesn't need preferred family/subfamily.
            tmpMacRec = Workers.NameWorker.winName2Mac(namRec)
            if tmpMacRec is None:
                continue  
            builder.addMacNameEx(tmpMacRec.string, tmpMacRec.nameID, tmpMacRec.langID)
        # Convert Mac names into Win
        for namRec in macNamRecs:
            if namRec.nameID == 18:
                continue  # Windows platform doesn't need Mac compatible full.
            tmpWinRecs = Workers.NameWorker.macName2WinAll(namRec, 1)
            if tmpWinRecs is None:
                continue
            for tmpWinRec in tmpWinRecs:
                builder.addWinNameEx(tmpWinRec.string, tmpWinRec.nameID, tmpWinRec.langID)
        # Update the `name` table with `cmap` consistency
        name = builder.build(cmap)
        name.names.extend(unsupported)
        self.font["name"] = name
        return

    def __fixCmap_categorize(self, cmap):
        # sourceSub = [uniFull, uniBMP, macRoman, uniBMPfromMacRoman]
        sourceSub = [None for i in range(4)]
        unsupported = []
        for subtable in cmap.tables:
            if subtable.isUnicode():
                if subtable.format == 12:  # Full repertoire
                    # Make sure MS subtables are prior than pure Unicode's
                    if subtable.platformID == 3:
                        sourceSub[0] = subtable
                    elif subtable.platformID == 0 and sourceSub[0] is None:
                        sourceSub[0] = subtable
                    else:
                        pass
                elif subtable.format in [4, 6]:  # BMP
                    if subtable.platformID == 3:
                        sourceSub[1] = subtable
                    elif subtable.platformID == 0 and sourceSub[1] is None:
                        sourceSub[1] = subtable
                    else:
                        pass
                else:
                    unsupported.append(subtable)
            elif Workers.CmapWorker.isMacRoman(subtable):
                sourceSub[2] = subtable
            else:
                unsupported.append(subtable)
        return sourceSub, unsupported

    def __fixCmap_helper(self, sourceSubtables):
        for level in range(3):
            if not sourceSubtables[level + 1]:
                sourceSubtables[level + 1] = \
                    self.__fixCmap_genNextSub(sourceSubtables[level])
        return

    def __fixCmap_genNextSub(self, cmapSubtable):
        if cmapSubtable is None:  # If current layer is empty
            return None  # Generate None as well
        elif cmapSubtable.isUnicode():  # Unicode subtable
            if cmapSubtable.format == 12:  # Full repertoire
                return self.__fixCmap_full2Bmp(cmapSubtable)
            elif cmapSubtable.format in [4, 6]:  # BMP
                return self.__fixCmap_bmp2Mac(cmapSubtable)
            else:  # Impossible to get here
                pass
        elif Workers.CmapWorker.isMacRoman(cmapSubtable):
            return self.__fixCmap_mac2Bmp(cmapSubtable)
        else:
            return None

    def __fixCmap_buildNew(self, sourceSubtables):
        newSubtables = []
        if sourceSubtables[0]:  # uniFull
            newSubtables.extend(
                Workers.CmapWorker.subtables_buildFmt12sFromFull(sourceSubtables[0])
                )
        if sourceSubtables[1]:  # uniBMP
            newSubtables.extend(
                Workers.CmapWorker.subtables_buildFmt4sFromBMP(sourceSubtables[1])
                )
        if sourceSubtables[2]:  # macRoman
            # **Mac Office 2011** sometimes overrides macRoman to all subtables.
            # In case of that, we temporarily turn it off.
            if not self.jobs.rebuild_macOffice:
                newSubtables.append(sourceSubtables[2])
        if sourceSubtables[3] and not sourceSubtables[1]:  # uniBMPfromMacRoman
            newSubtables.extend(
                Workers.CmapWorker.subtables_buildFmt4sFromBMP(sourceSubtables[3])
                )
        return newSubtables

    def __fixCmap_full2Bmp(self, cmapSubFull):
        subtables = Workers.CmapWorker.subtables_buildUnicodeAllFromFull(cmapSubFull)
        return subtables[0]

    def __fixCmap_bmp2Mac(self, cmapSubBmp):
        return Workers.CmapWorker.subtable_buildMacRomanFromUnicode(cmapSubBmp)

    def __fixCmap_mac2Bmp(self, cmapSubMac):
        subtables = Workers.CmapWorker.subtables_buildFmt4sFromMacRoman(cmapSubMac)
        return subtables[0]

