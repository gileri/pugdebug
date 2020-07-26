# -*- coding: utf-8 -*-

import os

from PyQt5.QtCore import QCoreApplication, QSettings, QByteArray
from PyQt5.QtGui import QFont, QFontInfo


class Settings(QSettings):

    def __init__(self):
        QCoreApplication.setOrganizationName('pugdebug')
        QCoreApplication.setOrganizationDomain(
            'http://github.com/robertbasic/pugdebug')
        QCoreApplication.setApplicationName('pugdebug')

        super().__init__()

        self.setFallbacksEnabled(False)

        self.settings_info = {
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

            # FIXME: deprecated!!!
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

            # FIXME: deprecated!!!
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


instance = None


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


# FIXME: deprecated!!!
def get_default(key):
    info = get_instance().get_info(key)
    if info:
        return info['default']


# FIXME: deprecated!!!
def has(key):
    return get_instance().contains(key)


# FIXME: deprecated!!!
def save(new_settings):
    changed_settings = {}

    for k, v in new_settings.items():
        if not has(k) or value(k) != v:
            set_value(k, v)
            changed_settings[k] = v

    return changed_settings


# FIXME: deprecated!!!
def add_project(project):
    index = __get_next_index(project)

    if index is not False:
        get_instance().beginWriteArray('projects')
        get_instance().setArrayIndex(index)
        get_instance().setValue('projects', project)
        get_instance().endArray()


# FIXME: deprecated!!!
def delete_project(project):
    size = get_instance().beginReadArray('projects')

    for i in range(0, size):
        get_instance().setArrayIndex(i)
        existing_project = get_instance().value('projects')

        if existing_project == project:
            get_instance().remove('projects')
            break

    get_instance().endArray()

    __reindex_projects_array()


# FIXME: deprecated!!!
def get_projects():
    size = get_instance().beginReadArray('projects')

    projects = []
    for i in range(0, size):
        get_instance().setArrayIndex(i)
        projects.append(get_instance().value('projects'))

    get_instance().endArray()

    return projects


# FIXME: deprecated!!!
def __get_next_index(project):
    size = get_instance().beginReadArray('projects')

    index = None

    for i in range(0, size):
        get_instance().setArrayIndex(i)
        existing_project = get_instance().value('projects')

        if existing_project == project:
            index = i
            break

    get_instance().endArray()

    return False if index is not None else size


# FIXME: deprecated!!!
def __reindex_projects_array():
    size = get_instance().beginReadArray('projects')

    projects = set()
    for i in range(0, size):
        get_instance().setArrayIndex(i)
        project = get_instance().value('projects')

        if project is not None:
            projects.add(project)

    get_instance().endArray()

    get_instance().remove('projects')

    get_instance().beginWriteArray('projects')

    i = 0
    for project in projects:
        get_instance().setArrayIndex(i)
        get_instance().setValue('projects', project)
        i += 1

    get_instance().endArray()
