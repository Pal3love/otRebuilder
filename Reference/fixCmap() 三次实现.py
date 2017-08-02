# ————第一次实现————
def fixCmap(self):
    cmap = self.font["cmap"]
    cmap.tableVersion = 0

    winBMP = None
    winFull = None
    macRoman = None
    macBMP = None
    macFull = None
    unsupported = []
    newSubtables = []

    for subtable in cmap.tables:
        # Skip the last resort font because that doesn't make sense.
        # It will be rebuilt by the Rebuilder class when needed.
        if Workers.CmapWorker.isLastResort(subtable):
            return
        elif Workers.CmapWorker.isMacRoman(subtable):
            macRoman = subtable
        elif subtable.platformID == 0 and (subtable.format == 4 or subtable.format == 6):
            macBMP = subtable  # Apple doesn't care the consistency of platEncID so we shouldn't depend on it as well.
        elif subtable.platformID == 0 and subtable.format == 12:
            macFull = subtable
        elif subtable.platformID == 3 and subtable.platEncID == 1 and (subtable.format == 4 or subtable.format == 6):
            winBMP = subtable
        elif subtable.platformID == 3 and subtable.format == 12:
            winFull = subtable
        else:
            unsupported.append(subtable)
    if len(unsupported) == 0:
        unsupported = None

    # Build standard BMPs first.
    if winBMP:
        newSubtables.extend(Workers.CmapWorker.subtables_buildFmt4sFromBMP(winBMP))
    elif macBMP:
        newSubtables.extend(Workers.CmapWorker.subtables_buildFmt4sFromBMP(macBMP))
    else:
        pass
    # If no BMPs found, try building standard BMPs and full repertoires from full repertoires;
    # else (BMPs has been built), try building only full repertoires.
    if len(newSubtables) == 0:
        if winFull:
            newSubtables.extend(Workers.CmapWorker.subtables_buildUnicodeAllFromFull(winFull))
        elif macFull:
            newSubtables.extend(Workers.CmapWorker.subtables_buildUnicodeAllFromFull(macFull))
        else:
            pass
    else:
        if winFull:
            newSubtables.extend(Workers.CmapWorker.subtables_buildFmt12sFromFull(winFull))
        elif macFull:
            newSubtables.extend(Workers.CmapWorker.subtables_buildFmt12sFromFull(macFull))
        else:
            pass
    # If still get nothing, as the last resort, build everything from MacRoman;
    # else (Unicode subtables has been successfully built), add MacRoman or build it if not found.
    if len(newSubtables) == 0:
        if macRoman:
            newSubtables.extend(Workers.CmapWorker.subtables_buildFmt4sFromMacRoman(macRoman))
            newSubtables.append(macRoman)
        else:  # Game over
            pass
    else:
        if macRoman:  # Add the original MacRoman
            newSubtables.append(macRoman)
        else:  # Build MacRoman from Unicode
            tempSubtable = newSubtables[0]  # Choose the first subtable, which must be a Unicode one, as build source
            newSubtables.append(Workers.CmapWorker.subtable_buildMacRomanFromUnicode(tempSubtable))

    if unsupported:
        newSubtables.extend(unsupported)  # Finally
    cmap.tables = newSubtables
    return


# ————第二次实现：递归————
def __fixCmap_helper(self, sourceSubtables, newSubtables, level):
    # Base case
    if level == len(sourceSubtables - 1):
        newSubtables.append(sourceSubtables[level])
        return
    # Recursive rules
    if not sourceSubtables[level + 1]:
        # If sourceSubtables[level] is None, generate None.
        soueceTables[level + 1].append(
            self.__fixCmap_genNextSub(sourceSubtables[level]
                ))
    self.__fixCmap_helper(sourceSubtables, newSubtables, level + 1)
    newSubtables.append(sourceSubtables[level])
    return


# ————第三次实现：尾递归转循环————
def fixCmap(self):
    cmap = self.font["cmap"]
    cmap.tableVersion = 0
    sourceSub, unsupported = self.__fixCmap_categorize(cmap)
    self.__fixCmap_helper(sourceSub)
    newSub = self.__fixCmap_buildNew(sourceSub)
    newSub.extend(unsupported)
    cmap.tables = newSub
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
            soueceTables[level + 1].append(
                self.__fixCmap_genNextSub(sourceSubtables[level]
                ))
    return

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
        newSubtables.append(sourceSubtables[2])
    if sourceSubtables[3] and not sourceSubtables[1]:  # uniBMPfromMacRoman
        newSubtables.extend(
            Workers.CmapWorker.subtables_buildFmt4sFromBMP(sourceSubtables[3])
            )
    return newSubtables

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

def __fixCmap_full2Bmp(self, cmapSubFull):
    subtables = Workers.CmapWorker.subtables_buildUnicodeAllFromFull(fullSubtable)
    return subtables[0]

def __fixCmap_bmp2Mac(self, cmapSubBmp):
    return Workers.CmapWorker.subtable_buildMacRomanFromUnicode(cmapSubBmp)

def __fixCmap_mac2Bmp(self, cmapSubMac):
    subtables = Workers.CmapWorker.subtables_buildFmt4sFromMacRoman(cmapSubMac)
    return subtables[0]
