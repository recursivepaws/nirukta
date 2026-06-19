import os
import re
import typst
import janim.utils.typst_compile as tc
from janim.gui.anim_viewer import AnimViewer
from janim.gui.timeline_view import TimelineView, LABEL_OBJ_NAME
from janim.gui.label import LazyLabelGroup, Label, LabelGroup
from janim.anims.animation import FOREVER, TimeRange
from janim.anims.composition import AnimGroup
from janim.anims.transform import MethodTransform
from PySide6.QtGui import QColor, QPen
from janim.utils.font.database import FontInfo, get_database
from fontTools.ttLib import TTCollection, TTFont, TTLibError
from janim.utils.font_manager import list_fonts, get_fontext_synonyms

# MethodTransform.__getattr__ accesses self.delayed_actions to record proxy calls.
# During deserialization, delayed_actions hasn't been set yet, so accessing it
# triggers __getattr__ again — infinite recursion. Guard against that case.
_orig_mt_getattr = MethodTransform.__getattr__

def _safe_mt_getattr(self, name):
    if 'delayed_actions' not in object.__getattribute__(self, '__dict__'):
        raise AttributeError(name)
    return _orig_mt_getattr(self, name)

MethodTransform.__getattr__ = _safe_mt_getattr

# Override fonts dir to include custom fonts
font_dir = os.path.join(os.path.dirname(__file__), "..", "fonts")
tc._typst_fonts = typst.Fonts(False, True, [font_dir])

db = get_database()

# Now inject custom fonts from your font_dir into the live database
extensions = get_fontext_synonyms("ttf")
for filepath in list_fonts(font_dir, extensions):
    try:
        fonts = (
            TTCollection(filepath, lazy=True).fonts
            if filepath.endswith("ttc")
            else [TTFont(filepath, lazy=True)]
        )
    except TTLibError:
        continue

    for i, font in enumerate(fonts):
        info = FontInfo(filepath, font, i)
        db.family_by_name[info.family_name].add(info)
        db.font_by_full_name[info.full_name] = info


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
        # if self.subtimeline_label_group is not None:
        #     for label in self.subtimeline_label_group.labels:
        #         expand_all(label)
        self.update()

    TimelineView.set_built = _patched_set_built
    TimelineView._init_label_group_patched = True  # type: ignore[attr-defined]

if not getattr(TimelineView, "_make_anim_label_group_patched", False):
    _orig_make_anim_label_group = TimelineView.make_anim_label_group

    @staticmethod
    def _patched_make_anim_label_group(built):
        def make_label_from_anim(anim, header=True):
            name = anim.name or anim.__class__.__name__
            color = QColor(*anim.label_color)
            if isinstance(anim, AnimGroup) and not getattr(anim, "flat_label", False):
                labels = [
                    label
                    for subanim in anim.anims
                    if (label := make_label_from_anim(subanim)) is not None
                ]
                if not labels:
                    return None
                label = LabelGroup(
                    name,
                    TimeRange(
                        min(lbl.t_range.at for lbl in labels),
                        max(lbl.t_range.end for lbl in labels),
                    ),
                    *labels,
                    collapse=anim.collapse,
                    header=header,
                    brush=color,  # pyright: ignore[reportArgumentType]
                    highlight_pen=QPen(QColor(41, 171, 202), 3),  # pyright: ignore[reportArgumentType]
                    highlight_brush=QColor(41, 171, 202, 40),  # pyright: ignore[reportArgumentType]
                )
            else:
                label = Label(
                    name,
                    anim.t_range
                    if anim.t_range.end is not FOREVER
                    else TimeRange(anim.t_range.at, built.duration),
                    brush=color,  # pyright: ignore[reportArgumentType]
                )
            setattr(label, LABEL_OBJ_NAME, anim)
            return label

        from janim.utils.rate_functions import linear as _linear

        return LabelGroup(
            "",
            TimeRange(0, built.duration),
            *[
                label
                for anim in built.timeline.anim_groups
                if (
                    label := make_label_from_anim(
                        anim,
                        len(anim.anims) != 1 or anim.rate_func is not _linear,
                    )
                )
                is not None
            ],
            collapse=False,
            header=False,
        )

    TimelineView.make_anim_label_group = _patched_make_anim_label_group
    TimelineView._make_anim_label_group_patched = True  # type: ignore[attr-defined]


_ADDR_SUFFIX_RE = re.compile(r" at 0x[0-9A-Fa-f]+ \(item at 0x[0-9A-Fa-f]+\)")

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


if not getattr(AnimViewer, "_set_built_name_patched", False):
    _orig_anim_viewer_set_built = AnimViewer.set_built

    def _patched_anim_viewer_set_built(self, built):
        from PySide6.QtCore import QTimer

        _orig_anim_viewer_set_built(self, built)

        rebuildable = getattr(type(built.timeline), "__rebuildable_name__", None)
        if rebuildable is not None:
            self.name_edit.setText(rebuildable)

        # If the user toggled vertical before the first build, the module loaded
        # with the wrong config. Detect the mismatch and re-trigger immediately.
        want_vertical = os.environ.get("NIRUKTA_VERTICAL") == "1"
        is_vertical = built.cfg.pixel_width < built.cfg.pixel_height
        if want_vertical != is_vertical:
            QTimer.singleShot(0, self.on_rebuild_triggered)

    AnimViewer.set_built = _patched_anim_viewer_set_built
    AnimViewer._set_built_name_patched = True  # type: ignore[attr-defined]
