# -*- coding: utf-8 -*-

import os
import stat


def is_readable_dir(path, *, isabs=None):
    if isabs is None or os.path.isabs(path) == isabs:
        try:
            mode = os.stat(path).st_mode
            return stat.S_ISDIR(mode) and os.access(path, os.R_OK)
        except OSError:
            pass

    return False
