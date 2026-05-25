from attr import dataclass
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


identify = MI.identify_meter
