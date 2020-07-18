# -*- coding: utf-8 -*-

import pygments
import pygments.formatter
import pygments.lexers.php

from PyQt5.QtGui import QSyntaxHighlighter, QColor, QFont, QTextCharFormat


class Syntaxer(QSyntaxHighlighter):

    formatter = None

    def __init__(self, document):
        super().__init__(document)

        if Syntaxer.formatter is None:
            Syntaxer.formatter = Formatter(style='default')

        self.lexer = pygments.lexers.php.PhpLexer()

        self.highlight()

    def highlight(self):
        document = self.document()
        self.formatter.document = document
        pygments.highlight(document.toPlainText(), self.lexer, self.formatter)

    def highlightBlock(self, text):
        block_number = self.currentBlock().blockNumber()
        start = 0

        if block_number not in self.formatter.formats:
            return

        for block_format in self.formatter.formats[block_number]:
            count = block_format['count']
            token = block_format['token']
            self.setFormat(start, count, self.formatter.styles[token])
            start += count


class Formatter(pygments.formatter.Formatter):

    def __init__(self, **options):
        super().__init__(**options)

        self.styles = {}
        self.formats = {}

        for token, style in self.style:
            format = QTextCharFormat()

            if style['color']:
                format.setForeground(QColor('#' + style['color']))
            if style['bgcolor']:
                format.setBackground(QColor('#' + style['bgcolor']))
            if style['italic']:
                format.setFontItalic(True)
            if style['bold']:
                format.setFontWeight(QFont.Bold)

            self.styles[token] = format

    def format(self, tokensource, outfile):
        """Format source file

        Formats are separated block by block.
        """
        # Formats for every block, block by block
        self.formats = {}

        # Current position in the source
        current_position = 0

        for token, value in tokensource:
            next_position = current_position + len(value)

            start_block = self.document.findBlock(current_position)
            start_block_number = start_block.blockNumber()

            end_block = self.document.findBlock(next_position - 1)
            end_block_number = end_block.blockNumber()

            if end_block_number > start_block_number:
                prev_position = current_position

                for block_number in range(start_block_number + 1,
                                          end_block_number + 1):
                    block = self.document.findBlockByNumber(block_number)
                    count = block.position() - prev_position
                    self.__add_block_format(block_number - 1, count, token)
                    prev_position = block.position()

                count = next_position - block.position()
                self.__add_block_format(block_number, count, token)

            else:
                self.__add_block_format(start_block_number, len(value), token)

            current_position = next_position

    def __add_block_format(self, block_number, count, token):
        if block_number not in self.formats:
            self.formats[block_number] = []

        self.formats[block_number].append({
            'count': count,
            'token': token
        })
