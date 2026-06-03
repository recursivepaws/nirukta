from attr import dataclass
from janim.imports import BLUE_E, RED_E
from nirukta.models import TokenType
from skrutable.meter_identification import MeterIdentifier

MI = MeterIdentifier()

_SLP1_VOWELS = frozenset("aAiIuUfFxXeEoO")
_SLP1_VOWELS_LONG = frozenset("AIUFXeEoO")

# vowels + anusvara + visarga
_SLP1_ENDS_CLEANLY = frozenset("aAiIuUfFxXeEoOMH")


@dataclass
class Akshara:
    text: str
    weight: str

    def is_long(self):
        """True if the SLP1 akshara contains a long vowel."""
        return any(c in _SLP1_VOWELS_LONG for c in self.text)

    def rgb_color(self):
        bg = BLUE_E if self.weight == "g" else RED_E
        return f'rgb("{bg.lstrip("#")}")'


identify = MI.identify_meter
