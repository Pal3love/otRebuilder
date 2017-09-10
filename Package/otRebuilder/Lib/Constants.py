#!/usr/bin/env python
# -*- coding:utf-8 -*-

from __future__ import print_function, division, absolute_import
import os.path
import sys

dependencyDir = os.path.join(os.path.dirname(os.path.realpath(__file__)), "../Dep")
sys.path.insert(0, dependencyDir)


REQUIRED_TABLES = ("cmap", "head", "hhea", "hmtx", "maxp")

# Default values
DEFAULT_FONT_NAME = "Untitled Font"
DEFAULT_OS2f2_VERSION = 3
DEFAULT_OS2f2_ACHVENDID = "DFLT"
DEFAULT_FONT_REVISION = 0.0
DEFAULT_ITALIC_ANGLE = -12.0
DEFAULT_UNDERLINE_POSITION = -200
DEFAULT_UNDERLINE_THICKNESS = 100

OS2f2_LEGACY_SPACE_WGHTFCTR = 166
OS2f2_LEGACY_LWRCASE_WGHTFCTR = (
    64, 14, 27, 35, 100, 20, 14, 42, 63, 3, 6, 35, 20,
    56, 56, 17, 4, 49, 56, 71, 31, 10, 18, 3, 18, 2
    )  # Legacy weight factors from 'a' to 'z'

# Default Parameters for otf2ttf
OTF2TTF_DFLT_MAX_ERR = 1.0  # Measured in UPM
OTF2TTF_DFLT_POST_FORMAT = 2.0
OTF2TTF_DFLT_REVERSE = True

# Embedding Restriction Codes
EMBED_INSTALLABLE = 0
EMBED_EDITABLE = 1
EMBED_PREVIEW_AND_PRINT = 2
EMBED_RESTRICTED = 3

# Stylelink Codes
STYLELINK_NONE = 0
STYLELINK_REGULAR = 1
STYLELINK_BOLD = 2
STYLELINK_ITALIC = 3
STYLELINK_BOLDITALIC = 4

# Style Strings
REGULAR_STYLES = ("Regular", "Rg", "Roman", "Rm", "R", "Normal", "Norm", "Nm", "Book", "Bk")
BOLD_STYLES = ("Bold", "Bd", "B")
ITALIC_STYLES = ("Italic", "It", "Oblique", "Obl")
LEGACY_WIN_STYLES = ("Regular", "Bold", "Italic", "Bold Italic")
CJK_REGULAR_WEIGHTS = ("W3", "W4", "507R", "508R", "50J", "50F", "50JF", "50W", "50S", "55J", "55F", "55JF", "55W", "55S")
CJK_BOLD_WEIGHTS = ("W6", "W7", "511M", "512B", "70J", "70F", "70JF", "70W", "70S", "75J", "75F", "75JF", "75W", "75S")

# Weight/Width Scales and Strings
WIDTH_SCALES = (1, 2, 3, 4, 5, 6, 7, 8, 9)
ABBREVIATED_WIDTHS = ("UCond", "XCond", "Cond", "DCond", "M", "DExt", "Ext", "XExt", "UExt")
STANDARD_WIDTHS = ("Ultra-condensed ", "Extra-condensed", "Condensed", "Semi-condensed", "Medium", "Semi-expanded", "Expanded", "Extra-expanded", "Ultra-expanded")
WIN_SAFE_WEIGHT_SCALES = (250, 275, 300, 400, 500, 600, 700, 800, 900, 950)
STANDARD_WEIGHT_SCALES = (100, 200, 300, 400, 500, 600, 700, 800, 900, 1000)
ABBREVIATED_WEIGHTS = ("UL", "EL", "L", "R", "M", "SB", "B", "EB", "H", "BL")
STANDARD_WEIGHTS = ("Ultralight", "Extralight", "Light", "Regular", "Medium", "Semibold", "Bold", "Extrabold", "Heavy", "Black")


