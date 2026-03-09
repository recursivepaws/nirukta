from __future__ import annotations
from dataclasses import dataclass, field
from enum import Enum
import re
from typing import List, Optional
from parser import SlokaFile
from colors import COLORS

from indic_transliteration import sanscript
from indic_transliteration.sanscript import transliterate
from parsimonious.grammar import Grammar
from parsimonious.nodes import NodeVisitor

SCALE = 2.0

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
    GrowFromCenter,
    ShrinkToCenter,
    Succession,
    TransformMatchingDiff,
    TypstText,
    Wait,
    Write,
)


class Language(Enum):
    ENGLISH = "english"
    SANSKRIT = "sanskrit"
    TRANSLIT = "translit"


@dataclass
class Node:
    text: str
    color: str = WHITE
    gloss: Optional[str] = None
    delay: int = 0
    children: List["Node"] = field(default_factory=list)

    def __repr__(self, indent=0):
        pad = "  " * indent
        attrs = []
        if self.color != WHITE:
            attrs.append(f"@{self.color}")
        if self.gloss:
            attrs.append(f"[{self.gloss}]")
        if self.delay:
            attrs.append(f"+{self.delay}")
        attr_str = " ".join(attrs)
        header = f'{pad}Node("{self.text}"{(", " + attr_str) if attr_str else ""})'
        if self.children:
            child_str = "\n".join(c.__repr__(indent + 1) for c in self.children)
            return f"{header} {{\n{child_str}\n{pad}}}"
        return header

    def __post_init__(self):
        self.text = self.text.replace("\\n", "#linebreak()")
        self.text = re.sub(
            r"\\translit\{([^}]+)\}",
            lambda m: transliterate(m.group(1), sanscript.ITRANS, sanscript.IAST),
            self.text,
        )

        if "#" not in self.color:
            self.color = COLORS[self.color]

        # auto-coerce string children to Node instances
        if self.delay > 0:
            node = Node(self.text, self.color, children=self.children)
            for i in range(self.delay):
                node = Node(self.text, children=[node])

            self.text = node.text
            self.color = node.color
            self.children = node.children
            self.label = node.label
        else:
            splits = self.text.split(" ")
            # If there are spaces
            if len(splits) > 1 and len(splits) == len(self.children):
                print(splits)
                new_children = []
                for i in range(len(splits)):
                    new_children.append(
                        Node(splits[i], self.color, children=[self.children[i]])
                    )

                self.text = self.text
                self.color = self.color
                self.children = new_children
                self.label = f"label{abs(hash(self.text)) % (10**8)}"
            else:
                self.text = self.text
                self.color = self.color
                self.children = self.children
                self.label = f"label{abs(hash(self.text)) % (10**8)}"

    def typst_code(self, language: Language):
        match language:
            case Language.ENGLISH:
                return Junicode(self.text, self.color, self.label)
            case Language.TRANSLIT:
                iast = transliterate(self.text, sanscript.ITRANS, sanscript.IAST)
                return Junicode(iast, self.color, self.label)
            case Language.SANSKRIT:
                deva = transliterate(self.text, sanscript.ITRANS, sanscript.DEVANAGARI)
                return Jaini(deva, self.color, self.label)

    def strings(self, language: Language):
        strings = [self.typst_code(language)]
        child_strings = []
        depth = 0

        if len(self.children) > 0:
            for child in self.children:
                cs = child.strings(language)
                if len(cs) > depth:
                    depth = len(cs)
                child_strings.append(cs)

        roots = []
        # each depth should have its own string
        for i in range(depth):
            root = []
            for cs in child_strings:
                if len(cs) > i:
                    root.append(cs[i])
                else:
                    root.append(cs[len(cs) - 1])
            roots.append(str(" ").join(root))

        return strings + roots

    def states(self, language: Language):
        return [
            (lambda s: TypstText(s, scale=SCALE))(s) for s in self.strings(language)
        ]

    def decompose_states(self, states: List[TypstText]):
        animations = []
        animations.append(Write(states[0], duration=1.0))

        for i in range(len(states) - 1):
            animations.append(
                TransformMatchingDiff(
                    states[i],
                    states[i + 1],
                    duration=0.5,
                    mismatch=(  # type: ignore[arg-type]
                        lambda item, p, **kwargs: ShrinkToCenter(item, **kwargs),
                        lambda item, p, **kwargs: GrowFromCenter(item, **kwargs),
                    ),
                )
            )
            animations.append(Wait(0.2))

        return Succession(
            *animations,
            Wait(1.2),
            FadeOut(states[len(states) - 1], duration=0.5),
        )


