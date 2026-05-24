from pathlib import Path

import vidyut
from vidyut.chandas import Chandas

_DATA_DIR = Path(__file__).parents[2] / "vidyut_data"
_METERS_TSV = _DATA_DIR / "chandas" / "meters.tsv"


if not _METERS_TSV.exists():
    _DATA_DIR.mkdir(exist_ok=True)
    vidyut.download_data(_DATA_DIR)
chandas = Chandas(str(_METERS_TSV))
