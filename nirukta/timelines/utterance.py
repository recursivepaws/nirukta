from dataclasses import dataclass
import hashlib
import dill as pickle
from typing import Any, List, Sequence

from nirukta.cache import build_cached

from janim.imports import (
    BLUE,
    C_LABEL_ANIM_ABSTRACT,
    C_LABEL_ANIM_IN,
    C_LABEL_ANIM_OUT,
    C_LABEL_ANIM_INDICATION,
    DOWN,
    LEFT,
    ORIGIN,
    UP,
    WHITE,
    FadeOut,
    Timeline,
    TypstText,
    Wait,
    Write,
    log,
)
from nirukta.models.tokens import fix_display_token_akshara_splitting
from nirukta.timelines.transform import LenientTransformMatchingDiff
from nirukta.constants import (
    COLORS,
    INACTIVE,
    LATIN_FONT,
    MISSING_CHUNK_RE,
    SANSKRIT_FONT,
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
)
from nirukta.strings import unswara
from nirukta.render import (
    Awaken,
    Diff,
    FlatAligned,
    Junicode_translit,
    set_font,
    transform_text,
    typst_code,
)


# Keyed by MD5 of pickled utterance data.
# Persists across JAnim GUI rebuilds so unchanged utterances are never re-built.
_built_cache: dict[str, Any] = {}


def build_utterance_cached(vAkya: Utterance):
    """Return a cached BuiltTimeline for *vAkya*, building it only on first use."""
    key = hashlib.md5(pickle.dumps((vAkya.tokens, vAkya.english))).hexdigest()
    return build_cached(
        _built_cache, key, lambda: UtteranceTimeline(vAkya).build(), label=vAkya.english
    )


@dataclass
class UtteranceTimeline(Timeline):
    tokens: Sequence[TokenType]
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
        visited = set()
        colorings = build_colorings(self.tokens, COLORS)
        display_tokens = [
            build_display_token(self.english, token, visited, colorings)
            for token in self.tokens
        ]

        display_tokens = fix_display_token_akshara_splitting(display_tokens)

        for i in range(len(display_tokens)):
            if _ := ALPHA_RE.search(display_tokens[i].slp1):
                display_tokens[i].is_root = True
                display_tokens[i].color = INACTIVE
                log.debug(f"{display_tokens[i].slp1} is a `DisplayToken` root")

        frames = frames_for_vakya(display_tokens)

        root = DisplayToken("", WHITE, children=display_tokens, english_spans=[])
        all_english_spans: List[tuple[int, int]] = root.all_spans()
        all_english_spans.append((len(self.english), len(self.english)))

        # Declension (underline) glosses stay white before their underline appears,
        # rather than going grey like an ordinary inactive gloss.
        outline_span_set = set(root.all_outline_spans())

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
                ((start, end), token.color, False)
                for token in frame
                for start, end in token.english_spans
            ] + [
                ((start, end), token.color, True)
                for token in frame
                for start, end in token.outline_spans
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

                # If it is represented in the current frame; otherwise inactive —
                # white for an underline gloss, grey for an ordinary one.
                inactive = WHITE if a in outline_span_set else INACTIVE
                color, stroke = next(
                    ((color, stroke) for b, color, stroke in frame_spans if a == b),
                    (inactive, False),
                )

                english += typst_code(
                    self.english[a[0] : a[1]],
                    Language.ENGLISH,
                    color,
                    stroke_mode=stroke,
                )

                cursor += a[1] - a[0]

            states[0].append(TypstText(set_font(sanskrit, SANSKRIT_FONT)))
            states[1].append(TypstText(set_font(translit, LATIN_FONT)))
            states[2].append(TypstText(set_font(english, LATIN_FONT, wrap=True)))

        # Position everything relative to the final state to minimize movement
        final = states[2][len(states[2]) - 1]
        final.points.move_to(ORIGIN + (DOWN))

        for i in range(len(states[0])):
            # Start the transliteration in the center
            states[0][i].points.next_to(final, direction=UP * 5.5, aligned_edge=LEFT)
            states[1][i].points.next_to(final, direction=UP * 3, aligned_edge=LEFT)
            states[2][i].points.next_to(final, direction=ORIGIN, aligned_edge=LEFT)

            # Initial write on
            if i == 0:
                for fa in [
                    FlatAligned(
                        *(Write(s[i]) for s in states),
                        duration=1.0,
                        name="Write",
                        label_color=C_LABEL_ANIM_IN,
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
                        FlatAligned(
                            *(
                                Awaken(dt)
                                for dt in [
                                    states[0][i - 1].get_label(diff.token_id),
                                    states[1][i - 1].get_label(diff.token_id),
                                ]
                            ),
                            name="Awaken",
                            label_color=C_LABEL_ANIM_INDICATION,
                        ),
                        duration=0.4,
                    )
                # elif diff.anim == Animation.COLORS:
                #     self.play(
                #         FlatAligned(
                #             *(
                #                 Awaken(dt)
                #                 for dt in [
                #                     states[0][i - 1].get_label(diff.token_id),
                #                     states[1][i].get_label(diff.token_id),
                #                 ]
                #             ),
                #             name="Colorize",
                #             label_color=C_LABEL_ANIM_INDICATION,
                #         ),
                #         duration=0.4,
                #     )
                # else:
                self.play(
                    FlatAligned(
                        *(
                            LenientTransformMatchingDiff(
                                s[i - 1],
                                s[i],
                                duration=diff.duration(),
                                mismatch=diff.mismatch(),  # type: ignore[arg-type]
                            )
                            for s in states
                        ),
                        name=diff.name(),
                        label_color=C_LABEL_ANIM_ABSTRACT,
                        rate_func=diff.rate_func(),
                    )
                )

                if diff == Animation.COLORS:
                    self.play(Wait(0.25))

        self.play(Wait(1.0))
        self.play(
            FlatAligned(
                *(FadeOut(s[-1]) for s in states),
                name="FadeOut",
                label_color=C_LABEL_ANIM_OUT,
            )
        )
