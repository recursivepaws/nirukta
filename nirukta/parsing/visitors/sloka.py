import logging
import os
import traceback
from typing import Sequence
from nirukta.models.enums import SoundChange
from nirukta.models.tokens import PunctuationToken, SoundChangeToken
from nirukta.render import transliterate
from nirukta.strings import unswara
import sandhi as sandhi_module
from janim.imports import log
from nirukta.inflection import Case, SanskritInflection
from nirukta.models import (
    CompoundToken,
    EnglishGloss,
    System,
    Line,
    SimpleToken,
    Sloka,
    TokenType,
    Utterance,
)
from nirukta.models import SlokaFile
from nirukta.parsing.grammars import SLOKA_GRAMMAR
from parsimonious.exceptions import ParseError
from parsimonious.nodes import NodeVisitor
from pysanskritv2.tables.decline_file import DeclRec

S = sandhi_module.Sandhi()


def models_for_stem(stem: str) -> list[str]:
    # check multi-char endings first (longest match wins)
    if stem.endswith("aYc"):
        return ["m_aYc", "n_aYc"]
    if stem.endswith("Iyas"):
        return ["m_Iyas", "n_Iyas"]
    if stem.endswith("vas"):
        return ["m_vas", "n_vas"]
    if stem.endswith("han"):
        return ["m_han", "n_han"]

    # mat also uses the vat paradigm
    if stem.endswith("vat") or stem.endswith("mat"):
        return ["m_vat", "n_vat"]
    if stem.endswith("an"):
        return ["m_an", "f_an", "n_an"]
    if stem.endswith("as"):
        return ["m_as", "f_as", "n_as"]
    if stem.endswith("is"):
        return ["m_is", "f_is", "n_is"]
    if stem.endswith("us"):
        return ["m_us", "f_us", "n_us"]
    if stem.endswith("in"):
        return ["m_in", "n_in"]

    # single-char endings
    endings = {
        "a": ["m_a", "n_a"],
        "A": ["f_A"],
        "i": ["m_i", "f_i", "n_i"],
        "I": ["f_I"],
        "u": ["m_u", "f_u", "n_u"],
        "U": ["f_U"],
        "f": ["m_f", "f_f", "n_f"],
        "F": ["m_F", "f_F"],
        "o": ["m_o", "f_o"],
        "O": ["m_O", "f_O"],
        "e": ["m_e"],
        "E": ["m_E", "f_E", "n_E"],
        "x": ["m_x", "f_x"],
    }
    return endings.get(stem[-1], [])


# def declension_candidates(stem: str):
#     canditates = []
#     for model in models_for_stem(stem):
#         rec = DeclRec(f"{model}\t{stem}\t")
#         for option in rec.inflection.split(":"):
#             if "/" in option:
#                 canditates + option.split("/")
#             else:
#                 canditates.append(option)
#     return canditates
def declension_candidates(model: str, stem: str):
    candidates = []
    rec = DeclRec(f"{model}\t{stem}\t")

    if rec.inflection is not None:
        for option in rec.inflection.split(":"):
            if "/" in option:
                candidates += option.split("/")
            else:
                candidates.append(option)

    return candidates


def validate_declension(stem: str, declined: str):
    validated = False

    print_stem = transliterate(System.SLP1, System.IAST, stem)
    print_declined = transliterate(System.SLP1, System.IAST, declined)

    for model in models_for_stem(stem):
        if declined in declension_candidates(model, stem):
            log.info(
                f"inflection validated [declension]:\t'{print_stem}' -> '{print_declined}' is a valid '{model}' declension."
            )
            validated = True

    if not validated:
        log.warning(
            f"inflection invalid   [declension]:\t'{print_stem}' -> '{print_declined}' is not a known declension."
        )
        for model in models_for_stem(stem):
            options = list(
                map(
                    lambda x: transliterate(System.SLP1, System.IAST, x),
                    declension_candidates(model, stem),
                )
            )
            log.info(f"{model}: {options}")


