from expression import Expression


class NumericalLiteral(Expression):
    def __init__(self, literal: str):
        super().__init__()
        self.literal: str = literal

    def get_str(self) -> str:
        return self.literal
