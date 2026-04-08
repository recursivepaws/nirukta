from typing import Optional
from enum import Enum


class Language(Enum):
    ENGLISH = "english"
    SANSKRIT = "sanskrit"
    TRANSLIT = "translit"


class Animation(Enum):
    # Swara removal
    SWARAS = "Swara"
    # Other spelling changes
    SPELLS = "Spelling"
    # Color changes only
    COLORS = "Colors"
    # Node quantity changes
    EXPAND = "Expansion"
