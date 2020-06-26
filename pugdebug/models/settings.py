# -*- coding: utf-8 -*-

"""
    pugdebug - a standalone PHP debugger
    =========================
    copyright: (c) 2015 Robert Basic
    license: GNU GPL v3, see LICENSE for more details
"""

__author__ = "robertbasic"

import os

from PyQt5.QtCore import QCoreApplication, QSettings


class PugdebugSettings():

    settings_info = {
        'debugger/host': dict(type=str, default='127.0.0.1'),
        'debugger/port_number': dict(type=int, default=9000),
        'debugger/idekey': dict(type=str, default='pugdebug'),
        'debugger/break_at_first_line': dict(type=bool, default=True),
        'debugger/max_depth': dict(type=int, default=3),
        'debugger/max_children': dict(type=int, default=128),
        'debugger/max_data': dict(type=int, default=512),

        'path/project_root': dict(type=str, default=os.path.expanduser('~')),
        'path/path_mapping': dict(type=str, default=''),

        'editor/tab_width': dict(type=int, default=80),
        'editor/font_size': dict(type=int, default=12),
    }

    def __init__(self):
        """Model object to handle application settings

        Sets up initial application settings.

        QSettings promises to work cross-platform.
        """
        QCoreApplication.setOrganizationName("pugdebug")
        QCoreApplication.setOrganizationDomain(
            "http://github.com/robertbasic/pugdebug"
        )
        QCoreApplication.setApplicationName("pugdebug")
        self.application_settings = QSettings()

        self.setup_default_settings()

    def setup_default_settings(self):
        """Set the default values for settings which don't have a value."""
        for key, setting_info in self.settings_info.items():
            if not self.has(key) and 'default' in setting_info:
                self.set(key, setting_info['default'])

    def get(self, key):
        default = self.get_default(key)
        to_type = self.get_type(key)

        if to_type is not None:
            try:
                value = self.application_settings.value(key, default, to_type)
            except TypeError:
                value = default
        else:
            value = self.application_settings.value(key, default)

        return value

    def get_default(self, key):
        if key in self.settings_info and 'default' in self.settings_info[key]:
            return self.settings_info[key]['default']

    def get_type(self, key):
        if key in self.settings_info and 'type' in self.settings_info[key]:
            return self.settings_info[key]['type']

    def has(self, key):
        return self.application_settings.contains(key)

    def set(self, key, value):
        return self.application_settings.setValue(key, value)

    def remove(self, key):
        return self.application_settings.remove(key)

    def add_project(self, project):
        index = self.__get_next_index(project)

        if index is not False:
            self.application_settings.beginWriteArray('projects')
            self.application_settings.setArrayIndex(index)
            self.application_settings.setValue('projects', project)
            self.application_settings.endArray()

    def delete_project(self, project):
        size = self.application_settings.beginReadArray('projects')

        for i in range(0, size):
            self.application_settings.setArrayIndex(i)
            existing_project = self.application_settings.value('projects')

            if existing_project == project:
                self.application_settings.remove('projects')
                break

        self.application_settings.endArray()

        self.__reindex_projects_array()

    def get_projects(self):
        size = self.application_settings.beginReadArray('projects')

        projects = []
        for i in range(0, size):
            self.application_settings.setArrayIndex(i)
            projects.append(self.application_settings.value('projects'))

        self.application_settings.endArray()

        return projects

    def __get_next_index(self, project):
        size = self.application_settings.beginReadArray('projects')

        index = None

        for i in range(0, size):
            self.application_settings.setArrayIndex(i)
            existing_project = self.application_settings.value('projects')

            if existing_project == project:
                index = i
                break

        self.application_settings.endArray()

        return False if index is not None else size

    def __reindex_projects_array(self):
        size = self.application_settings.beginReadArray('projects')

        projects = set()
        for i in range(0, size):
            self.application_settings.setArrayIndex(i)
            project = self.application_settings.value('projects')

            if project is not None:
                projects.add(project)

        self.application_settings.endArray()

        self.application_settings.remove('projects')

        self.application_settings.beginWriteArray('projects')

        i = 0
        for project in projects:
            self.application_settings.setArrayIndex(i)
            self.application_settings.setValue('projects', project)
            i += 1

        self.application_settings.endArray()


settings = PugdebugSettings()


def get_setting(key):
    return settings.get(key)


def get_default_setting(key):
    return settings.get_default(key)


def has_setting(key):
    return settings.has(key)


def set_setting(key, value):
    settings.set(key, value)


def remove_setting(key):
    settings.remove(key)


def save_settings(new_settings):
    changed_settings = {}

    for key in new_settings:
        value = new_settings[key]
        if not has_setting(key) or get_setting(key) != value:
            set_setting(key, value)
            changed_settings[key] = value

    return changed_settings


def add_project(project):
    settings.add_project(project)


def delete_project(project):
    settings.delete_project(project)


def get_projects():
    return settings.get_projects()
