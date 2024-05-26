from abc import abstractmethod

from syntax_node import SyntaxNode


class Expression(SyntaxNode):
    def __init__(self):
        super().__init__()

    @abstractmethod
    def get_str(self):
        return ""

    @property
    def can_be_lhs(self):
        return False
