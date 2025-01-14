import dataclasses

from lexer_ import Token
from syntax.node_ import Expression, SyntaxNode


@dataclasses.dataclass
class Identifier(Expression):
    identifier: Token

    @property
    def tokens_str(self) -> str:
        return self.identifier.src


@dataclasses.dataclass
class Literal(Expression):
    literal: Token

    @property
    def tokens_str(self) -> str:
        return self.literal.src


@dataclasses.dataclass
class UnaryOperator(Expression):
    expr: Expression

    @property
    def symbol(self) -> str:
        return ''

    @property
    def tokens_str(self) -> str:
        return f"{self.symbol}『{self.expr.tokens_str}』"


@dataclasses.dataclass
class BinaryOperator(Expression):
    left: Expression
    right: Expression

    @property
    def symbol(self) -> str:
        return ''

    @property
    def tokens_str(self) -> str:
        return f"『{self.left.tokens_str}』{self.symbol}『{self.right.tokens_str}』"


@dataclasses.dataclass
class UnaryPlus(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '+'


@dataclasses.dataclass
class UnaryMinus(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '-'


@dataclasses.dataclass
class BitNot(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '~'


@dataclasses.dataclass
class ReducedAnd(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '&'


@dataclasses.dataclass
class ReducedOr(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '|'


@dataclasses.dataclass
class ReducedXor(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '^'


@dataclasses.dataclass
class LogicNot(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '!'


@dataclasses.dataclass
class SelfIncrement(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '++'

    @property
    def tokens_str(self) -> str:
        return f"『{self.expr.tokens_str}』{self.symbol}"


@dataclasses.dataclass
class SelfDecrement(UnaryOperator):
    @property
    def symbol(self) -> str:
        return '--'

    @property
    def tokens_str(self) -> str:
        return f"『{self.expr.tokens_str}』{self.symbol}"


@dataclasses.dataclass
class BitAnd(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '&'


@dataclasses.dataclass
class BitOr(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '|'


@dataclasses.dataclass
class BitXor(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '^'


@dataclasses.dataclass
class LogicAnd(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '&&'


@dataclasses.dataclass
class LogicOr(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '||'


@dataclasses.dataclass
class Add(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '+'


@dataclasses.dataclass
class Sub(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '-'


@dataclasses.dataclass
class Mul(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '*'


@dataclasses.dataclass
class Div(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '/'


@dataclasses.dataclass
class Mod(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '%'


@dataclasses.dataclass
class Pow(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '**'


@dataclasses.dataclass
class LogicLeftShift(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '<<'


@dataclasses.dataclass
class LogicRightShift(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '>>'


@dataclasses.dataclass
class ArithmeticLeftShift(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '<<<'


@dataclasses.dataclass
class ArithmeticRightShift(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '>>>'


@dataclasses.dataclass
class Equal(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '=='


@dataclasses.dataclass
class InEqual(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '!='


@dataclasses.dataclass
class GreaterThan(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '>'


@dataclasses.dataclass
class LessThan(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '<'


@dataclasses.dataclass
class GreaterThanEqual(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '>='


@dataclasses.dataclass
class LessThanEqual(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '<='


@dataclasses.dataclass
class CaseEqual(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '==='


@dataclasses.dataclass
class CaseInEqual(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '!=='


@dataclasses.dataclass
class WildcardEqual(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '==?'


@dataclasses.dataclass
class WildcardInEqual(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '!=?'


@dataclasses.dataclass
class Parenthesis(Expression):
    expression: Expression

    @property
    def tokens_str(self) -> str:
        return f"(『{self.expression.tokens_str}』)"


@dataclasses.dataclass
class Slice(Expression):
    src: Expression
    left_idx: Expression
    right_idx: Expression

    @property
    def tokens_str(self) -> str:
        return f"『{self.src.tokens_str}』[『{self.left_idx.tokens_str}』:『{self.right_idx.tokens_str}』]"


@dataclasses.dataclass
class Index(Expression):
    src: Expression
    idx: Expression

    @property
    def tokens_str(self) -> str:
        return f"『{self.src.tokens_str}』[『{self.idx.tokens_str}』]"


@dataclasses.dataclass
class ScopeResolution(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '::'


@dataclasses.dataclass
class MemberAccess(BinaryOperator):
    @property
    def symbol(self) -> str:
        return '.'


@dataclasses.dataclass
class Conditional(Expression):
    condition: Expression
    true_expr: Expression
    false_expr: Expression

    @property
    def tokens_str(self) -> str:
        return f"『{self.condition.tokens_str}』?"\
               f"『{self.true_expr.tokens_str}』:"\
               f"『{self.false_expr.tokens_str}』]"


@dataclasses.dataclass
class BaseAssignment(BinaryOperator):
    delay: 'Delay | None'

    @property
    def symbol(self) -> str:
        return '='

    @property
    def tokens_str(self) -> str:
        if self.delay is None:
            return f"『{self.left.tokens_str}』{self.symbol}『{self.right.tokens_str}』"
        else:
            return f"『{self.left.tokens_str}』{self.symbol}『{self.delay.tokens_str}』『{self.right.tokens_str}』"

@dataclasses.dataclass
class Assignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '='


@dataclasses.dataclass
class AddAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '+='


@dataclasses.dataclass
class SubAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '-='


@dataclasses.dataclass
class MulAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '*='


@dataclasses.dataclass
class DivAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '/='


@dataclasses.dataclass
class ModAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '%='


@dataclasses.dataclass
class BitAndAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '&='


@dataclasses.dataclass
class BitOrAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '|='


@dataclasses.dataclass
class BitXorAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '^='


@dataclasses.dataclass
class LogicLeftShiftAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '<<='


@dataclasses.dataclass
class LogicRightShiftAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '>>='


@dataclasses.dataclass
class ArithmeticLeftShiftAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '<<<='


@dataclasses.dataclass
class ArithmeticRightShiftAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '>>>='


@dataclasses.dataclass
class NonBlockingAssignment(BaseAssignment):
    @property
    def symbol(self) -> str:
        return '<='


@dataclasses.dataclass
class Concatenation(Expression):
    args: 'Args'

    @property
    def tokens_str(self) -> str:
        return f"{{『{self.args.tokens_str}』}}"


@dataclasses.dataclass
class Repeat(Expression):
    times: Expression
    expr: Expression

    @property
    def tokens_str(self) -> str:
        return f"{{『{self.times.tokens_str}』{{『{self.expr.tokens_str}』}}}}"


@dataclasses.dataclass
class Args(Expression):
    args: list[Expression]

    @property
    def tokens_str(self) -> str:
        return ', '.join(map(lambda x: f"『{x.tokens_str}』", self.args))


@dataclasses.dataclass
class FuncCall(Expression):
    identifier: Expression
    args: Args

    @property
    def tokens_str(self) -> str:
        return f"『{self.identifier.tokens_str}』(『{self.args.tokens_str}』)"


@dataclasses.dataclass
class Delay(SyntaxNode):
    duration: Expression
    unit: Token | None


@dataclasses.dataclass
class UnpackedArrayCat(Expression):
    args: Args

    @property
    def tokens_str(self) -> str:
        return f"{{『{self.args.tokens_str}』}}"





