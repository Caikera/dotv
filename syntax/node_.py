import dataclasses

from lexer_ import Token


@dataclasses.dataclass
class SyntaxNode:
    ldx: int
    cdx: int
    tokens: list[Token]

    def get_str(self) -> str:
        return f"\"{{{' '.join(map(lambda x: x.src, self.tokens))}\" , ldx: {self.ldx}, cdx: {self.cdx}}}"

    def __str__(self) -> str:
        return self.get_str()

    def __repr__(self) -> str:
        return self.get_str()


@dataclasses.dataclass
class ModuleNode(SyntaxNode):
    name: str
    para_list: 'list[ParamDefNode]'
    port_list: 'list[AnsiPortDefNode] | list[NonAnsiPortDefNode]'
    body: 'list[ModuleBodyItemNode]'


@dataclasses.dataclass
class DatatypeNode(SyntaxNode):
    logic_or_bit: Token | None
    signing: Token | None
    range_: 'RangeNode | None'
    inherent_data_type: Token | None


@dataclasses.dataclass
class RangeNode(SyntaxNode):
    left: list[Token]
    right: list[Token]


@dataclasses.dataclass
class IndexNode(SyntaxNode):
    index: list[Token]


SizeNode = IndexNode


@dataclasses.dataclass
class ArrayIdentifiersNode(SyntaxNode):
    identifier_size_s: list[(Token, list[RangeNode | SizeNode] | None)]


@dataclasses.dataclass
class AnsiPortDefNode(SyntaxNode):
    direction: Token
    typ: Token
    data_type: DatatypeNode
    array_identifiers: ArrayIdentifiersNode


@dataclasses.dataclass
class NonAnsiPortDefNode(SyntaxNode):
    identifier: Token


@dataclasses.dataclass
class ParamDefNode(SyntaxNode):
    data_type: DatatypeNode
    identifier: Token
    default: list[Token]


@dataclasses.dataclass
class ModuleBodyItemNode(SyntaxNode):
    pass


@dataclasses.dataclass
class ParamDefInBodyNode(ModuleBodyItemNode):
    param_def_node: ParamDefNode


@dataclasses.dataclass
class PortDefInBodyNode(ModuleBodyItemNode):
    port_def_node: AnsiPortDefNode


@dataclasses.dataclass
class LocalParamDefNode(ModuleBodyItemNode):
    data_type: DatatypeNode
    identifier: Token
    val: list[Token]


@dataclasses.dataclass
class VariableDefNode(ModuleBodyItemNode):
    typ: Token | None
    data_type: Token | None
    identifier: Token


@dataclasses.dataclass
class VariableDefAndInitNode(ModuleBodyItemNode):
    typ: Token | None
    data_type: Token | None
    identifier: Token
    val: list[Token]


@dataclasses.dataclass
class AssignNode(ModuleBodyItemNode):
    lhs: list[Token]
    rhs: list[Token]


@dataclasses.dataclass
class AlwaysBlockNode(ModuleBodyItemNode):
    always_typ: Token
    sensitivity_list: list[Token]
    body: list[Token]


@dataclasses.dataclass
class ParaSetNode(SyntaxNode):
    param_name: Token
    param_value: list[Token]


@dataclasses.dataclass
class PortConnectNode(SyntaxNode):
    port_name: Token
    port_value: list[Token]


@dataclasses.dataclass
class InstantiationNode(ModuleBodyItemNode):
    prototype_identifier: Token
    para_set_list: list[ParaSetNode]
    instance_identifier: Token
    port_connect_list: list[PortConnectNode]
