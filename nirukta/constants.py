import re

from janim.imports import (
    BLUE,
    GREEN,
    MAROON,
    ORANGE,
    PINK,
    RED,
    TEAL,
    YELLOW,
    GREY,
)

SCALE = 1.3
SANSKRIT_FONT = "Tiro Devanagari Sanskrit"
LATIN_FONT = "Junicode"

COLORS = [RED, BLUE, YELLOW, GREEN, PINK, ORANGE, TEAL, MAROON]

# Typst Commands
TYPST_CMD_RE = re.compile(r"(#\w+\(\))")
WHITESPACE_RE = re.compile(r"\s+")
PUNCTUATION_RE = re.compile(r"[-,.!]+")
WORD_RE = re.compile(r"\w+")

known = [
    TYPST_CMD_RE.pattern,
    WHITESPACE_RE.pattern,
    PUNCTUATION_RE.pattern,
    WORD_RE.pattern,
]
fallback = r"(?:(?!" + "|".join(known) + r").)+"
MISSING_CHUNK_RE = re.compile("|".join(known + [fallback]))

DIGITS_RE = re.compile(r"\d+")
ALPHA_RE = re.compile(r"[a-zA-Z]+")

# I keep my shit fucking seven dimensional motherfucker
INACTIVE = GREY
