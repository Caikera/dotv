import dataclasses
from typing import TYPE_CHECKING

from lexer import Token

if TYPE_CHECKING:
    from syntax.expression import Assignment, Expression, Delay


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

    @property
    def tokens_str(self) -> str:
        return ' '.join(map(lambda x: x.src, self.tokens))

    @property
    def pos(self) -> (int, int):
        return self.ldx, self.cdx

    def as_dict(self) -> dict:
        return node_as_dict(self)


def node_as_dict(obj):
    if isinstance(obj, SyntaxNode):
        d = {"_type_": obj.__class__.__name__, "_str_": obj.tokens_str}
        for attr, value in obj.__dict__.items():
            d[attr] = node_as_dict(value)
        return d
    elif isinstance(obj, Token):
        d = {}
        for attr, value in obj.__dict__.items():
            d[attr] = node_as_dict(value)
        return d
    elif isinstance(obj, list):
        l = []
        for c in obj:
            l.append(node_as_dict(c))
        return l
    elif isinstance(obj, tuple):
        t = tuple()
        for c in obj:
            t = t + (node_as_dict(c),)
        return t
    elif isinstance(obj, set):
        s = set()
        for c in obj:
            s.add(node_as_dict(c))
        return s
    elif isinstance(obj, dict):
        d = {}
        for k, v in obj.items():
            d[node_as_dict(k)] = node_as_dict(v)
        return d
    else:
        return obj


@dataclasses.dataclass
class Expression(SyntaxNode):
    pass


@dataclasses.dataclass
class ModuleNode(SyntaxNode):
    name: str
    paras: 'list[ParamDefNode]'
    ports: 'list[AnsiPortDefNode] | list[NonAnsiPortDefNode]'
    body_items: 'list[ModuleBodyItemNode]'


@dataclasses.dataclass
class DataTypeNode(SyntaxNode):
    logic_or_bit: Token | None
    signing: Token | None
    range_: 'RangeNode | None'
    inherent_data_type: Token | None


@dataclasses.dataclass
class RangeNode(SyntaxNode):
    left: Expression
    right: Expression


@dataclasses.dataclass
class IndexNode(SyntaxNode):
    index: Expression


SizeNode = IndexNode


@dataclasses.dataclass
class ArrayIdentifierInitNode(SyntaxNode):
    identifier: Token
    size: list[RangeNode | SizeNode]


@dataclasses.dataclass
class AnsiPortDefNode(SyntaxNode):
    direction: Token
    typ: Token
    data_type: DataTypeNode
    array_identifiers: list[ArrayIdentifierInitNode]


@dataclasses.dataclass
class NonAnsiPortDefNode(SyntaxNode):
    identifier: Token


@dataclasses.dataclass
class ParamDefNode(SyntaxNode):
    data_type: DataTypeNode
    identifier_array_val_pairs: list[(ArrayIdentifierInitNode, Expression)]


@dataclasses.dataclass
class ModuleBodyItemNode(SyntaxNode):
    pass


@dataclasses.dataclass
class ParamDefInBodyNode(ModuleBodyItemNode):
    data_type: DataTypeNode
    identifier_array_val_pairs: list[(ArrayIdentifierInitNode, Expression)]


@dataclasses.dataclass
class PortDefAndInitInBodyNode(ModuleBodyItemNode):
    direction: Token
    typ: Token | None
    data_type: DataTypeNode | None
    identifier_array_val_pairs: list[(ArrayIdentifierInitNode, Expression)]


@dataclasses.dataclass
class LocalParamDefNode(ModuleBodyItemNode):
    data_type: DataTypeNode
    identifier_array_val_pairs: list[(ArrayIdentifierInitNode, Expression)]


@dataclasses.dataclass
class VariableDefInitNode(ModuleBodyItemNode):
    typ: Token | None
    data_type: Token | None
    identifier_array_val_pairs: list[(ArrayIdentifierInitNode, Expression)]


@dataclasses.dataclass
class GenvarDefNode(ModuleBodyItemNode):
    identifier: Token


@dataclasses.dataclass
class GenvarDefAndInitNode(ModuleBodyItemNode):
    identifier: Token
    val: Expression


@dataclasses.dataclass
class AssignNode(ModuleBodyItemNode):
    assignment: Expression


@dataclasses.dataclass
class AlwaysBlockNode(ModuleBodyItemNode):
    always_typ: Token
    sensitivity_list: list[Token]
    body: 'ProcedureStatementNode'


@dataclasses.dataclass
class InitialBlockNode(ModuleBodyItemNode):
    body: 'ProcedureStatementNode'


@dataclasses.dataclass
class ParaSetNode(SyntaxNode):
    param_name: Token
    param_value: Expression


@dataclasses.dataclass
class PortConnectNode(SyntaxNode):
    port_name: Token
    port_value: Expression


@dataclasses.dataclass
class InstantiationNode(ModuleBodyItemNode):
    prototype_identifier: Token
    para_sets: list[ParaSetNode]
    instance_identifier: Token
    port_connects: list[PortConnectNode]


@dataclasses.dataclass
class BeginEndNode(ModuleBodyItemNode):
    name: Token | None
    body_item: list[ModuleBodyItemNode]


@dataclasses.dataclass
class ProcedureStatementNode(SyntaxNode):
    pass


@dataclasses.dataclass
class ProcedureBeginEndBlockNode(ProcedureStatementNode):
    name: Token | None
    body: list[ProcedureStatementNode]


@dataclasses.dataclass
class ForStatementNode(ProcedureStatementNode):
    data_type: DataTypeNode | None
    init: Expression | None
    stop: Expression | None
    step: Expression | None
    body: ProcedureStatementNode


@dataclasses.dataclass
class IfElseBlock(ProcedureStatementNode):
    condition: Expression
    if_body: ProcedureStatementNode
    else_body: ProcedureStatementNode | None


@dataclasses.dataclass
class CaseStatementNode(ProcedureStatementNode):
    expression: Expression
    case_pairs: list[(Expression, ProcedureStatementNode)]
    default_statement: ProcedureStatementNode | None


@dataclasses.dataclass
class DelayStatementNode(ProcedureStatementNode):
    delay: 'Delay'


@dataclasses.dataclass
class ProcedureAssignmentNode(ProcedureStatementNode):
    assignment: 'Assignment'


@dataclasses.dataclass
class GenerateNode(ModuleBodyItemNode):
    pass


@dataclasses.dataclass
class GenerateNodeIf(GenerateNode):
    condition: Expression
    body: ModuleBodyItemNode


@dataclasses.dataclass
class GenerateNodeFor(GenerateNode):
    genvar_data_type: Token | None
    init: Expression | None
    stop: Expression | None
    step: Expression | None
    body: ModuleBodyItemNode


@dataclasses.dataclass
class GenerateNodeCase(GenerateNode):
    expression: Expression
    case_pairs: list[(Expression, ModuleBodyItemNode)]
    default_statement: ModuleBodyItemNode


@dataclasses.dataclass
class EmptyProcedureStatementNode(ProcedureStatementNode):
    pass


@dataclasses.dataclass
class EmptyModuleBodyItem(ModuleBodyItemNode):
    pass


@dataclasses.dataclass
class PreCompileDirectiveNode(SyntaxNode):
    pass


@dataclasses.dataclass
class PreCompileDirectiveInsideBodyNode(ModuleBodyItemNode):
    directive: PreCompileDirectiveNode
