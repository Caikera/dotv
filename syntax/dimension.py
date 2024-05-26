from typing import Union, Optional

from expression import Expression
from identifier import Identifier
from numerical_literal import NumericalLiteral
from syntax_node import SyntaxNode


class Dimension(SyntaxNode):
    def __init__(
            self,
            lb: Expression,
            rb: Expression
    ):
        self.lb: Expression = lb
        self.rb: Expression = rb

    def get_str(self) -> str:
        return ""
