# -*- coding: utf-8 -*-

"""
    pugdebug - a standalone PHP debugger
    =========================
    copyright: (c) 2015 Robert Basic
    license: GNU GPL v3, see LICENSE for more details
"""

__author__ = "robertbasic"

import math

from PyQt5.QtCore import pyqtSignal, Qt, QRect, QSize
from PyQt5.QtWidgets import (QWidget, QPlainTextEdit, QTextEdit,
                             QShortcut, QInputDialog)
from PyQt5.QtGui import (QColor, QTextFormat, QTextCursor, QPainter,
                         QTextBlockUserData, QFont, QKeySequence)

from pugdebug.syntaxer import PugdebugSyntaxer
from pugdebug import settings


class PugdebugDocument(QPlainTextEdit):
    """A document widget to display code and line numbers

    Line numbers is a separate widget that is rendered on the left margin
    of the QPlainTextEdit viewport.
    """

    document_double_clicked_signal = pyqtSignal(str, int)

    def __init__(self, document_model, formatter):
        super().__init__()

        self.set_editor_features()

        self.line_numbers = PugdebugLineNumbers(self)
        self.blockCountChanged.connect(self.update_line_numbers_width)
        self.updateRequest.connect(self.update_line_numbers)

        self.document_model = document_model

        self.setReadOnly(True)

        self.cursorPositionChanged.connect(self.highlight)

        self.setPlainText(document_model.contents)

        self.remove_line_highlights()

        self.syntaxer = PugdebugSyntaxer(self.document(), formatter)

        self.viewport().setCursor(Qt.ArrowCursor)

        self.shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_search.activated.connect(self.show_search_modal)

        self.shortcut_move_to_line = QShortcut(QKeySequence("Ctrl+G"), self)
        self.shortcut_move_to_line.activated.connect(self.show_move_to_line)

    def set_editor_features(self):
        font = QFont(settings.get('editor/font_family'))
        font.setPointSize(settings.get('editor/font_size'))
        self.setFont(font)

        self.setTabStopWidth(self.fontMetrics().width(' ') *
                             settings.get('editor/tab_size'))

        wrapMode = (QPlainTextEdit.WidgetWidth
                    if settings.get('editor/enable_text_wrapping')
                    else QPlainTextEdit.NoWrap)
        self.setLineWrapMode(wrapMode)

    def line_numbers_width(self):
        digits = math.floor(math.log10(self.blockCount()) + 1)
        return (self.line_numbers.padding_left +
                digits * self.fontMetrics().width('0') +
                self.line_numbers.padding_right)

    def update_line_numbers_width(self, new_block_count=0):
        self.setViewportMargins(self.line_numbers_width(), 0, 0, 0)

    def update_line_numbers(self, rect, dy):
        if dy:
            self.line_numbers.scroll(0, dy)
        else:
            self.line_numbers.update(0, rect.y(),
                                     self.line_numbers.width(),
                                     rect.height())

        if rect.contains(self.viewport().rect()):
            self.update_line_numbers_width()

    def resizeEvent(self, event):
        super().resizeEvent(event)

        cr = self.contentsRect()
        self.line_numbers.setGeometry(QRect(cr.x(), cr.y(),
                                            self.line_numbers_width(),
                                            cr.height()))

    def paint_line_numbers(self, event):
        """Paint the line numbers

        For every visible block in the document draw it's corresponding line
        number in the line numbers widget.
        """
        painter = QPainter(self.line_numbers)
        painter.fillRect(event.rect(), Qt.lightGray)

        block = self.firstVisibleBlock()
        block_number = block.blockNumber()

        content_offset = self.contentOffset()

        number_width = (self.line_numbers.width() -
                        self.line_numbers.padding_right)
        number_height = self.fontMetrics().height()

        breakpoint_size = 8
        breakpoint_y_offset = number_height / 2 - breakpoint_size / 2

        while block.isValid():
            # Get the top coordinate of the current block
            # to know where to paint the line number for it
            block_top = (self.blockBoundingGeometry(block)
                             .translated(content_offset)
                             .top())

            if not block.isVisible() or block_top > event.rect().bottom():
                break

            # If block has a breakpoint,
            # draw a green rectangle by the line number
            # if the block number matches the current line number
            # make it red, as it is then a breakpoint hit
            if self.block_has_breakpoint(block):
                brush = painter.brush()
                brush.setStyle(Qt.SolidPattern)
                if self.block_is_current(block):
                    brush.setColor(Qt.red)
                else:
                    brush.setColor(Qt.darkGreen)
                painter.setBrush(brush)
                painter.drawRect(QRect(0, block_top + breakpoint_y_offset,
                                       breakpoint_size, breakpoint_size))

            number_str = str(block_number + 1)
            painter.setPen(Qt.black)
            painter.drawText(0, block_top,
                             number_width, number_height,
                             Qt.AlignRight, number_str)

            block = block.next()
            block_number += 1

        painter.end()

    def mousePressEvent(self, event):
        pass

    def mouseDoubleClickEvent(self, event):
        path = self.document_model.path

        cursor = self.cursorForPosition(event.pos())

        block = cursor.block()

        # Do not try to set breakpoints on empty lines
        if len(block.text()) == 0:
            return

        # Set/unset breakpoint flag on the double clicked line
        if self.block_has_breakpoint(block):
            self.block_remove_breakpoint(block)
        else:
            self.block_set_breakpoint(block)

        line_number = block.blockNumber() + 1

        self.document_double_clicked_signal.emit(path, line_number)

    def contextMenuEvent(self, event):
        pass

    def move_to_line(self, line, is_current=True):
        """Move cursor to specified line

        Move the cursor block by block until the block number matches
        the line number.
        """
        line = line - 1
        if line < 0:
            line = 0

        cursor = self.textCursor()
        cursor.movePosition(QTextCursor.Start, QTextCursor.MoveAnchor, 0)

        block_number = cursor.blockNumber()

        while block_number < line:
            cursor_moved = cursor.movePosition(
                QTextCursor.NextBlock,
                QTextCursor.MoveAnchor,
                1
            )

            # Unmark block as current
            block = cursor.block()
            self.block_set_is_current(block, False)

            if cursor_moved is False:
                break

            block_number = cursor.blockNumber()

        # Mark block on which the cursor is as the current one
        block = cursor.block()
        self.block_set_is_current(block, is_current)

        self.setTextCursor(cursor)

        self.rehighlight_breakpoint_lines()

    def highlight(self):
        selection = QTextEdit.ExtraSelection()

        color = QColor(209, 220, 236)

        selection.format.setBackground(color)
        selection.format.setProperty(QTextFormat.FullWidthSelection, True)
        selection.cursor = self.textCursor()

        selection.cursor.clearSelection()

        self.setExtraSelections([selection])

    def remove_line_highlights(self):
        """Remove line highlights

        Move the cursor to first (zero) line.

        Clear the extra selections in the file.

        Rehighlight breakpoint lines.
        """
        self.setExtraSelections([])

        self.rehighlight_breakpoint_lines()

    def block_has_breakpoint(self, block):
        user_data = self.__get_block_user_data(block)
        return user_data.breakpoint

    def block_set_breakpoint(self, block):
        user_data = self.__get_block_user_data(block)
        user_data.breakpoint = True
        block.setUserData(user_data)

    def block_remove_breakpoint(self, block):
        user_data = self.__get_block_user_data(block)
        user_data.breakpoint = False
        block.setUserData(user_data)

    def block_is_current(self, block):
        user_data = self.__get_block_user_data(block)
        return user_data.is_current

    def block_set_is_current(self, block, is_current):
        user_data = self.__get_block_user_data(block)
        user_data.is_current = is_current
        block.setUserData(user_data)

    def __get_block_user_data(self, block):
        user_data = block.userData()
        if user_data is None:
            user_data = PugdebugBlockData()
        return user_data

    def show_search_modal(self):
        text, ok = QInputDialog.getText(self, 'Search', 'Insert word')
        self.find(text)

    def show_move_to_line(self):
        text, ok = QInputDialog.getText(self, 'Go To', 'Line number')
        self.move_to_line(int(text), True)

    def handle_document_changed(self, document_model):
        """Handle when a document gets changed

        Set the new contents of the document.

        Refresh the syntaxer.
        """
        self.setPlainText(document_model.contents)

        self.syntaxer.setDocument(self.document())
        self.syntaxer.highlight()

    def handle_editor_features_changed(self):
        self.set_editor_features()

    def get_path(self):
        return self.document_model.path

    def rehighlight_breakpoint_lines(self):
        """Rehighlight breakpoint lines

        Update the line numbers so the paint event gets fired
        and so the breakpoints get repainted as well.
        """
        self.line_numbers.update()


class PugdebugLineNumbers(QWidget):

    def __init__(self, document):
        super().__init__(document)

        self.document = document

        # additional space before and after number
        self.padding_left = 14
        self.padding_right = 5

    def sizeHint(self):
        return QSize(self.document.line_numbers_width(), 0)

    def paintEvent(self, event):
        self.document.paint_line_numbers(event)


class PugdebugBlockData(QTextBlockUserData):

    breakpoint = False
    is_current = False

    def __init__(self):
        super(PugdebugBlockData, self).__init__()
