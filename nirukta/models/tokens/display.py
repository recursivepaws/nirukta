from typing import List
import uuid
from dataclasses import dataclass, field


@dataclass
class DisplayToken:
    """A single renderable unit at a given animation stage."""

    slp1: str
    color: str  # resolved from colorings
    children: List["DisplayToken"]  # empty => leaf (SimpleToken or punct)
    english_spans: List[tuple[int, int]]  # the spans this token is responsible for
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    is_root: bool = field(default=False)

    @property
    def is_leaf(self) -> bool:
        return not self.children

    def at_depth(self, depth: int) -> List["DisplayToken"]:
        if self.is_leaf or depth == 0:
            return [self]
        return [leaf for child in self.children for leaf in child.at_depth(depth - 1)]

    def all_spans(self):
        def __all_spans(dt: "DisplayToken", spans: List[tuple[int, int]]):
            new_spans = spans + dt.english_spans
            for child in dt.children:
                new_spans.extend(__all_spans(child, []))
            return new_spans

        return sorted(__all_spans(self, []), key=lambda x: x[0])
