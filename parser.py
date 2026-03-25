from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import re
from typing import Dict, List, Optional, Set, Union

from aksharamukha import transliterate
from janim.imports import (
    BLUE,
    DOWN,
    GREEN,
    ORANGE,
    ORIGIN,
    PINK,
    RED,
    UP,
    WHITE,
    YELLOW,
    Aligned,
    FadeOut,
    Group,
    GrowFromEdge,
    ShrinkToEdge,
    Succession,
    TransformMatchingDiff,
    TypstText,
    Wait,
    Write,
    normalize,
    np,
)
from janim.typing import SupportsAnim
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

SCALE = 2.0
COLORS = [RED, BLUE, YELLOW, GREEN, PINK, ORANGE]


# ---------------------------------------------------------------------------
# Data model
# ---------------------------------------------------------------------------
class LenientTransformMatchingDiff(TransformMatchingDiff):
    @dataclass
    class MatchWrapper(TransformMatchingDiff.MatchWrapper):
        def __eq__(self, other):
            if not isinstance(other, LenientTransformMatchingDiff.MatchWrapper):
                return False
            if self.item.points.same_shape(other.item):
                return True
            return self._loosely_same_shape(other.item)

        def _loosely_same_shape(self, other_item) -> bool:
            p1 = self.item.points.get()[:-1]
            p2 = other_item.points.get()[:-1]
            if len(p1) != len(p2) or len(p1) < 2:
                return False
            p1 = p1 - p1[0]
            p2 = p2 - p2[0]
            w1 = (
                self.item.points.width_along_direction(
                    normalize(self.item.points.start_direction)
                )
                or 1.0
            )
            w2 = (
                other_item.points.width_along_direction(
                    normalize(other_item.points.start_direction)
                )
                or 1.0
            )
            return np.allclose(p1 / w1, p2 / w2, atol=0.33)

        def __hash__(self):
            return 0

    def __init__(self, *args, name=None, **kwargs):
        super().__init__(*args, **kwargs)
        if name is not None:
            self.name = name


def text_box(text: str, color: str):
    if color == "#FFFFFF":
        return f"#box[#text[{text}]]"
    else:
        return f'#box[#text(fill: rgb("{color}"))[{text}]]'


INTRO_FONT = "Jaini"
SANSKRIT_FONT = "Tiro Devanagari Sanskrit"
LATIN_FONT = "Junicode"


def set_font(text: str, font: str):
    return f'#set text(font: "{font}", stroke: none)\n{text}'


class Language(Enum):
    ENGLISH = "english"
    SANSKRIT = "sanskrit"
    TRANSLIT = "translit"


TYPST_CMD_RE = re.compile(r"(#\w+\(\))")
MISSING_CHUNK_RE = re.compile(r"#\w+\(\)|[a-zA-Z0-9']+|[^a-zA-Z0-9'\s#]+|#")


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


@dataclass
class DisplayToken:
    """A single renderable unit at a given animation stage."""

    slp1: str
    color: str  # resolved from colorings
    children: List["DisplayToken"]  # empty => leaf (SimpleToken or punct)
    english_spans: List[tuple[int, int]]  # the spans this token is responsible for

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def at_depth(self, depth: int) -> List["DisplayToken"]:
        if self.is_leaf or depth == 0:
            return [self]
        return [leaf for child in self.children for leaf in child.at_depth(depth - 1)]