WIN_LANGCODE_TO_MAC = {
    0x0409: 0,  # en-US
    0x0C09: 0,  # en-AU
    0x2809: 0,  # en-BZ
    0x1009: 0,  # en-CA
    0x2409: 0,  # en-029
    0x4009: 0,  # en-IN
    0x1809: 0,  # en-IE
    0x2009: 0,  # en-JM
    0x4409: 0,  # en-MY
    0x1409: 0,  # en-NZ
    0x3409: 0,  # en-PH
    0x4809: 0,  # en-SG
    0x1C09: 0,  # en-ZA
    0x2C09: 0,  # en-TT
    0x0809: 0,  # en-GB
    0x3009: 0,  # en-ZW
    0x0411: 11,  # ja-JP
    0x0404: 19,  # zh-TW
    0x0C04: 19,  # zh-HK
    0x1404: 19,  # zh-MO
    0x0412: 23,  # ko-KR
    0x0804: 33,  # zh-CN
    0x1004: 33,  # zh-SG
    # Languages untested:
    0x040C: 1,  # fr
    0x080C: 1,  # fr-BE
    0x0C0C: 1,  # fr-CA
    0x100C: 1,  # fr-CH
    0x140C: 1,  # fr-LU
    0x180C: 1,  # fr-MC
    0x0407: 2,  # de
    0x0484: 2,  # gsw (Swiss German)
    0x0807: 2,  # de-CH
    0x0C07: 2,  # de-AT
    0x1007: 2,  # de-LU
    0x1407: 2,  # de-LI
    0x0410: 3,  # it
    0x0810: 3,  # it-CH
    0x0413: 4,  # nl
    0x041D: 5,  # sv
    0x081D: 5,  # sv-FI
    0x040A: 6,  # es-Trad
    0x080A: 6,  # es-MX
    0x0C0A: 6,  # es-Mdrn
    0x100A: 6,  # es-GT
    0x140A: 6,  # es-CR
    0x180A: 6,  # es-PA
    0x1C0A: 6,  # es-DO
    0x200A: 6,  # es-VE
    0x240A: 6,  # es-CO
    0x280A: 6,  # es-PE
    0x2C0A: 6,  # es-AR
    0x300A: 6,  # es-EC
    0x340A: 6,  # es-CL
    0x380A: 6,  # es-UY
    0x3C0A: 6,  # es-PY
    0x400A: 6,  # es-BO
    0x440A: 6,  # es-SV
    0x480A: 6,  # es-HN
    0x4C0A: 6,  # es-NI
    0x500A: 6,  # es-PR
    0x540A: 6,  # es-US
    0x0406: 7,  # da
    0x0416: 8,  # pt
    0x0816: 8,  # pt-PT
    0x0414: 9,  # nb
    0x040B: 13,  # fi
    0x0408: 14,  # el
    0x040F: 15,  # is
    0x043A: 16,  # mt
    0x041F: 17,  # tr
    0x041A: 18,  # hr
    0x101A: 18,  # hr-BA
    0x0427: 24,  # lt
    0x0415: 25,  # pl
    0x040E: 26,  # hu
    0x0425: 27,  # et
    0x0426: 28,  # lv
    0x0438: 30,  # fo
    0x0419: 32,  # ru
    0x0813: 34,  # nl-BE
    0x083C: 35,  # ga
    0x041C: 36,  # sq
    0x0418: 37,  # ro
    0x0405: 38,  # cs
    0x041B: 39,  # sk
    0x0424: 40,  # sl
    0x081A: 42,  # sr-Latn
    0x0C1A: 42,  # sr
    0x181A: 42,  # sr-Latn-BA
    0x1C1A: 42,  # sr-Cyrl-BA
    0x042F: 43,  # mk
    0x0402: 44,  # bg
    0x0422: 45,  # uk
    0x0423: 46,  # be
    0x0443: 47,  # uz
    0x0843: 47,  # uz-Cyrl
    0x043F: 48,  # kk
    0x082C: 49,  # az-Cyrl
    0x0440: 54,  # ky
    0x0428: 55,  # tg
    0x0442: 56,  # tk
    0x0450: 58,  # mn
    0x0421: 81,  # id
    0x043E: 83,  # ms
    0x083E: 83,  # ms-BN
    0x0441: 89,  # sw
    0x0487: 90,  # rw
    0x0452: 128,  # cy
    0x042D: 129,  # eu
    0x0403: 130,  # ca
    0x046B: 132,  # qu-BO
    0x086B: 132,  # qu-EC
    0x0C6B: 132,  # qu
    0x0444: 135,  # tt
    0x0456: 140,  # gl
    0x0436: 141,  # af
    0x047E: 142,  # br
    0x046F: 149,  # kl
    0x042C: 150,  # az
    0x0814: 151,  # nn

}