# Result should be provided in slp1
def validate_equation(parts: Sequence[TokenType], result: str, kind: SoundChange):
    if len(parts) > 1:
        built = ""

        partinfo = []
        for part in parts:
            partinfo.append(f"'{part.slp1}'")
        log.debug(f"parts: {partinfo}")

        for i in range(len(parts)):
            A = built
            B = transliterate(
                System.SLP1,
                System.WX,
                unswara(parts[i].slp1),
            )
            log.debug(
                f"adding: '{transliterate(System.WX, System.IAST, A)}' + '{transliterate(System.WX, System.IAST, B)}'"
            )

            results = S.sandhi(A, B, input_scheme="wx")
            valid_forms = {r[0] for r in results}
            # compact_results = list(filter(lambda x: " " not in x, valid_forms))
            compact_results = list(
                map(lambda x: x.split(" ")[0] if " " in x else x, valid_forms)
            )
            compact_results = list(map(lambda x: x.replace("_", ""), compact_results))
            # log.info(f"compact_results: {compact_results}")

            if len(compact_results) == 0:
                unverified = list(
                    map(
                        lambda x: transliterate(System.WX, System.IAST, x),
                        compact_results,
                    )
                )
                log.warning(f"cannot validate: {unverified}")
            else:
                built = compact_results[0]

        built = transliterate(System.WX, System.IAST, built)
        final_result = transliterate(System.SLP1, System.IAST, unswara(result))
        built = final_result.replace("'", "")
        final_result = final_result.replace("'", "")

        # log.info(f"parts: {parts}")

        undone_parts = list(
            map(lambda x: transliterate(System.SLP1, System.IAST, x.slp1), parts)
        )

        if built != final_result:
            log.warning(
                f"unable for verify sandhi for these parts: {undone_parts}\n"
                f"expected '{final_result}' but got '{built}'"
            )
        else:
            if kind == SoundChange.EXTERNAL_SANDHI:
                log.info(
                    f"sandhi validated [external]:\t\t'{undone_parts[0]}' => '{final_result}' when preceding '{undone_parts[1]}'"
                )
            else:
                equation_string = " + ".join(
                    list(map(lambda x: f"'{x}'", undone_parts))
                )
                log.info(
                    f"sandhi validated [internal]:\t\t{equation_string} = '{final_result}'"
                )

    else:
        log.warning(f"no need to validate parts of n<2 {parts}")


def validate_sandhi(sequence: Sequence[TokenType]):

    def validate_compound(compound: CompoundToken):
        # External
        validate_sandhi(compound.parts)
        # Internal
        validate_equation(
            compound.parts,
            compound.slp1,
            SoundChange.INTERNAL_SANDHI,
        )

    for i in range(len(sequence)):
        current = sequence[i]

        match current:
            case SimpleToken():
                continue
            case PunctuationToken():
                continue
            case SoundChangeToken():
                match current.kind:
                    case SoundChange.INFLECTION:
                        validate_declension(current.part.slp1, current.slp1)
                    case SoundChange.EXTERNAL_SANDHI:
                        inner = current.part
                        if (
                            isinstance(inner, SoundChangeToken)
                            and inner.kind == SoundChange.INFLECTION
                        ):
                            validate_declension(inner.part.slp1, inner.slp1)
                        elif isinstance(inner, CompoundToken):
                            validate_compound(inner)
                        if i < len(sequence) - 2:
                            next = sequence[i + 1]
                            validate_equation(
                                [current.part, next],
                                current.slp1,
                                SoundChange.EXTERNAL_SANDHI,
                            )
            case CompoundToken():
                validate_compound(current)


