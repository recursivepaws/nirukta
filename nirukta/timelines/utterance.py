from dataclasses import dataclass
from typing import List

from janim.imports import (
    BLUE,
    DOWN,
    ORIGIN,
    UP,
    WHITE,
    Aligned,
    FadeOut,
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
)
from nirukta.models import (
    Animation,
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
        frames = frames_for_vakya(display_tokens)

        # sa, tr, en
        states = [[], [], []]
        # state_changes = []
        diffs: List[Diff] = []
        expansion_ids = []
        eii = 0

        # load_gun = True
        for i in range(len(frames) - 1):
            # compare this frame to the next frame
            animation = frames[i]
            b = frames[i + 1]

            # if load_gun:
            #     load_gun = False
            #     for j in range(len(animation)):
            #         if animation[j].slp1 != b[j].slp1 or animation[j]:
            #             print(f"appending {animation[j].id}")
            #             expansion_ids.append(animation[j].id)
            #             break
            #     # expansion_ids.append(animation[j].id)
            known_diffs = len(diffs)

            if len(animation) != len(b):
                # state_changes.append(AnimationChange.EXPAND)
                for j in range(len(animation)):
                    if animation[j].slp1 != b[j].slp1:
                        diffs.append(Diff(Animation.EXPAND, animation[j].id))
                        break
            else:
                for j in range(len(animation)):
                    id = animation[j].id
                    # Swaras changed
                    if (
                        unswara(animation[j].slp1) != animation[j].slp1
                        and unswara(animation[j].slp1) == b[j].slp1
                    ):
                        diffs.append(Diff(Animation.SWARAS, id))
                        break
                    # Spelling changed
                    elif animation[j].slp1 != b[j].slp1:
                        diffs.append(Diff(Animation.SPELLS, id))
                        break
                    # Color changed
                    elif animation[j].color != b[j].color:
                        diffs.append(Diff(Animation.COLORS, id))
                        break

                # else:
                #     raise ValueError("I don't know what kind of change occurred")

            assert len(diffs) != known_diffs, "Unknown diff type"

        # print([*((lambda c: c.value)(s) for s in diffs)])

        for i, frame in enumerate(frames):
            sanskrit = ""
            translit = ""
            english = ""

            for token in frame:
                sanskrit += f"{typst_code(token.slp1, Language.SANSKRIT, token.color)}<{token.id}> "
                iast = transform_text(token.slp1, Language.TRANSLIT)
                translit += f"{Junicode_translit(iast, token.color)}<{token.id}> "

            all_tuples = [
                ((start, end), token.color)
                for token in frame
                for start, end in token.english_spans
            ]
            all_tuples.append(((len(self.english), len(self.english)), WHITE))

            cursor = 0
            plain_english = 0
            for [start, end], color in sorted(all_tuples, key=lambda item: item[0]):
                # Emit any unspanned text before this span
                if start > cursor:
                    missing_text = self.english[cursor:start]
                    plain_english += len(missing_text)
                    for m in MISSING_CHUNK_RE.finditer(missing_text):
                        piece = m.group()
                        if TYPST_CMD_RE.fullmatch(piece):
                            english += piece
                        else:
                            english += typst_code(piece, Language.ENGLISH, WHITE)
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
                english_token = self.english[start:end]
                plain_english += len(english_token)
                english += typst_code_safe(english_token, Language.ENGLISH, color)
                cursor = end

                # Consume a trailing space so missing_text never starts with one
                if cursor < len(self.english) and self.english[cursor] == " ":
                    english += " "
                    cursor += 1

            states[0].append(TypstText(set_font(sanskrit, SANSKRIT_FONT), scale=SCALE))
            states[1].append(TypstText(set_font(translit, LATIN_FONT), scale=SCALE))
            states[2].append(TypstText(set_font(english, LATIN_FONT), scale=SCALE))

        # for s in states[1]:
        #     print(s.text)

        load_gun_v2 = True
        for i in range(len(states[0])):
            # Start the transliteration in the center
            states[1][i].points.move_to(ORIGIN)

            # Move sa and en above and below
            states[0][i].points.next_to(states[1][i], UP * SCALE)
            states[2][i].points.next_to(states[1][i], DOWN * SCALE)

            # Initial write on
            if i == 0:
                for animation in [
                    Aligned(
                        *(Write(s[i]) for s in states),
                        duration=1.0,
                    ),
                    Wait(1.0),
                ]:
                    self.play(animation)

            # Transformation into current state
            if i > 0:
                diff = diffs[i - 1]
                assert isinstance(diff, Diff), f"Invalid Change Type: {diff}"

                if diff.anim == Animation.EXPAND:
                    # dt_label = expansion_ids[eii]

                    self.play(
                        Aligned(
                            *(
                                ShowCreationThenFadeAround(
                                    dt, surrounding_rect_config={"color": WHITE}
                                )
                                for dt in [
                                    states[0][i - 1].get_label(diff.token_id),
                                    states[1][i - 1].get_label(diff.token_id),
                                ]
                            )
                        ),
                        duration=0.4,
                    )
                    eii += 1

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
