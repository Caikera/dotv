from abc import abstractmethod

class SyntaxNode:
    def __init__(self):
        pass

    @abstractmethod
    def get_str(self) -> str:
        return ""
