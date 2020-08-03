# -*- coding: utf-8 -*-

from PyQt5.QtCore import QDir, pyqtSignal
from PyQt5.QtWidgets import (QTreeView, QHeaderView, QFileSystemModel,
                             QMessageBox)

from pugdebug import settings, projects, utils


class FileBrowserModel(QFileSystemModel):

    file_activated = pyqtSignal(str)
    root_path_change_failed = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setFilter(QDir.AllEntries |
                       QDir.NoDotAndDotDot |
                       QDir.AllDirs |
                       QDir.Hidden)

        self.update_root_path()
        projects.active_project_changed().connect(self.update_root_path)

    def update_root_path(self):
        project_root = settings.value('project/' + projects.active() +
                                      '/path/project_root')
        self.setRootPath(project_root)

    def setRootPath(self, new_path):
        if utils.is_readable_dir(new_path, isabs=True):
            self.invalid_root_path = None
            return super().setRootPath(new_path)
        else:
            self.invalid_root_path = new_path
            self.root_path_change_failed.emit(new_path)
            return self.index(self.rootPath())

    def activate_item(self, index):
        if not self.isDir(index):
            self.file_activated.emit(self.filePath(index))


class FileBrowserView(QTreeView):

    def __init__(self, parent=None):
        super().__init__(parent)

        model = get_instance()
        self.setModel(model)

        self.update_root_path()
        model.rootPathChanged.connect(self.update_root_path)
        model.root_path_change_failed.connect(self.update_root_path)

        self.header().setSectionResizeMode(QHeaderView.ResizeToContents)
        self.header().setStretchLastSection(False)
        self.setHeaderHidden(True)

        # Hide extra columns (Size, Type, Date Modified)
        self.setColumnHidden(1, True)
        self.setColumnHidden(2, True)
        self.setColumnHidden(3, True)

        self.activated.connect(model.activate_item)

    def update_root_path(self):
        model = self.model()
        if model.invalid_root_path is None:
            self.setRootIndex(model.index(model.rootPath()))
        else:
            msg = ('Project root path \'%s\' does not exist or '
                   'cannot be read' % model.invalid_root_path)
            QMessageBox.warning(self, '', msg)


instance = None


def get_instance():
    global instance
    if instance is None:
        instance = FileBrowserModel()
    return instance


def file_activated():
    return get_instance().file_activated
