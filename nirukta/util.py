import os
import glob
import sys

from nirukta.parsing.visitors.sloka import SlokaVisitor, validate_sloka
from nirukta.parsing.visitors.sutra import SutraVisitor
from nirukta.timelines import ExplainSloka, SlokaFileTimeline, SutraFileTimeline


def is_nirukta_file(file: str):
    return ".sloka" in file or ".sutra" in file


def choose_nirukta_file() -> str:
    cached = os.environ.get("NIRUKTA_FILE")
    if cached:
        return cached

    from PySide6.QtWidgets import QApplication

    if QApplication.instance() is not None:
        return _choose_nirukta_file_gui()

    return _choose_nirukta_file_terminal()


# kept alive across rebuilds so the panel stays open
_picker = None


def _choose_nirukta_file_gui() -> str:
    global _picker
    from nirukta.gui.file_picker import NiruktaFilePicker

    if _picker is None:
        _picker = NiruktaFilePicker()
        _picker.destroyed.connect(_on_picker_destroyed)
        _picker.file_chosen.connect(_trigger_rebuild)
        _picker._rebuild_connected = True  # type: ignore[attr-defined]

    return os.environ.get("NIRUKTA_FILE", "")


def _on_picker_destroyed() -> None:
    global _picker
    _picker = None


def _trigger_rebuild(_path: str) -> None:
    from PySide6.QtWidgets import QApplication
    from janim.gui.anim_viewer import AnimViewer

    app = QApplication.instance()
    if app is None:
        return
    for w in app.topLevelWidgets():
        if isinstance(w, AnimViewer):
            w.on_rebuild_triggered()
            return


def _choose_nirukta_file_terminal() -> str:
    prefix = "./library"

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

    os.environ["NIRUKTA_FILE"] = chosen
    return chosen


def file_to_timeline(chosen: str):
    print(f"Loading {chosen}...")
    if ".sutra" in chosen:
        sloka_index = os.environ.get("NIRUKTA_SLOKA_INDEX")
        if sloka_index is not None:
            # rendering one sloka: parse without validating the whole sutra,
            # then validate only the sloka we are about to render
            sutra_file = SutraVisitor(chosen, validate=False).parse()
            sloka = sutra_file.slokas[int(sloka_index)]
            validate_sloka(sloka)
            return ExplainSloka(sloka=sloka)
        return SutraFileTimeline(SutraVisitor(chosen).parse())
    else:
        return SlokaFileTimeline(SlokaVisitor(chosen).parse())