def at_depth(node: DisplayToken, depth: int) -> List[DisplayToken]:
    """Flatten the tree to a specific expansion depth."""
    if node.is_leaf or depth == 0:
        return [node]
    return [child for c in node.children for child in at_depth(c, depth - 1)]


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
class Sloka:
    """"""

    lines: List[Line]

    def render_intro(
        self, line_duration=4.0, citation: Optional[str] = None
    ) -> List[SupportsAnim]:
        sloka = []

        for line in self.lines:
            sanskrit = ""
            for vAkya in line.vAkyAni:
                for token in vAkya.tokens:
                    if isinstance(token, str):
                        sanskrit += token
                    else:
                        sanskrit += token.slp1

                    sanskrit += " "

            sloka.append(
                TypstText(
                    set_font(typst_code(sanskrit, Language.SANSKRIT), INTRO_FONT),
                    scale=SCALE,
                )
            )

        sloka = Group(*sloka)
        sloka.points.arrange(DOWN)

        animations = []
        for line in sloka:
            animations.append(Write(line, duration=line_duration))

        if citation is not None:
            citation_text = TypstText(
                set_font(typst_code(citation, Language.SANSKRIT), INTRO_FONT),
                scale=SCALE,
            )
            citation_text.points.next_to(sloka, DOWN)
            animations.extend(
                [
                    Wait(2.0),
                    Write(citation_text, duration=1.0),
                    Wait(1.0),
                    FadeOut(Group(sloka, citation_text)),
                ]
            )
        else:
            animations.extend(
                [
                    Wait(1.0),
                    FadeOut(sloka),
                ]
            )
        return animations

    def explain(self) -> List[SupportsAnim]:
        animations = []
        for line in self.lines:
            # When doing translation pages we do an utterance at a time rather
            # than a line at a time.
            for vAkya in line.vAkyAni:
                refs: List[tuple[str, List[tuple[int, int]]]] = []

                visited = set()
                for token in vAkya.tokens:
                    refs += process_token(vAkya.english, token, visited)

                visited = set()
                colorings = build_colorings(vAkya.tokens, COLORS)
                display_tokens = [
                    build_display_token(vAkya.english, token, visited, colorings)
                    for token in vAkya.tokens
                ]
                frames = frames_for_vakya(display_tokens)

                # sa, tr, en
                states = [[], [], []]
                state_changes = []

                for i in range(len(frames) - 1):
                    # compare this frame to the next frame
                    a = frames[i]
                    b = frames[i + 1]

                    if len(a) != len(b):
                        state_changes.append(AnimationChange.EXPAND)
                    else:
                        swara_removal = False
                        spelling_intact = True
                        color_intact = True
                        for j in range(len(a)):
                            swara_removal |= (
                                unswara(a[j].slp1) != a[j].slp1
                                and unswara(a[j].slp1) == b[j].slp1
                            )
                            spelling_intact &= a[j].slp1 == b[j].slp1
                            color_intact &= a[j].color == b[j].color
                        if swara_removal:
                            state_changes.append(AnimationChange.SWARAS)
                        elif not spelling_intact:
                            state_changes.append(AnimationChange.SPELLS)
                        elif not color_intact:
                            state_changes.append(AnimationChange.COLORS)
                        else:
                            raise ValueError(
                                "I don't know what kind of change occurred"
                            )

                print([*((lambda c: c.value)(s) for s in state_changes)])

                for i, frame in enumerate(frames):
                    sanskrit = ""
                    translit = ""
                    english = ""

                    for token in frame:
                        sanskrit += (
                            typst_code(token.slp1, Language.SANSKRIT, token.color) + " "
                        )
                        iast = transform_text(token.slp1, Language.TRANSLIT)
                        translit += Junicode_translit(iast, token.color) + " "

                    all_tuples = [
                        ((start, end), token.color)
                        for token in frame
                        for start, end in token.english_spans
                    ]
                    all_tuples.append(((len(vAkya.english), len(vAkya.english)), WHITE))

                    cursor = 0
                    plain_english = 0
                    for [start, end], color in sorted(
                        all_tuples, key=lambda item: item[0]
                    ):
                        # Emit any unspanned text before this span
                        if start > cursor:
                            missing_text = vAkya.english[cursor:start]
                            plain_english += len(missing_text)
                            for m in MISSING_CHUNK_RE.finditer(missing_text):
                                piece = m.group()
                                if TYPST_CMD_RE.fullmatch(piece):
                                    english += piece
                                else:
                                    english += typst_code(
                                        piece, Language.ENGLISH, WHITE
                                    )
                                    # Only add a space if the original text has a space right after this piece
                                    next_pos = m.end()
                                    if (
                                        next_pos < len(missing_text)
                                        and missing_text[next_pos] == " "
                                    ):
                                        english += " "

                        if start == end:
                            break

                        # Emit the colored span
                        english_token = vAkya.english[start:end]
                        plain_english += len(english_token)
                        english += typst_code_safe(
                            english_token, Language.ENGLISH, color
                        )
                        cursor = end

                        # Consume a trailing space so missing_text never starts with one
                        if cursor < len(vAkya.english) and vAkya.english[cursor] == " ":
                            english += " "
                            cursor += 1

                    states[0].append(
                        TypstText(set_font(sanskrit, SANSKRIT_FONT), scale=SCALE)
                    )
                    states[1].append(
                        TypstText(set_font(translit, LATIN_FONT), scale=SCALE)
                    )
                    states[2].append(
                        TypstText(set_font(english, LATIN_FONT), scale=SCALE)
                    )

                # for s in states[1]:
                #     print(s.text)

                for i in range(len(states[0])):
                    # Start the transliteration in the center
                    states[1][i].points.move_to(ORIGIN)

                    # Move sa and en above and below
                    states[0][i].points.next_to(states[1][i], UP / SCALE * 4.0)
                    states[2][i].points.next_to(states[1][i], DOWN / SCALE * 4.0)

                    # Initial write on
                    if i == 0:
                        animations.append(
                            Succession(
                                Wait(1.0),
                                Aligned(
                                    *(Write(s[i]) for s in states),
                                    duration=1.0,
                                ),
                                Wait(1.0),
                            )
                        )

                    # Transformation into current state
                    if i > 0:
                        change_type = state_changes[i - 1]

                        assert isinstance(change_type, AnimationChange), (
                            "Invalid Change Type"
                        )

                        match change_type:
                            case AnimationChange.COLORS:
                                duration = 0.33
                            case AnimationChange.SWARAS:
                                duration = 0.44
                            case AnimationChange.SPELLS:
                                duration = 0.66
                            case AnimationChange.EXPAND:
                                duration = 0.99

                        delay = duration * 0.15

                        # Swara removals get a special animation for optimal seamlessness
                        if change_type == AnimationChange.SWARAS:
                            mismatch = (
                                lambda item, p, **kwargs: FadeOut(
                                    item, at=delay, shift=UP * 0.1, **kwargs
                                ),
                                lambda item, p, **kwargs: GrowFromEdge(
                                    item, DOWN, **kwargs
                                ),
                            )
                        else:
                            mismatch = (
                                lambda item, p, **kwargs: ShrinkToEdge(
                                    item, UP, at=delay, **kwargs
                                ),
                                lambda item, p, **kwargs: GrowFromEdge(
                                    item, DOWN, **kwargs
                                ),
                            )

                        animations.append(
                            Aligned(
                                *(
                                    LenientTransformMatchingDiff(
                                        s[i - 1],
                                        s[i],
                                        duration=duration,
                                        mismatch=mismatch,  # type: ignore[arg-type]
                                        name=str(change_type.value),
                                    )
                                    for s in states
                                ),
                            )
                        )

                        if change_type == AnimationChange.COLORS:
                            animations.append(Wait(0.25))

                animations.append(
                    Succession(Wait(2.0), Aligned(*(FadeOut(s[-1]) for s in states)))
                )
        return animations


