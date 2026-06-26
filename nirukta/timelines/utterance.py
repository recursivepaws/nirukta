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
from nirukta.models.tokens import (
    _PADA_SANDHI,
    animation_for,
    fix_display_token_akshara_splitting,
)
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


def _mark_dormant(dt: DisplayToken) -> None:
    """Grey a freshly-surfaced unit. Padas (anything that isn't a multi-part
    container) also get is_root, so they Awaken right before their first analysis;
    compounds / akshara-merges just split (grey -> grey), no awaken.
    """
    if not ALPHA_RE.search(dt.slp1):
        return
    dt.color = INACTIVE
    if len(dt.children) > 1:  # container: compound / akshara-merge
        for child in dt.children:
            if isinstance(child, DisplayToken):
                _mark_dormant(child)
    # external sandhi on a pada
    elif animation_for(dt) in _PADA_SANDHI:
        # grey this layer, no awaken; descend to the root beneath the sandhi
        _mark_dormant(dt.children[0])
    else:  # pada root
        dt.is_root = True


def render_frame_typst(
    frame: Sequence[DisplayToken],
    english_text: str,
    all_english_spans: List[tuple[int, int]],
    outline_span_set: set,
    span_to_leaf: dict[tuple[int, int], str] | None = None,
) -> tuple[str, str, str]:
    """Build the (sanskrit, translit, english) typst content strings for one frame."""
    span_to_leaf = span_to_leaf or {}
    sanskrit = ""
    translit = ""
    english = ""

    for token in frame:
        sanskrit += (
            f"{typst_code(token.slp1, Language.SANSKRIT, token.color)}<{token.id}> "
        )
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
            missing_text = english_text[cursor : a[0]]
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
            english_text[a[0] : a[1]],
            Language.ENGLISH,
            color,
            stroke_mode=stroke,
        )
        # Label fill glosses by owning-leaf id so they can Awaken with the pada
        if a in span_to_leaf:
            english += f"<{span_to_leaf[a]}>"

        cursor += a[1] - a[0]

    return sanskrit, translit, english


def utterance_final_typst(utterance: Utterance) -> tuple[str, str, str]:
    """The (sanskrit, translit, english) typst content for an utterance's final,
    fully-deconstructed state — the resting end of its timeline, with no animation."""
    colorings = build_colorings(utterance.tokens, COLORS)
    visited: set = set()
    dts = [
        build_display_token(utterance.english, t, visited, colorings)
        for t in utterance.tokens
    ]
    dts = fix_display_token_akshara_splitting(dts)
    frames = frames_for_vakya(dts)

    root = DisplayToken("", WHITE, children=dts, english_spans=[])
    all_english_spans = root.all_spans()
    all_english_spans.append((len(utterance.english), len(utterance.english)))

    return render_frame_typst(
        frames[-1],
        utterance.english,
        all_english_spans,
        set(root.all_outline_spans()),
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

        for dt in display_tokens:
            _mark_dormant(dt)

        frames = frames_for_vakya(display_tokens)

        root = DisplayToken("", WHITE, children=display_tokens, english_spans=[])
        all_english_spans: List[tuple[int, int]] = root.all_spans()
        all_english_spans.append((len(self.english), len(self.english)))

        # Declension (underline) glosses stay white before their underline appears,
        # rather than going grey like an ordinary inactive gloss.
        outline_span_set = set(root.all_outline_spans())

        # Label each (fill) gloss span with its owning leaf's id, so the english
        # gloss can be grabbed via get_label and Awakened together with its pada.
        span_to_leaf: dict[tuple[int, int], str] = {}
        outline_leaf_ids: set[str] = set()

        def _collect_gloss_owners(dt: DisplayToken) -> None:
            for span in dt.english_spans:
                span_to_leaf[span] = dt.id
            if dt.outline_spans:
                outline_leaf_ids.add(dt.id)
            for child in dt.children:
                _collect_gloss_owners(child)

        for dt in display_tokens:
            _collect_gloss_owners(dt)
        gloss_leaf_ids = set(span_to_leaf.values())

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

                # Colour the awakening token transitions into (its next form), and
                # the id of the form it becomes (whose english gloss awakens too)
                color = fb[j].color
                gloss_id = fb[j].id

                # Expansion
                if len(fa) != len(fb) and fa[j].slp1 != fb[j].slp1:
                    diffs.append(Diff(Animation.EXPAND, id, initial, color, gloss_id))
                # Swaras changed
                elif (
                    unswara(fa[j].slp1) != fa[j].slp1
                    and unswara(fa[j].slp1) == fb[j].slp1
                ):
                    diffs.append(Diff(Animation.SWARAS, id, initial, color, gloss_id))
                # Spelling changed
                elif fa[j].slp1 != fb[j].slp1:
                    diffs.append(Diff(Animation.SPELLS, id, initial, color, gloss_id))
                # Color changed
                elif fa[j].color != fb[j].color:
                    diffs.append(Diff(Animation.COLORS, id, initial, color, gloss_id))

                # Exit once we've added to the list
                if len(diffs) > diff_count:
                    break

            assert len(diffs) != diff_count, "Unknown diff type"

        for i, frame in enumerate(frames):
            sanskrit, translit, english = render_frame_typst(
                frame,
                self.english,
                all_english_spans,
                outline_span_set,
                span_to_leaf,
            )
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
                    # A beat before a pada wakes up
                    self.play(Wait(0.25))
                    awaken_labels = [
                        states[0][i - 1].get_label(diff.token_id),
                        states[1][i - 1].get_label(diff.token_id),
                    ]
                    # A pada awakening straight into its colour brings its english
                    # gloss along, in the same aligned animation (no separate recolour).
                    if (
                        diff.anim == Animation.COLORS
                        and diff.gloss_id in gloss_leaf_ids
                    ):
                        awaken_labels.append(states[2][i - 1].get_label(diff.gloss_id))
                    self.play(
                        FlatAligned(
                            *(Awaken(dt, color=diff.color) for dt in awaken_labels),
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
                # The awaken already performs the colour transition for a
                # COLORS-initial pada, so its transform would be a no-op — jump
                # straight to state i instead of replaying it. Unless the pada also
                # has a declension gloss, whose underline still needs the transform.
                if (
                    diff.initial
                    and diff.anim == Animation.COLORS
                    and diff.gloss_id not in outline_leaf_ids
                ):
                    self.hide(*(s[i - 1] for s in states))
                    self.show(*(s[i] for s in states))
                else:
                    # A beat before a compound destructures
                    if diff.anim == Animation.EXPAND:
                        self.play(Wait(0.25))
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

        self.play(Wait(1.0))
        self.play(
            FlatAligned(
                *(FadeOut(s[-1]) for s in states),
                name="FadeOut",
                label_color=C_LABEL_ANIM_OUT,
            )
        )
