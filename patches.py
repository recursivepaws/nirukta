import os
import typst
import janim.utils.typst_compile as tc
from janim.gui.timeline_view import TimelineView
from janim.gui.label import LazyLabelGroup, LabelGroup

# Override fonts dir to include my fonts
font_dir = os.path.join(os.path.dirname(__file__), "fonts")
tc._typst_fonts = typst.Fonts(True, True, [font_dir])


def expand_all(label):
    if isinstance(label, LazyLabelGroup) and label._collapse:
        label.switch_collapse()  # initializes children + sets _collapse=False
    if isinstance(label, LabelGroup) and not label._collapse:
        for child in label.labels:
            expand_all(child)


if not getattr(TimelineView.init_label_group, "_patched", False):
    _orig_init_label_group = TimelineView.init_label_group

    def _patched_init_label_group(self):
        _orig_init_label_group(self)
        if self.subtimeline_label_group is not None:
            for label in self.subtimeline_label_group.labels:
                expand_all(label)

    _patched_init_label_group._patched = True
    TimelineView.init_label_group = _patched_init_label_group
