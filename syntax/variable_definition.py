from typing import List, Literal, Optional, Tuple, Union

from value_set import ValueSet
from dimension import Dimension
from identifier import Identifier
from sv_built_in_type import SVBuiltInType
from syntax_node import SyntaxNode
from variable_type import VariableType

from exceptions import DataTypeError


class VariableDefinition(SyntaxNode):
    def __init__(
            self,
            variable_type: Optional[VariableType],
            value_set_or_data_type: Optional[Union[ValueSet, Identifier]],
            signed: Optional[bool],
            built_in_type: Optional[SVBuiltInType],
            packed_dimension: List[Dimension],
            identifier: Identifier,
            unpacked_dimension: List[Dimension]
    ):
        super().__init__()
        self.variable_type: Optional[VariableType] = variable_type
        self.value_set_or_data_type: Optional[Union[ValueSet, Identifier]] = value_set_or_data_type
        self.signed: Optional[bool] = signed
        self.built_in_type: Optional[SVBuiltInType] = built_in_type
        self.packed_dimension: List[Dimension] = packed_dimension
        self.identifier: Identifier = identifier
        self.unpacked_dimension: List[Dimension] = unpacked_dimension

    def get_str(self) -> str:
        variable_type_str = f"{self.variable_type.name} " if self.variable_type is not None else ''
        if self.value_set_or_data_type is None:
            value_set_or_data_type_str = ''
        elif isinstance(self.value_set_or_data_type, ValueSet):
            value_set_or_data_type_str = f"{self.value_set_or_data_type.name} "
        else:
            value_set_or_data_type_str = f"{self.value_set_or_data_type.get_str()} "
        if self.signed is None:
            signed_str = ''
        else:
            signed_str = "signed " if self.signed else "unsigned "
        if self.built_in_type is None:
            built_in_type_str = ''
        else:
            built_in_typ = f"{self.built_in_type.name} "
        return f"{variable_type_str}{value_set_or_data_type_str}{signed_str}{built_in_type_str}" \
               f"{''.join([d.get_str() for d in self.packed_dimension])} " \
               f"{self.identifier.get_str()}" \
               f"{''.join([d.get_str() for d in self.unpacked_dimension])}"
