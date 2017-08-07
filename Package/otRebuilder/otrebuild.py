#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import argparse
import codecs
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "Dep")
sys.path.insert(0, dependencyDir)

from fontTools.misc.macCreatorType import getMacCreatorAndType
from fontTools.misc.cliTools import makeOutputFileName
from fontTools.misc.py23 import *
from fontTools.ttLib import TTFont
import toml

from otRebuilder.Lib import Initializer
from otRebuilder.Lib import Fixer
from otRebuilder.Lib import Rebuilder
from otRebuilder.Lib import Converter
from otRebuilder.Lib import Constants


usageStr = "usage: otrebuild [options] <inputFont>"
descriptionStr = """    OpenType Font Rebuilder: Version 1.3.2, powered by fontTools

    This is a simple tool to resolve naming, styling and mapping issues
        among OpenType fonts. Without any options given, it can scan and
        maintain metedata consistencies among font tables; with a simple
        but powerful configuration file, all intricate data fields
        within font tables such as `name`, `head`, `OS/2` can be
        automatically generated without compromising platform-specific
        compatibilities. It also supplies extra useful functionalities
        to simplify the OpenType font packaging workflow.

    TrueType and OpenType fonts are both supported. Output files are
        always created with different names, so an existing file is
        never overwritten.

    Options:
        -o <outputFont>: Specify the output font file.
        -c <configTOML>: Specify the configuration file. It is an
            TOML-format text file and it must be UTF-8 encoded.
        --otf2ttf <targetUPM>: For CFF-based font only. Convert a 
            CFF-based font into TrueType font with the given units per
            em (UPM) value. A typical UPM for TrueType is 2048. Glyph
            bounding boxes and min/max values will be automatically
            recalculated. This option would be ignored if a TrueType
            font is specified. Please rebuild `GPOS`, `JSTF` and `MATH`
            table after conversion if UPM is changed.
        --refresh: Re-compile all font tables.
        --recalculate: Recalculate glyph bounding boxes, min/max values
            and Unicode ranges.
        --removeGlyphNames: Remove all glyph names for release.
        --removeBitmap: For TrueType fonts only. Remove bitmap data. It
            would be ignored if CFF-based font is specified.
        --removeHinting: For TrueType fonts only. Remove hinting/gridfit
            data. This is designed for ill-hinted fonts. Use it with
            caution when processing professional gridfitted fonts. It
            would be ignored if CFF-based font is specified.
        --smoothRendering: For TrueType fonts only. Smooth screen
            rendering on Windows 10 RTM or later without removing
            hinting/gridfit information. It would be ignored if
            CFF-based font is specified.
        --rebuildMapping: Regenerate character mappings of the font.
        --allowUpgrade: Allow upgrading `OS/2` table when advanced
            features are specified in the given configuration file.
        --dummySignature: Some apps such as Microsoft Office require a
            valid digital signature in order to enable advanced OpenType
            features. This option can forge an empty but valid DSIG
            placeholder.
        --O1: Mild optimization, as a shortcut to --smoothRendering,
            --allowUpgrade, and --dummySignature.
        --O2: Typical optimization, as a shortcut to --recalculate, 
            --smoothRendering, --rebuildMapping, --allowUpgrade,
            and --dummySignature.
        --O3: Comprehensive optimization for release, as a shortcut to
            --refresh, --recalculate, --removeBitmap, --removeHinting,
            --rebuildMapping, --allowUpgrade, and --dummySignature.

    ** Windows legacy symbol fonts are currently not supported.
    ** Variable fonts are currently not supported.
"""


def main():
    paths, jobs = parseArgs()
    processIO(paths)
    processFont(paths, jobs)
    return


