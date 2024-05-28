from abc import abstractmethod, ABC
from enum import Enum, auto
from typing import List, Optional, Union


class ValueSet(Enum):
    bit = auto()
    logic = auto()


class IODirection(Enum):
    input = auto()
    output = auto()
    inout = auto()


class SignalType(Enum):
    wire = auto()
    var = auto()
    reg = auto()


class SyntaxNode:
    def __init__(self):
        self.ldx: int = -1
        self.cdx: int = -1

    def set_location(self, ldx: int, cdx: int):
        self.ldx = ldx
        self.cdx = cdx

    def get_str(self) -> str:
        return ""

    def __str__(self) -> str:
        return self.get_str()

    def simple_str(self) -> str:
        return self.get_str()


""" Literal """


class Literal(SyntaxNode):
    @abstractmethod
    def get_str(self) -> str:
        return ""


class Number(Literal):
    def __init__(self, number: str):
        super().__init__()
        self.number: str = number

    def get_str(self) -> str:
        return f"{{number: self.number}}"


class TimeLiteral(Literal):
    def __init__(self, time: str):
        super().__init__()
        self.time: str = time

    def get_str(self) -> str:
        return f"{{time: self.time}}"


class StringLiteral(Literal):
    def __init__(self, string: str):
        super().__init__()
        self.string: str = string

    def get_str(self) -> str:
        return f"{{string: self.string}}"


class Numeral(SyntaxNode):
    def __init__(self, numeral: str):
        super().__init__()
        self.numeral: str = numeral

    def get_str(self) -> str:
        return f"{{numeral: self.numeral}}"


class Identifier(SyntaxNode):
    def __init__(self, identifier: str):
        super().__init__()
        self.identifier: str = identifier

    def get_str(self) -> str:
        return f"{{id: self.identifier}}"

    def simple_str(self) -> str:
        return self.identifier


class IdentifierList(SyntaxNode):
    """
    a list of identifiers separated by comma
    """
    def __init__(self, identifiers: List[Identifier]):
        super().__init__()
        self.identifiers: List[Identifier] = identifiers

    def get_str(self) -> str:
        return f"[{', '.join([str(idt) for idt in self.identifiers])}]"

    def simple_str(self) -> str:
        return ', '.join([i.simple_str() for i in self.identifiers])


class Index(SyntaxNode):
    """
    a[x]
    """
    def __init__(self, src: SyntaxNode, idx: SyntaxNode):
        super().__init__()
        self.src: SyntaxNode = src
        self.idx: SyntaxNode = idx

    def get_str(self) -> str:
        return f"{{index: {self.src}[{self.idx}]}}"

    def simple_str(self) -> str:
        return f"{self.src}[{self.idx}]"


class Range(SyntaxNode):
    """
    a[x:y]
    """

    def __init__(self, src: SyntaxNode, ldx: SyntaxNode, rdx: SyntaxNode):
        super().__init__()
        self.src: SyntaxNode = src
        self.ldx: SyntaxNode = ldx
        self.rdx: SyntaxNode = rdx

    def get_str(self) -> str:
        return f"{{range: {self.src}[{self.ldx}:{self.rdx}]}}"

    def simple_str(self) -> str:
        return f"{self.src}[{self.ldx}:{self.rdx}]"


class Expression(SyntaxNode):
    ...  # todo


class ConstantExpression(SyntaxNode):
    ...  # todo


class PackedDimension(SyntaxNode):
    """
    packed_dimension ::= "[" constant_range "]"
    refer to IEEE 1800-2017 P1111
    """
    def __init__(self, ldx: ConstantExpression, rdx: ConstantExpression):
        super().__init__()
        self.ldx: ConstantExpression = ldx
        self.rdx: ConstantExpression = rdx

    def get_str(self) -> str:
        return f"{{packed_dimension: [{self.ldx}:{self.rdx}]}}"

    def simple_str(self) -> str:
        return f"[{self.ldx}:{self.rdx}]"


