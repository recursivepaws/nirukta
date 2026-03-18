from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Set, Union

from aksharamukha import transliterate

from janim.imports import (
    BLUE,
    DOWN,
    GREEN,
    ORANGE,
    PINK,
    RED,
    WHITE,
    YELLOW,
    FadeOut,
    Group,
    Succession,
    TypstText,
    Wait,
    Write,
)
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor


SCALE = 2.0
# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------


def Junicode(text: str, color: str):
    return f'#text(font: "Junicode", stroke: none, fill: rgb("{color}"))[{text}]'


def Jaini(text: str, color: str):
    return f'#text(font: "Jaini", stroke: none, fill: rgb("{color}"))[{text}]'


class Language(Enum):
    ENGLISH = "english"
    SANSKRIT = "sanskrit"
    TRANSLIT = "translit"


def typst_code(text: str, language: Language, color: str = WHITE):
    match language:
        case Language.ENGLISH:
            return Junicode(text, color)
        case Language.TRANSLIT:
            iast = transliterate.process("SLP1", "IAST", text)
            if not iast:
                raise ValueError(f'Cannot represent "{text}" in IAST')
            return Junicode(iast, color)
        case Language.SANSKRIT:
            deva = transliterate.process("SLP1", "DEVANAGARI", text)
            if not deva:
                raise ValueError(f'Cannot represent "{text}" in devanagari')

            return Jaini(deva, color)


@dataclass
class Gloss:
    """A single English gloss attached to a Sanskrit token.

    etymological=False  ->  [] translation gloss, shown in animations
    etymological=True   ->  {} etymology gloss, hidden by default
    """

    text: str
    etymological: bool = False


@dataclass
class SimpleToken:
    """An unanalysed Sanskrit word with its glosses."""

    slp1: str
    glosses: List[Gloss] = field(default_factory=list)


@dataclass
class CompoundToken:
    """A sandhi compound.

    parts   -- ordered list of SimpleToken / CompoundToken (the components)
    slp1 -- the phonetically-merged SLP1 surface form (after '=')
    """

    parts: List[Union[SimpleToken, "CompoundToken"]]
    slp1: str


# Convenience type alias
TokenType = Union[SimpleToken, CompoundToken, str]  # str for punctuation


@dataclass
class VerseLine:
    """One sentence-worth of Sanskrit tokens paired with its English rendering."""

    tokens: List[TokenType]
    english: str


@dataclass
class Line:
    """A stanza-level grouping of verse lines (between --- line --- markers)."""

    vAkyAni: List[VerseLine]


@dataclass
class SlokaFile:
    citation: str
    lines: List[Line]

    def teach(self):
        sloka = []

        for line in self.lines:
            # english = ""
            sanskrit = ""
            # for each utterance we want to analyze separately
            for vAkya in line.vAkyAni:
                # english += vAkya.english
                for token in vAkya.tokens:
                    if isinstance(token, str):
                        sanskrit += token
                    else:
                        sanskrit += token.slp1

                    sanskrit += " "

            sloka.append(
                TypstText(typst_code(sanskrit, Language.SANSKRIT), scale=SCALE)
            )

        sloka = Group(*sloka)
        sloka.points.arrange(DOWN)
        animations = []
        for line in sloka:
            animations.append(Write(line, duration=6.0))

        citation = TypstText(typst_code(self.citation, Language.SANSKRIT), scale=SCALE)
        citation.points.next_to(sloka, DOWN)

        animations.append(
            Succession(
                Wait(2.0),
                Write(citation, duration=1.0),
                Wait(1.0),
                FadeOut(Group(sloka, citation)),
            )
        )

        colors = [RED, BLUE, YELLOW, GREEN, PINK, ORANGE]

        for line in self.lines:
            # When doing translation pages we do an utterance at a time rather
            # than a line at a time.
            for vAkya in line.vAkyAni:
                sanskrit = ""
                translit = ""
                english = ""
                plain_english = ""

                refs: List[tuple[str, List[tuple[int, int]]]] = []

                visited = set()
                for token in vAkya.tokens:
                    refs += process_token(vAkya.english, token, visited)

                print(f"vaaaaaaakya: {vAkya.english}")
                print("processed token dictionary for this vAkya:")
                print(refs)
                print("-------------------")

                # Mapping from slp1 sanskrit to color code
                colorings: Dict[str, str] = {}

                filtered_refs = [
                    ref for ref in refs if any(c.isalnum() for c in ref[0])
                ]

                for i, [slp1, _] in enumerate(filtered_refs):
                    if slp1 not in colorings:
                        colorings[slp1] = colors[i % len(colors)]

                # Iterate sorting by slp1 insertion order
                for slp1, _ in refs:
                    color = colorings.get(slp1, WHITE)

                    sanskrit += typst_code(slp1, Language.SANSKRIT, color) + " "
                    translit += typst_code(slp1, Language.TRANSLIT, color) + " "

                all_tuples = [
                    (start, end, slp1) for slp1, spans in refs for start, end in spans
                ]
                all_tuples.append((len(vAkya.english), len(vAkya.english), ""))
                print(all_tuples)
                cursor = 0
                for start, end, slp1 in sorted(all_tuples, key=lambda item: item[0]):
                    # if start < cursor:  # skip duplicates / overlaps
                    #     continue
                    if start > cursor:
                        missing_text = vAkya.english[cursor:start]
                        plain_english += missing_text
                        english += missing_text
                    color = colorings.get(slp1, WHITE)
                    plain_english += vAkya.english[start:end]
                    english += typst_code(
                        vAkya.english[start:end], Language.ENGLISH, color
                    )
                    cursor = end

                group = Group(
                    TypstText(english, scale=SCALE),
                    TypstText(translit, scale=SCALE),
                    TypstText(sanskrit, scale=SCALE),
                )
                group.points.arrange(DOWN)

                animations.append(
                    Succession(
                        Wait(2.0),
                        Write(group, duration=1.0),
                        Wait(1.0),
                        FadeOut(group),
                    )
                )

        return Succession(*animations)