class SlokaVisitor(NodeVisitor):
    file: str
    dir: str
    source: str

    def __init__(self, file: str):
        NodeVisitor.__init__(self)

        print(f"Loading {file}...")

        with open(file) as f:
            self.source = f.read()

        self.file = file
        self.directory = os.path.dirname(self.file)

    def _print_parse_error(self, e: ParseError) -> None:
        lines = self.source.splitlines()
        before = self.source[: e.pos]
        lineno = before.count("\n")
        col = e.pos - before.rfind("\n") - 1
        ctx_start = max(0, lineno - 2)
        ctx_end = min(len(lines), lineno + 3)
        print(f"\nParse error at line {lineno + 1}, col {col + 1}: {e}\n")
        for i, line in enumerate(lines[ctx_start:ctx_end], start=ctx_start + 1):
            print(f"  {i:4d} | {line}")
            if i == lineno + 1:
                print(f"       | {' ' * col}^")
        print()

    def parse(self) -> SlokaFile:
        try:
            tree = SLOKA_GRAMMAR.parse(self.source)
        except ParseError as e:
            self._print_parse_error(e)
            raise
        return self.visit(tree)

    # -- top level ----------------------------------------------------------

    def visit_sloka(self, _, visited_children):
        _, citation, _, lines, _ = visited_children
        return SlokaFile(citation=citation, sloka=Sloka(list(lines)))

    # -- citation -----------------------------------------------------------

    def visit_citation_line(self, _, visited_children):
        _, _, text, _, _ = visited_children
        return text

    def visit_citation_text(self, node, _):
        return node.text.strip()

    # -- line / verse line --------------------------------------------------

    def visit_line(self, _, visited_children):
        _, _, verse_lines = visited_children
        return Line(vAkyAni=list(verse_lines))

    def visit_verse_line(self, _, visited_children):
        # visited_children: [lookahead, token_seq, ws, first_quoted_str, rest_quoted_strs, ws]
        _, tokens, _, first, rest, _ = visited_children
        extra = [pair[1] for pair in rest]
        english = "#linebreak()".join([first] + extra)
        return Utterance(tokens=tokens, english=english)

    # -- token sequence -----------------------------------------------------

    def visit_token_seq(self, _, visited_children):
        first, rest = visited_children
        tokens: Sequence[TokenType] = [first]
        for pair in rest:
            tokens.append(pair[1])

        try:
            validate_sandhi(tokens)
        except Exception as e:
            log.error(f"Failed to validate sandhi: {e}")

        return tokens

    def visit_token(self, _, visited_children):
        return visited_children[0]

    # -- compound (sandhi) tokens -------------------------------------------

    def visit_text_token(self, _, visited_children):
        initial, inflect_parts, external_parts = visited_children

        # Start construction
        if isinstance(initial, list):
            assert len(initial) == 1
            result = initial[0]
        else:
            result = initial

        # normalize inflect_parts
        i_parts = inflect_parts if isinstance(inflect_parts, list) else []
        i_parts = [p for p in i_parts if isinstance(p, str)]

        for slp1 in i_parts:
            result = SoundChangeToken(
                part=result, slp1=slp1, kind=SoundChange.INFLECTION
            )

        e_parts = external_parts if isinstance(external_parts, list) else []
        e_parts = [p for p in e_parts if isinstance(p, str)]
        for slp1 in e_parts:
            result = SoundChangeToken(
                part=result, slp1=slp1, kind=SoundChange.EXTERNAL_SANDHI
            )

        return result

    def visit_equation_part(self, _, visited_children):
        first_part, plus_parts, _, slp1 = visited_children
        parts = list([first_part]) + list(plus_parts)
        return CompoundToken(parts, slp1)

    def visit_inflect_part(self, _, visited_children):
        _, slp1 = visited_children
        return slp1

    def visit_external_part(self, _, visited_children):
        _, slp1 = visited_children
        return slp1

    def visit_plus_part(self, _, visited_children):
        _plus, _newline, part = visited_children
        return part

    def visit_comp_part(self, _, visited_children):
        return visited_children[0]

    def visit_paren_compound(self, _, visited_children):
        _, compound, _ = visited_children
        return compound

    # -- simple tokens & glosses --------------------------------------------

    def visit_simple_token(self, _, visited_children):
        slp1, glosses = visited_children
        return SimpleToken(slp1=slp1, glosses=glosses)

    def visit_gloss(self, _, visited_children):
        return visited_children[0]

    def visit_trans_gloss(self, _, visited_children):
        _, content, _ = visited_children
        return EnglishGloss(text=content)

    def visit_etym_gloss(self, _, visited_children):
        _, content, _ = visited_children
        try:
            inflection = SanskritInflection.parse(content)
            return inflection
        except Exception:
            try:
                case = Case.parse(content)
                print(f"case: {case}")
                return case
            except Exception:
                print(f'Error! invalid etymological glossing: "{content}"\n')
                logging.error(traceback.format_exc())
                return None

    def visit_trans_content(self, node, _):
        return node.text

    def visit_etym_content(self, node, _):
        return node.text

    # -- terminals ----------------------------------------------------------

    def visit_punct(self, node, _):
        return PunctuationToken(slp1=node.text)

    def visit_slp1(self, node, _):
        return node.text

    def visit_quoted_str(self, node, _):
        return node.text[1:-1].replace('\\"', '"').replace("\\\\", "\\")

    def generic_visit(self, node, visited_children):
        return visited_children or node
