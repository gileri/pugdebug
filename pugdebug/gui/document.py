# -*- coding: utf-8 -*-

"""
    pugdebug - a standalone PHP debugger
    =========================
    copyright: (c) 2015 Robert Basic
    license: GNU GPL v3, see LICENSE for more details
"""

__author__ = "robertbasic"

import math

from PyQt5.QtCore import pyqtSignal, Qt, QRect
from PyQt5.QtWidgets import (QWidget, QPlainTextEdit, QTextEdit, QGridLayout,
                             QShortcut, QInputDialog)
from PyQt5.QtGui import (QColor, QTextFormat, QTextCursor, QPainter,
                         QTextBlockUserData, QFont, QKeySequence)

from pugdebug.syntaxer import PugdebugSyntaxer
from pugdebug.models.settings import get_setting


class PugdebugDocument(QWidget):
    """A document widget to display code and line numbers

    This document widget is built from two different widgets, one being
    a QPlainTextEdit widget that holds the contents of the document, and
    the other being a simple QWidget that gets the line numbers painted on.
    """

    document_contents = None

    line_numbers = None

    document_double_clicked_signal = pyqtSignal(str, int)

    def __init__(self, document_model, formatter):
        super(PugdebugDocument, self).__init__()

        # The QPlainTextEdit widget that holds the contents of the document
        self.document_contents = PugdebugDocumentContents(
            self,
            document_model,
            formatter
        )

        # The QWidget that gets the line numbers
        self.line_numbers = PugdebugLineNumbers(self)

        self.document_contents.updateRequest.connect(
            self.handle_document_contents_update_request
        )

        self.layout = QGridLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.addWidget(self.line_numbers, 0, 0, 1, 1)
        self.layout.addWidget(self.document_contents, 0, 1, 1, 1)

        self.shortcut_search = QShortcut(QKeySequence("Ctrl+F"), self)
        self.shortcut_search.activated.connect(self.show_search_modal)

        self.shortcut_move_to_line = QShortcut(QKeySequence("Ctrl+G"), self)
        self.shortcut_move_to_line.activated.connect(self.show_move_to_line)

    def show_search_modal(self):
        text, ok = QInputDialog.getText(self, 'Search', 'Insert word')
        self.document_contents.find(text)

    def show_move_to_line(self):
        text, ok = QInputDialog.getText(self, 'Go To', 'Line number')
        self.document_contents.move_to_line(int(text), True)

    def handle_document_changed(self, document_model):
        """Handle when a document gets changed

        Set the new document contents.
        """
        self.document_contents.update_contents(document_model)

    def handle_editor_features_changed(self):
        self.document_contents.set_editor_features()
        self.line_numbers.set_font()

    def handle_document_contents_update_request(self, rect, dy):
        """Handle the update request for document contents

        Scroll the line numbers along with the document contents.

        Set the width of the line numbers widget.
        """
        if (dy != 0):
            self.line_numbers.scroll(0, dy)

        line_count = self.document_contents.blockCount()
        self.line_numbers.set_line_count(line_count)

    def paint_line_numbers(self, line_numbers, event):
        """Paint the line numbers

        For every visible block in the document draw it's corresponding line
        number in the line numbers widget.
        """
        font_metrics = self.document_contents.fontMetrics()

        painter = QPainter(line_numbers)

        block = self.document_contents.firstVisibleBlock()
        line_number = block.blockNumber()

        height = font_metrics.height()
        width = line_numbers.width()
        breakpoint_size = 8
        breakpoint_y_offset = height / 2 - breakpoint_size / 2

        while block.isValid():
            # blocks are numbered from zero
            line_number += 1

            content_offset = self.document_contents.contentOffset()
            # Get the top coordinate of the current block
            # to know where to paint the line number for it
            block_top = (self.document_contents
                             .blockBoundingGeometry(block)
                             .translated(content_offset)
                             .top())

            if not block.isVisible() or block_top >= event.rect().bottom():
                break

            # If block has a breakpoint,
            # draw a green rectangle by the line number
            # if the block number matches the current line number
            # make it red, as it is then a breakpoint hit
            if self.document_contents.block_has_breakpoint(block):
                brush = painter.brush()
                brush.setStyle(Qt.SolidPattern)
                if self.document_contents.block_is_current(block):
                    brush.setColor(Qt.red)
                else:
                    brush.setColor(Qt.darkGreen)
                painter.setBrush(brush)
                rect = QRect(0, block_top + breakpoint_y_offset,
                             breakpoint_size, breakpoint_size)
                painter.drawRect(rect)

            # Convert the line number to string so we can paint it
            text = str(line_number)

            painter.drawText(0, block_top, width, height, Qt.AlignRight, text)

            block = block.next()

        painter.end()

    def get_path(self):
        return self.document_contents.document_model.path

    def move_to_line(self, line, is_current=True):
        self.document_contents.move_to_line(line, is_current)
        self.rehighlight_breakpoint_lines()

    def remove_line_highlights(self):
        self.document_contents.remove_line_highlights()
        self.rehighlight_breakpoint_lines()

    def rehighlight_breakpoint_lines(self):
        """Rehighlight breakpoint lines

        Update the line numbers so the paint event gets fired
        and so the breakpoints get repainted as well.
        """
        self.line_numbers.update()