MAC_LANGCODE_TO_WIN = {
    # 0: [0x0409, 0x0C09, 0x2809, 0x1009, 0x2409, 0x4009, 0x1809, 0x2009, 0x4409, 0x1409, 0x3409, 0x4809, 0x1C09, 0x2C09, 0x0809, 0x3009],  # English (Global)
    # 19: [0x0404, 0x0C04, 0x1404],  # Chinese Traditional
    # 33: [0x0804, 0x1004],  # Chinese Simplified
    0: [0x0409],  # English US (Last Resort)
    11: [0x0411],  # Japanese
    19: [0x0404, 0x0C04],  # Chinese Traditional (Taiwan and HK)
    23: [0x0412],  # Korean
    33: [0x0804],  # Chinese Simplified (PRC)
    # Languages untested:
    # 1: [0x040C, 0x080C, 0x0C0C, 0x100C, 0x140C, 0x180C],  # French
    # 2: [0x0407, 0x0C07, 0x0807, 0x1407, 0x1007, 0x0484],  # German and Swiss German
    # 3: [0x0410, 0x0810],  # Italian
    # 5: [0x041D, 0x081D],  # Swedish
    # 6: [0x2C0A, 0x400A, 0x340A, 0x240A, 0x140A, 0x1C0A, 0x300A, 0x100A, 0x480A, 0x0C0A, 0x080A, 0x4C0A, 0x180A, 0x280A, 0x500A, 0x3C0A, 0x440A, 0x040A, 0x540A, 0x380A, 0x200A],  # Spanish (with Traditional and Modern Sorting)
    1: [0x040C, 0x0C0C],  # French (France and Canada)
    2: [0x0407],  # German (Germany)
    3: [0x0410],  # Italian (Italy)
    4: [0x0413],  # Dutch
    5: [0x041D],  # Swedish (Sweden)
    6: [0x080A, 0x040A, 0x0C0A],  # Spanish (Mexico, Traditional Sort and Modern Sort)
    7: [0x0406],  # Danish
    8: [0x0416, 0x0816],  # Portuguese
    9: [0x0414],  # Norwegian (Bokmål)
    13: [0x040B],  # Finnish
    14: [0x0408],  # Greek
    15: [0x040F],  # Icelandic
    16: [0x043A],  # Maltese
    17: [0x041F],  # Turkish
    18: [0x041A, 0x101A],  # Croatian
    24: [0x0427],  # Lithuanian
    25: [0x0415],  # Polish
    26: [0x040E],  # Hungarian
    27: [0x0425],  # Estonian
    28: [0x0426],  # Latvian
    30: [0x0438],  # Faroese
    32: [0x0419],  # Russian
    34: [0x0813],  # Flemish
    35: [0x083C],  # IrishGaelic
    36: [0x041C],  # Albanian
    37: [0x0418],  # Romanian
    38: [0x0405],  # Czech
    39: [0x041B],  # Slovak
    40: [0x0424],  # Slovenian
    42: [0x0C1A, 0x1C1A, 0x081A, 0x181A],  # Serbian (Latin and Cyrillic)
    43: [0x042F],  # Macedonian
    44: [0x0402],  # Bulgarian
    45: [0x0422],  # Ukrainian
    46: [0x0423],  # Byelorussian
    47: [0x0443, 0x0843],  # Uzbek and Uzbek Cyrillic
    48: [0x043F],  # Kazakh
    49: [0x082C],  # Azerbaijani
    54: [0x0440],  # Kirghiz
    55: [0x0428],  # Tajiki
    56: [0x0442],  # Turkmen
    58: [0x0450],  # Mongolian (Cyrillic)
    81: [0x0421],  # Indonesian
    83: [0x043E, 0x083E],  # MalayRoman
    89: [0x0441],  # Swahili
    90: [0x0487],  # Kinyarwanda
    128: [0x0452],  # Welsh
    129: [0x042D],  # Basque
    130: [0x0403],  # Catalan
    132: [0x0C6B, 0x046B, 0x086B],  # Quechua
    135: [0x0444],  # Tatar
    140: [0x0456],  # Galician
    141: [0x0436],  # Afrikaans
    142: [0x047E],  # Breton
    149: [0x046F],  # Greenlandic
    150: [0x042C],  # AzerbaijanRoman
    151: [0x0814],  # Norwegian (Nynorsk)
}

