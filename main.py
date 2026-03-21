import importlib
from janim.imports import Config, Timeline
import glob
import os
import parser
from parser import parse, SlokaFile

importlib.reload(parser)


def get_sloka_file() -> str:
    cached = os.environ.get("JANIM_SLOKA_FILE")
    if cached:
        return cached

    sloka_files = sorted(glob.glob("./slokas/*.sloka"))
    sloka_files += sorted(glob.glob("./slokas/**/*.sloka"))
    if not sloka_files:
        print("No .sloka files found in ./slokas/")
        exit(1)

    print("Select a sloka file:")
    for i, path in enumerate(sloka_files):
        print(f"  [{i + 1}] {os.path.basename(path)}")

    selection = input("\nEnter number or filename: ").strip()

    if selection.isdigit():
        index = int(selection) - 1
        if not (0 <= index < len(sloka_files)):
            print(f"Invalid selection: {selection}")
            exit(1)
        chosen = sloka_files[index]
    else:
        matches = [
            f for f in sloka_files if os.path.basename(f) == selection or f == selection
        ]
        if not matches:
            print(f"No file found matching: {selection}")
            exit(1)
        chosen = matches[0]

    os.environ["JANIM_SLOKA_FILE"] = chosen
    return chosen


chosen = get_sloka_file()
print(f"Loading {chosen}...")

with open(chosen) as f:
    source = f.read()

sloka: SlokaFile = parse(source)


class SlokaTime(Timeline):
    CONFIG = Config(fps=60)

    def construct(self):
        self.play(sloka.teach())
        self.forward()
