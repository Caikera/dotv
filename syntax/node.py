from lexer_ import Token


class SyntaxNode:
    def __init__(self, ldx: int, cdx: int, tokens: list[Token] = None):
        self.ldx: int = ldx
        self.cdx: int = cdx
        self.tokens: list[Token] = [] if tokens is None else tokens

    def get_str(self) -> str:
        return f"\"{{{' '.join(map(lambda x: x.src, self.tokens))}\" , ldx: {self.ldx}, cdx: {self.cdx}}}"

    def __str__(self) -> str:
        return self.get_str()

    def __repr__(self) -> str:
        return self.get_str()


class ModuleNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 name: str,
                 para_list: 'list[ParamDefNode]',
                 port_list: 'list[AnsiPortDefNode] | NonAnsiPortDefsNode',
                 body):
        super().__init__(ldx, cdx, tokens)
        self.name: str = name
        self.parameter_define_node = para_list
        self.io_define_node = port_list
        self.body = body


class DatatypeNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 logic_or_bit: Token | None,
                 signing: Token | None,
                 range_: 'RangeNode | None',
                 inherent_data_type: Token | None):
        super().__init__(ldx, cdx, tokens)
        self.logic_or_bit: Token | None = logic_or_bit
        self.signing: Token | None = signing
        self.range_: RangeNode | None = range_
        self.inherent_data_type: Token | None = inherent_data_type


class RangeNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 left: list[Token],
                 right: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.left: list[Token] = left
        self.right: list[Token] = right


class IndexNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 index: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.index: list[Token] = index


SizeNode = IndexNode


class ArrayIdentifiersNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 identifier_size_s: list[(Token, list[RangeNode | SizeNode] | None)],):
        super().__init__(ldx, cdx, tokens)
        self.identifier_size_s: list[(Token, list[RangeNode | SizeNode] | None)] = identifier_size_s


class AnsiPortDefNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 direction: Token,
                 typ: Token,
                 data_type: DatatypeNode,
                 array_identifiers: ArrayIdentifiersNode):
        super().__init__(ldx, cdx, tokens)
        self.direction: Token = direction
        self.typ: Token = typ
        self.data_type: DatatypeNode = data_type
        self.array_identifiers: ArrayIdentifiersNode = array_identifiers


class NonAnsiPortDefNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 identifier: Token):
        super().__init__(ldx, cdx, tokens)
        self.identifier: Token = identifier


class ParamDefNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 data_type: DatatypeNode | None, identifier: Token, default: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.data_type: DatatypeNode | None = data_type
        self.identifier: Token = identifier
        self.default: list[Token] = default


class ModuleBodyItemNode(SyntaxNode):
    pass


class ParamDefInBodyNode(ModuleBodyItemNode):
    def __init__(self, param_def_node: ParamDefNode):
        super().__init__(param_def_node.ldx, param_def_node.cdx, param_def_node.tokens)
        self.param_def_node: ParamDefNode = param_def_node


class PortDefInBodyNode(ModuleBodyItemNode):
    def __init__(self, port_def_node: AnsiPortDefNode):
        super().__init__(port_def_node.ldx, port_def_node.cdx, port_def_node.tokens)
        self.port_def_node: AnsiPortDefNode = port_def_node


class LocalParamDefNode(ModuleBodyItemNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 data_type: DatatypeNode | None, identifier: Token, val: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.data_type: DatatypeNode | None = data_type
        self.identifier: Token = identifier
        self.val: list[Token] = val


class VariableDefNode(ModuleBodyItemNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 typ: Token | None, data_type: Token | None, identifier: Token):
        super().__init__(ldx, cdx, tokens)
        self.typ: Token | None = typ
        self.data_type: Token | None = data_type
        self.identifier: Token = identifier


class VariableDefAndInitNode(ModuleBodyItemNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 typ: Token | None, data_type: Token | None, identifier: Token, val: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.typ: Token | None = typ
        self.data_type: Token | None = data_type
        self.identifier: Token = identifier
        self.val: list[Token] = val


class AssignNode(ModuleBodyItemNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 lhs: list[Token], rhs: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.lhs: list[Token] = lhs
        self.rhs: list[Token] = rhs


class AlwaysBlockNode(ModuleBodyItemNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 always_typ: Token, sensitivity_list: list[Token], body: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.always_typ: Token = always_typ
        self.sensitivity_list: list[Token] = sensitivity_list
        self.body: list[Token] = body


class ParaSetNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 param_name: Token, param_value: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.param_name: Token = param_name
        self.param_value: list[Token] = param_value


class PortConnectNode(SyntaxNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 port_name: Token, port_value: list[Token]):
        super().__init__(ldx, cdx, tokens)
        self.port_name: Token = port_name
        self.port_value: list[Token] = port_value


class InstantiationNode(ModuleBodyItemNode):
    def __init__(self, ldx: int, cdx: int, tokens: list[Token],
                 prototype_identifier: Token,
                 para_set_list: list[ParaSetNode],
                 instance_identifier: Token,
                 port_connect_list: list[PortConnectNode]):
        super().__init__(ldx, cdx, tokens)
        self.prototype_identifier: Token = prototype_identifier
        self.para_set_list: list[ParaSetNode] = para_set_list
        self.instance_identifier: Token = instance_identifier
        self.port_connect_list: list[PortConnectNode] = port_connect_list
