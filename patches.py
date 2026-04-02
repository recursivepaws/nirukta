import os
import re
import typst
import janim.utils.typst_compile as tc
from janim.gui.timeline_view import TimelineView
from janim.gui.label import LazyLabelGroup, LabelGroup
from PySide6.QtGui import QColor

# Override fonts dir to include custom fonts
font_dir = os.path.join(os.path.dirname(__file__), "fonts")
tc._typst_fonts = typst.Fonts(True, True, [font_dir])


# Recursively expand all timeline dropdowns in the GUI by default
def expand_all(label):
    if isinstance(label, LazyLabelGroup) and label._collapse:
        label.switch_collapse()  # initializes children + sets _collapse=False
    if isinstance(label, LabelGroup) and not label._collapse:
        for child in label.labels:
            expand_all(child)


if not getattr(TimelineView, "_init_label_group_patched", False):
    _orig_set_built = TimelineView.set_built

    def _patched_set_built(self, built, pause_progresses):
        _orig_set_built(self, built, pause_progresses)
        # Run after restore, so we always end up fully expanded
        if self.subtimeline_label_group is not None:
            for label in self.subtimeline_label_group.labels:
                expand_all(label)
        self.update()

    TimelineView.set_built = _patched_set_built
    TimelineView._init_label_group_patched = True  # type: ignore[attr-defined]

_ADDR_SUFFIX_RE = re.compile(r" at 0x[0-9A-Fa-f]+ \(item at 0x[0-9A-Fa-f]+\)$")

if not getattr(TimelineView, "_make_subtimeline_name_patched", False):
    _orig_make_subtimeline_label_group = TimelineView.make_subtimeline_label_group

    @staticmethod
    def _patched_make_subtimeline_label_group(built):
        result = _orig_make_subtimeline_label_group(built)

        if result is not None:
            for label, item in zip(result.labels, built.timeline.subtimeline_items):
                tl = item._built.timeline
                if hasattr(tl, "gui_name"):
                    label.name = tl.gui_name
                else:
                    label.name = _ADDR_SUFFIX_RE.sub("", label.name)
                if hasattr(tl, "gui_color"):
                    color = QColor(tl.gui_color)
                    label.brush = QColor(color.red(), color.green(), color.blue(), 190)  # type: ignore[attr-defined]
                    label.pen = color  # type: ignore[attr-defined]

        return result

    TimelineView.make_subtimeline_label_group = _patched_make_subtimeline_label_group
    TimelineView._make_subtimeline_name_patched = True  # type: ignore[attr-defined]
