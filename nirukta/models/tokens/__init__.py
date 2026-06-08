from nirukta.models.tokens.simple import SimpleToken
from nirukta.models.tokens.compound import CompoundToken, SoundChangeToken
from nirukta.models.tokens.token import TokenType
from nirukta.models.tokens.display import DisplayToken
from nirukta.models.tokens.punctuation import PunctuationToken

from janim.imports import WHITE, log
from nirukta.strings import unswara
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


def process_token(
    english: str,
    token: TokenType,
    visited: Set[tuple[int, int]],
):
    refs: List[tuple[str, List[tuple[int, int]]]] = []

    match token:
        case PunctuationToken():
            refs.append((token, []))
        case SimpleToken():
            refs.append((token.slp1, token.gloss_refs(english, visited)))
        case SoundChangeToken():
            refs += process_token(english, token.part, visited)
        case CompoundToken():
            for part in token.parts:
                refs += process_token(english, part, visited)

    return refs


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
        case SoundChangeToken():
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
