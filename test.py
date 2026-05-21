import vidyut
from pathlib import Path
from vidyut.chandas import Chandas
from vidyut.lipi import transliterate, Scheme

DATA_DIR = Path(__file__).parent / "vidyut_data"
METERS_TSV = DATA_DIR / "chandas" / "meters.tsv"

if not METERS_TSV.exists():
    DATA_DIR.mkdir(exist_ok=True)
    vidyut.download_data(DATA_DIR)

# Lowercase so conventional caps don't confuse the IAST parser
padas_iast = [
    "vakratuṇḍa mahākāya",
    "sūryakoṭi samaprabha",
    "nirvighnaṃ kuru me deva",
    "sarva kāryeṣu sarvadā",
]

c = Chandas(str(METERS_TSV))

# Sanity check: known example from the vidyut docs (expects vasantatilakā)
_doc_match = c.classify("mAtaH samastajagatAM maDukEwaBAreH")
assert _doc_match.padya == "vasantatilakA", f"Library sanity check failed: got {_doc_match.padya}"
print("Sanity check passed: vasantatilakā identified correctly.\n")

for i, iast in enumerate(padas_iast):
    slp1 = transliterate(iast, Scheme.Iast, Scheme.Slp1)
    print(f"Pada {i + 1} (SLP1): {slp1}")
    match = c.classify(slp1)
    print(f"  Meter identified: {match.padya}")
    for pada in match.aksharas:
        for akshara in pada:
            print(f"    {akshara.text:12} {akshara.weight}")
    print()
