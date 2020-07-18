# -*- coding: utf-8 -*-

from PyQt5.QtCore import QDir, pyqtSignal
from PyQt5.QtWidgets import QTreeView, QHeaderView, QFileSystemModel


class FileBrowserModel(QFileSystemModel):

    file_activated_signal = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFilter(QDir.AllEntries |
                       QDir.NoDotAndDotDot |
                       QDir.AllDirs |
                       QDir.Hidden)

    def activate_item(self, index):
        if not self.isDir(index):
            self.file_activated_signal.emit(self.filePath(index))


class FileBrowserView(QTreeView):

    def __init__(self, parent=None):
        super().__init__(parent)

        model = get_instance()
        model.rootPathChanged.connect(self.set_root_path)
        self.setModel(model)

        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)
        self.setHeaderHidden(True)

        # Hide extra columns (Size, Type, Date Modified)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)

        self.activated.connect(model.activate_item)

    def set_root_path(self, path):
        self.setRootIndex(self.model().index(path))


instance = None


def get_instance():
    global instance
    if instance is None:
        instance = FileBrowserModel()
    return instance


def file_activated_signal():
    return get_instance().file_activated_signal


def get_root_path():
    return get_instance().rootPath()


def set_root_path(path):
    return get_instance().setRootPath(path)
