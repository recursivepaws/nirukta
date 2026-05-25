from attr import dataclass
from janim.imports import BLUE_E, RED_E
from skrutable.meter_identification import MeterIdentifier

MI = MeterIdentifier()


_LONG_VOWELS_SLP1 = frozenset("AIUFXeEoO")


@dataclass
class Akshara:
    text: str
    weight: str

    def is_long(self):
        """True if the SLP1 akshara contains a long vowel."""
        return any(c in _LONG_VOWELS_SLP1 for c in self.text)

    def rgb_color(self):
        bg = BLUE_E if self.weight == "g" else RED_E
        return f'rgb("{bg.lstrip("#")}")'


identify = MI.identify_meter