LANGTAG_TO_MAC_LANGCODE = {
    "en": 0,  # English US (Last Resort)
    "ja": 11,  # Japanese
    "zh-Hant": 19,  # Chinese Traditional
    "ko": 23,  # Korean
    "zh-Hans": 33,  # Chinese Simplified
    # Languages untested:
    "af": 141,  # Afrikaans
    "az": 150,  # AzerbaijanRoman
    "az-Cyrl": 49,  # Azerbaijani
    "be": 46,  # Byelorussian
    "bg": 44,  # Bulgarian
    "br": 142,  # Breton
    "ca": 130,  # Catalan
    "cy": 128,  # Welsh
    "cs": 38,  # Czech
    "da": 7,  # Danish
    "de": 2,  # German
    "el": 14,  # Greek
    "es": 27,  # Estonian
    "et": 6,  # Spanish
    "eu": 129,  # Basque
    "fi": 13,  # Finnish
    "fo": 30,  # Faroese
    "fr": 1,  # French
    "ga": 35,  # IrishGaelic
    "gl": 140,  # Galician
    "hr": 18,  # Croatian
    "hu": 26,  # Hungarian
    "id": 81,  # Indonesian
    "is": 15,  # Icelandic
    "it": 3,  # Italian
    "kk": 48,  # Kazakh
    "kl": 149,  # Greenlandic
    "ky": 54,  # Kirghiz
    "lt": 24,  # Lithuanian
    "lv": 28,  # Latvian
    "mk": 43,  # Macedonian
    "mn": 58,  # Mongolian (Cyrillic)
    "ms": 83,  # MalayRoman
    "mt": 16,  # Maltese
    "nl": 4,  # Dutch
    "nl-BE": 34,  # Flemish
    "nb": 9,  # Norwegian (Bokmål)
    "nn": 151,  # Norwegian (Nynorsk)
    "pl": 25,  # Polish
    "pt": 8,  # Portuguese
    "qu": 132,  # Quechua
    "ro": 37,  # Romanian
    "ru": 32,  # Russian
    "rw": 90,  # Kinyarwanda
    "sl": 40,  # Slovenian
    "sk": 39,  # Slovak
    "sq": 36,  # Albanian
    "sr": 42,  # Serbian
    "sv": 5,  # Swedish
    "sw": 89,  # Swahili
    "tg": 55,  # Tajiki
    "tk": 56,  # Turkmen
    "tr": 17,  # Turkish
    "tt": 135,  # Tatar
    "uk": 45,  # Ukrainian
    "uz": 47,  # Uzbek
}