def parseArgs():

    if len(sys.argv) < 2:
        print(usageStr + "\n", file = sys.stderr)
        print(descriptionStr, file = sys.stderr)
        print("optional arguments:", file = sys.stderr)
        print("  -h, --help  show this help message and exit", file = sys.stderr)
        sys.exit(2)

    parser = argparse.ArgumentParser(
        description = descriptionStr, 
        usage = "%(prog)s [options] <inputFont>", 
        formatter_class = argparse.RawDescriptionHelpFormatter
        )
    parser.add_argument("inputFont", metavar = "inputFont", help = argparse.SUPPRESS)
    parser.add_argument("-o", metavar = "outputFont", help = argparse.SUPPRESS)
    parser.add_argument("-c", metavar = "configTOML", help = argparse.SUPPRESS)
    parser.add_argument("--otf2ttf", metavar = "targetUPM", type = int, help = argparse.SUPPRESS)
    parser.add_argument("--refresh", action="store_true", help = argparse.SUPPRESS)
    parser.add_argument("--recalculate", action="store_true", help = argparse.SUPPRESS)
    parser.add_argument("--removeGlyphNames", action="store_true", help = argparse.SUPPRESS)
    parser.add_argument("--removeBitmap", action="store_true", help = argparse.SUPPRESS)
    parser.add_argument("--removeHinting", action="store_true", help = argparse.SUPPRESS)
    parser.add_argument("--smoothRendering", action="store_true", help = argparse.SUPPRESS)
    parser.add_argument("--rebuildMapping", action="store_true", help = argparse.SUPPRESS)
    parser.add_argument("--allowUpgrade", action="store_true", help = argparse.SUPPRESS)
    parser.add_argument("--dummySignature", action="store_true", help = argparse.SUPPRESS)
    mutexGroup = parser.add_mutually_exclusive_group()
    mutexGroup.add_argument("--O1", action="store_true", help = argparse.SUPPRESS)
    mutexGroup.add_argument("--O2", action="store_true", help = argparse.SUPPRESS)
    mutexGroup.add_argument("--O3", action="store_true", help = argparse.SUPPRESS)
    args = parser.parse_args()

    paths = Paths()
    jobs = Jobs()

    paths.inputFile = args.inputFont
    paths.configFile = args.c
    paths.outputFile = args.o

    if args.O1:
        args.smoothRendering = True 
        args.allowUpgrade = True
        args.dummySignature = True
    elif args.O2:
        args.recalculate = True
        args.rebuildMapping = True
        args.smoothRendering = True
        args.allowUpgrade = True
        args.dummySignature = True
    elif args.O3:
        args.refresh = True
        args.recalculate = True
        args.removeBitmap = True
        args.removeHinting = True
        args.rebuildMapping = True
        args.allowUpgrade = True
        args.dummySignature = True

    if args.removeHinting:
        jobs.init_removeHinting = True
        jobs.rebuild_gasp = True
        jobs.rebuild_prep = True
    elif args.smoothRendering:
        jobs.rebuild_gasp = True
    else:
        pass
    if args.rebuildMapping:
        jobs.fix_cmap = False
        jobs.rebuild_cmap = True
    if paths.configFile:
        jobs.fix_name = False

    jobs.general_recalc = args.recalculate
    jobs.init_refreshTables = args.refresh
    jobs.init_removeGlyphNames = args.removeGlyphNames
    jobs.init_removeBitmap = args.removeBitmap
    jobs.rebuild_allowUpgrade = args.allowUpgrade
    jobs.rebuild_DSIG = args.dummySignature
    jobs.convert_otf2ttf = args.otf2ttf
    
    return paths, jobs


class Paths(object):
    def __init__(self):
        self.inputFile = None
        self.configFile = None
        self.outputFile = None


class Jobs(object):
    def __init__(self):
        self.general_recalc = False
        self.init_refreshTables = False
        self.init_removeGlyphNames = False
        self.init_removeBitmap = False
        self.init_removeHinting = False
        self.fix_fromCFF = True
        self.fix_cmap = True
        self.fix_name = True
        self.rebuild_allowUpgrade = False
        self.rebuild_cmap = False
        self.rebuild_gasp = False
        self.rebuild_prep = False
        self.rebuild_DSIG = False
        self.convert_otf2ttf = None


def processIO(paths):
    if not os.path.exists(paths.inputFile):
        print("ERROR: Input font file does not exist.", file = sys.stderr)
        sys.exit(2)
    elif getFontType(paths.inputFile) is None:
        print("ERROR: Invalid font file. Only TTF and OTF are supported.", file = sys.stderr)
        sys.exit(1)
    else:
        pass
    if paths.configFile and not os.path.exists(paths.configFile):
        print("ERROR: Config TOML file does not exist.", file = sys.stderr)
        sys.exit(2)
    if paths.outputFile is None:
        paths.outputFile = makeOutputFileName(paths.inputFile)
    elif not os.path.exists(os.path.dirname(os.path.realpath(paths.outputFile))):
        print("ERROR: Output location does not exist.", file = sys.stderr)
        sys.exit(2)
    else:
        paths.outputFile = makeOutputFileName(paths.outputFile)
    return


# Modified from ttx.guessFileType()
def getFontType(fileName):
    base, ext = os.path.splitext(fileName)
    try:
        _file = open(fileName, "rb")
    except IOError:
        return None
    header = _file.read(256)
    _file.close()
    cr, tp = getMacCreatorAndType(fileName)
    if tp in ("sfnt", "FFIL"):
        return "TTF"
    head = Tag(header[:4])
    if head == "OTTO":
        return "OTF"
    elif head in ("\0\1\0\0", "true"):
        return "TTF"
    return None