@dataclass
class Citation:
    node: Node
    lang: Language

    def __init__(self, text: str, lang: Language):
        self.node = Node(text)
        self.lang = lang

    def __repr__(self):
        return f'Citation("{self.node}", {self.lang})'


@dataclass
class Sloka:
    citation: Citation
    sanskrit: List[List[Node]]  # list of lines, each line a list of nodes
    english: List[List[Node]]

    def __init__(self, file: SlokaFile):
        # For each visual row
        for line in file.lines:
            # For each utterance
            for vAkya in line.vAkyAni:
                print("meow")

    def __repr__(self):
        def fmt_section(lines):
            out = []
            for i, line in enumerate(lines):
                out.append(f"  --- line {i + 1} ---")
                for node in line:
                    for ln in node.__repr__(indent=2).splitlines():
                        out.append(ln)
            return "\n".join(out)

        return (
            f"Sloka(\n"
            f"  {self.citation!r},\n"
            f"  sanskrit=[\n{fmt_section(self.sanskrit)}\n  ],\n"
            f"  english=[\n{fmt_section(self.english)}\n  ]\n"
            f")"
        )

    def teach(self):
        sloka = []

        for i in range(len(self.sanskrit)):
            line = ""
            for sentence in self.sanskrit[i]:
                line += sentence.typst_code(Language.SANSKRIT)

            sloka.append(TypstText(line, scale=SCALE))

        sloka = Group(*sloka)
        sloka.points.arrange(DOWN)

        animations = []

        for line in sloka:
            animations.append(Write(line, duration=6.0))

        citation = TypstText(
            self.citation.node.typst_code(self.citation.lang), scale=SCALE
        )
        citation.points.next_to(sloka, DOWN)

        animations.append(
            Succession(
                Wait(2.0),
                Write(citation, duration=0.5),
                Wait(0.5),
                FadeOut(Group(sloka, citation)),
            )
        )

        for i in range(len(self.sanskrit)):
            for j in range(len(self.sanskrit[i])):
                sa = self.sanskrit[i][j].states(Language.SANSKRIT)
                ia = self.sanskrit[i][j].states(Language.TRANSLIT)
                en = self.english[i][j].states(Language.ENGLISH)

                for xi in range(len(sa)):
                    ia_ref = ia[min(xi, len(ia) - 1)]
                    ia_ref.points.move_to(ORIGIN)
                    sa[min(xi, len(sa) - 1)].points.next_to(ia_ref, UP / SCALE * 4.0)
                    en[min(xi, len(en) - 1)].points.next_to(ia_ref, DOWN / SCALE * 4.0)
                    # Language.SANSKRIT, ORIGIN + UP / SCALE * 2.0

                animations.append(
                    Aligned(
                        self.sanskrit[i][j].decompose_states(sa),
                        self.sanskrit[i][j].decompose_states(ia),
                        self.english[i][j].decompose_states(en),
                    )
                )

        return Succession(*animations)


def Junicode(text: str, color: str, label: str):
    return (
        f'#text(font: "Junicode", stroke: none, fill: rgb("{color}"))[{text}] <{label}>'
    )


def Jaini(text: str, color: str, label: str):
    return f'#text(font: "Jaini", stroke: none, fill: rgb("{color}"))[{text}] <{label}>'
