from syntax_node import SyntaxNode
from io_direction import IODirection
from variable_definition import VariableDefinition


class IOVariableDefinition(SyntaxNode):
    def __init__(
            self,
            direction: IODirection,
            variable_definition: VariableDefinition
    ):
        super().__init__()
        self.direction: IODirection = direction
        self.variable_definition: VariableDefinition = variable_definition

    def get_str(self) -> str:
        return f"{self.direction.name.lower()} {self.variable_definition.get_str()}"
