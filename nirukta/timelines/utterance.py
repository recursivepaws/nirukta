from dataclasses import dataclass
from itertools import chain
from typing import List

from janim.imports import (
    BLUE,
    DOWN,
    GREEN,
    GREY,
    GREY_B,
    ORIGIN,
    UP,
    WHITE,
    Aligned,
    FadeOut,
    GREY_B,
    FocusOn,
    Group,
    GrowFromEdge,
    Indicate,
    ShowCreationThenFadeAround,
    ShowPassingFlashAround,
    ShrinkToEdge,
    SurroundingRect,
    Timeline,
    TypstText,
    Wait,
    Write,
    log,
    rush_into,
    linear,
)
from nirukta.timelines.transform import LenientTransformMatchingDiff
from nirukta.constants import (
    COLORS,
    LATIN_FONT,
    MISSING_CHUNK_RE,
    SANSKRIT_FONT,
    SCALE,
    TYPST_CMD_RE,
    ALPHA_RE,
    WHITESPACE_RE,
)
from nirukta.models import (
    Animation,
    DisplayToken,
    Language,
    TokenType,
    Utterance,
    build_colorings,
    build_display_token,
    frames_for_vakya,
    process_token,
)
from nirukta.strings import unswara
from nirukta.render import (
    Awaken,
    Diff,
    Junicode_translit,
    set_font,
    transform_text,
    typst_code,
    typst_code_safe,
)


@dataclass
class UtteranceTimeline(Timeline):
    tokens: List[TokenType]
    english: str

    def __init__(self, utterance: Utterance):
        super().__init__()
        self.tokens = utterance.tokens
        self.english = utterance.english

    @property
    def gui_name(self) -> str:
        return self.english

    @property
    def gui_color(self) -> str:
        return BLUE

    def construct(self):
        refs: List[tuple[str, List[tuple[int, int]]]] = []

        visited = set()
        for token in self.tokens:
            refs += process_token(self.english, token, visited)

        visited = set()
        colorings = build_colorings(self.tokens, COLORS)
        display_tokens = [
            build_display_token(self.english, token, visited, colorings)
            for token in self.tokens
        ]

        for i in range(len(display_tokens)):
            if _ := ALPHA_RE.search(display_tokens[i].slp1):
                display_tokens[i].is_root = True
                display_tokens[i].color = GREY_B
                log.debug(f"{display_tokens[i].slp1} is a `DisplayToken` root")

        frames = frames_for_vakya(display_tokens)

        all_english_spans: List[tuple[int, int]] = DisplayToken(
            "", WHITE, children=display_tokens, english_spans=[]
        ).all_spans()
        all_english_spans.append((len(self.english), len(self.english)))

        log.debug(f"all english spans: {all_english_spans}")

        # sa, tr, en
        states: List[List[TypstText]] = [[], [], []]
        diffs: List[Diff] = []

        # is_root = True

        for i in range(len(frames) - 1):
            # compare this frame to the next frame
            fa = frames[i]
            fb = frames[i + 1]

            # Keep track of known diffs to ensure compliance
            diff_count = len(diffs)

            # For each item in the new frame
            for j in range(len(fa)):
                id = fa[j].id
                initial = fa[j].is_root

                # Expansion
                if len(fa) != len(fb) and fa[j].slp1 != fb[j].slp1:
                    diffs.append(Diff(Animation.EXPAND, id, initial))
                # Swaras changed
                elif (
                    unswara(fa[j].slp1) != fa[j].slp1
                    and unswara(fa[j].slp1) == fb[j].slp1
                ):
                    diffs.append(Diff(Animation.SWARAS, id, initial))
                # Spelling changed
                elif fa[j].slp1 != fb[j].slp1:
                    diffs.append(Diff(Animation.SPELLS, id, initial))
                # Color changed
                elif fa[j].color != fb[j].color:
                    diffs.append(Diff(Animation.COLORS, id, initial))

                # Exit once we've added to the list
                if len(diffs) > diff_count:
                    break

            assert len(diffs) != diff_count, "Unknown diff type"

        for i, frame in enumerate(frames):
            sanskrit = ""
            translit = ""
            english = ""

            for token in frame:
                sanskrit += f"{typst_code(token.slp1, Language.SANSKRIT, token.color)}<{token.id}> "
                iast = transform_text(token.slp1, Language.TRANSLIT)
                translit += f"{Junicode_translit(iast, token.color)}<{token.id}> "

            frame_spans = [
                ((start, end), token.color)
                for token in frame
                for start, end in token.english_spans
            ]

            cursor = 0
            for a in all_english_spans:
                if a[0] > cursor:
                    missing_text = self.english[cursor : a[0]]
                    for chunk in MISSING_CHUNK_RE.finditer(missing_text):
                        chunk = chunk.group()
                        # Whitespace is already in the right format
                        if WHITESPACE_RE.fullmatch(chunk):
                            english += chunk
                        # Typst Commands are already in the right format
                        elif TYPST_CMD_RE.fullmatch(chunk):
                            english += chunk
                        # Everything else should be wrapped
                        else:
                            english += typst_code(chunk, Language.ENGLISH, WHITE)

                        # Move cursor
                        cursor += len(chunk)

                    assert cursor == a[0], "Cursor moved to span start"

                # If it is represented in the current frame
                inactive = WHITE + "7D"

                color = next((color for b, color in frame_spans if a == b), inactive)

                english += typst_code(
                    self.english[a[0] : a[1]],
                    Language.ENGLISH,
                    color,
                )

                cursor += a[1] - a[0]

            states[1].append(TypstText(set_font(translit, LATIN_FONT), scale=SCALE))
            states[2].append(TypstText(set_font(english, LATIN_FONT), scale=SCALE))

        for i in range(len(states[0])):
            # Start the transliteration in the center
            states[1][i].points.move_to(ORIGIN)

            # Move sa and en above and below
            states[0][i].points.next_to(states[1][i], UP * SCALE)
            states[2][i].points.next_to(states[1][i], DOWN * SCALE)

            # Initial write on
            if i == 0:
                for fa in [
                    Aligned(
                        *(Write(s[i]) for s in states),
                        duration=1.0,
                    ),
                    Wait(1.0),
                ]:
                    self.play(fa)

            # Transformation into current state
            if i > 0:
                diff = diffs[i - 1]
                assert isinstance(diff, Diff), f"Invalid Change Type: {diff}"

                if diff.initial:
                    self.play(
                        Aligned(
                            *(
                                Awaken(dt)
                                for dt in [
                                    states[0][i - 1].get_label(diff.token_id),
                                    states[1][i - 1].get_label(diff.token_id),
                                ]
                            )
                        ),
                        duration=0.4,
                    )

                self.play(
                    Aligned(
                        *(
                            LenientTransformMatchingDiff(
                                s[i - 1],
                                s[i],
                                duration=diff.duration(),
                                mismatch=diff.mismatch(),  # type: ignore[arg-type]
                                name=diff.name(),
                            )
                            for s in states
                        ),
                        rate_func=diff.rate_func(),
                    )
                )

                if diff == Animation.COLORS:
                    self.play(Wait(0.25))

        self.play(Wait(2.0))
        self.play(Aligned(*(FadeOut(s[-1]) for s in states)))
