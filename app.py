#!/usr/bin/python3

# -*- coding: utf-8 -*-

"""
    pugdebug - a standalone PHP debugger
    =========================
    copyright: (c) 2015 Robert Basic and fork's contributors
    license: GNU GPL v3, see LICENSE for more details
"""

# Fix for Gtk-CRITICAL issues on Ubuntu
# Turn off that stupid overlay scrollbars
import os
os.environ['LIBOVERLAY_SCROLLBAR'] = '0'

import sys

import logging
import argparse
from logging.config import dictConfig

from PyQt5.QtWidgets import QApplication
from pugdebug.pugdebug import Pugdebug
VERSION = '1.0.0'

if __name__ == "__main__":
    config = dict(
        version=1,
        formatters={
            'f': {'format': '%(levelname)s %(asctime)s %(message)s'}
        },
        handlers={
            'h': {
                'class': 'logging.FileHandler',
                'level': logging.DEBUG,
                'formatter': 'f',
                'filename': os.path.expanduser('~') + '/pugdebug.log'
            }
        },
        root={
            'handlers': ['h'],
            'level': logging.DEBUG
        }
    )

    parser = argparse.ArgumentParser()
    parser.add_argument('--version', help='Version of pugdebug', action="store_true")
    args = parser.parse_args()
    if args.version:
        print('Pubdebug version: ' + VERSION)
        sys.exit()

    dictConfig(config)
    logger = logging.getLogger()
    app = QApplication(sys.argv)
    logger.debug('Hello pugdebug!')
    pugdebug = Pugdebug()
    logger.debug('Running pugdebug ...')
    pugdebug.run()
    app.exit(app.exec_())
    logger.debug('Pugdebug finished. Bye!')
