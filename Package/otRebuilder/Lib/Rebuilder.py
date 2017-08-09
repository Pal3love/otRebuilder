#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)

import re
from time import mktime
from datetime import datetime
from fontTools.misc.timeTools import epoch_diff
from fontTools.ttLib import newTable
from fontTools.ttLib.tables.ttProgram import Program

from otRebuilder.Lib import Builders
from otRebuilder.Lib import Constants
from otRebuilder.Lib import Workers
from otRebuilder.Lib import Fixer


class Rebuilder(Workers.Worker):

    def __init__(self, ttfontObj, jobsObj, configDict):
        super(Rebuilder, self).__init__(ttfontObj, jobsObj)
        self.config = configDict  # None if -c is not specified

    def rebuildGasp(self):
        gasp = newTable("gasp")
        gasp.version = 1
        gasp.gaspRange = {65535: 10}
        self.font["gasp"] = gasp
        return

    # Create global instruction table with basic rendering settings
    def rebuildPrep(self):
        hintProg = Program()
        hintProg.fromBytecode([184, 1, 255, 133, 184, 0, 4, 141])
        prep = newTable("prep")
        prep.program = hintProg
        self.font["prep"] = prep
        return

    def rebuildDSIG(self):
        DSIG = newTable("DSIG")
        DSIG.ulVersion = 1
        DSIG.usNumSigs = 0
        DSIG.usFlag = 0
        DSIG.signatureRecords = []
        self.font["DSIG"] = DSIG
        return

    def rebuildCmap(self):
        cmap = self.font.get("cmap")
        cmap.tableVersion = 0
        # sourceSub = [winBMP, winFull, macRoman, macBMP, macFull, macLastResort]
        sourceSub = [None for i in range(7)]
        unsupported = []  # Unsupported Unicode subtables, like winSymbol, macUVS, etc.
        newSub = []
        for subtable in cmap.tables:
            if subtable.isUnicode():
                if Workers.CmapWorker.isLastResort(subtable):
                    sourceSub[5] = subtable  # macLastResort
                elif subtable.format == 12:  # Full repertoire
                    if subtable.platformID == 3:
                        sourceSub[1] = subtable  # winFull
                    elif subtable.platformID == 0:
                        sourceSub[4] = subtable  # macFull
                    else:
                        pass
                elif subtable.format in [4, 6]:  # BMP
                    if subtable.platformID == 3:
                        sourceSub[0] = subtable  # winBMP
                    elif subtable.platformID == 0:
                        sourceSub[3] = subtable  # macBMP
                    else:
                        pass
                else:
                    unsupported.append(subtable)
            elif Workers.CmapWorker.isMacRoman(subtable):
                sourceSub[2] = subtable  # macRoman
            else:
                continue
        # Build all from top to bottom.
        # Priority ranking: macLastResort > winFull > macFull > winBMP > macBMP > macRoman
        # *MS Office 2011 for Mac* sometimes overrides macRoman to all subtables.
        # In case of that, we temporarily turn it off.
        if sourceSub[5]:  # macLastResort, 4->3 subtables in total
            newSub.extend(Workers.CmapWorker.subtables_buildfmt13sFromLastResort(sourceSub[5]))
            # newSub.append(Workers.CmapWorker.subtable_buildMacRomanFromUnicode(sourceSub[5]))
        elif sourceSub[1]:  # winFull, 5->4 subtables in total
            newSub.extend(Workers.CmapWorker.subtables_buildUnicodeAllFromFull(sourceSub[1]))
            # newSub.append(Workers.CmapWorker.subtable_buildMacRomanFromUnicode(sourceSub[1]))
        elif sourceSub[4]:  # macFull, 5->4 subtables in total
            newSub.extend(Workers.CmapWorker.subtables_buildUnicodeAllFromFull(sourceSub[4]))
            # newSub.append(Workers.CmapWorker.subtable_buildMacRomanFromUnicode(sourceSub[4]))
        elif sourceSub[0]:  # winBMP, 3->2 subtables in total
            newSub.extend(Workers.CmapWorker.subtables_buildFmt4sFromBMP(sourceSub[0]))
            # newSub.append(Workers.CmapWorker.subtable_buildMacRomanFromUnicode(sourceSub[0]))
        elif sourceSub[3]:  # macBMP, 3->2 subtables in total
            newSub.extend(Workers.CmapWorker.subtables_buildFmt4sFromBMP(sourceSub[3]))
            # newSub.append(Workers.CmapWorker.subtable_buildMacRomanFromUnicode(sourceSub[3]))
        elif sourceSub[2]:  # macRoman, 3->2 subtables in total
            newSub.extend(Workers.CmapWorker.subtables_buildFmt4sFromMacRoman(sourceSub[2]))
            # newSub.append(sourceSub[2])
        else:
            pass
        newSub.extend(unsupported)
        cmap.tables = newSub
        # Recheck consistency between `cmap` and `name` if configDict is not specified (with fix_name set).
        if self.jobs.fix_name:
            fixer = Fixer.Fixer(self.font, self.jobs)
            fixer.fixName()
            del fixer
        return

    def rebuildByConfig(self):
        if self.config is None:
            return
        self.__updateCFF()
        self.__updateHead()
        self.__updateHhea()
        self.__updateVhea()
        self.__updatePost()
        self.__updateOS2f2()
        self.__rebuildName()
        return

    # This method must be called first so that rebuildName() can update its psName property later.
    def __updateCFF(self):
        cffT = self.font.get("CFF ")
        if not cffT:
            return
        general = self.config.get("General")
        style = self.config.get("Style")
        name = self.config.get("Name")
        builder = Builders.cffTopDictBuilder()
        if general:  # Version priority: `head`.fontRevision < *specified*
            builder.setVersion(self.font["head"].fontRevision)
            builder.setVersion(general.get("version"))
            builder.setROS(general.get("cidRegistry"), 
                general.get("cidOrdering"), 
                general.get("cidSupplement")
                )
        if style:
            styleLink = style.get("styleLink")
            weightScale = style.get("weightScale")
            if styleLink in range(0, 5):
                if styleLink == 2:
                    builder.setItalicAngle(0.0)
                    builder.setWeight(Constants.STANDARD_WEIGHTS[6])
                elif styleLink == 3:
                    builder.setItalicAngle(Constants.DEFAULT_ITALIC_ANGLE)
                    builder.setWeight(Constants.STANDARD_WEIGHTS[3])
                elif styleLink == 4:
                    builder.setItalicAngle(Constants.DEFAULT_ITALIC_ANGLE)
                    builder.setWeight(Constants.STANDARD_WEIGHTS[6])
                else:
                    builder.setItalicAngle(0.0)
                    builder.setWeight(Constants.STANDARD_WEIGHTS[3])
            if weightScale in range(1, 11):
                builder.setWeight(Constants.STANDARD_WEIGHTS[weightScale - 1])
            builder.setMonospaced(style.get("isMonospaced"))
            builder.setItalicAngle(style.get("italicAngle"))
            builder.setUnderlinePosition(style.get("underlinePosition"))
            builder.setUnderlineThickness(style.get("underlineThickness"))
        if name and name.get("en"):
            family = self.__loadUstr(name["en"].get("fontFamily"))
            subfamily = self.__loadUstr(name["en"].get("fontSubfamily"))
            fullName = self.__loadUstr(name["en"].get("fontFullName"))
            if family:
                builder.clearCFFnameMenu(cffT)
            else:  # No family, no update
                builder.applyToCFFtable(cffT)
                return
            if not fullName and (family and subfamily):
                fullName = family + u" " + subfamily
            builder.setFamily(family)
            builder.setFullName(fullName)
            builder.setPostScriptName(name["en"].get("postScriptName"))
            builder.setCopyright(name["en"].get("copyright"))
            builder.setTrademark(name["en"].get("trademark"))
        builder.applyToCFFtable(cffT)
        return

    def __updateHead(self):
        headT = self.font.get("head")
        if not headT:
            return
        general = self.config.get("General")
        style = self.config.get("Style")
        if general:
            version = general.get("version")
            createdTime = general.get("createdTime")
            modifiedTime = general.get("modifiedTime")
            if isinstance(version, float) or isinstance(version, int):
                headT.fontRevision = float(abs(version))
            if isinstance(createdTime, datetime):
                headT.created = long(mktime(datetime.timetuple(createdTime)) - epoch_diff)
            if isinstance(modifiedTime, datetime):
                headT.modified = long(mktime(datetime.timetuple(modifiedTime)) - epoch_diff)
                self.font.recalcTimestamp = False
        if style:
            styleLink = style.get("styleLink")
            widthScale = style.get("widthScale")
            if styleLink in range(0, 5):
                # Clear related bits first
                headT.macStyle &= ~0b11
                if styleLink == Constants.STYLELINK_BOLD:
                    headT.macStyle |= 1
                elif styleLink == Constants.STYLELINK_ITALIC:
                    headT.macStyle |= 1<<1
                elif styleLink == Constants.STYLELINK_BOLDITALIC:
                    headT.macStyle |= 1
                    headT.macStyle |= 1<<1
                else:
                    pass
            if widthScale in range(1, 10):
                headT.macStyle &= ~(0b11<<5)
                if widthScale < 5:
                    headT.macStyle |= 1<<5
                elif widthScale > 5:
                    headT.macStyle |= 1<<6
                else:
                    pass
        return

    def __updateHhea(self):
        hheaT = self.font.get("hhea")
        if not hheaT:
            return
        metrics = self.config.get("Metrics")
        if metrics:
            hheaAscender = metrics.get("hheaAscender")
            hheaDescender = metrics.get("hheaDescender")
            hheaLineGap = metrics.get("hheaLineGap")
            if isinstance(hheaAscender, float) or isinstance(hheaAscender, int):
                hheaT.ascent = int(hheaAscender)
            if isinstance(hheaDescender, float) or isinstance(hheaDescender, int):
                hheaT.descent = int(hheaDescender)
            if isinstance(hheaLineGap, float) or isinstance(hheaLineGap, int):
                hheaT.lineGap = int(hheaLineGap)
        return

    def __updateVhea(self):
        vheaT = self.font.get("vhea")
        if not vheaT:
            return
        metrics = self.config.get("Metrics")
        if metrics:
            vheaAscender = metrics.get("vheaAscender")
            vheaDescender = metrics.get("vheaDescender")
            vheaLineGap = metrics.get("vheaLineGap")
            if isinstance(vheaAscender, float) or isinstance(vheaAscender, int):
                vheaT.ascent = int(vheaAscender)
            if isinstance(vheaDescender, float) or isinstance(vheaDescender, int):
                vheaT.descent = int(vheaDescender)
            if isinstance(vheaLineGap, float) or isinstance(vheaLineGap, int):
                vheaT.lineGap = int(vheaLineGap)
        return

    def __updatePost(self):
        postT = self.font.get("post")
        if not postT:
            return
        style = self.config.get("Style")
        if style:
            isMonospaced = style.get("isMonospaced")
            styleLink = style.get("styleLink")
            italicAngle = style.get("italicAngle")
            underlinePosition = style.get("underlinePosition")
            underlineThickness = style.get("underlineThickness")
            if isinstance(isMonospaced, bool):
                if isMonospaced:
                    postT.isFixedPitch = 1
                else:
                    postT.isFixedPitch = 0
            if styleLink in range(0, 5):
                if styleLink > 2:
                    postT.italicAngle = Constants.DEFAULT_ITALIC_ANGLE
                else:
                    postT.italicAngle = 0.0
            if isinstance(italicAngle, float) or isinstance(italicAngle, int):
                postT.italicAngle = float(italicAngle)
            if isinstance(underlinePosition, float) or isinstance(underlinePosition, int):
                postT.underlinePosition = int(underlinePosition)
            if isinstance(underlineThickness, float) or isinstance(underlineThickness, int):
                postT.underlineThickness = int(underlineThickness)
        return

    def __updateOS2f2(self):
        OS2f2T = self.font.get("OS/2")
        if not OS2f2T:
            return
        self.__updateOS2f2_addNewAttrs()
        general = self.config.get("General")
        name = self.config.get("Name")
        metrics = self.config.get("Metrics")
        style = self.config.get("Style")
        if general:
            embeddingRestriction = general.get("embeddingRestriction")
            activeCodepages = general.get("codepages")
            if embeddingRestriction in range(0, 4):
                if embeddingRestriction == 1:  # Editable
                    OS2f2T.fsType = 8
                elif embeddingRestriction == 2:  # Preview & Print
                    OS2f2T.fsType = 4
                elif embeddingRestriction == 3:  # Restricted
                    OS2f2T.fsType = 2
                else:  # No Restriction
                    OS2f2T.fsType = 0
            if isinstance(activeCodepages, list) and \
                (OS2f2T.version > 0 or self.jobs.rebuild_allowUpgrade):
                OS2f2T.ulCodePageRange1 = 0
                OS2f2T.ulCodePageRange2 = 0
                for codepage in activeCodepages:
                    if Constants.CHARSET_TO_CODEPAGE_RANGE_1.has_key(codepage):
                        OS2f2T.ulCodePageRange1 |= 1<<Constants.CHARSET_TO_CODEPAGE_RANGE_1[codepage]
                    elif Constants.CHARSET_TO_CODEPAGE_RANGE_2.has_key(codepage):
                        OS2f2T.ulCodePageRange2 |= 1<<Constants.CHARSET_TO_CODEPAGE_RANGE_2[codepage]
                    else:
                        continue
                if OS2f2T.version < 1:
                    OS2f2T.version = 1
        if name and name.get("en") and name["en"].get("distributorID"):
            uArcID = re.sub(r"[^A-Za-z0-9]+", r"", name["en"]["distributorID"])
            arcID = uArcID.encode("ascii")
            arcID += "    "
            OS2f2T.achVendID = arcID[:4]
        if metrics:
            typoAscender = metrics.get("typoAscender")
            typoDescender = metrics.get("typoDescender")
            typoLineGap = metrics.get("typoLineGap")
            winAscender = metrics.get("winAscender")
            winDescender = metrics.get("winDescender")
            if isinstance(typoAscender, float) or isinstance(typoAscender, int):
                OS2f2T.sTypoAscender = int(typoAscender)
            if isinstance(typoDescender, float) or isinstance(typoDescender, int):
                OS2f2T.sTypoDescender = int(typoDescender)
            if isinstance(typoLineGap, float) or isinstance(typoLineGap, int):
                OS2f2T.sTypoLineGap = int(typoLineGap)
            if isinstance(winAscender, float) or isinstance(winAscender, int):
                OS2f2T.usWinAscent = abs(int(winAscender))
            if isinstance(winDescender, float) or isinstance(winDescender, int):
                OS2f2T.usWinDescent = abs(int(winDescender))
        if style:
            widthScale = style.get("widthScale")
            weightScale = style.get("weightScale")
            styleLink = style.get("styleLink")
            useTypoMetrics = style.get("useTypoMetrics")
            forcePreferredFamily = style.get("forcePreferredFamily")
            isMonospaced = style.get("isMonospaced")
            monoLatinWidth = style.get("monoLatinWidth")
            ibmClass = style.get("IBM")
            panose = style.get("PANOSE")
            if widthScale in range(1, 10):
                OS2f2T.usWidthClass = Constants.WIDTH_SCALES[widthScale - 1]
                self.__updateOS2f2_width2Panose(widthScale, OS2f2T.panose)
            if weightScale in range(1, 11):
                # OS2f2T.usWeightClass = Constants.STANDARD_WEIGHT_SCALES[weightScale - 1]
                OS2f2T.usWeightClass = Constants.WIN_SAFE_WEIGHT_SCALES[weightScale - 1]
                if OS2f2T.panose.bFamilyType in [2, 3, 4]:
                    OS2f2T.panose.bWeight = weightScale + 1
                OS2f2T.fsSelection &= ~0b1111110  # Clear regular, bold and legacy bits
                if weightScale == 4:
                    OS2f2T.fsSelection |= 1<<6
                elif weightScale > 6:
                    OS2f2T.fsSelection |= 1<<5
                else:
                    pass
            if styleLink in range(0, 5):
                OS2f2T.fsSelection &= ~1  # Clear italic bit
                if styleLink == Constants.STYLELINK_REGULAR:
                    OS2f2T.fsSelection |= 1<<6
                    if not weightScale:
                        OS2f2T.usWeightClass = 400
                        OS2f2T.fsSelection &= ~0b0111111
                        if OS2f2T.panose.bFamilyType in [2, 3, 4]:
                            OS2f2T.panose.bWeight = 5
                elif styleLink == Constants.STYLELINK_BOLD:
                    OS2f2T.fsSelection |= 1<<5
                    if not weightScale:
                        OS2f2T.usWeightClass = 700
                        OS2f2T.fsSelection &= ~0b1011111
                        if OS2f2T.panose.bFamilyType in [2, 3, 4]:
                            OS2f2T.panose.bWeight = 8
                elif styleLink == Constants.STYLELINK_ITALIC:
                    OS2f2T.fsSelection |= 1
                    if not weightScale:
                        OS2f2T.usWeightClass = 400
                        OS2f2T.fsSelection &= ~0b1111110
                        if OS2f2T.panose.bFamilyType in [2, 3, 4]:
                            OS2f2T.panose.bWeight = 5
                elif styleLink == Constants.STYLELINK_BOLDITALIC:
                    OS2f2T.fsSelection |= 1<<5
                    OS2f2T.fsSelection |= 1
                    if not weightScale:
                        OS2f2T.usWeightClass = 700
                        OS2f2T.fsSelection &= ~0b1011110
                        if OS2f2T.panose.bFamilyType in [2, 3, 4]:
                            OS2f2T.panose.bWeight = 8
                else:  # Constants.STYLELINK_NONE
                    pass
            if isinstance(useTypoMetrics, bool) and \
                (OS2f2T.version > 3 or self.jobs.rebuild_allowUpgrade):
                if useTypoMetrics:
                    OS2f2T.fsSelection |= 1<<7
                else:
                    OS2f2T.fsSelection &= ~(1<<7)
                if OS2f2T.version < 4:
                    OS2f2T.version = 4
            if isinstance(forcePreferredFamily, bool) and \
                (OS2f2T.version > 3 or self.jobs.rebuild_allowUpgrade):
                if forcePreferredFamily:
                    OS2f2T.fsSelection |= 1<<8
                else:
                    OS2f2T.fsSelection &= ~(1<<8)
                if OS2f2T.version < 4:
                    OS2f2T.version = 4
            if isinstance(isMonospaced, bool):
                if isMonospaced:
                    # Update average char width
                    if (isinstance(monoLatinWidth, int) or isinstance(monoLatinWidth, float)):
                        OS2f2T.xAvgCharWidth = int(abs(monoLatinWidth))
                    elif self.jobs.general_recalc:
                        OS2f2T.xAvgCharWidth = Workers.OS2f2Worker.recalcXAvgCharWidth(self.font["hmtx"], True)
                    else:
                        pass
                    # Update PANOSE
                    if OS2f2T.panose.bFamilyType in [2, 4]:
                        OS2f2T.panose.bProportion = 9
                    elif OS2f2T.panose.bFamilyType in [3, 5]:
                        OS2f2T.panose.bProportion = 3
                    else:
                        pass
                else:
                    # Update average char width
                    if self.jobs.general_recalc:
                        OS2f2T.xAvgCharWidth = Workers.OS2f2Worker.recalcXAvgCharWidth(self.font["hmtx"], False)
                    # Update PANOSE
                    if OS2f2T.panose.bFamilyType == 2:
                        OS2f2T.panose.bProportion = 3
                    elif OS2f2T.panose.bFamilyType in [3, 5]:
                        OS2f2T.panose.bProportion = 2
                    elif OS2f2T.panose.bFamilyType == 4:
                        OS2f2T.panose.bProportion = 5
                    else:
                        pass
            if ibmClass:
                styleClass = OS2f2T.sFamilyClass>>8
                styleSubclass = OS2f2T.sFamilyClass & 0b11111111
                if ibmClass.get("ibmStyleClass") in range(0, 16):
                    styleClass = ibmClass.get("ibmStyleClass")
                if ibmClass.get("ibmStyleSubclass") in range(0, 16):
                    styleSubclass = ibmClass.get("ibmStyleSubclass")
                OS2f2T.sFamilyClass = (styleClass<<8) + styleSubclass
            if panose:
                if panose.get("familykind") in range(0, 6):
                    OS2f2T.panose.bFamilyType = panose.get("familykind")
                if panose.get("subkind1") in range(0, 17):
                    OS2f2T.panose.bSerifStyle = panose.get("subkind1")
                if panose.get("subkind2") in range(0, 17):
                    OS2f2T.panose.bWeight = panose.get("subkind2")
                if panose.get("subkind3") in range(0, 17):
                    OS2f2T.panose.bProportion = panose.get("subkind3")
                if panose.get("subkind4") in range(0, 17):
                    OS2f2T.panose.bContrast = panose.get("subkind4")
                if panose.get("subkind5") in range(0, 17):
                    OS2f2T.panose.bStrokeVariation = panose.get("subkind5")
                if panose.get("subkind6") in range(0, 17):
                    OS2f2T.panose.bArmStyle = panose.get("subkind6")
                if panose.get("subkind7") in range(0, 17):
                    OS2f2T.panose.bLetterForm = panose.get("subkind7")
                if panose.get("subkind8") in range(0, 17):
                    OS2f2T.panose.bMidline = panose.get("subkind8")
                if panose.get("subkind9") in range(0, 17):
                    OS2f2T.panose.bXHeight = panose.get("subkind9")
        return

    def __updateOS2f2_addNewAttrs(self):
        OS2f2T = self.font.get("OS/2")
        # Add version 1 stuff:
        if not hasattr(OS2f2T, "ulCodePageRange1"):
            OS2f2T.ulCodePageRange1 = 0
        if not hasattr(OS2f2T, "ulCodePageRange2"):
            OS2f2T.ulCodePageRange2 = 0
        # Add version 2 stuff:
        if not hasattr(OS2f2T, "sxHeight"):
            OS2f2T.sxHeight = 0
        if not hasattr(OS2f2T, "sCapHeight"):
            OS2f2T.sCapHeight = 0
        if not hasattr(OS2f2T, "usDefaultChar"):
            OS2f2T.usDefaultChar = 0
        if not hasattr(OS2f2T, "usBreakChar"):
            OS2f2T.usBreakChar = 0
        if not hasattr(OS2f2T, "usMaxContext"):
            OS2f2T.usMaxContext = 0
        # Add version 5 stuff:
        if not hasattr(OS2f2T, "usLowerOpticalPointSize"):
            OS2f2T.usLowerOpticalPointSize = 0
        if not hasattr(OS2f2T, "usUpperOpticalPointSize"):
            OS2f2T.usUpperOpticalPointSize = 0
        return

    def __updateOS2f2_width2Panose(self, widthScale, panose):
        if panose.bFamilyType == 2:
            if widthScale in [1, 2]:
                panose.bProportion = 8
            elif widthScale in [3, 4]:
                panose.bProportion = 6
            elif widthScale in [6, 7]:
                panose.bProportion = 5
            elif widthScale in [8, 9]:
                panose.bProportion = 7
            else:
                pass
        elif panose.bFamilyType == 3:
            if widthScale in [1, 2]:
                panose.bContrast = 2
            elif widthScale in [3, 4]:
                panose.bContrast = 3
            elif widthScale == 5:
                panose.bContrast = 4
            elif widthScale in [6, 7]:
                panose.bContrast = 5
            elif widthScale in [8, 9]:
                panose.bContrast = 6
            else:
                pass
        elif panose.bFamilyType == 4:
            if widthScale == 1:
                panose.bProportion = 2
            elif widthScale == 2:
                panose.bProportion = 3
            elif widthScale in [3, 4]:
                panose.bProportion = 4
            elif widthScale == 5:
                panose.bProportion = 5
            elif widthScale in [6, 7]:
                panose.bProportion = 6
            elif widthScale == 8:
                panose.bProportion = 7
            elif widthScale == 9:
                panose.bProportion = 8
            else:
                pass
        return

    def __rebuildName(self):
        name = self.config.get("Name")
        if not name:
            return
        elif not name.get("en") or not self.__loadUstr(name["en"].get("fontFamily")):
            print("WARNING: No valid English font family detected in the configuration.", file = sys.stderr)
            print("Please make sure that [Name.en] and English \"fontFamily\" are correctly specified.", file = sys.stderr)
            print("Configurating section [Name] is now ignored.", file = sys.stderr)
            return

        en = name.get("en")
        general = self.config.get("General")
        style = self.config.get("Style")
        builder = Builders.NameTableBuilder()

        # Add PostScript CID Findfont name from old `name` table if it exists
        builder.addPSCIDFFNameFromNameTable(self.font.get("name"))

        # Get PostScript Name from `CFF ` table if it exists
        cffRecords = Workers.NameWorker.getRecordsFromCFF(self.font.get("CFF "))
        cffPSname = None
        if cffRecords:
            cffPSname = cffRecords[3].decode()

        # Basic name records's initialization
        # From here the English font family always exists.
        enFamily = en.get("fontFamily")
        enSubfamily = u"R"  # Default English subfamily
        enLgcFmly = enFamily  # Default English legacy family
        enWWS = [None, None, None]  # [enWidth, enWeight, enItalic]
        enFullName = psName = versionStr = uniqueID = None

        # Add style-links, generate English subfamily and legacy family
        if style:
            slCode = style.get("styleLink")
            widthScale = style.get("widthScale")
            weightScale = style.get("weightScale")
            italicAngle = style.get("italicAngle")
            # Try to get width, weight and italic string.
            if widthScale in range(1, 10) and widthScale != 5:
                enWWS[0] = Constants.ABBREVIATED_WIDTHS[widthScale - 1].decode()
            if weightScale in range(1, 11):
                enWWS[1] = Constants.ABBREVIATED_WEIGHTS[weightScale - 1].decode()
            if (isinstance(italicAngle, float) or isinstance(italicAngle, int)) and \
                italicAngle != 0:
                enWWS[2] = u"It"
            # Fill English subfamily with abbreviated strings from above
            isFirst = True
            for item in enWWS:
                if item:
                    if isFirst:
                        isFirst = False
                        enSubfamily = item
                    else:
                        enSubfamily += u" " + item
            # Add style-link and generate English legacy family
            # Version 1.3.4 update: now style-link only affects Win platform.
            if enWWS[0]:  # enWidth
                enLgcFmly += u" " + enWWS[0]
            if slCode == Constants.STYLELINK_REGULAR:
                builder.addStylelink(slCode)
                if weightScale and weightScale != 4:
                    enLgcFmly += u" " + enWWS[1]  # enWeight
            elif slCode == Constants.STYLELINK_BOLD:
                builder.addStylelink(slCode)
            elif slCode == Constants.STYLELINK_ITALIC:
                builder.addStylelink(slCode)
                if weightScale:
                    enLgcFmly += u" " + enWWS[1]
            elif slCode == Constants.STYLELINK_BOLDITALIC:
                builder.addStylelink(slCode)
            else:
                builder.addStylelink(Constants.STYLELINK_NONE)
                if enWWS[1]:  # enWeight
                    enLgcFmly += u" " + enWWS[1]
                if enWWS[2]:  # enItalic
                    enLgcFmly += u" " + enWWS[2]
        else:
            builder.addStylelink(Constants.STYLELINK_NONE)

        # Get English subfamily and legacy family from configuration
        if self.__loadUstr(en.get("fontSubfamily")):
            # Deal with Windows subfamily
            enSubfamily = self.__loadUstr(en.get("fontSubfamily"))
            # Generate English legacy family from enSubfamily and style-links
            enLgcFmly = enFamily + u" " + enSubfamily
            if style:
                slCode = style.get("styleLink")
                if slCode in [2, 4]:
                    enLgcFmly = enFamily
                elif slCode == Constants.STYLELINK_REGULAR:
                    for styl in Constants.REGULAR_STYLES:
                        # Use regex for case-insensitive removal
                        enLgcFmly = re.sub(r"(?i)\b" + styl + r"\b", "", enLgcFmly)
                elif slCode == Constants.STYLELINK_ITALIC:
                    for styl in Constants.ITALIC_STYLES:
                        enLgcFmly = re.sub(r"(?i)\b" + styl + r"\b", "", enLgcFmly)
                else:
                    pass
            while enLgcFmly != enLgcFmly.replace(u"  ", u" "):
                enLgcFmly = enLgcFmly.replace(u"  ", u" ")
            enLgcFmly = enLgcFmly.strip()

        # Deal with fullName with priority below:
        # family + subfamily < *specified*
        enFullName = enFamily + u" " + enSubfamily
        if self.__loadUstr(en.get("fontFullName")):
            enFullName = self.__loadUstr(en.get("fontFullName"))

        # Deal with psName with priority below:
        # fullName < cffPSname < *specified*
        # Incompatible chars will be discarded
        psName = enFamily.replace(u" ", u"") + u"-" + enSubfamily.replace(u" ", u"")
        if cffPSname:
            psName = cffPSname
        if self.__loadUstr(en.get("postScriptName")):
            psName = self.__loadUstr(en.get("postScriptName"))

        # Deal with versionStr with priority below:
        # `head`.fontRevision < General.version < *specified*
        # Strings without the decimal dot will be added
        versionStr = Workers.NameWorker.getVersionString(self.font["head"])
        if general:
            versionNum = general.get("version")
            if isinstance(versionNum, float) or isinstance(versionNum, int):
                versionStr = "Version " + "%.2f" % abs(versionNum)
        if self.__loadUstr(en.get("versionString")):
            versionStr = self.__loadUstr(en.get("versionString"))

        # Deal with uniqueID with priority below:
        # fullName + versionStr < *specified*
        uniqueID = enFullName + u"; " + versionStr
        if self.__loadUstr(en.get("uniqueID")):
            uniqueID = self.__loadUstr(en.get("uniqueID"))

        # Build English part of `name`
        # Family and subfamily
        builder.addMacNameEx(enFamily, 1, 0)
        builder.addMacNameEx(enSubfamily, 2, 0)
        builder.addWinNameEx(enLgcFmly, 1, 0x0409)
        # name ID 2 has been already added by addStylelink()
        builder.addWinNameEx(enFamily, 16, 0x0409)
        builder.addWinNameEx(enSubfamily, 17, 0x0409)
        # Full name
        builder.addEngName(enFullName, 4)  # name ID 4 for both platforms
        builder.addMacCompatibleFullEx(enFullName, 0)  # name ID 18 for only Macintosh
        # Other stuff
        builder.addFontUniqueID(uniqueID)     # name ID 3
        builder.addVersionString(versionStr)  # name ID 5
        builder.addPostScriptName(psName)     # name ID 6
        if self.__loadUstr(en.get("copyright")):
            builder.addEngName(en["copyright"], 0)
        if self.__loadUstr(en.get("trademark")):
            builder.addEngName(en["trademark"], 7)
        if self.__loadUstr(en.get("description")):
            builder.addEngName(en["description"], 10)
        if self.__loadUstr(en.get("designer")):
            builder.addEngName(en["designer"], 9)
        if self.__loadUstr(en.get("designerURL")):
            builder.addEngName(en["designerURL"], 12)
        if self.__loadUstr(en.get("distributor")):
            builder.addEngName(en["distributor"], 8)
        if self.__loadUstr(en.get("distributorURL")):
            builder.addEngName(en["distributorURL"], 11)
        if self.__loadUstr(en.get("license")):
            builder.addEngName(en["license"], 13)
        if self.__loadUstr(en.get("licenseURL")):
            builder.addEngName(en["licenseURL"], 14)

        # Add multilingual names
        enEssentials = (enFamily, enSubfamily, uniqueID, versionStr, psName)
        for langTag in name.keys():
            if langTag == "en":
                continue
            else:
                self.__rebuildName_addMultiLang(builder, langTag, enEssentials)

        self.font["name"] = builder.build(self.font["cmap"])
        return

    # enEssentials = (enFamily, enSubfamily, uniqueID, versionStr, psName)
    def __rebuildName_addMultiLang(self, nameTableBuilder, langTag, enEssentials):
        builder = nameTableBuilder
        style = self.config.get("Style")
        lang = self.config["Name"][langTag]

        lgcFmly = lgcSubfmly = None
        family = self.__loadUstr(lang.get("fontFamily"))
        subfamily = self.__loadUstr(lang.get("fontSubfamily"))
        fullName = self.__loadUstr(lang.get("fontFullName"))

        # While the Mac platform needs complete name IDs for each language, Windows doesn't.
        macFamily = enEssentials[0]      # Mac name ID 1
        macSubfamily = enEssentials[1]   # Mac name ID 2
        macUniqueID = enEssentials[2]    # Mac name ID 3
        macFullName = macFamily + u" " + macSubfamily #4
        macVersionStr = enEssentials[3]  # Mac name ID 5
        macPSname = enEssentials[4]      # Mac name ID 6

        # Deal with Windows legacy subfamily, which is the Win's mandatory item.
        if style.get("styleLink") in range(1, 5):
            lgcFmly = family  # family might be None
            slCode = style.get("styleLink")
            lgcSubfmly = Constants.LEGACY_WIN_STYLES[slCode - 1].decode()
        elif family and subfamily:
            lgcFmly = family + u" " + subfamily
            lgcSubfmly = u"Regular"
        else:
            lgcFmly = family
            lgcSubfmly = u"Regular"

        # The logic of Windows is different from Mac, so we can't merge both cases from above.
        if not fullName and family and subfamily:
            fullName = family + u" " + subfamily

        # Consolidate Mac family/subfamily/fullName
        if family:
            macFamily = family
        if subfamily:
            macSubfamily = subfamily
        if fullName:
            macFullName = fullName

        # Build multilingual part of `name`
        # Build Mac essentials first
        builder.addMacName(macFamily, 1, langTag)
        builder.addMacName(macSubfamily, 2, langTag)
        builder.addMacName(macUniqueID, 3, langTag)
        builder.addMacName(macFullName, 4, langTag)
        builder.addMacName(macVersionStr, 5, langTag)
        builder.addMacName(macPSname, 6, langTag)
        builder.addMacCompatibleFull(macFullName, langTag)
        # Build Win then
        builder.addWinNames(lgcSubfmly, 2, langTag)
        if lgcFmly:
            builder.addWinNames(lgcFmly, 1, langTag)
        if family:
            builder.addWinNames(family, 16, langTag)
        if subfamily:
            builder.addWinNames(subfamily, 17, langTag)
        if fullName:
            builder.addWinNames(fullName, 4, langTag)
        # Other stuff
        if self.__loadUstr(lang.get("copyright")):
            builder.addName(lang["copyright"], 0, langTag)
        if self.__loadUstr(lang.get("trademark")):
            builder.addName(lang["trademark"], 7, langTag)
        if self.__loadUstr(lang.get("description")):
            builder.addName(lang["description"], 10, langTag)
        if self.__loadUstr(lang.get("designer")):
            builder.addName(lang["designer"], 9, langTag)
        if self.__loadUstr(lang.get("designerURL")):
            builder.addName(lang["designerURL"], 12, langTag)
        if self.__loadUstr(lang.get("distributor")):
            builder.addName(lang["distributor"], 8, langTag)
        if self.__loadUstr(lang.get("distributorURL")):
            builder.addName(lang["distributorURL"], 11, langTag)
        if self.__loadUstr(lang.get("license")):
            builder.addName(lang["license"], 13, langTag)
        if self.__loadUstr(lang.get("licenseURL")):
            builder.addName(lang["licenseURL"], 14, langTag)
        return

    # Return uString and filter others out.
    def __loadUstr(self, uString):
        if uString and \
            (isinstance(uString, unicode) or isinstance(uString, str)):
            return uString.strip()
        else:
            return None

    # Add standard weight/width/slope strings on Mac name ID 2.
    # This is only designed for Mac Office 2011.
    def addMacOffice(self):
        name = self.font.get("name")
        OS2f2 = self.font.get("OS/2")
        if not name or not OS2f2:
            return
        # Get the Macintosh English subfamily
        macEnSubfmlyRec = name.getName(2, 1, 0, 0)
        if macEnSubfmlyRec is None:
            return
        macEnSubfmlyStr = macEnSubfmlyRec.toUnicode()
        # Replace nonstandard italic styles with "Italic"
        for item in Constants.ITALIC_STYLES:
            macEnSubfmlyStr = re.sub(r"(?i)\b" + item + r"\b", "Italic", macEnSubfmlyStr)
        # Remove width and weight strings
        for item in Constants.STANDARD_WIDTHS:
            macEnSubfmlyStr = re.sub(r"(?i)\b" + item + r"\b", "", macEnSubfmlyStr)
        for item in Constants.ABBREVIATED_WIDTHS:
            macEnSubfmlyStr = re.sub(r"(?i)\b" + item + r"\b", "", macEnSubfmlyStr)
        for item in Constants.STANDARD_WEIGHTS:
            macEnSubfmlyStr = re.sub(r"(?i)\b" + item + r"\b", "", macEnSubfmlyStr)
        for item in Constants.ABBREVIATED_WEIGHTS:
            macEnSubfmlyStr = re.sub(r"(?i)\b" + item + r"\b", "", macEnSubfmlyStr)
        # Add standard width and weight string
        widthScale = self.__getWidthScale(OS2f2.usWidthClass)
        weightScale = self.__getWeightScale(OS2f2.usWeightClass)
        macEnSubfmlyStr += u" " + self.__getWidthString(widthScale) + u" " + self.__getWeightString(weightScale)
        # Clean-ups
        while macEnSubfmlyStr != macEnSubfmlyStr.replace(u"  ", u" "):
            macEnSubfmlyStr = macEnSubfmlyStr.replace(u"  ", u" ")
        macEnSubfmlyStr = macEnSubfmlyStr.strip()
        # Apply changes
        macEnSubfmlyRec.string = macEnSubfmlyStr
        return

    def __getWidthScale(self, usWidthClass):
        if usWidthClass in range(1, 10):
            return usWidthClass
        else:
            return 5

    def __getWeightScale(self, usWeightClass):
        if usWeightClass <= 100:
            return 1
        elif usWeightClass <= 200:
            return 2
        elif usWeightClass == 250:
            return 1
        elif usWeightClass == 275:
            return 2
        elif usWeightClass <= 300:
            return 3
        elif usWeightClass <= 400:
            return 4
        elif usWeightClass <= 500:
            return 5
        elif usWeightClass <= 600:
            return 6
        elif usWeightClass <= 700:
            return 7
        elif usWeightClass <= 800:
            return 8
        elif usWeightClass <= 900:
            return 9
        elif usWeightClass <= 1000:
            return 10
        else:
            return 4

    def __getWidthString(self, widthScale):
        widthString = None
        if widthScale != 5:
            widthString = Constants.STANDARD_WIDTHS[widthScale - 1]
        else:
            widthString = ""
        return widthString.decode()

    def __getWeightString(self, weightScale):
        return Constants.STANDARD_WEIGHTS[weightScale - 1].decode()

