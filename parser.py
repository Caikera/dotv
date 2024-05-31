from typing import List, Tuple

import re

from lexer import Lexer, Token
from log import log
from syntax.syntax_node import *


identifier_pat = re.compile(r'[$a-zA-Z_][a-zA-Z_0-9]*')


unary_operator = ['+', '-', '&', '|', '^', '~', '!']

binary_opeartor = ['+', '-', '*', '/', '%',
                   '&', '|', '^', "&&", "||", "~^", "^~",
                   "==", "!=", ">", ">=", "<", "<=",
                   "<<", ">>", "<<<", ">>>"
                   ]


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

    """ 
    expressions:
        parenthesized ::= '(' expr ')'
        index_range ::= (identifier | parenthesized) {_index | _range}
            _index ::= '[' expr ']'
            _range ::= '[' expr : expr ']'
        member_access ::= member_access_prefix '.' member_access_suppix
            member_access_prefix ::= identifier | parenthesized | index_range
            member_access_suppix ::= member_access_prefix '.' member_access_suppix
        
        atom ::= identifier | literal | parenthesized | index_range | member_access
        level_0 ::= atom
        ============================================================
        unary_op ::= ('+' | '-' | '!' | '~' | '&' | '|' | '^') atom
        
        level_1 ::= level_0
                  | unary_op
        ============================================================  
        power ::= level_0 "**" level_1
        
        level_2 ::= level_1
                  | power
        ============================================================
        mul ::= level_2 '*' level_2
        div ::= level_2 '/' level_2
        mod ::= level_2 '%' level_2
        
        level_3 ::= level_2
                  | mul
                  | div
                  | mod
        ============================================================
        add ::= level_3 '+' level_3
        sub ::= level_3 '-' level_3
        
        level_4 ::= level_3
                  | add
                  | mod
        ============================================================
        shift ::= level_4 + "<<" | ">>" | "<<<" | ">>>" + level_4
        
        level_5 ::= level_4
                  | shift
        ============================================================
        compare_0 ::= level_5 "<" | "<=" | ">" | ">=" level_5
        
        level_6 ::= level_5
                  | compare_0
        ============================================================
        compare_1 ::= level_6 "==" | "!=" | "===" | "!==" | "==?" | "!=?" level_6
        
        level_7 ::= level_6
                  | compare_1
        ============================================================
        bin_bit_and ::= level_7 '&' level_7
        
        level_8 ::= level_7
                  | bin_bit_and
        ============================================================
        bin_bit_xor ::= level_8 '^' level_8
        
        level_9 ::= level_8
                  | bin_bit_xor
        ============================================================
        bin_bit_or  ::= level_9 '|' level_9
        
        level_10 ::= level_9
                   | bin_bit_or
        ============================================================
        bin_logic_and ::= level_10 '&&' level_10
        
        level_11 ::= level_10
                   | bin_logic_and
        ============================================================
        bin_logic_or ::= level_11 '&&' level_11
        
        level_12 ::= level_11
                   | bin_logic_or
        ============================================================
        ternary ::= level_12 '?' level_12 : level_12
        
        level_13 ::= level_12
                   | ternary
        ============================================================
        concatenation ::= '{' level_13 {',' level_13} '}'
        repeat ::= '{' level_13 concatenation '}'
    """

    def parse_expr(self) -> Expression:
        ...

    def parse_expr_parenthesized(self) -> Parenthesized:
        assert self.lexer.token == Token.LParen
        self.lexer.next()
        expr = self.parse_expr()
        assert self.lexer.token == Token.RParen
        self.lexer.next()
        e = Parenthesized(expr)
        return e

    def parse_index_or_range(self) -> List[Union[Expression, Tuple[Expression, Expression]]]:
        assert self.lexer.token == Token.LBracket
        self.lexer.next()
        irs = []
        while True:
            expr_0 = self.parse_expr()
            if self.lexer.token == Token.Colon:
                self.lexer.next()
                expr_1 = self.parse_expr()
                assert self.lexer.token == Token.RBracket
                irs.append((expr_0, expr_1))
            else:
                assert self.lexer.token == Token.RBracket
                self.lexer.next()
                irs.append(expr_0)
            self.lexer.next()
            if self.lexer.token != Token.LBracket:
                break
            else:
                self.lexer.next()
        return irs

    def try_parse_expr_index_range(self) -> Optional[IndexRange]:
        if not (self.lexer.token == IdentifierAsExpression or self.lexer.token == Token.LParen):
            return None

        if self.lexer.token == IdentifierAsExpression:
            src = self.try_parse_expr()
        elif self.lexer.token == Token.LParen:
            src = self.try_parse_expr_parenthesized()
        else:
            return None

        if self.lexer.token() != Token.LBracket:
            return None

        irs = self.parse_index_or_range()
        e = IndexRange(src, irs)
        return e



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













        




