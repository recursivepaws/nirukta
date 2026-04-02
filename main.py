import importlib
from janim.imports import Timeline
import glob
import os

import parser
import patches

from parser import parse_sloka, parse_sutra
from nirukta import Nirukta

importlib.reload(parser)
importlib.reload(patches)


def is_nirukta_file(file: str):
    return ".sloka" in file or ".sutra" in file


def get_nirukta_file() -> str:
    cached = os.environ.get("JANIM_SLOKA_FILE")
    if cached:
        return cached

    prefix = "./blueprints"

    end_loop = False

    while not end_loop:
        nirukta_files = []
        nirukta_files += sorted(glob.glob(f"{prefix}/**/"))
        nirukta_files += sorted(glob.glob(f"{prefix}/*.sloka"))
        nirukta_files += sorted(glob.glob(f"{prefix}/*.sutra"))
        if not nirukta_files:
            print(f"No nirukta files found in {prefix}")
            exit(1)

        print("Select a sloka file or nested folder:")
        for i, path in enumerate(nirukta_files):
            name = os.path.basename(path)
            dir = os.path.dirname(path).removeprefix(prefix)
            print(f"  [{i + 1}] {name if is_nirukta_file(name) else dir}")

        selection = input("\nEnter number or filename: ").strip()

        if selection.isdigit():
            index = int(selection) - 1
            if not (0 <= index < len(nirukta_files)):
                print(f"Invalid selection: {selection}")
                exit(1)
            chosen = nirukta_files[index]
        else:
            raise ValueError("Select valid index")

        if is_nirukta_file(chosen):
            end_loop = True
        else:
            prefix = chosen

    os.environ["JANIM_SLOKA_FILE"] = chosen
    return chosen


chosen = get_nirukta_file()

print(f"Loading {chosen}...")

with open(chosen) as f:
    source = f.read()


if ".sutra" in chosen:
    nirukta = parse_sutra(source)
else:
    nirukta = parse_sloka(source)


class EntryPoint(Timeline):
    def construct(self):
        timeline = Nirukta(nirukta).build().to_item().show()
        self.forward_to(timeline.end)
