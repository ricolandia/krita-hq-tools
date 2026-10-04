"""Imports de Qt com compatibilidade entre PyQt5 (Krita 5.x) e PyQt6 (Krita 6.x)."""

from .erros import escrever_erro
from .qt_probe import escolher as _escolher_qt
from .qt_probe import versao_do_krita

_KRITA_QT = versao_do_krita()
_USAR_PYQT6 = _escolher_qt(_KRITA_QT) >= 6
if _KRITA_QT is not None and not _USAR_PYQT6:
    escrever_erro(
        "[hq_tools] Krita {0} detectado: usando PyQt5\n".format(_KRITA_QT)
    )

if _USAR_PYQT6:  # Krita 6
    try:
        from PyQt6 import QtCore, QtGui, QtWidgets
        from PyQt6.QtCore import pyqtSignal, pyqtSlot
    except ImportError as _erro:  # pragma: no cover
        escrever_erro(
            "[hq_tools] Krita {0} pede PyQt6 e ele não está disponível: "
            "{1}\n".format(_KRITA_QT, _erro)
        )
        raise

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
    CURSOR_SIZE_ALL = QtCore.Qt.CursorShape.SizeAllCursor
    CURSOR_SIZE_FDIAG = QtCore.Qt.CursorShape.SizeFDiagCursor
    CURSOR_ARROW = QtCore.Qt.CursorShape.ArrowCursor
    ALIGN_CENTER_FULL = QtCore.Qt.AlignmentFlag.AlignCenter
    TOOL_BUTTON_TEXT_BESIDE_ICON = QtCore.Qt.ToolButtonStyle.ToolButtonTextBesideIcon
    WA_TRANSLUCENT_BACKGROUND = QtCore.Qt.WidgetAttribute.WA_TranslucentBackground
    WA_NO_SYSTEM_BACKGROUND = QtCore.Qt.WidgetAttribute.WA_NoSystemBackground
    WA_TRANSPARENT_FOR_MOUSE = QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents
    DIALOG_YES = QtWidgets.QMessageBox.StandardButton.Yes
    DIALOG_NO = QtWidgets.QMessageBox.StandardButton.No
    DIALOG_OK = QtWidgets.QMessageBox.StandardButton.Ok
    DIALOG_CANCEL = QtWidgets.QMessageBox.StandardButton.Cancel
    DIALOG_OPEN = QtWidgets.QFileDialog.Option.ShowDirsOnly
else:  # Krita 5.x
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
    CURSOR_SIZE_ALL = QtCore.Qt.SizeAllCursor
    CURSOR_SIZE_FDIAG = QtCore.Qt.SizeFDiagCursor
    CURSOR_ARROW = QtCore.Qt.ArrowCursor
    ALIGN_CENTER_FULL = QtCore.Qt.AlignCenter
    TOOL_BUTTON_TEXT_BESIDE_ICON = QtCore.Qt.ToolButtonTextBesideIcon
    WA_TRANSLUCENT_BACKGROUND = QtCore.Qt.WA_TranslucentBackground
    WA_NO_SYSTEM_BACKGROUND = QtCore.Qt.WA_NoSystemBackground
    WA_TRANSPARENT_FOR_MOUSE = QtCore.Qt.WA_TransparentForMouseEvents
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
    ANTIALIASING = QtGui.QPainter.RenderHint.Antialiasing
    IMAGE_FORMAT_RGBA8888 = QtGui.QImage.Format.Format_RGBA8888
else:
    ANTIALIASING = QtGui.QPainter.Antialiasing
    IMAGE_FORMAT_RGBA8888 = QtGui.QImage.Format_RGBA8888


def standard_icon(name):
    """Ícone de tema do Qt a partir do nome do QStyle.StandardPixmap."""
    style = QtWidgets.QApplication.style()
    if style is None:  # pragma: no cover
        return QIcon()
    if QT_VERSION == 6:
        enum = QtWidgets.QStyle.StandardPixmap
    else:
        enum = QtWidgets.QStyle
    pixmap = style.standardPixmap(getattr(enum, name, enum.SP_FileIcon))
    return QIcon(pixmap)


