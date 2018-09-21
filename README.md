# The OpenType Font Rebuilder, Powered by [fontTools](https://github.com/fonttools/fonttools)

This is a quick tool to resolve naming, styling and mapping issues
among OpenType fonts. Without any options given, it scans and
maintains the metedata consistency among font tables; with a simple
but powerful configuration file, all intricate data fields
between font tables such as `name`, `head`, `OS/2` can be
automatically generated without compromising platform-specific
compatibility. It also supplies extra useful functionalities
to simplify multilingual OpenType font packaging workflow.

TrueType and OpenType fonts are both supported. Output files are
always created with different names, so an existing file is
never overwritten.

***

## Options:
`-o <outputFont>`: Specify the output font file.

`-c <configTOML>`: Specify the configuration file. It is an
    TOML-format text file and it must be UTF-8 encoded.

`--UPM <targetUPM>`: Change a TrueType font's units-per-em value.
    The entire font will be rescaled to adapt the new UPM value.
    A typical UPM for TrueType font is 2048, and for CFF-based
    font is 1000. UPM > 5000 will cause problems in Adobe apps
    such as InDesign and Illustrator. `MATH` table is currently
    not supported; please rebuild it after application.

`--otf2ttf`: For CFF-based font only. Convert a CFF-based font
    into a TrueType-outline font. Glyph bounding boxes and
    min/max values will be automatically recalculated. This
    option would be ignored if a TrueType font is specified.

`--macOffice`: Add standard weight strings onto Mac English
    subfamily and remove legacy Macintosh Roman character
    mapping in order to obtain maximum compatibilities with
    Microsoft Office 2011 for Mac. ONLY enable this option when
    one or more subfamilies are missing from Mac Office 2011's
    font menu or characters outside Mac Roman are unavailable on
    Mac Office 2011. DO NOT USE for later Mac Office versions
    nor Windows Office releases.

`--refresh`: Re-compile all font tables.

`--recalculate`: Recalculate glyph bounding boxes, min/max values
    and Unicode ranges.

`--removeGlyphNames`: Remove all glyph names for release.

`--removeBitmap`: For TrueType fonts only. Remove bitmap data. It
    would be ignored if CFF-based font is specified.

`--removeHinting`: For TrueType fonts only. Remove hinting/gridfit
    data. This is designed for ill-hinted fonts. Use it with
    caution when processing professional gridfitted fonts. It
    would be ignored if CFF-based font is specified.
    
`--smoothRendering`: For TrueType fonts only. Smooth screen
    rendering on Windows 10 RTM or later without removing
    hinting/gridfit information. It would be ignored if
    CFF-based font is specified.

`--rebuildMapping`: Regenerate character mappings of the font.

`--allowUpgrade`: Allow upgrading `OS/2` table when advanced
    features are specified in the given configuration file.

`--dummySignature`: Some apps such as Microsoft Office require a
    valid digital signature in order to enable advanced OpenType
    features. This option can forge an empty but valid DSIG
    placeholder.

`--O1`: Mild optimization, as a shortcut to `--smoothRendering`,
    `--allowUpgrade`, and `--dummySignature`.

`--O2`: Typical optimization, as a shortcut to `--recalculate`, 
    `--smoothRendering`, `--rebuildMapping`, `--allowUpgrade`,
    and `--dummySignature`.

`--O3`: Comprehensive optimization for release, as a shortcut to
    `--refresh`, `--recalculate`, `--removeBitmap`, `--removeHinting`,
    `--rebuildMapping`, `--allowUpgrade`, and `--dummySignature`.

***

** Windows legacy symbol fonts are currently not supported.

** Variable fonts are currently not supported.
