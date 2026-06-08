import os
import glob
import sys

from nirukta.parsing.visitors.sloka import SlokaVisitor
from nirukta.parsing.visitors.sutra import SutraVisitor
from nirukta.timelines import SlokaFileTimeline, SutraFileTimeline


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
    from PySide6.QtCore import QEventLoop
    from nirukta.gui.file_picker import NiruktaFilePicker

    if _picker is None:
        _picker = NiruktaFilePicker()
        _picker.destroyed.connect(_on_picker_destroyed)

    loop = QEventLoop()
    chosen: list[str] = []

    def _on_first_chosen(path: str) -> None:
        chosen.append(path)
        loop.quit()

    _picker.file_chosen.connect(_on_first_chosen)
    _picker.destroyed.connect(loop.quit)
    _picker.show()
    loop.exec()
    _picker.file_chosen.disconnect(_on_first_chosen)

    if not chosen:
        exit(0)

    # Subsequent selections trigger a viewer rebuild instead of blocking again.
    if not getattr(_picker, "_rebuild_connected", False):
        _picker.file_chosen.connect(_trigger_rebuild)
        _picker._rebuild_connected = True  # type: ignore[attr-defined]

    return chosen[0]


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
    #
    # with open(chosen) as f:
    #     source = f.read()

    if ".sutra" in chosen:
        return SutraFileTimeline(SutraVisitor(chosen).parse())
    else:
        return SlokaFileTimeline(SlokaVisitor(chosen).parse())
