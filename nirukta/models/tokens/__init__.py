from nirukta.models.tokens.simple import SimpleToken
from nirukta.models.tokens.compound import CompoundToken
from nirukta.models.tokens.display import DisplayToken

from janim.imports import WHITE
from nirukta.strings import unswara
from nirukta.inflection import SanskritInflection
from nirukta.models.gloss import EnglishGloss

from typing import Union, List, Set, Dict

type TokenType = Union[SimpleToken, CompoundToken, str]  # str for punctuation


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
    token: Union[SimpleToken, CompoundToken, str],
    visited: Set[tuple[int, int]],
):
    refs: List[tuple[str, List[tuple[int, int]]]] = []

    if isinstance(token, SimpleToken):
        refs.append((token.slp1, token.gloss_refs(english, visited)))
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


def build_display_token(
    english: str,
    token: TokenType,
    visited: Set[tuple[int, int]],
    colorings: Dict[str, str],
) -> DisplayToken:
    if isinstance(token, SimpleToken):
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
    elif isinstance(token, CompoundToken):
        sandhi_compound = (
            isinstance(token.etym_gloss, SanskritInflection)
            and token.etym_gloss.compound_type is not None
        )

        unswarad = token.slp1.replace("\\'", "").replace("\\_", "")

        children = []

        if sandhi_compound:
            children.append(build_display_token(english, "\\[", visited, colorings))

        for i, part in enumerate(token.parts):
            etymological_token_part = False
            if isinstance(part, SimpleToken):
                etym_glosses = list(
                    gloss
                    for gloss in part.glosses
                    if not isinstance(gloss, EnglishGloss)
                )
                # print(f"etymglosses: {etym_glosses}")
                etymological_token_part = len(etym_glosses) > 0

            if etymological_token_part:
                children.append(build_display_token(english, "\\{", visited, colorings))

            children.append(build_display_token(english, part, visited, colorings))

            if etymological_token_part:
                children.append(build_display_token(english, "\\}", visited, colorings))

            if sandhi_compound:
                if i < len(token.parts) - 1:
                    children.append(
                        build_display_token(english, "+", visited, colorings)
                    )
                else:
                    children.append(
                        build_display_token(english, "\\]", visited, colorings)
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

    else:  # str punctuation
        return DisplayToken(
            slp1=token,
            color=WHITE,
            children=[],
            english_spans=[],
        )
