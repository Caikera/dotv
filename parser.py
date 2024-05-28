from typing import List

import re

from lexer import Lexer, Token
from log import log
from syntax.syntax_node import *


identifier_pat = re.compile(r'[$a-zA-Z_][a-zA-Z_0-9]*')


def is_valid_identifier(s: str):
    return identifier_pat.fullmatch(s)


class ParserError(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class Parser:
    def __init__(self, context: List[str]):
        self.lexer = Lexer(context)

    def parse(self):
        while self.lexer.token() != Token.EOF:
            if self.lexer.token == Token.Module:
                self.parse_module()
            else:
                self.lexer.next()

    def parse_module(self):
        assert self.lexer.token == Token.Module
        module_name = self.lexer.next()
        if module_name != Token.Identifier:
            log.fatal(f"invalid module name: {module_name} at {module_name}, "
                      f"ldx: {self.lexer.ldx}, cdx: {self.lexer.cdx}\n", ParserError)
        tok = self.lexer.peek()
        if tok == Token.Sharp:
            self.parse_parameter_declaration_list()
        elif tok == Token.LParen:
            self.parse_io_declaration_list()
        elif tok == Token.SemiColon:
            self.parse_items()
        else:
            log.fatal(f"invalid syntax: tok: {self.lexer.curTok.name}, "
                      f"ldx: {self.lexer.ldx}, cdx: {self.lexer.cdx}\n", ParserError)

    def parse_parameter_declaration_list(self):
        assert self.lexer.token == Token.Sharp

        assert self.lexer.next() == Token.LParen
        level = 1

        while level > 0:
            tok = self.lexer.token()
            if tok == Token.LParen:
                level += 1
            elif tok == Token.RParen:
                level -= 1
            elif tok == Token.Parameter:
                parameter_declaration = self.parse_parameter_declaration()

    def parse_parameter_declaration(self):
        assert self.lexer.token == Token.Parameter


    def parse_data_type(self):
        tok = self.lexer.next()
        if tok == Token.String:
            return StringDataType()
        elif tok == Token.Real:
            return NonIntegerDataType(NonIntegerType.real)
        elif tok == Token.ShortReal:
            return NonIntegerDataType(NonIntegerType.short_real)
        elif tok == Token.Byte or tok == Token.ShortInt or tok == Token.Int or tok == Token.Integer or\
             tok == Token.LongInt:
            return self.parse_integer_atom_data_type()
        elif tok == Token.Bit or tok == Token.Logic or tok == Token.Reg:
            return self.parse_integer_vector_data_type()
        else:
            return None

    def parse_integer_atom_data_type(self):
        assert self.lexer.token() == Token.Byte or \
               self.lexer.token() == Token.ShortInt or \
               self.lexer.token() == Token.Int or \
               self.lexer.token() == Token.Integer or \
               self.lexer.token() == Token.LongInt

        signing = None
        if self.lexer.peek() == Token.Signed:
            signing = "signed"
            self.lexer.next()
        elif self.lexer.peek() == Token.Unsigned:
            signing = "unsigned"
            self.lexer.next()

        if self.lexer.peek() == Token.LBracket:
            dimensions = self.parse_unpacked_dimensions()

    def parse_unpacked_dimensions(self):
        assert self.lexer.token() == Token.LBracket
        dimensions = []
        while self.lexer.token() == Token.LBracket:
            dimensions.append(self.parse_packed_dimension())
        return dimensions

    def parse_unpacked_dimension(self):
        assert self.lexer.token() == Token.LBracket













        




