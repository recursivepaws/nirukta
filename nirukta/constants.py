import re

from janim.imports import BLUE, GREEN, MAROON, ORANGE, PINK, RED, TEAL, YELLOW

SCALE = 1.3
INTRO_FONT = "Tiro Devanagari Sanskrit"
SANSKRIT_FONT = "Tiro Devanagari Sanskrit"
LATIN_FONT = "Junicode"

COLORS = [RED, BLUE, YELLOW, GREEN, PINK, ORANGE, TEAL, MAROON]

TYPST_CMD_RE = re.compile(r"(#\w+\(\))")
MISSING_CHUNK_RE = re.compile(r"#\w+\(\)|[a-zA-Z0-9']+|[^a-zA-Z0-9'\s#]+|#")
DIGITS_RE = re.compile(r"\d+")
ALPHA_RE = re.compile(r"[a-zA-Z]+")