class PugdebugDocumentContents(QPlainTextEdit):

    document_widget = None

    document_model = None

    syntaxer = None

    def __init__(self, document_widget, document_model, formatter):
        super(PugdebugDocumentContents, self).__init__()

        self.document_widget = document_widget

        self.document_model = document_model

        self.setReadOnly(True)

        self.cursorPositionChanged.connect(self.highlight)

        self.setPlainText(document_model.contents)

        self.remove_line_highlights()

        self.syntaxer = PugdebugSyntaxer(self.document(), formatter)

        self.viewport().setCursor(Qt.ArrowCursor)

        self.set_editor_features()

    def update_contents(self, document_model):
        """Update the contents of the document

        Set the new contents of the document.

        Refresh the syntaxer.
        """
        self.setPlainText(document_model.contents)
        self.syntaxer.setDocument(self.document())
        self.syntaxer.highlight()

    def set_editor_features(self):
        font = QFont(get_setting('editor/font_family'))
        font.setPointSize(get_setting('editor/font_size'))
        self.setFont(font)

        self.setTabStopWidth(self.fontMetrics().width(' ') *
                             get_setting('editor/tab_size'))

        wrapMode = (QPlainTextEdit.WidgetWidth
                    if get_setting('editor/enable_text_wrapping')
                    else QPlainTextEdit.NoWrap)
        self.setLineWrapMode(wrapMode)

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

        self.document_widget.document_double_clicked_signal.emit(
            path,
            line_number
        )

    def contextMenuEvent(self, event):
        pass

    def move_to_line(self, line, is_current=True):
        """Move cursor to line

        Move the cursor of the QPlainTextEdit that holds the document
        contents to the line.

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
        """
        self.setExtraSelections([])

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


class PugdebugLineNumbers(QWidget):

    document_widget = None

    line_count = 1

    def __init__(self, document_widget):
        super(PugdebugLineNumbers, self).__init__()

        self.document_widget = document_widget

        self.set_font()

    def set_font(self):
        font = QFont(get_setting('editor/font_family'))
        font.setPointSize(get_setting('editor/font_size'))
        self.setFont(font)

        self.__set_width()

    def set_line_count(self, line_count):
        self.line_count = line_count
        self.__set_width()

    def __set_width(self):
        digits = math.floor(math.log10(self.line_count) + 1)
        # add 14 to have space to paint the breakpoint markers
        width = digits * self.fontMetrics().width('0') + 14
        self.setFixedWidth(width)

    def paintEvent(self, event):
        self.document_widget.paint_line_numbers(self, event)


class PugdebugBlockData(QTextBlockUserData):

    breakpoint = False
    is_current = False

    def __init__(self):
        super(PugdebugBlockData, self).__init__()
