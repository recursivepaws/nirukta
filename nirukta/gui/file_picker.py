import os
import glob

from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QCheckBox,
    QVBoxLayout,
    QWidget,
)
from nirukta.models import System
from nirukta.render import transliterate

LIBRARY_ROOT = os.path.join(os.path.dirname(__file__), "..", "..", "library")


def _is_nirukta_file(name: str) -> bool:
    return name.endswith(".sloka") or name.endswith(".sutra")


def _display_name(path: str) -> str:
    name = os.path.basename(path.rstrip("/"))
    for ext in (".sloka", ".sutra"):
        if name.endswith(ext):
            stem = name[: -len(ext)]
            iast = transliterate(System.SLP1, System.IAST, stem)
            return iast + ext
    return transliterate(System.SLP1, System.IAST, name)


class NiruktaFilePicker(QWidget):
    _path_label: QLabel
    _list: QListWidget
    _up_btn: QPushButton
    _select_btn: QPushButton
    _rebuild: QCheckBox
    _vertical: QCheckBox

    file_chosen = Signal(str)  # emits absolute path when a file is confirmed

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
        self._root = os.path.realpath(LIBRARY_ROOT)
        self._current = self._root
        self._sutra_path: str | None = None

        self.setWindowTitle("Nirukta File Picker")
        self.setWindowFlags(Qt.WindowType.Tool)
        self.setAttribute(Qt.WidgetAttribute.WA_DeleteOnClose)
        self.setStyleSheet("""
            * { font-size: 15pt; }
            QListWidget { padding: 4px; }
            QListWidget::item { padding: 6px 4px; }
            QPushButton { padding: 8px 20px; }
        """)
        self.resize(520, 480)

        self._path_label = QLabel()
        self._path_label.setWordWrap(True)

        self._list = QListWidget()
        self._list.itemDoubleClicked.connect(self._on_double_click)
        self._list.itemSelectionChanged.connect(self._on_selection_changed)

        self._up_btn = QPushButton("↑  Up")
        self._up_btn.clicked.connect(self._go_up)

        self._select_btn = QPushButton("Select")
        self._select_btn.setEnabled(False)
        self._select_btn.clicked.connect(self._confirm_selection)

        self._rebuild = QCheckBox("Rebuild")
        self._rebuild.toggled.connect(self._toggle_rebuild)

        self._vertical = QCheckBox("Vertical")
        self._vertical.toggled.connect(self._toggle_vertical)

        btn_row = QHBoxLayout()
        btn_row.addWidget(self._up_btn)
        btn_row.addWidget(self._rebuild)
        btn_row.addWidget(self._vertical)
        btn_row.addStretch()
        btn_row.addWidget(self._select_btn)

        layout = QVBoxLayout(self)
        layout.addWidget(self._path_label)
        layout.addWidget(self._list)
        layout.addLayout(btn_row)

        self._populate()

    # ------------------------------------------------------------------
    def _populate(self) -> None:
        if self._sutra_path is not None:
            self._populate_sutra()
        else:
            self._populate_files()

    def _populate_files(self) -> None:
        self._list.clear()

        dirs = sorted(
            p for p in glob.glob(os.path.join(self._current, "*/")) if os.path.isdir(p)
        )
        files = sorted(
            p
            for p in (
                glob.glob(os.path.join(self._current, "*.sloka"))
                + glob.glob(os.path.join(self._current, "*.sutra"))
            )
        )

        for d in dirs:
            item = QListWidgetItem(f"📁  {_display_name(d)}")
            item.setData(Qt.ItemDataRole.UserRole, d)
            self._list.addItem(item)

        for f in files:
            item = QListWidgetItem(f"  {_display_name(f)}")
            item.setData(Qt.ItemDataRole.UserRole, f)
            self._list.addItem(item)

        rel = os.path.relpath(self._current, self._root)
        label = "library/" if rel == "." else f"library/{rel}/"
        self._path_label.setText(label)
        self._up_btn.setEnabled(self._current != self._root)
        self._select_btn.setEnabled(False)

    def _populate_sutra(self) -> None:
        from nirukta.parsing.visitors.sutra import SutraVisitor
        from nirukta.models.presentation.sloka import sloka_label

        self._list.clear()
        # validation-free parse: we only need the slokas listed, not validated
        sutra_file = SutraVisitor(self._sutra_path, validate=False).parse()

        whole = QListWidgetItem("  Whole Sutra")
        whole.setData(Qt.ItemDataRole.UserRole, ("whole", self._sutra_path))
        self._list.addItem(whole)

        for i, sloka in enumerate(sutra_file.slokas):
            item = QListWidgetItem(f"  {sloka_label(i, sloka)}")
            item.setData(Qt.ItemDataRole.UserRole, (i, self._sutra_path))
            self._list.addItem(item)

        rel = os.path.relpath(self._sutra_path, self._root)
        self._path_label.setText(f"library/{rel}")
        self._up_btn.setEnabled(True)
        self._select_btn.setEnabled(False)

    def _go_up(self) -> None:
        if self._sutra_path is not None:
            self._sutra_path = None
            self._populate()
        else:
            self._current = os.path.dirname(self._current)
            self._populate()

    def _on_double_click(self, item: QListWidgetItem) -> None:
        data = item.data(Qt.ItemDataRole.UserRole)
        if isinstance(data, str) and os.path.isdir(data):
            self._current = os.path.realpath(data)
            self._populate()
        else:
            self._confirm_selection()

    def _on_selection_changed(self) -> None:
        items = self._list.selectedItems()
        if not items:
            self._select_btn.setEnabled(False)
            return
        data = items[0].data(Qt.ItemDataRole.UserRole)
        if isinstance(data, str):
            self._select_btn.setEnabled(_is_nirukta_file(data))
        else:
            self._select_btn.setEnabled(True)

    def _confirm_selection(self) -> None:
        items = self._list.selectedItems()
        if not items:
            return
        data = items[0].data(Qt.ItemDataRole.UserRole)

        if isinstance(data, str):
            if not _is_nirukta_file(data):
                return
            if data.endswith(".sutra"):
                self._sutra_path = data
                self._populate()
                return
            os.environ["NIRUKTA_FILE"] = data
            os.environ.pop("NIRUKTA_SLOKA_INDEX", None)
            self.file_chosen.emit(data)
        else:
            kind, sutra_path = data
            os.environ["NIRUKTA_FILE"] = sutra_path
            if kind == "whole":
                os.environ.pop("NIRUKTA_SLOKA_INDEX", None)
            else:
                os.environ["NIRUKTA_SLOKA_INDEX"] = str(kind)
            self.file_chosen.emit(sutra_path)

    def _toggle_rebuild(self) -> None:
        if self._rebuild.isChecked():
            os.environ["REBUILD"] = "1"
        else:
            os.environ.pop("REBUILD", None)

    def _toggle_vertical(self) -> None:
        if self._vertical.isChecked():
            os.environ["NIRUKTA_VERTICAL"] = "1"
        else:
            os.environ.pop("NIRUKTA_VERTICAL", None)

        from PySide6.QtWidgets import QApplication
        from janim.gui.anim_viewer import AnimViewer

        app = QApplication.instance()
        if app is None:
            return
        for w in app.topLevelWidgets():
            if isinstance(w, AnimViewer):
                w.on_rebuild_triggered()
                return
