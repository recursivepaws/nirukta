from nirukta.models.tokens.simple import SimpleToken
from nirukta.models.tokens.compound import CompoundToken, SoundChangeToken
from nirukta.models.tokens.token import TokenType
from nirukta.models.tokens.display import DisplayToken
from nirukta.models.tokens.punctuation import PunctuationToken

from janim.imports import WHITE, log
from nirukta.strings import unswara
from nirukta.models.enums import SoundChange, Animation
from nirukta.models.gloss import EnglishGloss

from typing import List, Set, Dict, Sequence

_SLP1_VOWELS = frozenset("aAiIuUfFxXeEoO")

# vowels + anusvara + visarga
_SLP1_ENDS_CLEANLY = frozenset("aAiIuUfFxXeEoOMH")


def skip_spaces_str(last_line: str, next_line: str) -> bool:
    last = last_line[-1]
    nxt = next_line[0]
    return (
        last is not None
        and nxt is not None
        and last not in _SLP1_ENDS_CLEANLY
        and nxt in _SLP1_VOWELS
    )


def skip_spaces_token(last_line: TokenType, next_line: TokenType) -> bool:
    if type(last_line) is PunctuationToken or type(next_line) is PunctuationToken:
        return False
    else:
        return skip_spaces_str(last_line.slp1[-1], next_line.slp1[0])


# Pada-sandhi (traditional "external" sandhi) expansions are hoisted to the front:
# compound un-joins (=, EXPAND) and contextual sandhi (=>, SPELLS).
_PADA_SANDHI = frozenset({Animation.EXPAND, Animation.SPELLS})


def animation_for(parent: DisplayToken) -> Animation | None:
    """Which Animation expanding *parent* (a non-leaf) into its children produces.

    Mirrors the diff classification in `UtteranceTimeline.construct()`.
    """
    child = parent.children[0]
    if len(parent.children) != 1 and parent.slp1 != child.slp1:
        return Animation.EXPAND  # compound un-join  (= , pada-sandhi)
    if unswara(parent.slp1) != parent.slp1 and unswara(parent.slp1) == child.slp1:
        return Animation.SWARAS  # swara strip       (word-internal)
    if parent.slp1 != child.slp1:
        return Animation.SPELLS  # external sandhi   (=>, pada-sandhi)
    if parent.color != child.color:
        return Animation.COLORS  # inflection colour (word-internal)
    return None


def frames_for_vakya(tokens: List[DisplayToken]) -> List[List[DisplayToken]]:
    """
    Generate animation frames by expanding one node at a time.

    All pada-sandhi (compound splits + external sandhi) across the whole vakya is
    deconstructed first, before any per-word colouring — a breadth-first pass — then
    everything else proceeds left to right. Each frame is a flat list of
    DisplayTokens (the current visible surface).
    """
    current: List[DisplayToken] = list(tokens)
    frames = [list(current)]

    while True:
        # First pass: deconstruct all pada-sandhi across the line.
        idx = next(
            (
                i
                for i, t in enumerate(current)
                if not t.is_leaf and animation_for(t) in _PADA_SANDHI
            ),
            None,
        )
        # Second pass: everything else (colours, swaras), left to right.
        if idx is None:
            idx = next((i for i, t in enumerate(current) if not t.is_leaf), None)
        if idx is None:
            break
        token = current[idx]
        current = current[:idx] + token.children + current[idx + 1 :]
        frames.append(list(current))

    return frames


def collect_leaf_slp1s(token: TokenType):
    """Walk the token tree yielding leaf slp1 strings in order."""
    match token:
        case SimpleToken():
            yield token.slp1
        case SoundChangeToken():
            yield from collect_leaf_slp1s(token.part)
        case CompoundToken():
            for part in token.parts:
                yield from collect_leaf_slp1s(part)
        # case PunctuationToken():
        # Do nothing