MAC_LANGCODE_TO_PLATENCID = {
    0: 0,  # langEnglish -> smRoman
    11: 1,  # langJapanese -> smJapanese
    19: 2,  # langTradChinese -> smTradChinese
    23: 3,  # langKorean -> smKorean
    33: 25,  # langSimpChinese -> smSimpChinese
    1: 0,  # langFrench -> smRoman
    2: 0,  # langGerman -> smRoman
    3: 0,  # langItalian -> smRoman
    4: 0,  # langDutch -> smRoman
    5: 0,  # langSwedish -> smRoman
    6: 0,  # langSpanish -> smRoman
    7: 0,  # langDanish -> smRoman
    8: 0,  # langPortuguese -> smRoman
    9: 0,  # langNorwegian -> smRoman
    13: 0,  # langFinnish -> smRoman
    15: 0,  # langIcelandic -> smRoman (modified)
    16: 0,  # langMaltese -> smRoman
    17: 0,  # langTurkish -> smRoman (modified)
    18: 0,  # langCroatian -> smRoman (modified)
    29: 0,  # langSami -> smRoman
    30: 0,  # langFaroese -> smRoman (modified)
    34: 0,  # langFlemish -> smRoman
    35: 0,  # langIrishGaelic -> smRoman (modified)
    36: 0,  # langAlbanian -> smRoman
    37: 0,  # langRomanian -> smRoman (modified)
    40: 0,  # langSlovenian -> smRoman (modified)
    81: 0,  # langIndonesian -> smRoman
    82: 0,  # langTagalog -> smRoman
    83: 0,  # langMalayRoman -> smRoman
    88: 0,  # langSomali -> smRoman
    89: 0,  # langSwahili -> smRoman
    90: 0,  # langKinyarwanda -> smRoman
    91: 0,  # langRundi -> smRoman
    92: 0,  # langNyanja -> smRoman
    93: 0,  # langMalagasy -> smRoman
    94: 0,  # langEsperanto -> smRoman
    128: 0,  # langWelsh -> smRoman (modified)
    129: 0,  # langBasque -> smRoman
    130: 0,  # langCatalan -> smRoman
    131: 0,  # langLatin -> smRoman
    132: 0,  # langQuechua -> smRoman
    133: 0,  # langGuarani -> smRoman
    134: 0,  # langAymara -> smRoman
    138: 0,  # langJavaneseRom -> smRoman
    139: 0,  # langSundaneseRom -> smRoman
    140: 0,  # langGalician -> smRoman
    141: 0,  # langAfrikaans -> smRoman
    142: 0,  # langBreton -> smRoman (modified)
    144: 0,  # langScottishGaelic -> smRoman (modified)
    145: 0,  # langManxGaelic -> smRoman (modified)
    146: 0,  # langIrishGaelicScript -> smRoman (modified)
    147: 0,  # langTongan -> smRoman
    149: 0,  # langGreenlandic -> smRoman
    150: 0,  # langAzerbaijanRoman -> smRoman
    151: 0,  # langNynorsk -> smRoman
    14: 6,  # langGreek -> smGreek
    148: 6,  # langGreekAncient -> smRoman
    32: 7,  # langRussian -> smCyrillic
    42: 7,  # langSerbian -> smCyrillic
    43: 7,  # langMacedonian -> smCyrillic
    44: 7,  # langBulgarian -> smCyrillic
    45: 7,  # langUkrainian -> smCyrillic (modified)
    46: 7,  # langByelorussian -> smCyrillic
    47: 7,  # langUzbek -> smCyrillic
    48: 7,  # langKazakh -> smCyrillic
    49: 7,  # langAzerbaijani -> smCyrillic
    53: 7,  # langMoldavian -> smCyrillic
    54: 7,  # langKirghiz -> smCyrillic
    55: 7,  # langTajiki -> smCyrillic
    56: 7,  # langTurkmen -> smCyrillic
    58: 7,  # langMongolianCyr -> smCyrillic
    135: 7,  # langTatar -> smCyrillic
    24: 29,  # langLithuanian -> smCentralEuroRoman
    25: 29,  # langPolish -> smCentralEuroRoman
    26: 29,  # langHungarian -> smCentralEuroRoman
    27: 29,  # langEstonian -> smCentralEuroRoman
    28: 29,  # langLatvian -> smCentralEuroRoman
    38: 29,  # langCzech -> smCentralEuroRoman
    39: 29,  # langSlovak -> smCentralEuroRoman       
}

UNSUPPORTED_LANGTAG_TO_MAC_LANGCODE = {
    # They are not supported by fontTools because their platEncID cannot be encoded/decoded yet.
    "he": 10,
    "ar": 12,
    "ur": 20,
    "hi": 21,
    "th": 22,
    "fa": 31,
    "yi": 41,
    "az-Arab": 50,
    "hy": 51,
    "ka": 52,
    "mn-CN": 57,  # Inner Mongolian (Traditional)
    "ps": 59,
    "ks": 60,
    "ku": 61,
    "sd": 62,
    "bo": 63,
    "ne": 64,
    "sa": 65,
    "mr": 66,
    "bn": 67,
    "as": 68,
    "gu": 69,
    "pa": 70,
    "or": 71,
    "ml": 72,
    "kn": 73,
    "ta": 74,
    "te": 75,
    "si": 76,
    "my": 77,
    "km": 78,
    "lo": 79,
    "vi": 80,
    "ms-Arab": 84,
    "am": 85,
    "ti": 86,
    "om": 87,
    "ug": 136,
    "dz": 137,
    "iu": 143,
    # The following are unsupported because there are no overlaps between MS langcodes and them.
    "ay": 134,  # Aymara
    "el-polyton": 148,  # GreekAncient
    "eo": 94,  # Esperanto
    "ga": 146,  # IrishGaelicScript
    "gd": 144,  # ScottishGaelic
    "gn": 133,  # Guarani
    "gv": 145,  # ManxGaelic
    "jv": 138,  # JavaneseRom
    "la": 131,  # Latin
    "mg": 93,  # Malagasy
    "mo": 53,  # Moldavian
    "ny": 92,  # Nyanja
    "rn": 91,  # Rundi
    "se": 29,  # Sami
    "so": 88,  # Somali
    "su": 139,  # SundaneseRom
    "tl": 82,  # Tagalog
    "to": 147,  # Tongan
}

