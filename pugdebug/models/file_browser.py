# -*- coding: utf-8 -*-

"""
    pugdebug - a standalone PHP debugger
    =========================
    copyright: (c) 2015 Robert Basic
    license: GNU GPL v3, see LICENSE for more details
"""

__author__ = "robertbasic"

from PyQt5.QtWidgets import QFileSystemModel
from PyQt5.QtCore import QDir


class PugdebugFileBrowser(QFileSystemModel):

    def __init__(self, parent):
        super(PugdebugFileBrowser, self).__init__(parent)
        self.setFilter(QDir.AllEntries |
                       QDir.NoDotAndDotDot |
                       QDir.AllDirs |
                       QDir.Hidden)

    def set_path(self, path):
        self.setRootPath(path)
        self.start_index = self.index(path)

    def get_file_path(self, model_index):
        if not self.isDir(model_index):
            return self.filePath(model_index)
        return None