class UnPackedDimension(SyntaxNode):
    def __init__(self,
                 lr_dx: Optional[ConstantExpression, ConstantExpression],
                 dimension: ConstantExpression):

        super().__init__()
        self.ldx: Optional[ConstantExpression] = lr_dx[0]
        self.rdx: Optional[ConstantExpression] = lr_dx[1]
        self.dimension: Union[Range, ConstantExpression] = dimension

    def get_str(self) -> str:
        if self.ldx is not None and self.rdx is not None:
            return f"{{unpacked_dimension: [{self.ldx}:{self.rdx}]}}"
        else:
            return f"{{unpacked_dimension: [{self.dimension}]}}"

    def simple_str(self) -> str:
        if self.ldx is not None and self.rdx is not None:
            return f"[{self.ldx}:{self.rdx}]"
        else:
            return f"[{self.dimension}]"


class IntegerVectorType(Enum):
    """
    refer to IEEE 1800-2017 P1109
    """
    bit = auto()
    logic = auto()
    reg = auto()


class IntegerAtomType(Enum):
    """
    refer to IEEE 1800-2017 P1109
    """
    byte = auto()
    short_int = auto()
    int = auto()
    long_int = auto()
    integer = auto()


class NonIntegerType(Enum):
    """
    refer to IEEE 1800-2017 P1109
    """
    short_real = auto()
    real = auto()
    real_time = auto()


class Signing(Enum):
    """
    refer to IEEE 1800-2017 P1109
    """
    signed = auto()
    unsigned = auto()


class DataType(SyntaxNode):
    """
    data_type ::= integer_vector_type [signing] {packed_dimension}
                | integer_atom_type [signing]
                | non_integer_type
                | "string"
    """
    pass


class IntegerVectorDataType(DataType):
    def __init__(self,
                 integer_vector_type: IntegerVectorType,
                 signing: Optional[Signing],
                 dimensions: Optional[List[UnPackedDimension]]
                 ):

        super().__init__()
        self.integer_vector_type: IntegerVectorType = integer_vector_type
        self.signing: Optional[Signing] = signing
        self.dimensions: Optional[List[UnPackedDimension]] = dimensions

    def get_str(self) -> str:
        integer_vector_type = self.integer_vector_type.name
        signing = "" if self.signing is None else self.signing.name
        dimensions = "".join([dimension.simple_str() for dimension in self.dimensions])
        return f"{{integer_vector_type: {integer_vector_type} {signing} {dimensions}}}"

    def simple_str(self) -> str:
        integer_vector_type = self.integer_vector_type.name
        signing = "" if self.signing is None else self.signing.name
        dimensions = "".join([dimension.simple_str() for dimension in self.dimensions])
        return f"{integer_vector_type} {signing} {dimensions}"


class IntegerAtomDataType(DataType):
    def __init__(self,
                 integer_atom_type: IntegerAtomType,
                 signing: Optional[Signing]
                 ):

        super().__init__()
        self.integer_atom_type: IntegerAtomType = integer_atom_type
        self.signing: Optional[Signing] = signing

    def get_str(self) -> str:
        integer_atom_type = self.integer_atom_type.name
        signing = "" if self.signing is None else self.signing.name
        return f"{{integer_atom_type: {integer_atom_type} {signing}}}"

    def simple_str(self) -> str:
        integer_atom_type = self.integer_atom_type.name
        signing = "" if self.signing is None else self.signing.name
        return f"{integer_atom_type} {signing}"


class NonIntegerDataType(DataType):
    def __init__(self,
                 non_integer_type: NonIntegerType
                 ):

        super().__init__()
        self.non_integer_type: NonIntegerType = non_integer_type

    def get_str(self) -> str:
        non_integer_type = self.non_integer_type.name
        return f"{{non_integer_type: {non_integer_type}}}"

    def simple_str(self) -> str:
        non_integer_type = self.non_integer_type.name
        return f"{non_integer_type}"


class StringDataType(DataType):
    def get_str(self) -> str:
        return f"{{string}}"

    def simple_str(self) -> str:
        return "string"


class Lifetime(Enum):
    static = auto()
    automatic = auto()


class NetType(Enum):
    """
    refer to IEEE 1800-2017 P1110
    """
    u_wire = auto()
    wire = auto()


