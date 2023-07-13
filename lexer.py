from enum import Enum, auto
from typing import Dict, List, Sequence, Set, Tuple, Union

import re


class UnterminatedStringLiteral(Exception):
    def __init__(self, ldx: int, cdx: int, string_literal: str):
        self.ldx = ldx
        self.cdx = cdx
        self.stringLiteral = string_literal


class UnterminatedBlockComment(Exception):
    def __init__(self, ldx: int, cdx: int, block_comment: List[str]):
        self.ldx = ldx
        self.cdx = cdx
        self.blockComment = block_comment


class InvalidLiteral(Exception):
    def __init__(self, ldx: int, cdx: int, literal: str):
        self.ldx = ldx
        self.cdx = cdx
        self.literal = literal


class UnidentifiableChar(Exception):
    def __init__(self, ldx: int, cdx: int, char: str):
        self.ldx = ldx
        self.cdx = cdx
        self.char = char

class UnexpectedBackSlash(Exception):
    def __init__(self, ldx: int, cdx: int):
        self.ldx = ldx
        self.cdx = cdx

class Token(Enum):
    Number = auto()
    StringLiteral = auto()
    Identifier = auto()
    Directive = auto()
    LineComment = auto()
    BlockComment = auto()

    Module = auto()
    EndModule = auto()
    Reg = auto()
    Wire = auto()
    Var = auto()
    Logic = auto()
    Bit = auto()
    Signed = auto()
    Unsigned = auto()

    Int = auto()
    Integer = auto()

    Assign = auto()
    Always = auto()
    AlwaysFF = auto()
    AlwaysComb = auto()
    AlwaysLatch = auto()
    Posedge = auto()
    Negedge = auto()

    Begin = auto()
    End = auto()
    Generate = auto()
    EndGenerate = auto()
    If = auto()
    Else = auto()
    Case = auto()
    EndCase = auto()

    BackQuote = auto()        # '
    Sharp = auto()            # #
    LParen = auto()           # (
    RParen = auto()           # )
    LBracket = auto()         # [
    RBracket = auto()         # ]
    LBrace = auto()           # {
    RBrace = auto()           # }
    Comma = auto()            # ,
    Colon = auto()            # :
    SemiColon = auto()        # ;
    At = auto()               # @
    Dot = auto()              # .
    SingleQuote = auto()      # '
    DoubleQuote = auto()      # "
    Equal = auto()            # =
    BackSlash = auto()        # \
    Dollar = auto()           # $
    QuestionMark = auto()     # ?

    OpAdd = auto()            # +
    OpSub = auto()            # -
    OpMul = auto()            # *
    OpDiv = auto()            # /
    OpMod = auto()            # %
    OpEqual = auto()          # ==
    OpUnequal = auto()        # !=
    OpGreaterThan = auto()    # >
    OpNotLessThan = auto()    # >=
    OpLessThan = auto()       # <
    OpNotGreaterThan = auto() # <=
    OpBitAnd = auto()         # &
    OpBitOr = auto()          # |
    OpBitXor = auto()         # ^
    OpBitNxor1 = auto()       # ~^
    OpBitNxor2 = auto()       # ^~
    OpBitInv = auto()         # ~
    OpAnd = auto()            # &&
    OpOr = auto()             # ||
    OpInv = auto()            # !
    OpLShift = auto()         # <<
    OpRShift = auto()         # >>
    OpALShift = auto()        # <<<
    OpARshift = auto()        # >>>

    DoubleBackQuote = auto()  # ''

    EOF = auto()

    def __eq__(self, other):
        return self.name == other.name and self.value == other.value


