# BACKUP
def fixName(self):
    name = self.font["name"]
    cmap = self.font["cmap"]

    newNames = []
    macNames = []
    winLegacyNames = []
    winBMPNames = []
    winFullNames = []
    unsupported = []
    psCIDffNames = []  # PostScript CID findfont NameRecords generated for the new `name`
    psCIDffName = None  # PostScript CID findfont NameRecord retrieved from the source `name`

    # Only supported name records listed in Constants.py will be processed.
    supportedMacLangs = Constants.MAC_LANGCODE_TO_WIN.keys()
    supportedWinLangs = Constants.WIN_LANGCODE_TO_MAC.keys()

    for namRec in name.names:
        # Decode everything, including MS Unicode (utf_16_be), to Python Unicode first.
        try:
            namRec.string = namRec.toUnicode()
        except UnicodeDecodeError:
            unsupported.append(namRec)
            continue
        # On the OpenType spec this is rather undocumented: the string length of nameID 1 must be less than 32,
        # otherwise the font will not load in Windows.
        if namRec.nameID == 1 and len(namRec.string) > 31:
            namRec.string = namRec.string[:31]
        if namRec.nameID == 20:
            psCIDffName = namRec
        elif Workers.NameWorker.isMacintosh(namRec) and namRec.langID in supportedMacLangs:
            macNames.append(namRec)
        elif Workers.NameWorker.isWindowsLegacy(namRec) and namRec.langID in supportedMacLangs:
            winLegacyNames.append(namRec)
        elif Workers.NameWorker.isWindowsBMP(namRec) and namRec.langID in supportedWinLangs:
            winBMPNames.append(namRec)
        elif Workers.NameWorker.isWindowsFull(namRec) and namRec.langID in supportedWinLangs:
            winFullNames.append(namRec)
        else:
            unsupported.append(namRec)

    # Convert all winLegacyNames to winBMPNames
    for namRec in winLegacyNames:
        if self.__getName(winBMPNames, namRec.nameID, 3, 1, namRec.langID) is None:
            winBMPNames.append(self.__makeName(namRec.string, namRec.nameID, 3, 1, namRec.langID))
    # Build all from winFullNames
    for namRec in winFullNames:
        macLngID = Constants.WIN_LANGCODE_TO_MAC[namRec.langID]
        macEncID = Constants.MAC_LANGCODE_TO_PLATENCID[macLngID]
        if self.__getName(winBMPNames, namRec.nameID, 3, 1, namRec.langID) is None:
            winBMPNames.append(self.__makeName(namRec.string, namRec.nameID, 3, 1, namRec.langID))
        if self.__getName(macNames, namRec.nameID, 1, macEncID, macLngID) is None:
            macNames.append(self.__winName2Mac(namRec))
    # Build all from winBMPNames
    for namRec in winBMPNames:
        macLngID = Constants.WIN_LANGCODE_TO_MAC[namRec.langID]
        macEncID = Constants.MAC_LANGCODE_TO_PLATENCID[macLngID]
        if self.__getName(winFullNames, namRec.nameID, 3, 10, namRec.langID) is None:
            winFullNames.append(self.__makeName(namRec.string, namRec.nameID, 3, 10, namRec.langID))
        if self.__getName(macNames, namRec.nameID, 1, macEncID, macLngID) is None:
            macNames.append(self.__winName2Mac(namRec))
    # Build all from macNames
    for namRec in macNames:
        if namRec.nameID == 18:
            continue  # Those items don't make sense for Windows.
        if psCIDffName and self.__getName(psCIDffNames, 20, 1, namRec.platEncID, 65535) is None:
            psCIDffNames.append(self.__makeName(psCIDffName.string, 20, 1, namRec.platEncID, 65535))
        winLngIDs = Constants.MAC_LANGCODE_TO_WIN[namRec.langID]
        for winLngID in winLngIDs:
            if self.__getName(winBMPNames, namRec.nameID, 3, 1, winLngID) is None:
                winBMPNames.append(self.__macName2Win(namRec, 1, winLngID))
            if self.__getName(winFullNames, namRec.nameID, 3, 10, winLngID) is None:
                winFullNames.append(self.__macName2Win(namRec, 10, winLngID))

    # `cmap`-`name consistency check and clean-ups
    if Workers.CmapWorker.getLastResort(cmap.tables):
        if cmap.getcmap(0, 4) or cmap.getcmap(0, 6):
            newNames.extend(macNames)
            newNames.extend(psCIDffNames)
    else:
        if cmap.getcmap(1, 0):
            newNames.extend(macNames)
            newNames.extend(psCIDffNames)
        if cmap.getcmap(3, 1):
            newNames.extend(winBMPNames)
    if cmap.getcmap(3, 10):
        newNames.extend(winFullNames)

    newNames.extend(unsupported)

    name.names = newNames
    return

def __getName(self, nameRecords, nameID, platformID, platEncID, langID):
    return Workers.NameWorker.getName(nameRecords, nameID, platformID, platEncID, langID)

def __makeName(self, string, nameID, platformID, platEncID, langID):
    return _n_a_m_e.makeName(string, nameID, platformID, platEncID, langID)

def __winName2Mac(self, winNameRecord):
    return Workers.NameWorker.winName2Mac(winNameRecord)

def __macName2Win(self, macNameRecord, winPlatEncID, winLangID):
    return Workers.NameWorker.macName2Win(macNameRecord, winPlatEncID, winLangID)

def __macName2WinAll(self, macNameRecord, winPlatEncID):
    return Workers.NameWorker.macName2WinAll(macNameRecord, winPlatEncID)