class NetPortType(SyntaxNode):
    """
    refer to IEEE 1800-2017 P1110
    """

    def __init__(self,
                 net_type: NetType,
                 data_type: Optional[DataType]):

        super().__init__()
        self.net_type: NetType = net_type
        self.data_type: Optional[DataType] = data_type

    def get_str(self):
        return f"{{net_port_type: {self.net_type.name} {self.data_type.simple_str()}}}"

    def simple_str(self) -> str:
        return f"{self.net_type.name} {self.data_type.simple_str()}"


class VarDataType(SyntaxNode):
    """
    refer to IEEE 1800-2017 P1110
    """

    def __init__(self,
                 data_type: DataType,
                 dimensions: Optional[List[UnPackedDimension]]):

        super().__init__()
        self.data_type: DataType = data_type
        self.dimensions: Optional[List[UnPackedDimension]] = dimensions

    def get_str(self) -> str:
        dimensions = "".join([dimension.simple_str() for dimension in self.dimensions])
        return f"{{var_data_type: {self.data_type.simple_str()} {dimensions}}}"

    def simple_str(self) -> str:
        dimensions = "".join([dimension.simple_str() for dimension in self.dimensions])
        return f"{self.data_type.simple_str()} {dimensions}"


class VarPortType(VarDataType):
    """
    refer to IEEE 1800-2017 P1110
    """
    def get_str(self) -> str:
        dimensions = "".join([dimension.simple_str() for dimension in self.dimensions])
        return f"{{var_port_type: {self.data_type.simple_str()} {dimensions}}}"

    def simple_str(self) -> str:
        dimensions = "".join([dimension.simple_str() for dimension in self.dimensions])
        return f"{self.data_type.simple_str()} {dimensions}"


class PortDeclaration(SyntaxNode):
    """
    refer to IEEE 1800-2017 P1108
    """
    pass


class ParamAssignment(SyntaxNode):
    """
    refer to IEEE 1800-2017 P1111
    """
    def __init__(self,
                 param_identifier: Identifier,
                 unpacked_dimensions: List[UnPackedDimension],
                 constant_param_expression: Expression
                 ):

        super().__init__()
        self.param_identifier: Identifier = param_identifier
        self.unpacked_dimensions: List[UnPackedDimension] = unpacked_dimensions
        self.constant_param_expression: Expression = constant_param_expression

    def get_str(self) -> str:
        dimensions = "".join([dimension.simple_str() for dimension in self.unpacked_dimensions])
        return f"{{param_assignment: {self.param_identifier.simple_str()} {dimensions} "\
               f"{self.constant_param_expression.simple_str()}}}"

    def simple_str(self) -> str:
        dimensions = "".join([dimension.simple_str() for dimension in self.unpacked_dimensions])
        return f"{self.param_identifier.simple_str()} {dimensions} "\
               f"{self.constant_param_expression.simple_str()}"


class LocalparamDeclaration(SyntaxNode):
    """
    refer to IEEE 1800-2017 P1108
    """
    def __init__(self,
                 data_type: Optional[DataType],
                 param_assignments: List[ParamAssignment]
                 ):

        super().__init__()
        self.data_type: Optional[DataType] = data_type
        self.param_assignments: List[ParamAssignment] = param_assignments

    def get_str(self) -> str:
        param_assignments = ", ".join([param_assignment.simple_str() for param_assignment in self.param_assignments])
        return f"{{localparam_declaration: {self.data_type.simple_str()} {param_assignments}}}"

    def simple_str(self) -> str:
        param_assignments = ", ".join([param_assignment.simple_str() for param_assignment in self.param_assignments])
        return f"{self.data_type.simple_str()} {param_assignments}"


class ParameterDeclaration(SyntaxNode):
    """
    refer to IEEE 1800-2017 P1108
    """
    def __init__(self,
                 data_type: Optional[DataType],
                 param_assignments: List[ParamAssignment]
                 ):

        super().__init__()
        self.data_type: Optional[DataType] = data_type
        self.param_assignments: List[ParamAssignment] = param_assignments

    def get_str(self) -> str:
        param_assignments = ", ".join([param_assignment.simple_str() for param_assignment in self.param_assignments])
        return f"{{parameter_declaration: {self.data_type.simple_str()} {param_assignments}}}"

    def simple_str(self) -> str:
        param_assignments = ", ".join([param_assignment.simple_str() for param_assignment in self.param_assignments])
        return f"{self.data_type.simple_str()} {param_assignments}"


