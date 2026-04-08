import re

from janim.imports import BLUE, GREEN, MAROON, ORANGE, PINK, RED, TEAL, YELLOW

SCALE = 1.3
INTRO_FONT = "Tiro Devanagari Sanskrit"
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

# MISSING_CHUNK_RE = re.compile(r"#\w+\(\)|[a-zA-Z0-9']+|[^a-zA-Z0-9'\s#]+|\s+|#")

# combined = re.compile("|".join([re1.pattern, re2.pattern]))

DIGITS_RE = re.compile(r"\d+")
ALPHA_RE = re.compile(r"[a-zA-Z]+")
