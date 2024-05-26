from expression import Expression


class Identifier(Expression):
    def __init__(self, name: str):
        super().__init__()
        self.name = name

    def get_str(self) -> str:
        return self.name