def extract_rgb_values(s):
    return "".join(re.findall(r'rgb\("(#[0-9A-Fa-f]{6})"\)', s))


class AnimationChange(Enum):
    # Swara removal
    SWARAS = "Swara"
    # Other spelling changes
    SPELLS = "Spelling"
    # Color changes only
    COLORS = "Colors"
    # Node quantity changes
    EXPAND = "Expansion"


class NiruktaFile:
    def teach(self) -> Succession:
        return Succession()


@dataclass
class SutraFile(NiruktaFile):
    citation: str
    slokas: List[Sloka]

    def teach(self) -> Succession:
        animations = []
        citation = TypstText(
            set_font(typst_code(self.citation, Language.SANSKRIT), INTRO_FONT),
            scale=SCALE,
        )
        citation.points.move_to(ORIGIN)

        # Introduce the text by its title
        animations.extend(
            [
                Write(citation),
                Wait(1.5),
                FadeOut(citation),
            ]
        )

        for sloka in self.slokas:
            animations.extend(sloka.render_intro())

        for sloka in self.slokas:
            animations.extend(sloka.explain())

        return Succession(*animations)


@dataclass
class SlokaFile(NiruktaFile):
    citation: str
    sloka: Sloka

    def teach(self) -> Succession:
        animations = self.sloka.render_intro(citation=self.citation)
        animations.extend(self.sloka.explain())

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


def frames_for_vakya(tokens: List[DisplayToken]) -> List[List[DisplayToken]]:
    """
    Generate animation frames by expanding one compound at a time, left to right.
    Each frame is a flat list of DisplayTokens — the current visible surface.
    """
    current: List[DisplayToken] = list(tokens)
    frames = [list(current)]

    while True:
        idx = next((i for i, t in enumerate(current) if not t.is_leaf), None)
        if idx is None:
            break
        token = current[idx]
        current = current[:idx] + token.children + current[idx + 1 :]
        frames.append(list(current))

    return frames


def collect_leaf_slp1s(token: TokenType):
    """Walk the token tree yielding leaf slp1 strings in order."""
    if isinstance(token, SimpleToken):
        yield token.slp1
    elif isinstance(token, CompoundToken):
        for part in token.parts:
            yield from collect_leaf_slp1s(part)


def build_colorings(tokens: List[TokenType], colors: List[str]) -> Dict[str, str]:
    colorings: Dict[str, str] = {}
    idx = 0
    for token in tokens:
        for slp1 in collect_leaf_slp1s(token):
            unswarad = unswara(slp1)
            if unswarad not in colorings and any(c.isalnum() for c in unswarad):
                colorings[unswarad] = colors[idx % len(colors)]
                idx += 1
    return colorings


def unswara(s):
    return s.replace("\\'", "").replace("\\_", "")


