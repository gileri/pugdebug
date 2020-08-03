# -*- coding: utf-8 -*-

import os
import re

from PyQt5.QtCore import Qt, pyqtSignal, QAbstractListModel, QModelIndex
from PyQt5.QtGui import QFont, QIcon, QKeySequence
from PyQt5.QtWidgets import (QDialog, QPushButton, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QLineEdit, QSpinBox, QCheckBox,
                             QGroupBox, QListView, QAction, QMenu, QMessageBox,
                             QFileDialog)

from pugdebug import settings, utils


class ProjectsBrowserModel(QAbstractListModel):

    active_project_changed = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)

        self.load_data()

        self.active = settings.value('active_project')
        if not self.exists(self.active):
            self.set_active('default')

    def load_data(self):
        with settings.open_group('project'):
            self.projects = list(filter(lambda s: s.lower() != 'default',
                                        settings.child_groups()))
            self.projects.sort(key=str.lower)
            self.projects.insert(0, 'default')

        self.emit_data_changed()

    def exists(self, project_name, *, ignore_case=False):
        try:
            projects = self.projects
            if ignore_case:
                projects = [s.lower() for s in projects]
                project_name = project_name.lower()
            return projects.index(project_name) >= 0

        except ValueError:
            return False

    def emit_data_changed(self):
        self.dataChanged.emit(QModelIndex(), QModelIndex())

    def rowCount(self, parent):
        return len(self.projects)

    def data(self, index, role):
        if role == Qt.DisplayRole:
            return self.projects[index.row()]

        if role == Qt.FontRole:
            if self.projects[index.row()] == self.active:
                font = QFont()
                font.setBold(True)
                return font

    def set_active(self, project_name):
        if project_name != self.active and self.exists(project_name):
            self.active = project_name
            settings.set_value('active_project', project_name)
            self.emit_data_changed()
            self.active_project_changed.emit()

    def name_by_index(self, index):
        return self.projects[index.row()]

    def delete(self, project_name):
        if project_name != 'default':
            if project_name == self.active:
                self.set_active('default')
            settings.remove('project/' + project_name)
            self.load_data()

    def update(self, old_name, new_name, new_settings):
        if old_name and old_name != new_name:
            settings.remove('project/' + old_name)

        with settings.open_group('project/' + new_name):
            for k, v in new_settings.items():
                settings.set_value(k, v)

        if not old_name:
            self.load_data()
            self.set_active(new_name)
        elif old_name != new_name:
            self.load_data()
            if old_name == self.active:
                self.set_active(new_name)
        elif old_name == self.active:
            self.active_project_changed.emit()

    def activate_item(self, index):
        self.set_active(self.projects[index.row()])


class ProjectsBrowserView(QListView):

    def __init__(self, parent=None):
        super().__init__(parent)

        model = get_instance()
        self.setModel(model)

        self.add_action = QAction(QIcon.fromTheme('list-add'),
                                  '&Add...', self)
        self.add_action.triggered.connect(show_add_dialog)

        self.edit_action = QAction('&Edit...', self)
        self.edit_action.triggered.connect(self.edit_selected_item)

        self.delete_action = QAction(QIcon.fromTheme('list-remove'),
                                     '&Delete', self)
        self.delete_action.setShortcut(QKeySequence('Del'))
        self.delete_action.setShortcutContext(Qt.WidgetShortcut)
        self.delete_action.triggered.connect(self.delete_selected_item)
        self.addAction(self.delete_action)

        self.setContextMenuPolicy(Qt.CustomContextMenu)
        self.customContextMenuRequested.connect(self.show_context_menu)

        self.activated.connect(model.activate_item)

    def show_context_menu(self, point):
        context_menu = QMenu(self)
        context_menu.aboutToHide.connect(self.hide_context_menu)

        context_menu.addAction(self.add_action)

        index = self.indexAt(point)
        if index.isValid():
            project_name = self.model().name_by_index(index)
            context_menu.addAction(self.edit_action)
            if project_name != 'default':
                context_menu.addAction(self.delete_action)

        if context_menu.actions():
            # Remove all actions from the widget
            # while the context menu is visible
            self.__actions = self.actions()
            for action in self.__actions:
                self.removeAction(action)

            context_menu.popup(self.mapToGlobal(point))

    def hide_context_menu(self):
        # Restore all actions on the widget
        self.addActions(self.__actions)

    def edit_selected_item(self):
        indexes = self.selectedIndexes()
        if indexes:
            project_name = self.model().name_by_index(indexes[0])
            show_edit_dialog(project_name)

    def delete_selected_item(self):
        indexes = self.selectedIndexes()
        if indexes:
            project_name = self.model().name_by_index(indexes[0])
            if project_name != 'default':
                text = ('Are you sure you want to delete the \'%s\' project?'
                        % project_name)
                if QMessageBox.question(self, '', text) == QMessageBox.Yes:
                    self.model().delete(project_name)


class ProjectEditDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.project_name = ''

        self.setModal(True)
        self.setMinimumWidth(400)

        self.accepted.connect(self.save)

        # Project name

        self.project_name_input = QLineEdit()

        project_name_layout = QFormLayout()
        project_name_layout.addRow('Project name:', self.project_name_input)

        # Path group

        self.project_root_input = QLineEdit()

        browse_button = QPushButton('&Browse...')
        browse_button.clicked.connect(self.select_project_root)

        project_root_layout = QHBoxLayout()
        project_root_layout.addWidget(self.project_root_input)
        project_root_layout.addWidget(browse_button)

        self.path_mapping_input = QLineEdit()

        path_layout = QFormLayout()
        path_layout.addRow('Root:', project_root_layout)
        path_layout.addRow('Maps from:', self.path_mapping_input)

        path_group = QGroupBox('Path')
        path_group.setLayout(path_layout)

        # Debugger group

        self.host_input = QLineEdit()

        self.port_number_input = QSpinBox()
        self.port_number_input.setRange(1, 65535)

        self.idekey_input = QLineEdit()
        self.break_at_first_line_input = QCheckBox('Break at first line')

        self.max_depth_input = QSpinBox()
        self.max_depth_input.setRange(1, 999999999)

        self.max_children_input = QSpinBox()
        self.max_children_input.setRange(1, 999999999)

        self.max_data_input = QSpinBox()
        self.max_data_input.setRange(1, 999999999)

        debugger_layout = QFormLayout()
        debugger_layout.addRow('Host:', self.host_input)
        debugger_layout.addRow('Port:', self.port_number_input)
        debugger_layout.addRow('IDE Key:', self.idekey_input)
        debugger_layout.addRow('', self.break_at_first_line_input)
        debugger_layout.addRow('Max depth:', self.max_depth_input)
        debugger_layout.addRow('Max children:', self.max_children_input)
        debugger_layout.addRow('Max data:', self.max_data_input)

        debugger_group = QGroupBox('Debugger')
        debugger_group.setLayout(debugger_layout)

        # Buttons

        save_button = QPushButton('OK')
        save_button.setDefault(True)
        save_button.clicked.connect(self.validate)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(save_button, 1, Qt.AlignRight)
        button_layout.addWidget(cancel_button)

        # Main layout

        main_layout = QVBoxLayout()
        main_layout.addLayout(project_name_layout)
        main_layout.addWidget(path_group)
        main_layout.addWidget(debugger_group)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def select_project_root(self):
        dir = QFileDialog.getExistingDirectory(
            self, '',
            self.project_root_input.text() or os.path.expanduser('~'),
            QFileDialog.ShowDirsOnly | QFileDialog.DontResolveSymlinks)

        if dir:
            self.project_root_input.setText(dir)

    def set_project(self, project_name):
        self.project_name = project_name

    def show(self):
        title = 'Edit Project' if self.project_name else 'New Project'
        self.setWindowTitle(title)

        self.project_name_input.setText(self.project_name)
        if self.project_name != 'default':
            self.project_name_input.setDisabled(False)
            self.project_name_input.setFocus(Qt.OtherFocusReason)
        else:
            self.project_name_input.setDisabled(True)
            self.project_root_input.setFocus(Qt.OtherFocusReason)

        group = 'project/' + (self.project_name or 'default')
        with settings.open_group(group):
            if self.project_name:
                self.project_root_input.setText(
                    settings.value('path/project_root'))

                self.path_mapping_input.setText(
                    settings.value('path/path_mapping'))
            else:
                self.project_root_input.setText('')
                self.path_mapping_input.setText('')

            self.host_input.setText(
                settings.value('debugger/host'))

            self.port_number_input.setValue(
                settings.value('debugger/port_number'))

            self.idekey_input.setText(
                settings.value('debugger/idekey'))

            self.break_at_first_line_input.setChecked(
                settings.value('debugger/break_at_first_line'))

            self.max_depth_input.setValue(
                settings.value('debugger/max_depth'))

            self.max_children_input.setValue(
                settings.value('debugger/max_children'))

            self.max_data_input.setValue(
                settings.value('debugger/max_data'))

        super().show()

    def validate(self):
        try:
            project_name = self.project_name_input.text().strip()
            if not project_name:
                raise ValueError('Project name is required')

            if not re.match('^[A-Za-z0-9\-_]+$', project_name):
                raise ValueError(
                    'Project name can only contain latin characters, digits, '
                    'dashes and underscores')

            if (get_instance().exists(project_name, ignore_case=True) and
                    project_name.lower() != self.project_name.lower()):
                raise ValueError('Project name must be unique')

            project_root = self.project_root_input.text().strip()
            if not project_root:
                raise ValueError('Project root path is required')

            project_root = os.path.normpath(project_root)
            if not utils.is_readable_dir(project_root, isabs=True):
                raise ValueError('Project root path \'%s\' does not exist or '
                                 'cannot be read' % project_root)

            self.accept()

        except ValueError as err:
            QMessageBox.critical(self, '', str(err))

    def save(self):
        old_name = self.project_name
        new_name = self.project_name_input.text().strip()

        new_settings = {
            'path/project_root': os.path.normpath(
                self.project_root_input.text().strip()),
            'path/path_mapping': self.path_mapping_input.text().strip(),
            'debugger/host': self.host_input.text().strip(),
            'debugger/port_number': self.port_number_input.value(),
            'debugger/idekey': self.idekey_input.text().strip(),
            'debugger/break_at_first_line':
                self.break_at_first_line_input.isChecked(),
            'debugger/max_depth': self.max_depth_input.value(),
            'debugger/max_children': self.max_children_input.value(),
            'debugger/max_data': self.max_data_input.value(),
        }

        get_instance().update(old_name, new_name, new_settings)


instance = None
edit_dialog = None


def get_instance():
    global instance
    instance = instance or ProjectsBrowserModel()
    return instance


def active():
    return get_instance().active


def active_project_changed():
    return get_instance().active_project_changed


def show_add_dialog():
    show_edit_dialog('')


def show_edit_dialog(project_name):
    global edit_dialog
    edit_dialog = edit_dialog or ProjectEditDialog()
    edit_dialog.set_project(project_name)
    edit_dialog.show()