# Source - https://stackoverflow.com/a/1884277
def find_nth(haystack: str, needle: str, n: int) -> int:
    start = haystack.find(needle)
    while start >= 0 and n > 1:
        start = haystack.find(needle, start + len(needle))
        n -= 1
    return start


def process_token(
    english: str,
    token: Union[SimpleToken, CompoundToken, str],
    visited: Set[tuple[int, int]],
):
    refs: List[tuple[str, List[tuple[int, int]]]] = []

    if isinstance(token, SimpleToken):
        gloss_refs: List[tuple[int, int]] = []

        for gloss in token.glosses:
            n = 1
            while True:
                print("meowing")
                gi = find_nth(english, gloss.text, n)

                assert gi >= 0, (
                    "Gloss cannot reference text not contained in the english translation!"
                    + "\n"
                    + f'Tried to find "{gloss.text}" in "{english}" but was unable.'
                )

                index = (gi, gi + len(gloss.text))

                assert english[index[0] : index[1]] == gloss.text, (
                    "Invalid gloss index into english text"
                )

                # If we've already found this instance of the gloss text
                if index in visited:
                    # Find the next one
                    n += 1
                else:
                    gloss_refs.append(index)
                    visited.add(index)
                    break

        refs.append((token.slp1, gloss_refs))
        return refs
    elif isinstance(token, CompoundToken):
        # assume for now that there are no "etymological" glosses and that
        # compound tokens MUST be recursed in order to reveal full meanings
        for part in token.parts:
            # recurse on child tokens
            refs += process_token(english, part, visited)
        return refs
    else:
        refs.append((token, []))
        return refs


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

GRAMMAR = Grammar(r"""
    sloka           = ws citation_line ws line+ ws

    citation_line   = "===" ws citation_text ws "==="
    citation_text   = ~r"[^=]+"

    line            = "--- line ---" ws verse_line+
    verse_line      = !"--- line ---" token_seq ws quoted_str ws

    token_seq       = token (ws token)*

    token           = compound_token / simple_token / punct

    # Sandhi: one or more components joined by '+', then '=' surface form.
    # Components may themselves be parenthesised sandhi groups, enabling
    # arbitrary nesting:  (a[x]+b[y]=ab)+c[z]=abc
    compound_token  = comp_part plus_part+ "=" slp1
    plus_part       = "+" comp_part
    comp_part       = paren_compound / simple_token
    paren_compound  = "(" compound_token ")"

    simple_token    = slp1 gloss*
    gloss           = trans_gloss / etym_gloss
    trans_gloss     = "[" trans_content "]"
    etym_gloss      = "{" etym_content "}"
    trans_content   = ~r"[^\]]+"
    etym_content    = ~r"[^}]+"

    # '..' must precede '.' so the longer match wins
    punct           = ~r"\.\.|[.;]"

    # SLP1: anything that isn't a format metacharacter or whitespace
    slp1            = ~r"[^[\]{}.;=+()\"\s]+"

    quoted_str      = '"' ~r'(?:[^"\\]|\\.)*' '"'
    ws              = ~r"\s*"
""")