def build_display_token(
    english: str,
    token: TokenType,
    visited: Set[tuple[int, int]],
    colorings: Dict[str, str],
) -> DisplayToken:
    if isinstance(token, SimpleToken):
        spans: List[tuple[int, int]] = []

        for gloss in token.glosses:
            n = 1
            while True:
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

                if index in visited:
                    n += 1
                else:
                    spans.append(index)
                    visited.add(index)
                    break

        unswarad = unswara(token.slp1)

        leaf = DisplayToken(
            slp1=unswarad,
            color=colorings.get(unswarad, WHITE),
            children=[],
            english_spans=spans,
        )

        if unswarad != token.slp1:
            dt = DisplayToken(
                slp1=unswarad,
                color=WHITE,
                children=[leaf],
                english_spans=[],
            )
        else:
            dt = leaf

        # Wrap in a single-child compound so color is only revealed on expansion
        return DisplayToken(
            slp1=token.slp1,
            color=WHITE,
            children=[dt],
            english_spans=[],
        )

    elif isinstance(token, CompoundToken):
        unswarad = token.slp1.replace("\\'", "").replace("\\_", "")
        children = [
            build_display_token(english, part, visited, colorings)
            for part in token.parts
        ]
        leaf = DisplayToken(
            slp1=unswarad,
            color=WHITE,
            children=children,
            english_spans=[],  # spans live only on leaves
        )
        if unswarad != token.slp1:
            return DisplayToken(
                slp1=token.slp1,
                color=WHITE,
                children=[leaf],
                english_spans=[],  # spans live only on leaves
            )
        else:
            return leaf

    else:  # str punctuation
        return DisplayToken(
            slp1=token,
            color=WHITE,
            children=[],
            english_spans=[],
        )


# ---------------------------------------------------------------------------
# Grammar
# ---------------------------------------------------------------------------

SLOKA_GRAMMAR_STR = r"""
    sloka           = ws citation_line ws line+ ws

    citation_line   = "===" ws citation_text ws "==="
    citation_text   = ~r"[^=]+"

    line            = "--- line ---" ws verse_line+
    verse_line      = !"--- line ---" token_seq ws quoted_str (ws quoted_str)* ws

    token_seq       = token (ws token)*

    token           = compound_token / simple_token / punct

    # Sandhi: one or more components joined by '+', then '=' surface form.
    # Components may themselves be parenthesised sandhi groups, enabling
    # arbitrary nesting:  (a[x]+b[y]=ab)+c[z]=abc
    compound_token  = comp_part plus_part* "=" slp1
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
"""


SUTRA_GRAMMAR_STR = (
    r"""
    sutra           = sloka inline_sloka* ws
    inline_sloka    = ws "=== sloka ===" ws line+ ws
"""
    + "\n"
    + SLOKA_GRAMMAR_STR
)

SLOKA_GRAMMAR = Grammar(SLOKA_GRAMMAR_STR)
SUTRA_GRAMMAR = Grammar(SUTRA_GRAMMAR_STR)

# ---------------------------------------------------------------------------
# Visitor
# ---------------------------------------------------------------------------


class SlokaVisitor(NodeVisitor):
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
        return VerseLine(tokens=tokens, english=english)

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
        first_part, plus_parts, _, surface = visited_children
        parts = [first_part] + list(plus_parts)
        return CompoundToken(parts=parts, slp1=surface)

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
        return SimpleToken(slp1=slp1, glosses=list(glosses))

    def visit_gloss(self, _, visited_children):
        return visited_children[0]

    def visit_trans_gloss(self, _, visited_children):
        _, content, _ = visited_children
        return Gloss(text=content, etymological=False)

    def visit_etym_gloss(self, _, visited_children):
        _, content, _ = visited_children
        return Gloss(text=content, etymological=True)

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


class SutraVisitor(SlokaVisitor):
    def visit_sutra(self, _, visited_children):
        [citation, first], rest, _ = visited_children
        slokas = [first, *rest]

        print(f"slokas: {len(slokas)}")
        # for sloka in slokas:
        #     assert isinstance(sloka, Sloka), f"not a sloka: {sloka}"

        return SutraFile(citation, slokas)

    def visit_inline_sloka(self, _, visited_children):
        _, _, _, lines, _ = visited_children
        return Sloka(list(lines))

    def visit_sloka(self, _, visited_children):
        _, citation, _, lines, _ = visited_children
        return [citation, Sloka(list(lines))]


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def parse_sutra(source: str) -> SutraFile:
    """Parse a sutra source string and return a Sutra object."""
    tree = SUTRA_GRAMMAR.parse(source)
    return SutraVisitor().visit(tree)


def parse_sloka(source: str) -> SlokaFile:
    """Parse a sloka source string and return a Sloka object."""
    tree = SLOKA_GRAMMAR.parse(source)
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
    sloka = parse_sloka(sample)
    print(sloka)
