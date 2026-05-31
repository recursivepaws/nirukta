import logging
import os
import traceback
from typing import List, Union
from nirukta.render import transliterate
from nirukta.strings import unswara
import sandhi as sandhi_module
from janim.imports import log
from nirukta.inflection import Case, SanskritInflection
from nirukta.models import (
    CompoundToken,
    EnglishGloss,
    Language,
    System,
    Line,
    SimpleToken,
    Sloka,
    Utterance,
)
from nirukta.models import SlokaFile
from nirukta.parsing.grammars import SLOKA_GRAMMAR
from parsimonious.exceptions import ParseError
from parsimonious.nodes import NodeVisitor

S = sandhi_module.Sandhi()



def validate_equation(parts: List[Union[CompoundToken, SimpleToken]], result: str):
    if len(parts) > 1:
        built = ""
        # log.info(f"parts: {parts}")
        for i in range(len(parts)):
            # log.info(f"part: {parts[i]}")
            A = built
            B = transliterate(System.SLP1, System.WX, unswara(parts[i].slp1))
            log.debug(f"adding: \'{transliterate(System.WX,System.IAST, A)}\' + \'{transliterate(System.WX,System.IAST, B)}\'")

            results = S.sandhi(A, B, input_scheme="wx")
            valid_forms = {r[0] for r in results}
            compact_results = list(filter(lambda x: " " not in x, valid_forms))
            compact_results = list(
                map(lambda x: x.replace("_", ""), compact_results)
            )

            if len(compact_results) > 1 or len(compact_results) == 0:
                log.warning(f"cannot verify: {compact_results}")
            else:
                built = compact_results[0]


        built = transliterate(System.WX, System.IAST, built)
        final_result = transliterate(System.SLP1, System.IAST, unswara(result))
        built = final_result.replace("\'","")
        final_result = final_result.replace("\'","")

        undone_parts = list(
            map(lambda x: transliterate(System.SLP1, System.IAST, x.slp1), parts)
        )

        if built != final_result:
            log.warning(
                f"unable for verify sandhi for these parts: {undone_parts}\n"
                f"expected \'{final_result}\' but got \'{built}\'"
            )
        else:
            log.info(f"sandhi verified:\t{undone_parts} = \'{final_result}\'")
    else:
        log.warning(f"no need to validate parts of n<2 {parts}")

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
        before = self.source[:e.pos]
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
        tokens = [first]
        for pair in rest:
            # pair = [ws_node, token_result] from the anonymous (ws token) sequence
            tokens.append(pair[1])
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
            result = CompoundToken(parts=[result], slp1=slp1)

        e_parts = external_parts if isinstance(external_parts, list) else []
        e_parts = [p for p in e_parts if isinstance(p, str)]
        for slp1 in e_parts:
            result = CompoundToken(parts=[result], slp1=slp1)

        return result

    def visit_equation_part(self, _, visited_children):
        first_part, plus_parts, _, slp1 = visited_children

        parts = list([first_part]) + list(plus_parts)
        validate_equation(parts, slp1)
        return CompoundToken(parts, slp1)

    def visit_inflect_part(self, _, visited_children):
        _, slp1 = visited_children
        return slp1

    def visit_external_part(self, _, visited_children):
        _, slp1 = visited_children
        return slp1

    def visit_plus_part(self, _, visited_children):
        _, part = visited_children
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
        return node.text

    def visit_slp1(self, node, _):
        return node.text

    def visit_quoted_str(self, node, _):
        return node.text[1:-1].replace('\\"', '"').replace("\\\\", "\\")

    def generic_visit(self, node, visited_children):
        return visited_children or node