def qlibrary_prefix():
    """Prefixo de instalação do Qt (raiz dos recursos do Krita no AppImage)."""
    if QT_VERSION == 6:
        return QtCore.QLibraryInfo.path(QtCore.QLibraryInfo.LibraryPath.PrefixPath)
    return QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.PrefixPath)

if QT_VERSION == 6:
    IMAGE_FORMAT_ARGB32 = QtGui.QImage.Format.Format_ARGB32
    TRANSPARENT = QtCore.Qt.GlobalColor.transparent
    LIST_ADJUST = QtWidgets.QListView.ResizeMode.Adjust
    LIST_STATIC = QtWidgets.QListView.Movement.Static
    USER_ROLE = QtCore.Qt.ItemDataRole.UserRole
    DRAG_INTERNAL_MOVE = QtWidgets.QAbstractItemView.DragDropMode.InternalMove
    MOVE_ACTION = QtCore.Qt.DropAction.MoveAction
    WAIT_CURSOR = QtCore.Qt.CursorShape.WaitCursor
    CONTEXT_MENU = QtCore.Qt.ContextMenuPolicy.CustomContextMenu
    SIZE_EXPANDING = QtWidgets.QSizePolicy.Policy.Expanding
    SIZE_FIXED = QtWidgets.QSizePolicy.Policy.Fixed
    NO_ITEM_FLAGS = QtCore.Qt.ItemFlag.NoItemFlags
    SINGLE_SELECTION = QtWidgets.QAbstractItemView.SelectionMode.SingleSelection
    FRAME_HLINE = QtWidgets.QFrame.Shape.HLine
else:
    IMAGE_FORMAT_ARGB32 = QtGui.QImage.Format_ARGB32
    TRANSPARENT = QtCore.Qt.transparent
    LIST_ADJUST = QtWidgets.QListView.Adjust
    LIST_STATIC = QtWidgets.QListView.Static
    USER_ROLE = QtCore.Qt.UserRole
    DRAG_INTERNAL_MOVE = QtWidgets.QAbstractItemView.InternalMove
    MOVE_ACTION = QtCore.Qt.MoveAction
    WAIT_CURSOR = QtCore.Qt.WaitCursor
    CONTEXT_MENU = QtCore.Qt.CustomContextMenu
    SIZE_EXPANDING = QtWidgets.QSizePolicy.Expanding
    SIZE_FIXED = QtWidgets.QSizePolicy.Fixed
    NO_ITEM_FLAGS = QtCore.Qt.NoItemFlags
    SINGLE_SELECTION = QtWidgets.QAbstractItemView.SingleSelection
    FRAME_HLINE = QtWidgets.QFrame.HLine

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
    "ANTIALIASING",
    "IMAGE_FORMAT_RGBA8888",
    "standard_icon",
    "qlibrary_prefix",
    "IMAGE_FORMAT_ARGB32",
    "TRANSPARENT",
    "LIST_ADJUST",
    "LIST_STATIC",
    "USER_ROLE",
    "DRAG_INTERNAL_MOVE",
    "MOVE_ACTION",
    "WAIT_CURSOR",
    "CONTEXT_MENU",
    "SIZE_EXPANDING",
    "SIZE_FIXED",
    "FRAME_HLINE",
    "NO_ITEM_FLAGS",
    "SINGLE_SELECTION",
    "ICON_MODE",
    "ADJUST_IGNORED",
    "ALIGN_CENTER",
    "KEEP_ASPECT",
    "SMOOTH_TRANSFORMATION",
    "NO_FOCUS",
    "CURSOR_POINTING",
    "CURSOR_SIZE_ALL",
    "CURSOR_SIZE_FDIAG",
    "CURSOR_ARROW",
    "ALIGN_CENTER_FULL",
    "TOOL_BUTTON_TEXT_BESIDE_ICON",
    "WA_TRANSLUCENT_BACKGROUND",
    "WA_NO_SYSTEM_BACKGROUND",
    "WA_TRANSPARENT_FOR_MOUSE",
    "DIALOG_YES",
    "DIALOG_NO",
    "DIALOG_OK",
    "DIALOG_CANCEL",
    "DIALOG_OPEN",
]