def processFont(paths, jobs):
    print("Input Font: " + paths.inputFile + "\nProcessing...")
    font = TTFont(
        file = paths.inputFile, 
        res_name_or_index = 0, 
        recalcBBoxes = jobs.general_recalc, 
        ignoreDecompileErrors = True, 
        recalcTimestamp = True  # It might be altered by Rebuilder
        )
    config = None
    if paths.configFile:
        doJobs(font, jobs, getConfigDict(paths.configFile))
    else:
        doJobs(font, jobs)
    font.save(paths.outputFile)
    print("Done.\nOutput Font: " + paths.outputFile)
    return


def getConfigDict(configPath):
    configDict = None
    try:
        configRaw = open(configPath, "rb").read()
    except IOError:
        print("ERROR: I/O fatal error.", file = sys.stderr)
        sys.exit(1)
    if configRaw.startswith(codecs.BOM_UTF8):
        configRaw = configRaw[3:]
    try:
        configDict = toml.loads(configRaw)
    except toml.TomlDecodeError:
        print("ERROR: Invalid config file. Please make sure it complies TOML specification and is UTF-8 encoded.", file = sys.stderr)
        sys.exit(1)
    except:
        print("ERROR: Invalid config file. Please make sure it complies TOML specification.", file = sys.stderr)
        print("Please review TOML specification at: https://github.com/toml-lang/toml", file = sys.stderr)
        sys.exit(1)
    return configDict


def doJobs(ttfontObj, jobsObj, configDict = None):
    doInits(ttfontObj, jobsObj)
    doFixes(ttfontObj, jobsObj)
    doRebuilds(ttfontObj, jobsObj, configDict)
    doConverts(ttfontObj, jobsObj)
    return


def doInits(ttfontObj, jobsObj):
    init = Initializer.Initializer(ttfontObj, jobsObj)
    if init.isSymbolFont():
        print("ERROR: Windows legacy symbol font detected. It is currently not supported.", file = sys.stderr)
        sys.exit(1)
    if init.isVariableFont():
        print("ERROR: Variable font detected. It is currently not supported.", file = sys.stderr)
        sys.exit(1)
    if jobsObj.init_refreshTables:
        init.refreshTables()
    if jobsObj.init_removeBitmap:
        init.removeBitmap()
    if jobsObj.init_removeGlyphNames:
        init.removeGlyphNames()
    if jobsObj.init_removeHinting:
        init.removeHinting()  # `gasp` will also be removed
    elif jobsObj.rebuild_gasp:
        init.removeGasp()  # Remove only `gasp`
    else:
        pass
    return


def doFixes(ttfontObj, jobsObj):
    fixer = Fixer.Fixer(ttfontObj, jobsObj)
    fixer.fixHeader()
    fixer.fixHead()
    fixer.fixHhea()
    fixer.fixOS2f2()
    if ttfontObj.has_key("CFF ") and jobsObj.fix_fromCFF:
        fixer.fixFromCFF()
    if jobsObj.fix_cmap:
        fixer.fixCmap()
    if jobsObj.fix_name:
        fixer.fixName()
    return


def doRebuilds(ttfontObj, jobsObj, configDict):
    rebuilder = Rebuilder.Rebuilder(ttfontObj, jobsObj, configDict)
    if jobsObj.rebuild_gasp:
        rebuilder.rebuildGasp()
    if jobsObj.rebuild_prep:
        rebuilder.rebuildPrep()
    if jobsObj.rebuild_DSIG:
        rebuilder.rebuildDSIG()
    if jobsObj.rebuild_cmap:
        rebuilder.rebuildCmap()
    if configDict:
        rebuilder.rebuildByConfig()
    return


def doConverts(ttfontObj, jobsObj):
    converter = Converter.Converter(ttfontObj, jobsObj)
    targetUPM = jobsObj.convert_otf2ttf
    if targetUPM:
        if jobsObj.init_removeGlyphNames:
            converter.otf2ttf(
                Constants.OTF2TTF_DFLT_MAX_ERR,
                3.0,  # Ignore any stored glyph names.
                Constants.OTF2TTF_DFLT_REVERSE,
                targetUPM
                )
        else:
            converter.otf2ttf(
                Constants.OTF2TTF_DFLT_MAX_ERR,
                Constants.OTF2TTF_DFLT_POST_FORMAT,
                Constants.OTF2TTF_DFLT_REVERSE,
                targetUPM
                )
    return


if __name__ == "__main__":
    sys.exit(main())

