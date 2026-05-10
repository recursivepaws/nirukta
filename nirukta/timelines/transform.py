from dataclasses import dataclass

from janim.imports import TransformMatchingDiff, normalize, np


class LenientTransformMatchingDiff(TransformMatchingDiff):
    flat_label = True

    @dataclass
    class _MatchWrapper(TransformMatchingDiff._MatchWrapper):
        def __eq__(self, other):
            if not isinstance(other, LenientTransformMatchingDiff._MatchWrapper):
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
