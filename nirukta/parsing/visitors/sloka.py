import logging
import os
import traceback
from aksharamukha import transliterate
from nirukta.render import transform_text, untransform_text
from nirukta.strings import unswara
import sandhi as sandhi_module
from janim.imports import log
from nirukta.inflection import Case, SanskritInflection
from nirukta.models import (
    CompoundToken,
    EnglishGloss,
    Language,
    Line,
    SimpleToken,
    Sloka,
    Utterance,
)
from nirukta.models import SlokaFile
from nirukta.parsing.grammars import SLOKA_GRAMMAR
from parsimonious.nodes import NodeVisitor

S = sandhi_module.Sandhi()


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

    def parse(self) -> SlokaFile:
        tree = SLOKA_GRAMMAR.parse(self.source)
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

    def visit_compound_token(self, _, visited_children):
        first_part, plus_parts, _, surface, inflect_parts = visited_children

        parts = [first_part] + list(plus_parts)

        log.info("===")
        if len(parts) > 1:
            built = ""
            for i in range(len(parts)):
                A = built
                B = transliterate.process("SLP1", "WX", unswara(parts[i].slp1))
                log.debug(f"adding: \'{transliterate.process("WX","IAST", A)}\' + \'{transliterate.process("WX","IAST", B)}\'")
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


            built = transliterate.process("WX", "IAST", built)
            final_result = transliterate.process("SLP1", "IAST", unswara(surface))
            assert final_result is not None
            final_result = final_result.replace("\'","")

            undone_parts = list(
                map(lambda x: transliterate.process("SLP1", "IAST", x.slp1), parts)
            )

            if built != final_result:
                log.warning(
                    f"unable for verify sandhi for these parts: {undone_parts}\n"
                    f"expected {final_result} but got {built}"
                )
            else:
                log.info(f"sandhi verified:\t{undone_parts} = {final_result}")

        # normalize inflect_parts
        i_parts = inflect_parts if isinstance(inflect_parts, list) else []
        i_parts = [p for p in i_parts if isinstance(p, str)]

        # fold left: each >> wraps the previous result in a new CompoundToken
        result = CompoundToken(
            parts=parts,
            slp1=surface,
        )

        for slp1 in i_parts:
            result = CompoundToken(parts=[result], slp1=slp1)

        return result

    def visit_plus_part(self, _, visited_children):
        _, part = visited_children
        return part

    def visit_inflect_part(self, _, visited_children):
        _, slp1 = visited_children
        return slp1

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
