from lexer_ import Token, TokenKind
from syntax.expression import *
from parser import log, Context, ParserError, SourceInfo


def bp(token: Token, prefix: bool = False, assign_statement: bool = False) -> int:
    if token.kind_ in [TokenKind.LParen, TokenKind.RParen, TokenKind.ScopeResolution, TokenKind.Dot]:
        return 160
    elif token.kind_ in [TokenKind.Add, TokenKind.Sub, TokenKind.BitAnd, TokenKind.BitOr, TokenKind.BitXor] and prefix or \
         token.kind_ in [TokenKind.LogicNot, TokenKind.BitNot, TokenKind.SelfIncrement, TokenKind.SelfDecrement]:
        return 150
    elif token.kind_ in [TokenKind.Pow]:
        return 140
    elif token.kind_ in [TokenKind.Mul, TokenKind.Div, TokenKind.Mod]:
        return 130
    elif token.kind_ in [TokenKind.Add, TokenKind.Sub] and not prefix:
        return 120
    elif token.kind_ in [TokenKind.LogicLeftShift, TokenKind.LogicRightShift, TokenKind.ArithLeftShiftAssignment, TokenKind.ArithRightShiftAssignment]:
        return 110
    elif token.kind_ in [TokenKind.LessThan, TokenKind.GreaterThan, TokenKind.GreaterEqual, TokenKind.Inside] or \
         token.kind_ in [TokenKind.LessEqual] and not assign_statement:
        return 100
    elif token.kind_ in [TokenKind.Equal, TokenKind.InEqual, TokenKind.CaseEqual, TokenKind.CaseInEqual,
                         TokenKind.WildcardEqual, TokenKind.WildcardInEqual]:
        return 90
    elif token.kind_ in [TokenKind.BitAnd]:
        return 80
    elif token.kind_ in [TokenKind.BitXor]:
        return 70
    elif token.kind_ in [TokenKind.LogicNot]:
        return 60
    elif token.kind_ in [TokenKind.LogicAnd]:
        return 50
    elif token.kind_ in [TokenKind.LogicOr]:
        return 40
    elif token.kind_ in [TokenKind.QuestionMark]:
        return 30
    elif token.kind_ in [TokenKind.Implication, TokenKind.Equivalence]:
        return 20
    elif token.kind_ in [TokenKind.Assignment, TokenKind.AddAssignment, TokenKind.SubAssignment, TokenKind.MulAssignment,
                         TokenKind.DivAssignment, TokenKind.ModAssignment, TokenKind.BitAndAssignment, TokenKind.BitXorAssignment,
                         TokenKind.BitOrAssignment, TokenKind.LogicLeftShiftAssignment, TokenKind.LogicRightShiftAssignment,
                         TokenKind.ArithLeftShiftAssignment, TokenKind.ArithRightShiftAssignment] or \
         token.kind_ in [TokenKind.LessEqual] and assign_statement:
        return 10
    elif token.kind_ in [TokenKind.LBrace]:
        return 0
    elif token.kind_ in [TokenKind.Colon, TokenKind.Comma]:
        return 0


def parse_expression(src_info: SourceInfo, ctx: Context, ctx_bp: int) -> Expression:
    pass


def nud(src_info: SourceInfo, ctx: Context, token: Token) -> Expression:
    if token.kind_ == TokenKind.Add:
        ctx.consume()
        src = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return UnaryPlus(ldx=token.rdx, cdx=token.cdx, tokens=[token]+src.tokens, expr=src)
    elif token.kind_ == TokenKind.Sub:
        ctx.consume()
        src = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return UnaryMinus(ldx=token.rdx, cdx=token.cdx, tokens=[token]+src.tokens, expr=src)
    elif token.kind_ == TokenKind.BitAnd:
        ctx.consume()
        src = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return ReducedAnd(ldx=token.rdx, cdx=token.cdx, tokens=[token]+src.tokens, expr=src)
    elif token.kind_ == TokenKind.BitOr:
        ctx.consume()
        src = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return ReducedOr(ldx=token.rdx, cdx=token.cdx, tokens=[token]+src.tokens, expr=src)
    elif token.kind_ == TokenKind.BitXor:
        ctx.consume()
        src = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return ReducedXor(ldx=token.rdx, cdx=token.cdx, tokens=[token]+src.tokens, expr=src)
    elif token.kind_ == TokenKind.BitNot:
        ctx.consume()
        src = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return BitNot(ldx=token.rdx, cdx=token.cdx, tokens=[token]+src.tokens, expr=src)
    elif token.kind_ == TokenKind.LogicNot:
        ctx.consume()
        src = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return LogicNot(ldx=token.rdx, cdx=token.cdx, tokens=[token] + src.tokens, expr=src)
    elif token.kind_ == TokenKind.LParen:
        ctx.consume()
        expr = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        if token.kind_ != TokenKind.RParen:
            log.fatal(f"invalid syntax for expression, no matching ')' for '(',\n"
                      f"{src_info.error_context(token.rdx, token.cdx)}\n")
        ctx.consume()
    elif token.kind_ == TokenKind.LBrace:
        pass
    elif token.kind_ in [TokenKind.Literal, TokenKind.StringLiteral]:
        ctx.consume()
        return Literal(ldx=token.rdx, cdx=token.cdx, tokens=[token], literal=token)
    elif token.kind_ in TokenKind.Identifier:
        ctx.consume()
        return Identifier(ldx=token.rdx, cdx=token.cdx, tokens=[token], identifier=token)
    else:
        log.fatal(f"invalid token `{token}` for nud\n")
        raise ParserError


def led(src_info: SourceInfo, ctx: Context, operator: Token, lhs: Expression) -> Expression:
    if operator.kind_ == TokenKind.LBracket:
        ctx.consume()
        expr_l = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        if token.kind_ == TokenKind.RBracket:
            ctx.consume()
            return Index(ldx=operator.rdx, cdx=operator.cdx,
                         tokens=lhs.tokens + [operator] + expr_l.tokens + [token],
                         src=lhs,
                         idx=expr_l)
        if token.kind_ != TokenKind.Colon:
            log.fatal(f"invalid syntax for expression, expecting ']' or ':',\n"
                      f"{src_info.error_context(token.rdx, token.cdx)}\n")
        colon = token
        ctx.consume()
        expr_r = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        if token.kind_ != TokenKind.RBracket:
            log.fatal(f"invalid syntax for expression, expecting ']'\n"
                      f"{src_info.error_context(token.rdx, token.cdx)}\n")
        return Slice(ldx=operator.rdx, cdx=operator.cdx,
                     tokens=lhs.tokens + [operator] + expr_l.tokens + [colon] + expr_r.tokens + [token],
                     src=lhs,
                     left_idx=expr_l,
                     right_idx=expr_r)
    elif operator.kind_ == TokenKind.QuestionMark:
        ctx.consume()
        true_val = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        if token.kind_ != TokenKind.Colon:
            log.fatal(f"invalid syntax for expression, expecting ':'\n"
                      f"{src_info.error_context(token.rdx, token.cdx)}\n")
        colon = token
        ctx.consume()
        false_val = parse_expression(src_info=src_info, ctx=ctx, ctx_bp=0)
        return Conditional(ldx=operator.rdx, cdx=operator.cdx,
                           tokens=lhs.tokens + [operator] + true_val.tokens + [colon] + false_val.tokens,
                           condition=lhs,
                           true_expr=true_val,
                           false_expr=false_val)




