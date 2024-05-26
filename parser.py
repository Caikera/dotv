from typing import List
from lexer import Lexer, Token


class ParserError(Exception):
    def __init__(self, msg: str):
        self.msg = msg


class Parser:
    def __init__(self, context: List[str]):
        self.context: List[str] = context
        self.lexer: Lexer = Lexer(context)

    def parse_io_definition(self):
        direction = self.lexer.get_next_tok()
        if direction != Token.Input or direction != Token.Output or direction != Token.Inout:
            raise ParserError(f"expect io direction.")
        