class PortIdentifier(SyntaxNode):
    """
    refer to IEEE 1800-2017 P1111
    """
    pass


class InputPortDeclaration(PortDeclaration):
    def __init__(self,
                 port_type: Union[NetPortType, VarPortType],
                 port_identifiers: List[PortIdentifier]
                 ):

        super().__init__()
        self.port_type: Union[NetPortType, VarPortType] = port_type
        self.port_identifiers: List[PortIdentifier] = port_identifiers

    def get_str(self) -> str:
        port_identifiers = ", ".join([port_identifier.simple_str() for port_identifier in self.port_identifiers])
        return f"{{input_port_declaration: {self.port_type.simple_str()} {port_identifiers}}}"

    def simple_str(self) -> str:
        port_identifiers = ", ".join([port_identifier.simple_str() for port_identifier in self.port_identifiers])
        return f"{self.port_type.simple_str()} {port_identifiers}"


class OutputPortDeclaration(PortDeclaration):
    def __init__(self,
                 port_type: Union[NetPortType, VarPortType],
                 port_identifiers: List[PortIdentifier]
                 ):

        super().__init__()
        self.port_type: Union[NetPortType, VarPortType] = port_type
        self.port_identifiers: List[PortIdentifier] = port_identifiers

    def get_str(self) -> str:
        port_identifiers = ", ".join([port_identifier.simple_str() for port_identifier in self.port_identifiers])
        return f"{{output_port_declaration: {self.port_type.simple_str()} {port_identifiers}}}"

    def simple_str(self) -> str:
        port_identifiers = ", ".join([port_identifier.simple_str() for port_identifier in self.port_identifiers])
        return f"{self.port_type.simple_str()} {port_identifiers}"


class InoutPortDeclaration(PortDeclaration):
    def __init__(self,
                 net_port_type: NetPortType,
                 port_identifiers: List[PortIdentifier]
                 ):

        super().__init__()
        self.net_port_type: NetPortType = net_port_type
        self.port_identifiers: List[PortIdentifier] = port_identifiers

    def get_str(self) -> str:
        port_identifiers = ", ".join([port_identifier.simple_str() for port_identifier in self.port_identifiers])
        return f"{{inout_port_declaration: {self.net_port_type.simple_str()} {port_identifiers}}}"

    def simple_str(self) -> str:
        port_identifiers = ", ".join([port_identifier.simple_str() for port_identifier in self.port_identifiers])
        return f"{self.net_port_type.simple_str()} {port_identifiers}"


class ParameterDeclarationList(SyntaxNode):
    def __init__(self,
                 parameter_declarations: List[ParameterDeclaration]
                 ):

        super().__init__()
        self.parameter_declarations: List[ParameterDeclaration] = parameter_declarations

    def get_str(self) -> str:
        parameter_declarations = ", ".join([parameter_declaration.simple_str() for parameter_declaration in self.parameter_declarations])
        return f"{{parameter_declaration_list: {parameter_declarations}}}"

    def simple_str(self) -> str:
        parameter_declarations = ", ".join([parameter_declaration.simple_str() for parameter_declaration in self.parameter_declarations])
        return f"{parameter_declarations}"


class NonANSIPortDeclarationList(SyntaxNode):
    def __init__(self,
                 identifiers: List[Identifier]
                 ):

        super().__init__()
        self.identifiers: List[Identifier] = identifiers

    def get_str(self) -> str:
        identifiers = ", ".join([identifier.simple_str() for identifier in self.identifiers])
        return f"{{non_ansi_port_list: {identifiers}}}"


class ANSIPortDeclarationList(SyntaxNode):
    def __init__(self,
                 port_declarations: List[PortDeclaration]
                 ):

        super().__init__()
        self.port_declarations: List[PortDeclaration] = port_declarations

    def get_str(self) -> str:
        port_declarations = ", ".join([port_declaration.simple_str() for port_declaration in self.port_declarations])
        return f"{{ansi_port_list: {port_declarations}}}"

    def simple_str(self) -> str:
        port_declarations = ", ".join([port_declaration.simple_str() for port_declaration in self.port_declarations])
        return f"{port_declarations}"







