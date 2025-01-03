import dataclasses

from lexer_ import Token
from node_ import SyntaxNode


@dataclasses.dataclass
class Expression(SyntaxNode):
    pass


@dataclasses.dataclass
class Identifier(Expression):
    identifier: Token



@dataclasses.dataclass
class Literal(Expression):
    literal: Token


@dataclasses.dataclass
class UnaryOperator(Expression):
    expr: Expression


@dataclasses.dataclass
class BinaryOperator(Expression):
    left: Expression
    right: Expression


@dataclasses.dataclass
class UnaryPlus(UnaryOperator):
    pass


@dataclasses.dataclass
class UnaryMinus(UnaryOperator):
    pass


@dataclasses.dataclass
class BitNot(UnaryOperator):
    pass


@dataclasses.dataclass
class ReducedAnd(UnaryOperator):
    pass


@dataclasses.dataclass
class ReducedOr(UnaryOperator):
    pass


@dataclasses.dataclass
class ReducedXor(UnaryOperator):
    pass


@dataclasses.dataclass
class LogicNot(UnaryOperator):
    pass


@dataclasses.dataclass
class SelfIncrement(UnaryOperator):
    pass


@dataclasses.dataclass
class SelfDecrement(UnaryOperator):
    pass


@dataclasses.dataclass
class BitAnd(BinaryOperator):
    pass


@dataclasses.dataclass
class BitOr(BinaryOperator):
    pass


@dataclasses.dataclass
class BitXor(BinaryOperator):
    pass


@dataclasses.dataclass
class LogicAnd(BinaryOperator):
    pass


@dataclasses.dataclass
class LogicOr(BinaryOperator):
    pass


@dataclasses.dataclass
class Add(BinaryOperator):
    pass


@dataclasses.dataclass
class Sub(BinaryOperator):
    pass


@dataclasses.dataclass
class Mul(BinaryOperator):
    pass


@dataclasses.dataclass
class Dvd(BinaryOperator):
    pass


@dataclasses.dataclass
class Mod(BinaryOperator):
    pass


@dataclasses.dataclass
class Pow(BinaryOperator):
    pass


@dataclasses.dataclass
class LogicLeftShift(BinaryOperator):
    pass


@dataclasses.dataclass
class LogicRightShift(BinaryOperator):
    pass


@dataclasses.dataclass
class ArithmeticLeftShift(BinaryOperator):
    pass


@dataclasses.dataclass
class ArithmeticRightShift(BinaryOperator):
    pass


@dataclasses.dataclass
class Equal(BinaryOperator):
    pass


@dataclasses.dataclass
class InEqual(BinaryOperator):
    pass


@dataclasses.dataclass
class GreaterThan(BinaryOperator):
    pass


@dataclasses.dataclass
class LessThan(BinaryOperator):
    pass


@dataclasses.dataclass
class GreaterThanEqual(BinaryOperator):
    pass


@dataclasses.dataclass
class LessThanEqual(BinaryOperator):
    pass


@dataclasses.dataclass
class CaseEqual(BinaryOperator):
    pass


@dataclasses.dataclass
class CaseInEqual(BinaryOperator):
    pass


@dataclasses.dataclass
class WildcardEqual(BinaryOperator):
    pass


@dataclasses.dataclass
class WildcardInEqual(BinaryOperator):
    pass


@dataclasses.dataclass
class Parenthesis(Expression):
    expression: Expression


@dataclasses.dataclass
class Slice(Expression):
    src: Expression
    left_idx: Expression
    right_idx: Expression


@dataclasses.dataclass
class Index(Expression):
    src: Expression
    idx: Expression


@dataclasses.dataclass
class ScopeResolution(BinaryOperator):
    pass


@dataclasses.dataclass
class MemberAccess(BinaryOperator):
    pass


@dataclasses.dataclass
class Conditional(Expression):
    condition: Expression
    true_expr: Expression
    false_expr: Expression


@dataclasses.dataclass
class Assignment(BinaryOperator):
    pass


@dataclasses.dataclass
class AddAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class SubAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class MulAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class DvdAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class ModAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class BitAndAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class BitOrAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class BitXorAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class LogicLeftShiftAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class LogicRightShiftAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class ArithmeticLeftShiftAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class ArithmeticRightShiftAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class NonBlockingAssignment(BinaryOperator):
    pass


@dataclasses.dataclass
class Concatenation(Expression):
    exprs: list[Expression]


@dataclasses.dataclass
class Repeat(Expression):
    expr: Expression
    times: Expression


