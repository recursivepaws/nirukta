import os
import glob
from janim.imports import WHITE
from aksharamukha import transliterate

from nirukta.models.enums import Language
from nirukta.parsing import parse_sloka, parse_sutra
from nirukta.constants import SCALE, TYPST_CMD_RE
from nirukta.timelines import SlokaFileTimeline, SutraFileTimeline


def is_nirukta_file(file: str):
    return ".sloka" in file or ".sutra" in file


def choose_nirukta_file() -> str:
    cached = os.environ.get("NIRUKTA_FILE")
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

    os.environ["NIRUKTA_FILE"] = chosen
    return chosen


def file_to_timeline(chosen: str):
    print(f"Loading {chosen}...")

    with open(chosen) as f:
        source = f.read()

    if ".sutra" in chosen:
        return SutraFileTimeline(parse_sutra(source))
    else:
        return SlokaFileTimeline(parse_sloka(source))


def set_font(text: str, font: str):
    return f'#set text(font: "{font}", stroke: none)\n#set page(width: {240 * SCALE}pt)\n{text}'


def text_box(text: str, color: str):
    if color == "#FFFFFF":
        return f"#box[#text[{text}]]"
    else:
        return f'#box[#text(fill: rgb("{color}"))[{text}]]'


def typst_code_safe(text: str, language: Language, color: str = WHITE) -> str:
    """Like typst_code, but splits out any embedded #foo() commands so they
    are never trapped inside a #box[#text[...]]."""
    parts = TYPST_CMD_RE.split(text)  # alternates: plain text, cmd, plain text, ...
    result = ""
    for part in parts:
        if not part:
            continue
        if TYPST_CMD_RE.fullmatch(part):
            result += part  # emit the command bare, e.g. #linebreak()
        else:
            result += typst_code(part, language, color)
    return result


def Junicode_translit(iast: str, color: str) -> str:
    """Like Junicode() but splits ṃ into m + combining dot for clean animation."""
    if "ṃ" not in iast:
        return text_box(iast, color)

    def T(s):
        return f'#text(fill: rgb("{color}"))[{s}]'

    parts = iast.split("ṃ")
    inner = ""
    for i, part in enumerate(parts):
        if i < len(parts) - 1:
            # everything up to and including the m of ṃ
            inner += T(part + "m")
            inner += r"#h(-0.175em)" + T("\u0323") + r"#h(0.175em)"
        else:
            # tail after the last ṃ
            if part:
                inner += T(part)

    return f"#box[{inner}]"


def transform_text(text: str, language: Language):
    match language:
        case Language.ENGLISH:
            return text
        case Language.TRANSLIT:
            iast = transliterate.process("SLP1", "IAST", text)
            if not iast:
                raise ValueError(f'Cannot represent "{text}" in IAST')
            return iast
        case Language.SANSKRIT:
            deva = transliterate.process("SLP1", "DEVANAGARI", text)
            if not deva:
                raise ValueError(f'Cannot represent "{text}" in devanagari')
            return deva


def typst_code(text: str, language: Language, color: str = WHITE):
    transformed = transform_text(text, language)
    return text_box(transformed, color)