# ---------------------------------------------------------------------------
# Visitor
# ---------------------------------------------------------------------------


class SlokaVisitor(NodeVisitor):
    # -- top level ----------------------------------------------------------

    def visit_sloka(self, node, visited_children):
        _, citation, _, lines, _ = visited_children
        return SlokaFile(citation=citation, lines=list(lines))

    # -- citation -----------------------------------------------------------

    def visit_citation_line(self, node, visited_children):
        _, _, text, _, _ = visited_children
        return text

    def visit_citation_text(self, node, visited_children):
        return node.text.strip()

    # -- line / verse line --------------------------------------------------

    def visit_line(self, node, visited_children):
        _, _, verse_lines = visited_children
        return Line(vAkyAni=list(verse_lines))

    def visit_verse_line(self, node, visited_children):
        # visited_children: [lookahead, token_seq, ws, quoted_str, ws]
        _, tokens, _, english, _ = visited_children
        return VerseLine(tokens=tokens, english=english)

    # -- token sequence -----------------------------------------------------

    def visit_token_seq(self, node, visited_children):
        first, rest = visited_children
        tokens = [first]
        for pair in rest:
            # pair = [ws_node, token_result] from the anonymous (ws token) sequence
            tokens.append(pair[1])
        return tokens

    def visit_token(self, node, visited_children):
        return visited_children[0]

    # -- compound (sandhi) tokens -------------------------------------------

    def visit_compound_token(self, node, visited_children):
        first_part, plus_parts, _, surface = visited_children
        parts = [first_part] + list(plus_parts)
        return CompoundToken(parts=parts, slp1=surface)

    def visit_plus_part(self, node, visited_children):
        _, part = visited_children
        return part

    def visit_comp_part(self, node, visited_children):
        return visited_children[0]

    def visit_paren_compound(self, node, visited_children):
        _, compound, _ = visited_children
        return compound

    # -- simple tokens & glosses --------------------------------------------

    def visit_simple_token(self, node, visited_children):
        slp1, glosses = visited_children
        return SimpleToken(slp1=slp1, glosses=list(glosses))

    def visit_gloss(self, node, visited_children):
        return visited_children[0]

    def visit_trans_gloss(self, node, visited_children):
        _, content, _ = visited_children
        print(f"visit_trans_gloss: children: {visited_children}")
        return Gloss(text=content, etymological=False)

    def visit_etym_gloss(self, node, visited_children):
        _, content, _ = visited_children
        return Gloss(text=content, etymological=True)

    def visit_trans_content(self, node, visited_children):
        return node.text

    def visit_etym_content(self, node, visited_children):
        return node.text

    # -- terminals ----------------------------------------------------------

    def visit_punct(self, node, visited_children):
        return node.text

    def visit_slp1(self, node, visited_children):
        return node.text

    def visit_quoted_str(self, node, visited_children):
        return node.text[1:-1].replace('\\"', '"').replace("\\\\", "\\")

    def generic_visit(self, node, visited_children):
        return visited_children or node


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse(source: str) -> SlokaFile:
    """Parse a sloka source string and return a Sloka object."""
    tree = GRAMMAR.parse(source)
    return SlokaVisitor().visit(tree)


# ---------------------------------------------------------------------------
# Test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    sample = r"""
=== tEttirIyopaniSade 2.2.2 ===

--- line ---
saha[together]  nO[we both]+avatu[May][be protected]=nAvavatu  .
"May we both be protected together."

saha[together]  nO[we both]  Bunaktu[May][be nourished]  .
"May we both be nourished together."

saha[together]  vIryaM[vigorously]  karavAvahai[May we both work]  .
"May we both work vigorously together."

--- line ---
tejasvi[brilliant]  (nO[both our]+aDItam[study]=nAvaDItam)+astu[May][be]=nAvaDItamastu  ;  mA[not]  vidvizAvahai[hate one another]  ..
"May both our study be brilliant; may we not hate one another."

--- line ---
oM[OM]  SAntiH[peace]+SAntiH[peace]+SAntiH[peace]=SAntiSSAntiSSAntiH  ..
"OM, peace, peace, peace."
"""
    sloka = parse(sample)
    print(sloka)
