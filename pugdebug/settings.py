# -*- coding: utf-8 -*-

import os
from contextlib import contextmanager

from PyQt5.QtCore import (Qt, pyqtSignal, QCoreApplication, QSettings,
                          QByteArray)
from PyQt5.QtGui import QFont, QFontInfo
from PyQt5.QtWidgets import (QDialog, QPushButton, QVBoxLayout, QHBoxLayout,
                             QFormLayout, QSpinBox, QCheckBox, QFontComboBox,
                             QGroupBox)

from pugdebug import projects


class Settings(QSettings):

    edit_dialog_saved = pyqtSignal()

    def __init__(self):
        QCoreApplication.setOrganizationName('pugdebug')
        QCoreApplication.setOrganizationDomain(
            'http://github.com/robertbasic/pugdebug')
        QCoreApplication.setApplicationName('pugdebug')

        super().__init__()

        self.setFallbacksEnabled(False)

        self.settings_info = {
            'active_project': {
                'type': str,
                'default': 'default'
            },
            'window': {
                'geometry': {
                    'type': QByteArray,
                },
                'state': {
                    'type': QByteArray,
                },
            },
            'editor': {
                'font_family': {
                    'type': str,
                    'default_func': self.get_default_font_family,
                },
                'font_size': {
                    'type': int,
                    'default': 10,
                },
                'tab_size': {
                    'type': int,
                    'default': 4,
                },
                'enable_text_wrapping': {
                    'type': bool,
                    'default': False,
                },
            },
            'project': {
                '*': {
                    'path': {
                        'project_root': {
                            'type': str,
                            'default': os.path.expanduser('~'),
                        },
                        'path_mapping': {
                            'type': str,
                            'default': '',
                        },
                    },
                    'debugger': {
                        'host': {
                            'type': str,
                            'default': '127.0.0.1',
                        },
                        'port_number': {
                            'type': int,
                            'default': 9000,
                        },
                        'idekey': {
                            'type': str,
                            'default': 'pugdebug',
                        },
                        'break_at_first_line': {
                            'type': bool,
                            'default': True,
                        },
                        'max_depth': {
                            'type': int,
                            'default': 3,
                        },
                        'max_children': {
                            'type': int,
                            'default': 128,
                        },
                        'max_data': {
                            'type': int,
                            'default': 512,
                        },
                    },
                },
            },
        }

        self.settings_info_cache = {}

    def get_info(self, key):
        full_key = self.group()
        if full_key:
            full_key += '/'
        full_key += key

        if full_key in self.settings_info_cache:
            return self.settings_info_cache[full_key]

        node = self.settings_info

        for sub_key in full_key.split('/'):
            if sub_key != '':
                if sub_key in node:
                    node = node[sub_key]
                elif '*' in node:
                    node = node['*']
                else:
                    return None

        info = {}

        if 'default' in node:
            info['default'] = node['default']
        elif 'default_func' in node:
            info['default'] = node['default'] = node['default_func']()
        else:
            info['default'] = None

        info['type'] = node['type'] if 'type' in node else None

        self.settings_info_cache[full_key] = info

        return info

    def get_default_font_family(self):
        font = QFont('Monospace')
        font.setStyleHint(QFont.Monospace)
        return QFontInfo(font).family()

    @contextmanager
    def open_group(self, prefix):
        self.beginGroup(prefix)
        try:
            yield None
        finally:
            self.endGroup()

    def value(self, key):
        info = self.get_info(key)
        if not info:
            return super().value(key)

        if info['type']:
            try:
                return super().value(key, info['default'], info['type'])
            except TypeError:
                return info['default']
        else:
            return super().value(key, info['default'])

    def setValue(self, key, value):
        info = self.get_info(key)

        if info and info['type']:
            try:
                value = info['type'](value)
            except (ValueError, TypeError):
                value = info['default']

        return super().setValue(key, value)


class SettingsEditDialog(QDialog):

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setModal(True)
        self.setWindowTitle('Settings')
        self.setMinimumWidth(400)

        self.accepted.connect(self.save)

        # Editor group

        self.font_family_input = QFontComboBox()

        self.font_size_input = QSpinBox()
        self.font_size_input.setRange(8, 24)
        self.font_size_input.setSuffix(' pt')

        self.tab_size_input = QSpinBox()
        self.tab_size_input.setRange(1, 16)
        self.tab_size_input.setSuffix(' spaces')

        self.enable_text_wrapping_input = QCheckBox('Enable text wrapping')

        editor_layout = QFormLayout()
        editor_layout.addRow('Font family:', self.font_family_input)
        editor_layout.addRow('Font size:', self.font_size_input)
        editor_layout.addRow('Tab size:', self.tab_size_input)
        editor_layout.addRow('', self.enable_text_wrapping_input)

        editor_group = QGroupBox('Editor')
        editor_group.setLayout(editor_layout)

        # Buttons

        edit_project_button = QPushButton('Edit default project...')
        edit_project_button.clicked.connect(
            lambda: projects.show_edit_dialog('default'))

        save_button = QPushButton('OK')
        save_button.setDefault(True)
        save_button.clicked.connect(self.accept)

        cancel_button = QPushButton('Cancel')
        cancel_button.clicked.connect(self.reject)

        button_layout = QHBoxLayout()
        button_layout.addWidget(edit_project_button, 1, Qt.AlignLeft)
        button_layout.addWidget(save_button, 0, Qt.AlignRight)
        button_layout.addWidget(cancel_button)

        # Main layout

        main_layout = QVBoxLayout()
        main_layout.addWidget(editor_group)
        main_layout.addLayout(button_layout)

        self.setLayout(main_layout)

    def show(self):
        font = QFont(value('editor/font_family'))
        self.font_family_input.setCurrentFont(font)
        self.font_family_input.setCurrentText(QFontInfo(font).family())
        self.font_family_input.setFocus(Qt.OtherFocusReason)

        self.font_size_input.setValue(value('editor/font_size'))

        self.tab_size_input.setValue(value('editor/tab_size'))

        self.enable_text_wrapping_input.setChecked(
            value('editor/enable_text_wrapping'))

        super().show()

    def save(self):
        set_value('editor/font_family',
                  QFontInfo(self.font_family_input.currentFont()).family())
        set_value('editor/font_size', self.font_size_input.value())
        set_value('editor/tab_size', self.tab_size_input.value())
        set_value('editor/enable_text_wrapping',
                  self.enable_text_wrapping_input.isChecked())

        edit_dialog_saved().emit()


instance = None
edit_dialog = None


def get_instance():
    global instance
    instance = instance or Settings()
    return instance


def value(key):
    return get_instance().value(key)


def set_value(key, value):
    return get_instance().setValue(key, value)


def remove(key):
    return get_instance().remove(key)


def open_group(prefix):
    return get_instance().open_group(prefix)


def child_groups():
    return get_instance().childGroups()


def edit_dialog_saved():
    return get_instance().edit_dialog_saved


def show_edit_dialog():
    global edit_dialog
    edit_dialog = edit_dialog or SettingsEditDialog()
    edit_dialog.show()
