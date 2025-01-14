import dataclasses
from typing import TYPE_CHECKING

from lexer_ import Token

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


is_first_tuple = True


def node_as_dict(obj):
    if isinstance(obj, SyntaxNode):
        d = {}
        d["_type_"] = obj.__class__.__name__
        d["_str_"] = obj.tokens_str
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
        global is_first_tuple
        if is_first_tuple:
            is_first_tuple = False
        print(f"===== tuple: {obj}")
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
class ArrayIdentifier(SyntaxNode):
    identifier: Token
    size: list[RangeNode | SizeNode]


@dataclasses.dataclass
class AnsiPortDefNode(SyntaxNode):
    direction: Token
    typ: Token
    data_type: DatatypeNode
    array_identifiers: list[ArrayIdentifier]


@dataclasses.dataclass
class NonAnsiPortDefNode(SyntaxNode):
    identifier: Token


@dataclasses.dataclass
class ParamDefNode(SyntaxNode):
    data_type: DatatypeNode
    identifier_array_val_pairs: list[(ArrayIdentifier, Expression)]


@dataclasses.dataclass
class ModuleBodyItemNode(SyntaxNode):
    pass


@dataclasses.dataclass
class ParamDefInBodyNode(ModuleBodyItemNode):
    data_type: DatatypeNode
    identifier_array_val_pairs: list[(ArrayIdentifier, Expression)]


@dataclasses.dataclass
class PortDefAndInitInBodyNode(ModuleBodyItemNode):
    direction: Token
    typ: Token | None
    data_type: Token | None
    identifier_array_val_pairs: list[(ArrayIdentifier, Expression)]


@dataclasses.dataclass
class LocalParamDefNode(ModuleBodyItemNode):
    data_type: DatatypeNode
    identifier_array_val_pairs: list[(ArrayIdentifier, Expression)]


@dataclasses.dataclass
class VariableDefAndInitNode(ModuleBodyItemNode):
    typ: Token | None
    data_type: Token | None
    identifier_array_val_pairs: list[(ArrayIdentifier, Expression)]


# @dataclasses.dataclass
# class VariableDefNode(ModuleBodyItemNode):
#     typ: Token | None
#     data_type: Token | None
#     identifier: Token
#
#
# @dataclasses.dataclass
# class VariableDefAndInitNode(ModuleBodyItemNode):
#     typ: Token | None
#     data_type: Token | None
#     identifier: Token
#     val: Expression



@dataclasses.dataclass
class GenvarDefNode(ModuleBodyItemNode):
    identifier: Token


@dataclasses.dataclass
class GenvarDefAndInitNode(ModuleBodyItemNode):
    identifier: Token
    val: Expression


@dataclasses.dataclass
class AssignNode(ModuleBodyItemNode):
    assignment: 'Expression'


@dataclasses.dataclass
class AlwaysBlockNode(ModuleBodyItemNode):
    always_typ: Token
    sensitivity_list: list[Token]
    body: 'ProcedureStatement'


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


@dataclasses.dataclass
class BeginEndBlock(ModuleBodyItemNode):
    name: Token | None
    body: list[ModuleBodyItemNode]


@dataclasses.dataclass
class ProcedureStatement(SyntaxNode):
    pass


@dataclasses.dataclass
class ProcedureBeginEndBlock(ProcedureStatement):
    name: Token | None
    body: list[ProcedureStatement]


@dataclasses.dataclass
class ForStatement(ProcedureStatement):
    data_type: DatatypeNode | None
    init: 'Expression | None'
    stop: 'Expression | None'
    step: 'Expression | None'
    body: ProcedureStatement


@dataclasses.dataclass
class IfElseBlock(ProcedureStatement):
    condition: 'Expression'
    if_body: ProcedureStatement
    else_body: ProcedureStatement | None


@dataclasses.dataclass
class CaseStatement(ProcedureStatement):
    expression: 'Expression'
    case_pairs: 'list[(Expression, ProcedureStatement)]'
    default_statement: ProcedureStatement | None


@dataclasses.dataclass
class DelayStatement(ProcedureStatement):
    delay: 'Delay'


@dataclasses.dataclass
class ProcedureAssignment(ProcedureStatement):
    assignment: 'Assignment'



@dataclasses.dataclass
class Generate(ModuleBodyItemNode):
    pass


@dataclasses.dataclass
class GenerateIf(Generate):
    condition: 'Expression'
    body: ModuleBodyItemNode


@dataclasses.dataclass
class GenerateFor(Generate):
    data_type: Token | None
    init: 'Expression | None'
    stop: 'Expression | None'
    step: 'Expression | None'
    body: ModuleBodyItemNode


@dataclasses.dataclass
class GenerateCase(Generate):
    expression: 'Expression'
    case_pairs: 'list[(Expression, ModuleBodyItemNode)]'
    default_statement: ModuleBodyItemNode


