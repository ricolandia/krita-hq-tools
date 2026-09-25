"""Imports de Qt com compatibilidade entre PyQt5 (Krita 5.x) e PyQt6 (Krita 6.x)."""

try:  # Krita 6
    from PyQt6 import QtCore, QtGui, QtWidgets
    from PyQt6.QtCore import pyqtSignal, pyqtSlot

    try:
        from PyQt6.QtSvg import QSvgRenderer
    except ImportError:  # pragma: no cover
        QSvgRenderer = None

    QT_VERSION = 6

    ICON_MODE = QtWidgets.QListView.ViewMode.IconMode
    ADJUST_IGNORED = QtCore.Qt.ScrollBarPolicy.ScrollBarAlwaysOff
    ALIGN_CENTER = QtCore.Qt.AlignmentFlag.AlignCenter
    KEEP_ASPECT = QtCore.Qt.AspectRatioMode.KeepAspectRatio
    SMOOTH_TRANSFORMATION = QtCore.Qt.TransformationMode.SmoothTransformation
    NO_FOCUS = QtCore.Qt.FocusPolicy.NoFocus
    CURSOR_POINTING = QtCore.Qt.CursorShape.PointingHandCursor
    DIALOG_YES = QtWidgets.QMessageBox.StandardButton.Yes
    DIALOG_NO = QtWidgets.QMessageBox.StandardButton.No
    DIALOG_OK = QtWidgets.QMessageBox.StandardButton.Ok
    DIALOG_CANCEL = QtWidgets.QMessageBox.StandardButton.Cancel
    DIALOG_OPEN = QtWidgets.QFileDialog.Option.ShowDirsOnly
except ImportError:  # Krita 5.x
    from PyQt5 import QtCore, QtGui, QtWidgets
    from PyQt5.QtCore import pyqtSignal, pyqtSlot

    try:
        from PyQt5.QtSvg import QSvgRenderer
    except ImportError:  # pragma: no cover
        QSvgRenderer = None

    QT_VERSION = 5

    ICON_MODE = QtWidgets.QListView.IconMode
    ADJUST_IGNORED = QtCore.Qt.ScrollBarAlwaysOff
    ALIGN_CENTER = QtCore.Qt.AlignCenter
    KEEP_ASPECT = QtCore.Qt.KeepAspectRatio
    SMOOTH_TRANSFORMATION = QtCore.Qt.SmoothTransformation
    NO_FOCUS = QtCore.Qt.NoFocus
    CURSOR_POINTING = QtCore.Qt.PointingHandCursor
    DIALOG_YES = QtWidgets.QMessageBox.Yes
    DIALOG_NO = QtWidgets.QMessageBox.No
    DIALOG_OK = QtWidgets.QMessageBox.Ok
    DIALOG_CANCEL = QtWidgets.QMessageBox.Cancel
    DIALOG_OPEN = QtWidgets.QFileDialog.ShowDirsOnly

QImage = QtGui.QImage
QIcon = QtGui.QIcon
QPixmap = QtGui.QPixmap
QSize = QtCore.QSize

if QT_VERSION == 6:
    IMAGE_FORMAT_ARGB32 = QtGui.QImage.Format.Format_ARGB32
    TRANSPARENT = QtCore.Qt.GlobalColor.transparent
    LIST_ADJUST = QtWidgets.QListView.ResizeMode.Adjust
    LIST_STATIC = QtWidgets.QListView.Movement.Static
    USER_ROLE = QtCore.Qt.ItemDataRole.UserRole
    DRAG_INTERNAL_MOVE = QtWidgets.QAbstractItemView.DragDropMode.InternalMove
    MOVE_ACTION = QtCore.Qt.DropAction.MoveAction
    WAIT_CURSOR = QtCore.Qt.CursorShape.WaitCursor
else:
    IMAGE_FORMAT_ARGB32 = QtGui.QImage.Format_ARGB32
    TRANSPARENT = QtCore.Qt.transparent
    LIST_ADJUST = QtWidgets.QListView.Adjust
    LIST_STATIC = QtWidgets.QListView.Static
    USER_ROLE = QtCore.Qt.UserRole
    DRAG_INTERNAL_MOVE = QtWidgets.QAbstractItemView.InternalMove
    MOVE_ACTION = QtCore.Qt.MoveAction
    WAIT_CURSOR = QtCore.Qt.WaitCursor

__all__ = [
    "QtCore",
    "QtGui",
    "QtWidgets",
    "pyqtSignal",
    "pyqtSlot",
    "QSvgRenderer",
    "QT_VERSION",
    "QImage",
    "QIcon",
    "QPixmap",
    "QSize",
    "IMAGE_FORMAT_ARGB32",
    "TRANSPARENT",
    "LIST_ADJUST",
    "LIST_STATIC",
    "USER_ROLE",
    "DRAG_INTERNAL_MOVE",
    "MOVE_ACTION",
    "WAIT_CURSOR",
    "ICON_MODE",
    "ADJUST_IGNORED",
    "ALIGN_CENTER",
    "KEEP_ASPECT",
    "SMOOTH_TRANSFORMATION",
    "NO_FOCUS",
    "CURSOR_POINTING",
    "DIALOG_YES",
    "DIALOG_NO",
    "DIALOG_OK",
    "DIALOG_CANCEL",
    "DIALOG_OPEN",
]