class Lexer:
    def __init__(self, context: List[str]):
        self.context: List[str] = context
        self.ldx: int = 0
        self.cdx: int = 0
        self.curTok: Token = None
        self.curTokPos: Tuple[int, int] = None
        self.number: str = ""
        self.stringLiteral: str = ""
        self.directive: str = ""
        self.identifier: str = ""
        self.lineComment: str = ""
        self.blockComment: List[str] = ""

    def get_next_tok(self) :
        while True:
            line = self.context[self.ldx]
            while True:
                char = line[self.cdx]

                if char == '\0':
                    self.curTokPos = self.ldx, self.cdx
                    self.curTok = Token.EOF
                    return self.curTok
                elif char == '\n':
                    self.curTokPos = self.ldx, self.cdx
                    self.ldx += 1
                    self.cdx = 0
                    break
                elif char == ' ' or char == '\t':
                    self.cdx += 1
                elif char == '#':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.Sharp
                    return self.curTok
                elif char == '(':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.LParen
                    return self.curTok
                elif char == ')':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.RParen
                    return self.curTok
                elif char == '[':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.LBracket
                    return self.curTok
                elif char == ']':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.RBracket
                    return self.curTok
                elif char == '{':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.LBrace
                    return self.curTok
                elif char == '}':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.RBrace
                    return self.curTok
                elif char == ',':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.Comma
                    return self.curTok
                elif char == ':':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.Colon
                    return self.curTok
                elif char == ';':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.SemiColon
                    return self.curTok
                elif char == '@':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.At
                    return self.curTok
                elif char == '.':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.Dot
                    return self.curTok
                elif char == '\'':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.SingleQuote
                    return self.curTok
                elif char == '$':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.Dollar
                    return self.curTok
                elif char == '?':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.QuestionMark
                    return self.curTok
                elif char == '+':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.OpAdd
                    return self.curTok
                elif char == '-':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.OpSub
                    return self.curTok
                elif char == '*':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.OpMul
                    return self.curTok
                elif char == '%':
                    self.curTokPos = self.ldx, self.cdx
                    self.cdx += 1
                    self.curTok = Token.OpMod
                    return self.curTok
                elif char == '=':
                    if line[self.cdx+1] == '=':
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 2
                        self.curTok = Token.OpEqual
                        return self.curTok
                    else:
                       self.curTokPos = self.ldx, self.cdx
                       self.cdx += 1
                       self.curTok = Token.Equal
                       return self.curTok
                elif char == '!':
                    if line[self.cdx+1] == '=':
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 2
                        self.curTok = Token.OpUnequal
                        return self.curTok
                    else:
                       self.curTokPos = self.ldx, self.cdx
                       self.cdx += 1
                       self.curTok = Token.OpInv
                       return self.curTok
                elif char == '&':
                    if line[self.cdx+1] == '&':
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 2
                        self.curTok = Token.OpAnd
                        return self.curTok
                    else:
                       self.curTokPos = self.ldx, self.cdx
                       self.cdx += 1
                       self.curTok = Token.OpBitAnd
                       return self.curTok
                elif char == '|':
                    if line[self.cdx+1] == '|':
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 2
                        self.curTok = Token.OpOr
                        return self.curTok
                    else:
                       self.curTokPos = self.ldx, self.cdx
                       self.cdx += 1
                       self.curTok = Token.OpBitOr
                       return self.curTok
                elif char == '~':
                    if line[self.cdx+1] == '^':
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 2
                        self.curTok = Token.OpBitNxor1
                        return self.curTok
                    else:
                       self.curTokPos = self.ldx, self.cdx
                       self.cdx += 1
                       self.curTok = Token.OpBitInv
                       return self.curTok
                elif char == '^':
                    if line[self.cdx+1] == '~':
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 2
                        self.curTok = Token.OpBitNxor2
                        return self.curTok
                    else:
                       self.curTokPos = self.ldx, self.cdx
                       self.cdx += 1
                       self.curTok = Token.OpBitXor
                       return self.curTok
                elif char == '>':
                    if line[self.cdx+1] == '>':
                        if line[self.cdx+2] == '>':
                            self.curTokPos = self.ldx, self.cdx
                            self.cdx += 3
                            self.curTok = Token.OpARshift
                            return self.curTok
                        else:
                            self.curTokPos = self.ldx, self.cdx                           
                            self.cdx += 2
                            self.curTok = Token.OpRshift
                            return self.curTok
                    elif line[self.cdx+1] == '=':
                            self.curTokPos = self.ldx, self.cdx
                            self.cdx += 2
                            self.curTok = Token.OpNotLessThan
                            return self.curTok
                    else:
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 1
                        self.curTok = Token.OpGreaterThan
                        return self.curTok
                elif char == '<':
                    if line[self.cdx+1] == '<':
                        if line[self.cdx+2] == '<':
                            self.curTokPos = self.ldx, self.cdx
                            self.cdx += 3
                            self.curTok = Token.OpALshift
                            return self.curTok
                        else:
                            self.curTokPos = self.ldx, self.cdx
                            self.cdx += 2
                            self.curTok = Token.OpLshift
                            return self.curTok
                    elif line[self.cdx+1] == '=':
                            self.curTokPos = self.ldx, self.cdx
                            self.cdx += 2
                            self.curTok = Token.OpNotGreaterThan
                            return self.curTok
                    else:
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 1
                        self.curTok = Token.OpLessThan
                        return self.curTok
                elif char == '`':
                    if line[self.cdx+1] == '`':
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 2
                        self.curTok = Token.DoubleBackQuote
                        return self.curTok
                    else:
                        chars = "" + char
                        ldx = self.ldx
                        cdx = self.cdx + 1
                        while True:
                            line = self.context[ldx]
                            while True:
                                char = line[cdx]
                                if char == '\0' or char == '\n' or char == ' ' or char == '\t':
                                    if chars == '`define' or \
                                       chars == '`undef' or \
                                       chars == '`timescale' or \
                                       chars == '`default_nettype' or \
                                       chars == '`ifdef' or \
                                       chars == '`ifndef' or \
                                       chars == '`else' or \
                                       chars == '`endif':
                                        self.curTokPos = self.ldx, self.cdx
                                        self.curTok = Token.Directive
                                        self.directive = chars[:-1]
                                        self.ldx = ldx
                                        self.cdx = cdx
                                        return self.curTok
                                    else:
                                        self.curTokPos = self.ldx, self.cdx
                                        self.curTok = Token.BackQuote
                                        self.ldx = ldx
                                        self.cdx = self.cdx + 1
                                        return self.curTok
                                else:
                                    chars += char
                                    cdx += 1
                                    if len(char) >= 17:
                                        self.curTokPos = self.ldx, self.cdx
                                        self.curTok = Token.BackQuote
                                        self.ldx = self.ldx
                                        self.cdx = self.cdx + 1
                                        return self.curTok
                elif char == '\"':
                    chars = "" + char
                    ldx = self.ldx
                    cdx = self.cdx + 1
                    while True:
                        line = self.context[ldx]
                        while True:
                            char = line[cdx]
                            if char == '\\':
                                if line[cdx+1] == '\n':
                                    ldx += 1
                                    cdx = 0
                                    break
                                if line[cdx+1] == '\"':
                                    cdx += 2
                                    chars += "\""
                                    continue
                                else:
                                    chars += char
                                    cdx += 1
                            elif char == '\0' or char == '\n' or char == ' ' or char == '\t':
                                self.curTokPos = self.ldx, self.cdx
                                self.curTok = Token.StringLiteral
                                self.ldx = ldx
                                self.cdx = cdx
                                raise UnterminatedStringLiteral(*self.curTokPos, chars)
                            elif char == '\"':
                                chars += char
                                cdx += 1
                                self.curTokPos = self.ldx, self.cdx
                                self.curTok = Token.StringLiteral
                                self.stringLiteral = chars
                                self.ldx = ldx
                                self.cdx = cdx
                                return self.curTok
                            else:
                                chars += char
                                cdx += 1
                elif char == '/':
                    if line[self.cdx+1] == '/':
                        cdx = self.cdx + 1
                        lineComment = "" + "//"
                        while True:
                            char = line[cdx]
                            if char == '\n' or char == '\0':
                                self.curTokPos = self.ldx, self.cdx
                                self.curTok = Token.LineComment
                                self.lineComment = lineComment
                                self.cdx = cdx
                                return self.curTok
                            else:
                                cdx += 1
                                self.lineComment += char
                    elif line[self.cdx+1] == '*':
                        ldx = self.ldx
                        cdx = self.cdx + 1
                        blockComment = []
                        lineComment = "/*"
                        while True:
                            line = self.context[ldx]
                            while True:
                                char = line[cdx]
                                if char == '\0':
                                    blockComment.append(lineComment)
                                    self.curTokPos = self.ldx, self.cdx
                                    self.curTok = Token.BlockComment
                                    self.blockComment = blockComment
                                    self.ldx = ldx
                                    self.cdx = cdx
                                    raise UnterminatedBlockComment(*self.curTokPos, blockComment)
                                elif char == '\n':
                                    lineComment += "\n"
                                    blockComment.append(lineComment)
                                    ldx += 1
                                    cdx = 0
                                    break
                                elif char == '*':
                                    if line[cdx+1] == '/':
                                        cdx += 2
                                        lineComment += "*/"
                                        blockComment.append(lineComment)
                                        self.curTokPos = self.ldx, self.cdx
                                        self.curTok = Token.BlockComment
                                        self.blockComment = blockComment
                                        self.ldx = ldx
                                        self.cdx = cdx
                                        return self.curTok
                                    else:
                                        cdx += 1
                                        lineComment += char
                                        continue
                                else:
                                    lineComment += char
                                    cdx += 1
                                    continue
                    else:
                        self.curTokPos = self.ldx, self.cdx
                        self.cdx += 1
                        self.curTok = Token.OpDiv
                        return self.curTok
                elif re.match("[0-9]", char): # the handling of '\' is different from verdi
                    literal = "" + char
                    ldx = self.ldx
                    cdx = self.cdx + 1
                    while True:
                        line = self.context[ldx]
                        while True:
                            char = line[cdx]
                            if char == '\\':
                                if line[cdx+1] == '\n':
                                    ldx += 1
                                    cdx = 0
                                    break
                                else:
                                    cdx += 1
                                    self.curTokPos = self.ldx, self.cdx
                                    self.curTok = Token.Number
                                    self.ldx = ldx
                                    self.cdx = cdx
                                    raise UnexpectedBackSlash(ldx, cdx-1)
                            elif char == '\'':
                                if not re.match('[bBoOhH]', line[cdx+1]):
                                    cdx += 1
                                    self.curTokPos = self.ldx, self.cdx
                                    self.curTok = Token.Number
                                    self.number = literal
                                    self.ldx = ldx
                                    self.cdx = cdx
                                    raise InvalidLiteral(*self.curTokPos, literal)
                                else: # xx'h
                                    literal += f"\'{line[cdx+1]}"
                                    cdx += 2
                                    while True:
                                        line = self.context[ldx]
                                        while True:
                                            char = line[cdx]
                                            if char == '\\':
                                                if line[cdx+1] == '\n':
                                                    ldx += 1
                                                    cdx = 0
                                                    break
                                                else:
                                                    cdx += 1
                                                    self.curTokPos = self.ldx, self.cdx
                                                    self.curTok = Token.Number
                                                    self.ldx = ldx
                                                    self.cdx = cdx
                                                    raise UnexpectedBackSlash(ldx, cdx-1)
                                            elif re.match("[_0-9a-fA-F]", char):
                                                cdx += 1
                                                literal += char
                                                continue
                                            else:
                                                self.curTokPos = self.ldx, self.cdx
                                                self.curTok = Token.Number
                                                self.number = literal
                                                self.ldx = ldx
                                                self.cdx = cdx
                                                return self.curTok
                            elif re.match("[_0-9]", char):
                                cdx += 1
                                literal += char
                                continue
                            else:
                                self.curTokPos = self.ldx, self.cdx
                                self.curTok = Token.Number
                                self.number = literal
                                self.ldx = ldx
                                self.cdx = cdx
                                return self.curTok
                elif re.match('[_a-zA-Z]', char):
                    identifier = "" + char
                    cdx = self.cdx + 1
                    while True:
                        char = line[cdx]
                        if re.match('[_0-9a-zA-Z]', char):
                            cdx += 1
                            identifier += char
                            continue
                        else:
                            self.curTokPos = self.ldx, self.cdx
                            self.curTok = Token.Identifier
                            self.identifier = identifier
                            for t in Token:
                                if identifier == t.name.lower():
                                    self.curTok = t
                            self.cdx = cdx
                            return self.curTok
                elif char == '\\':
                    if line[self.cdx+1] == '\n':
                        self.ldx += 1
                        self.cdx = 0
                        break
                    else:
                        self.curTokPos = self.ldx, self.cdx
                        self.curTok = Token.BackSlash
                        self.cdx += 1
                        raise UnexpectedBackSlash(*self.curTokPos)
                else:
                    raise UnidentifiableChar(self.ldx, self.cdx, char)

if __name__ == "__main__":
    context = []
    with open("./test.v", 'r', encoding="utf-8") as v:
        for line in v:
            context.append(line)
    if len(context) > 0:
        context[-1] = context[-1] + '\0'
    lexer = Lexer(context)
    token = lexer.get_next_tok()
    while token != Token.EOF:
        print(f"line {lexer.curTokPos[0]+1:<3}, column {lexer.curTokPos[1]+1:<3}, {token.name:<20}: ", end='')
        if token == Token.Identifier:
            print(f"{lexer.identifier}")
        elif token == Token.Number:
            print(f"{lexer.number}")
        else:
            print(f"")
        token = lexer.get_next_tok()