def build_colorings(tokens: Sequence[TokenType], colors: List[str]) -> Dict[str, str]:
    colorings: Dict[str, str] = {}
    idx = 0
    for token in tokens:
        for slp1 in collect_leaf_slp1s(token):
            unswarad = unswara(slp1)
            if unswarad not in colorings and any(c.isalnum() for c in unswarad):
                colorings[unswarad] = colors[idx % len(colors)]
                idx += 1
    return colorings


def _root_color(token: TokenType, colorings: Dict[str, str]) -> str:
    """The coloring assigned to *token*'s first leaf (its underlying root)."""
    for slp1 in collect_leaf_slp1s(token):
        return colorings.get(unswara(slp1), WHITE)
    return WHITE


def _stem_gloss_refs(
    token: TokenType, english: str, visited: Set[tuple[int, int]]
) -> List[tuple[int, int]]:
    """English gloss spans of *token*'s underlying stem leaves, in order."""
    refs: List[tuple[int, int]] = []
    match token:
        case SimpleToken():
            refs += token.gloss_refs(english, visited)
        case SoundChangeToken():
            refs += _stem_gloss_refs(token.part, english, visited)
        case CompoundToken():
            for part in token.parts:
                refs += _stem_gloss_refs(part, english, visited)
    return refs


def build_display_token(
    english: str,
    token: TokenType,
    visited: Set[tuple[int, int]],
    colorings: Dict[str, str],
) -> DisplayToken:
    match token:
        case SimpleToken():
            spans = token.gloss_refs(english, visited)
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

            return DisplayToken(
                slp1=token.slp1,
                color=WHITE,
                children=[dt],
                english_spans=[],
            )
        case SoundChangeToken() if token.kind == SoundChange.INFLECTION:
            # An inflection stays at its inflected surface form (e.g. Bojanezu) — it
            # never resolves down to the bare stem. The sanskrit colours in like a
            # normal word (white -> root colour, always filled, never outlined). On
            # the coloured form the stem's meaning ("foods") rides as a fill span and
            # the inflection's own meaning ("among") rides as an *english* outline span.
            leaf = DisplayToken(
                slp1=token.slp1,
                color=_root_color(token.part, colorings),
                children=[],
                english_spans=_stem_gloss_refs(token.part, english, visited),
                outline_spans=SimpleToken(token.slp1, token.glosses).gloss_refs(
                    english, visited
                ),
            )
            return DisplayToken(
                slp1=token.slp1,
                color=WHITE,
                children=[leaf],
                english_spans=[],
            )
        case SoundChangeToken():
            # External sandhi: resolve the merged surface form into its part.
            return build_display_token(english, token.as_compound(), visited, colorings)
        case CompoundToken():
            unswarad = token.slp1.replace("\\'", "").replace("\\_", "")

            children = []

            for i, part in enumerate(token.parts):
                etymological_token_part = False
                if isinstance(part, SimpleToken):
                    etym_glosses = list(
                        gloss
                        for gloss in part.glosses
                        if not isinstance(gloss, EnglishGloss)
                    )
                    etymological_token_part = len(etym_glosses) > 0

                child_parts = (
                    ["\\{", part, "\\}"] if etymological_token_part else [part]
                )

                children += list(
                    map(
                        lambda x: build_display_token(english, x, visited, colorings),
                        child_parts,
                    )
                )

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
        case PunctuationToken():
            return DisplayToken(
                slp1=token.slp1,
                color=WHITE,
                children=[],
                english_spans=[],
            )


def fix_display_token_akshara_splitting(tokens: Sequence[TokenType]):
    i = 0

    while i < len(tokens) - 1:
        last = tokens[i]
        next = tokens[i + 1]

        if skip_spaces_token(last, next):
            tokens[i] = CompoundToken(
                parts=[last, next], slp1=f"{last.slp1}{next.slp1}"
            )
            tokens[i] = DisplayToken(
                slp1=f"{last.slp1}{next.slp1}",
                color=WHITE,
                children=[last, next],
                english_spans=[],
            )

            i += 1

            if i == len(tokens) - 1:
                tokens = tokens[:i]
            else:
                tokens = tokens[:i] + tokens[i + 1 :]
        else:
            i += 1

    return tokens