# They are not supported by fontTools because their platEncID cannot be encoded/decoded yet.
UNSUPPORTED_MAC_LANGCODE_TO_PLATENCID = {
    12: 4,  # langArabic -> smArabic
    20: 4,  # langUrdu -> smArabic
    31: 4,  # langFarsi -> smArabic (modified)
    50: 4,  # langAzerbaijanAr -> smArabic
    59: 4,  # langPashto -> smArabic
    60: 4,  # langKurdish -> smArabic
    61: 4,  # langKashmiri -> smArabic
    62: 4,  # langSindhi -> smArabic
    84: 4,  # langMalayArabic -> smArabic
    136: 4,  # langUighur -> smArabic
    10: 5,  # langHebrew -> smHebrew
    41: 5,  # langYiddish -> smHebrew
    21: 9,  # langHindi -> smDevanagari
    64: 9,  # langNepali -> smDevanagari
    65: 9,  # langSanskrit -> smDevanagari
    66: 9,  # langMarathi -> smDevanagari
    70: 10,  # langPunjabi -> smGurmukhi
    69: 11,  # langGujarati -> smGujarati
    71: 12,  # langOriya -> smOriya
    67: 13,  # langBengali -> smBengali
    68: 13,  # langAssamese -> smBengali
    74: 14,  # langTamil -> smTamil
    75: 15,  # langTelugu -> smTelugu
    73: 16,  # langKannada -> smKannada
    72: 17,  # langMalayalam -> smMalayalam
    76: 18,  # langSinhalese -> smSinhalese
    77: 19,  # langBurmese -> smBurmese
    78: 20,  # langKhmer -> smKhmer
    22: 21,  # langThai -> smThai
    79: 22,  # langLao -> smLao
    52: 23,  # langGeorgian -> smGeorgian
    51: 24,  # langArmenian -> smArmenian
    63: 26,  # langTibetan -> smTibetan
    137: 26,  # langDzongkha -> smTibetan
    57: 27,  # langMongolian -> smMongolian
    85: 28,  # langAmharic -> smEthiopic
    86: 28,  # langTigrinya -> smEthiopic
    87: 28,  # langOromo -> smEthiopic
    143: 28,  # langInuktitut -> smEthiopic (modified)
    80: 30,  # langVietnamese -> smVietnamese
}


CHARSET_TO_CODEPAGE_RANGE_1 = {
    "latin" : 0,
    "latinExt" : 1,
    "cyrillic" : 2,
    "greek" : 3,
    "turkish" : 4,
    "hebrew" : 5,
    "arabic" : 6,
    "baltic" : 7,
    "vietnamese" : 8,
    "ansi1" : 9,
    "ansi2" : 10,
    "ansi3" : 11,
    "ansi4" : 12,
    "ansi5" : 13,
    "ansi6" : 14,
    "ansi7" : 15,
    "thai" : 16,
    "jis" : 17,
    "gbk" : 18,
    "korWansung" : 19,
    "big5" : 20,
    "korJohab" : 21,
    "oem1" : 22,
    "oem2" : 23,
    "oem3" : 24,
    "oem4" : 25,
    "oem5" : 26,
    "oem6" : 27,
    "oem7" : 28,
    "macRoman" : 29,
    "oem" : 30,
    "symbol" : 31,
}

CHARSET_TO_CODEPAGE_RANGE_2 = {
    "oem8": 0,
    "oem9": 1,
    "oem10": 2,
    "oem11": 3,
    "oem12": 4,
    "oem13": 5,
    "oem14": 6,
    "oem15": 7,
    "oem16": 8,
    "oem17": 9,
    "oem18": 10,
    "oem19": 11,
    "oem20": 12,
    "oem21": 13,
    "oem22": 14,
    "oem23": 15,
    "dosGreek": 16,
    "dosRussian": 17,
    "dosNordic": 18,
    "dosArabic": 19,
    "dosCanadianFrench": 20,
    "dosHebrew": 21,
    "dosIcelandic": 22,
    "dosPortuguese": 23,
    "dosTurkish": 24,
    "dosCyrillic": 25,
    "dosLatinExt": 26,
    "dosBaltic": 27,
    "dosGreekFormer437G": 28,
    "dosArabicASMO708": 29,
    "dosLatinWE": 30,
    "dosAscii": 31,
}

