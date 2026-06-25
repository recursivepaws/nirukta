import os
import sys

from nirukta.util import (
    SlokaVisitor,
    SutraVisitor,
    choose_nirukta_file,
    is_nirukta_file,
)
from nirukta.models.presentation.sloka import sloka_label
from nirukta.parsing.visitors.sloka import validate_sloka


def _prompt(message: str, on_eof: str) -> str:
    # validation closes the sys.stdin object (a dependency does this) while
    # leaving fd 0 open, so reopen it before reading or input() would raise
    if sys.stdin.closed:
        sys.stdin = open(0, closefd=False)
    try:
        return input(message)
    except EOFError:
        print()
        return on_eof


def validate_sutra(path: str) -> None:
    # parse once without validating so we can list the slokas cheaply
    slokas = SutraVisitor(path, validate=False).parse().slokas

    # parity with the GUI: NIRUKTA_SLOKA_INDEX picks a single sloka up front
    index = os.environ.get("NIRUKTA_SLOKA_INDEX")
    if index is not None:
        validate_sloka(slokas[int(index)])
        return

    while True:
        print("\nSelect a sloka to validate:")
        print("  [0] Whole Sutra")
        for i, sloka in enumerate(slokas):
            print(f"  [{i + 1}] {sloka_label(i, sloka)}")

        selection = _prompt("\nEnter number ([q] to quit): ", on_eof="q").strip()
        if selection in ("q", "n"):
            break
        if not selection.isdigit():
            print(f"Invalid selection: {selection}")
            continue

        choice = int(selection)
        if choice == 0:
            for sloka in slokas:
                validate_sloka(sloka)
        elif 1 <= choice <= len(slokas):
            validate_sloka(slokas[choice - 1])
        else:
            print(f"Invalid selection: {selection}")


def validate_single_sloka(path: str) -> None:
    while True:
        SlokaVisitor(path).parse()
        if _prompt("validate again? [Y]/n\n", on_eof="n") == "n":
            break


chosen = choose_nirukta_file()
assert is_nirukta_file(chosen), "Invalid file"

if ".sutra" in chosen:
    validate_sutra(chosen)
else:
    validate_single_sloka(chosen)
