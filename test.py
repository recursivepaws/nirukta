import vidyut
from pathlib import Path
from vidyut.chandas import Chandas
from vidyut.cheda import Chedaka

# from vidyut.kosha import Pada, Pratipadika
from vidyut.lipi import transliterate, Scheme
from vidyut.prakriya import (
    Dhatu,
    # Gana,
    Lakara,
    Linga,
    # Pada,
    # Pratipadika,
    Purusha,
    Prayoga,
    Vacana,
    # Vibhakti,
    Vyakarana,
)

DATA_DIR = Path(__file__).parent / "vidyut_data"
METERS_TSV = DATA_DIR / "chandas" / "meters.tsv"

if not METERS_TSV.exists():
    DATA_DIR.mkdir(exist_ok=True)
    vidyut.download_data(DATA_DIR)


# ── 1. chandas ─────────────────────────────────────────────────────────────────
# Identify meter and classify syllable weights

print("─" * 60)
print("1. CHANDAS — meter identification")
print("─" * 60)

padas_slp1 = [
    "vakratuRqa mahAkAya",
    "sUryakowi samapraBa",
    "nirviGnaM kuru me deva",
    "sarva kAryezu sarvadA",
]

c = Chandas(str(METERS_TSV))
chedaka = Chedaka(str(DATA_DIR))

_doc_match = c.classify("mAtaH samastajagatAM maDukEwaBAreH")
assert _doc_match.padya == "vasantatilakA", (
    f"Sanity check failed: got {_doc_match.padya}"
)
print("Sanity check passed: vasantatilakā identified correctly.\n")

for i, slp1 in enumerate(padas_slp1):
    iast = transliterate(slp1, Scheme.Slp1, Scheme.Iast)
    match = c.classify(slp1)
    weights = " ".join(akshara.weight for pada in match.aksharas for akshara in pada)
    print(f"Pada {i + 1}: {slp1}")
    print(f"  Meter : {match.padya}")
    print(f"  G/L   : {weights}\n")
    tokens = chedaka.run(slp1)
    for token in tokens:
        print(transliterate(token.lemma, Scheme.Slp1, Scheme.Iast))
        print(token)
        print()


# ── 2. prakriya ────────────────────────────────────────────────────────────────
# Derive word forms by applying Paninian grammar rules step-by-step.
# Using words from the sloka itself: kuru (do!) and deva (god).

# print("─" * 60)
# print("2. PRAKRIYA — Paninian derivation")
# print("─" * 60)
#
# v = Vyakarana()

# # kuru — imperative 2sg of kṛ (to do), the verb in "kuru me deva"
# # aupadeshika (dhatupatha) form of kṛ is qukf\Y, tanadi (8th) gana
# dhatu_kr = Dhatu.mula(r"qukf\Y", Gana.Tanadi)
# pada_kuru = Pada.Tinanta(
#     dhatu_kr, Prayoga.Kartari, Lakara.Lot, Purusha.Madhyama, Vacana.Eka
# )
# results = v.derive(pada_kuru)
# print(f"kṛ (to do) → imperative 2sg: {[r.text for r in results]}")
# print("Derivation steps for 'kuru':")
# kuru_result = next(r for r in results if r.text == "kuru")
# for step in kuru_result.history:
#     print(f"  [{step.code}] {' + '.join(step.result)}")
#
# print()
#
# devaḥ — nominative singular masculine of deva (god)
# prati_deva = Pratipadika.basic("deva")
# pada_devah = Pada.Subanta(prati_deva, Linga.Pum, Vibhakti.Prathama, Vacana.Eka)
# results = v.derive(pada_devah)
# print(f"deva (god) → nominative sg masc: {[r.text for r in results]}")
# print("Derivation steps for 'devaḥ':")
# for step in results[0].history:
#     print(f"  [{step.code}] {' + '.join(step.result)}")
#
# print()


# ── 3. cheda ───────────────────────────────────────────────────────────────────
# Segment and morphologically tag a Sanskrit sentence.

# print("─" * 60)
# print("3. CHEDA — word segmentation + morphological tagging")
# print("─" * 60)


# Use the third pada in SLP1
# slp1_pada = transliterate("nirvighnaṃ kuru me deva", Scheme.Iast, Scheme.Slp1)
# print(f"Input (SLP1): {slp1_pada}\n")
