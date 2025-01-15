import dataclasses

from lexer import Token, TokenKind
from syntax.expression import *
from parser import log, Context, ParserError, SourceInfo
from syntax.node import node_as_dict


def bp(token: Token, prefix: bool = False, assign_statement: bool = False) -> int:
    if token.kind_ in [TokenKind.LParen, TokenKind.RParen, TokenKind.LBracket,
                       TokenKind.ScopeResolution, TokenKind.Dot]:
        return 170
    elif token.kind_ in [TokenKind.Add, TokenKind.Sub, TokenKind.BitAnd, TokenKind.BitOr, TokenKind.BitXor] and prefix or \
         token.kind_ in [TokenKind.LogicNot, TokenKind.BitNot, TokenKind.SelfIncrement, TokenKind.SelfDecrement]:
        return 160
    elif token.kind_ in [TokenKind.Pow]:
        return 150
    elif token.kind_ in [TokenKind.Mul, TokenKind.Div, TokenKind.Mod]:
        return 140
    elif token.kind_ in [TokenKind.Add, TokenKind.Sub] and not prefix:
        return 130
    elif token.kind_ in [TokenKind.LogicLeftShift, TokenKind.LogicRightShift, TokenKind.ArithLeftShift, TokenKind.ArithRightShift]:
        return 120
    elif token.kind_ in [TokenKind.LessThan, TokenKind.GreaterThan, TokenKind.GreaterEqual, TokenKind.Inside] or \
         token.kind_ in [TokenKind.LessEqual] and not assign_statement:
        return 110
    elif token.kind_ in [TokenKind.Equal, TokenKind.InEqual, TokenKind.CaseEqual, TokenKind.CaseInEqual,
                         TokenKind.WildcardEqual, TokenKind.WildcardInEqual]:
        return 100
    elif token.kind_ in [TokenKind.BitAnd]:
        return 90
    elif token.kind_ in [TokenKind.BitXor]:
        return 80
    elif token.kind_ in [TokenKind.BitOr]:
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
    elif token.kind_ in [TokenKind.LBrace, TokenKind.SingleQuoteLBrace]:
        return 0
    elif token.kind_ in [TokenKind.Colon, TokenKind.Comma]:
        return 0
    else:
        return 0


led_prefix = [TokenKind.LBracket, TokenKind.ScopeResolution, TokenKind.Dot,
              TokenKind.Pow, TokenKind.Mul, TokenKind.Div, TokenKind.Mod,
              TokenKind.Add, TokenKind.Sub,
              TokenKind.LogicLeftShift, TokenKind.LogicRightShift,
              TokenKind.ArithLeftShift, TokenKind.ArithRightShift,
              TokenKind.LessThan, TokenKind.LessEqual, TokenKind.GreaterThan, TokenKind.GreaterEqual,
              TokenKind.Equal, TokenKind.InEqual, TokenKind.CaseEqual, TokenKind.CaseInEqual,
              TokenKind.WildcardEqual, TokenKind.WildcardInEqual,
              TokenKind.BitAnd,
              TokenKind.BitXor,
              TokenKind.BitOr,
              TokenKind.LogicAnd,
              TokenKind.LogicOr,
              TokenKind.QuestionMark,
              TokenKind.Assignment, TokenKind.AddAssignment, TokenKind.SubAssignment, TokenKind.MulAssignment,
              TokenKind.DivAssignment, TokenKind.ModAssignment, TokenKind.BitAndAssignment, TokenKind.BitXorAssignment,
              TokenKind.BitOrAssignment, TokenKind.LogicLeftShiftAssignment, TokenKind.LogicRightShiftAssignment]


def parse_expression(depth: int, ctx: Context, ctx_bp: int) -> Expression:
    token = ctx.current()
    if token is None or token.kind_ == TokenKind.EOF:
        log.fatal(f"no tokens to parse expression\n"
                  f"{ctx.src_info.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
        raise ParserError

    lhs = nud(ctx=ctx, token=token, depth=depth)
    while True:
        # log.hint(f"lhs: {lhs}, ctx_bp: {ctx_bp}\n")
        operator = ctx.current()
        if operator is None or operator.kind_ == TokenKind.EOF:
            break
        if operator.kind_ not in led_prefix:
            break
        obp = bp(token=operator, prefix=False, assign_statement=depth==0)
        # log.hint(f"operator: {operator}, bp: {obp}\n")
        if bp(token=operator, prefix=False, assign_statement=depth==0) <= ctx_bp:
            break
        lhs = led(ctx=ctx, operator=operator, lhs=lhs, depth=depth)
    return lhs


def parse_args(depth: int, ctx: Context, ctx_bp: int, stop_by: TokenKind) -> Args:
    token = ctx.current()
    ldx = token.ldx
    cdx = token.cdx

    tokens = []
    args = []
    while True:
        token = ctx.current()
        if token is None or token.kind_ == stop_by:
            break
        expr = parse_expression(depth=depth, ctx=ctx, ctx_bp=ctx_bp)
        tokens.extend(expr.tokens)
        args.append(expr)
        token = ctx.current()
        if token is None or token.kind_ != TokenKind.Comma and token.kind_ != stop_by:
            log.fatal(f"invalid syntax for argument list, expecting ',' or {stop_by}\n"
                      f"{ctx.src_info.error_context(ldx=ctx.near().ldx, cdx=ctx.near().cdx)}\n")
            raise ParserError
        if token.kind_ == TokenKind.Comma:
            ctx.consume()
        tokens.append(token)
    return Args(ldx=ldx, cdx=cdx, tokens=tokens,
                args=args)


def nud(ctx: Context, token: Token, depth: int = 0) -> Expression:
    if token.kind_ == TokenKind.Add:
        ctx.consume()
        src = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return UnaryPlus(ldx=token.ldx, cdx=token.cdx, tokens=[token] + src.tokens, expr=src)
    elif token.kind_ == TokenKind.Sub:
        ctx.consume()
        src = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return UnaryMinus(ldx=token.ldx, cdx=token.cdx, tokens=[token] + src.tokens, expr=src)
    elif token.kind_ == TokenKind.BitAnd:
        ctx.consume()
        src = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return ReducedAnd(ldx=token.ldx, cdx=token.cdx, tokens=[token] + src.tokens, expr=src)
    elif token.kind_ == TokenKind.BitOr:
        ctx.consume()
        src = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return ReducedOr(ldx=token.ldx, cdx=token.cdx, tokens=[token] + src.tokens, expr=src)
    elif token.kind_ == TokenKind.BitXor:
        ctx.consume()
        src = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return ReducedXor(ldx=token.ldx, cdx=token.cdx, tokens=[token] + src.tokens, expr=src)
    elif token.kind_ == TokenKind.BitNot:
        ctx.consume()
        src = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return BitNot(ldx=token.ldx, cdx=token.cdx, tokens=[token] + src.tokens, expr=src)
    elif token.kind_ == TokenKind.LogicNot:
        ctx.consume()
        src = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(token, prefix=True))
        return LogicNot(ldx=token.ldx, cdx=token.cdx, tokens=[token] + src.tokens, expr=src)
    elif token.kind_ == TokenKind.LParen:
        start_idx = ctx.token_idx
        ctx.consume()
        expr = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        end_idx = ctx.token_idx
        if token.kind_ != TokenKind.RParen:
            log.fatal(f"invalid syntax for expression, no matching ')' for '(',\n"
                      f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
        ctx.consume()
        return Parenthesis(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1], expression=expr)
    elif token.kind_ == TokenKind.SingleQuoteLBrace:
        start_idx = ctx.token_idx
        ldx = token.ldx
        cdx = token.cdx
        ctx.consume()
        args = parse_args(depth=depth + 1, ctx=ctx, ctx_bp=0, stop_by=TokenKind.RBrace)
        token = ctx.current()
        if token.kind_ != TokenKind.RBrace:
            log.fatal(f"invalid syntax for expression, no matching '}}' for '{{',\n"
                      f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
            raise ParserError
        end_idx = ctx.token_idx
        ctx.consume()
        return UnpackedArrayCat(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                args=args)

    elif token.kind_ == TokenKind.LBrace:
        start_idx = ctx.token_idx
        ldx = token.ldx
        cdx = token.cdx
        ctx.consume()

        first_expr = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        if token.kind_ == TokenKind.LBrace:
            ctx.consume()
            args = parse_args(depth=depth+1, ctx=ctx, ctx_bp=0, stop_by=TokenKind.RBrace)
            token = ctx.current()
            if token.kind_ != TokenKind.RBrace:
                log.fatal(f"invalid syntax for expression, no matching '}}' for '{{',\n"
                          f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            ctx.consume()
            token = ctx.current()
            if token.kind_ != TokenKind.RBrace:
                log.fatal(f"invalid syntax for expression, no matching '}}' for '{{',\n"
                          f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            end_idx = ctx.token_idx
            ctx.consume()
            return Repeat(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                          times=first_expr, expr=args)
        else:
            ctx.token_idx = start_idx + 1
            args = parse_args(depth=depth + 1, ctx=ctx, ctx_bp=0, stop_by=TokenKind.RBrace)
            token = ctx.current()
            if token.kind_ != TokenKind.RBrace:
                log.fatal(f"invalid syntax for expression, no matching '}}' for '{{',\n"
                          f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            end_idx = ctx.token_idx
            ctx.consume()
            return Concatenation(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                                 args=args)
    elif token.kind_ in [TokenKind.Literal, TokenKind.StringLiteral]:
        ctx.consume()
        return Literal(ldx=token.ldx, cdx=token.cdx, tokens=[token], literal=token)
    elif token.kind_ == TokenKind.Identifier:
        ctx.consume()
        identifier = Identifier(ldx=token.ldx, cdx=token.cdx, tokens=[token], identifier=token)
        token = ctx.current()
        if token is None:
            return identifier
        ldx = token.ldx
        cdx = token.cdx
        if token.kind_ == TokenKind.LParen:
            lparen = token
            ctx.consume()
            args = parse_args(depth=depth+1, ctx=ctx, ctx_bp=0, stop_by=TokenKind.RParen)
            token = ctx.current()
            if token.kind_ != TokenKind.RParen:
                log.fatal(f"syntax error, no matching ')' for '(' in expression,\n"
                          f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            ctx.consume()
            return FuncCall(ldx=ldx, cdx=cdx, tokens=identifier.tokens+[lparen]+args.tokens+[token],
                            identifier=identifier,
                            args=args)
        else:
            return identifier
    else:
        log.fatal(f"invalid token `{token}` for nud\n"
                  f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
        raise ParserError


def led(ctx: Context, operator: Token, lhs: Expression, depth: int) -> Expression:
    if operator.kind_ == TokenKind.LBracket:
        ctx.consume()
        expr_l = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        if token.kind_ == TokenKind.RBracket:
            ctx.consume()
            return Index(ldx=operator.ldx, cdx=operator.cdx,
                         tokens=lhs.tokens + [operator] + expr_l.tokens + [token],
                         src=lhs,
                         idx=expr_l)
        if token.kind_ != TokenKind.Colon:
            log.fatal(f"invalid syntax for expression, expecting ']' or ':',\n"
                      f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
        colon = token
        ctx.consume()
        expr_r = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        if token.kind_ != TokenKind.RBracket:
            log.fatal(f"invalid syntax for expression, expecting ']'\n"
                      f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
        ctx.consume()
        return Slice(ldx=operator.ldx, cdx=operator.cdx,
                     tokens=lhs.tokens + [operator] + expr_l.tokens + [colon] + expr_r.tokens + [token],
                     src=lhs,
                     left_idx=expr_l,
                     right_idx=expr_r)
    elif operator.kind_ == TokenKind.QuestionMark:
        ctx.consume()
        true_val = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=0)
        token = ctx.current()
        if token.kind_ != TokenKind.Colon:
            log.fatal(f"invalid syntax for expression, expecting ':'\n"
                      f"{ctx.src_info.error_context(token.ldx, token.cdx)}\n")
        colon = token
        ctx.consume()
        false_val = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=0)
        return Conditional(ldx=operator.ldx, cdx=operator.cdx,
                           tokens=lhs.tokens + [operator] + true_val.tokens + [colon] + false_val.tokens,
                           condition=lhs,
                           true_expr=true_val,
                           false_expr=false_val)
    elif operator.kind_ == TokenKind.ScopeResolution:
        ctx.consume()
        name = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return ScopeResolution(ldx=operator.ldx, cdx=operator.cdx,
                               tokens=lhs.tokens + [operator] + name.tokens,
                               left=lhs,
                               right=name)
    elif operator.kind_ == TokenKind.Dot:
        ctx.consume()
        name = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return MemberAccess(ldx=operator.ldx, cdx=operator.cdx,
                            tokens=lhs.tokens + [operator] + name.tokens,
                            left=lhs,
                            right=name)
    elif operator.kind_ == TokenKind.Pow:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return Pow(ldx=operator.ldx, cdx=operator.cdx,
                   tokens=lhs.tokens + [operator] + rop.tokens,
                   left=lhs,
                   right=rop)
    elif operator.kind_ == TokenKind.Mul:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return Mul(ldx=operator.ldx, cdx=operator.cdx,
                   tokens=lhs.tokens + [operator] + rop.tokens,
                   left=lhs,
                   right=rop)
    elif operator.kind_ == TokenKind.Div:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return Div(ldx=operator.ldx, cdx=operator.cdx,
                   tokens=lhs.tokens + [operator] + rop.tokens,
                   left=lhs,
                   right=rop)
    elif operator.kind_ == TokenKind.Mod:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return Mod(ldx=operator.ldx, cdx=operator.cdx,
                   tokens=lhs.tokens + [operator] + rop.tokens,
                   left=lhs,
                   right=rop)
    elif operator.kind_ == TokenKind.Add:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, prefix=False))
        return Add(ldx=operator.ldx, cdx=operator.cdx,
                   tokens=lhs.tokens + [operator] + rop.tokens,
                   left=lhs,
                   right=rop)
    elif operator.kind_ == TokenKind.Sub:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, prefix=False))
        return Sub(ldx=operator.ldx, cdx=operator.cdx,
                   tokens=lhs.tokens + [operator] + rop.tokens,
                   left=lhs,
                   right=rop)
    elif operator.kind_ == TokenKind.LogicLeftShift:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return LogicLeftShift(ldx=operator.ldx, cdx=operator.cdx,
                              tokens=lhs.tokens + [operator] + rop.tokens,
                              left=lhs,
                              right=rop)
    elif operator.kind_ == TokenKind.LogicRightShift:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return LogicRightShift(ldx=operator.ldx, cdx=operator.cdx,
                               tokens=lhs.tokens + [operator] + rop.tokens,
                               left=lhs,
                               right=rop)
    elif operator.kind_ == TokenKind.ArithLeftShift:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return ArithmeticLeftShift(ldx=operator.ldx, cdx=operator.cdx,
                                   tokens=lhs.tokens + [operator] + rop.tokens,
                                   left=lhs,
                                   right=rop)
    elif operator.kind_ == TokenKind.ArithRightShift:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return ArithmeticRightShift(ldx=operator.ldx, cdx=operator.cdx,
                                    tokens=lhs.tokens + [operator] + rop.tokens,
                                    left=lhs,
                                    right=rop)
    elif operator.kind_ == TokenKind.GreaterThan:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return GreaterThan(ldx=operator.ldx, cdx=operator.cdx,
                           tokens=lhs.tokens + [operator] + rop.tokens,
                           left=lhs,
                           right=rop)
    elif operator.kind_ == TokenKind.GreaterEqual:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return GreaterThanEqual(ldx=operator.ldx, cdx=operator.cdx,
                                tokens=lhs.tokens + [operator] + rop.tokens,
                                left=lhs,
                                right=rop)
    elif operator.kind_ == TokenKind.LessThan:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return LessThan(ldx=operator.ldx, cdx=operator.cdx,
                        tokens=lhs.tokens + [operator] + rop.tokens,
                        left=lhs,
                        right=rop)
    elif operator.kind_ == TokenKind.LessEqual:
        ctx.consume()
        if depth != 0:
            rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=False))
            return LessThanEqual(ldx=operator.ldx, cdx=operator.cdx,
                                 tokens=lhs.tokens + [operator] + rop.tokens,
                                 left=lhs,
                                 right=rop)
        else:
            delay = None
            token = ctx.current()
            if token.kind_ == TokenKind.SharpPat:
                delay = parse_delay(ctx=ctx)
            rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
            return NonBlockingAssignment(ldx=operator.ldx, cdx=operator.cdx,
                                         tokens=lhs.tokens + [operator] + rop.tokens,
                                         left=lhs,
                                         delay=delay,
                                         right=rop)
    elif operator.kind_ == TokenKind.Equal:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return Equal(ldx=operator.ldx, cdx=operator.cdx,
                     tokens=lhs.tokens + [operator] + rop.tokens,
                     left=lhs,
                     right=rop)
    elif operator.kind_ == TokenKind.InEqual:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return InEqual(ldx=operator.ldx, cdx=operator.cdx,
                       tokens=lhs.tokens + [operator] + rop.tokens,
                       left=lhs,
                       right=rop)
    elif operator.kind_ == TokenKind.CaseEqual:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return CaseEqual(ldx=operator.ldx, cdx=operator.cdx,
                         tokens=lhs.tokens + [operator] + rop.tokens,
                         left=lhs,
                         right=rop)
    elif operator.kind_ == TokenKind.CaseInEqual:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return CaseInEqual(ldx=operator.ldx, cdx=operator.cdx,
                           tokens=lhs.tokens + [operator] + rop.tokens,
                           left=lhs,
                           right=rop)
    elif operator.kind_ == TokenKind.WildcardEqual:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return WildcardEqual(ldx=operator.ldx, cdx=operator.cdx,
                             tokens=lhs.tokens + [operator] + rop.tokens,
                             left=lhs,
                             right=rop)
    elif operator.kind_ == TokenKind.WildcardInEqual:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator))
        return WildcardInEqual(ldx=operator.ldx, cdx=operator.cdx,
                               tokens=lhs.tokens + [operator] + rop.tokens,
                               left=lhs,
                               right=rop)
    elif operator.kind_ == TokenKind.BitAnd:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, prefix=False))
        return BitAnd(ldx=operator.ldx, cdx=operator.cdx,
                      tokens=lhs.tokens + [operator] + rop.tokens,
                      left=lhs,
                      right=rop)
    elif operator.kind_ == TokenKind.BitXor:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, prefix=False))
        return BitXor(ldx=operator.ldx, cdx=operator.cdx,
                      tokens=lhs.tokens + [operator] + rop.tokens,
                      left=lhs,
                      right=rop)
    elif operator.kind_ == TokenKind.BitOr:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, prefix=False))
        return BitOr(ldx=operator.ldx, cdx=operator.cdx,
                     tokens=lhs.tokens + [operator] + rop.tokens,
                     left=lhs,
                     right=rop)
    elif operator.kind_ == TokenKind.LogicAnd:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, prefix=False))
        return LogicAnd(ldx=operator.ldx, cdx=operator.cdx,
                        tokens=lhs.tokens + [operator] + rop.tokens,
                        left=lhs,
                        right=rop)
    elif operator.kind_ == TokenKind.LogicOr:
        ctx.consume()
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, prefix=False))
        return LogicOr(ldx=operator.ldx, cdx=operator.cdx,
                       tokens=lhs.tokens + [operator] + rop.tokens,
                       left=lhs,
                       right=rop)
    elif operator.kind_ == TokenKind.Assignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return Assignment(ldx=operator.ldx, cdx=operator.cdx,
                          tokens=lhs.tokens + [operator] + rop.tokens,
                          left=lhs,
                          delay=delay,
                          right=rop)
    elif operator.kind_ == TokenKind.AddAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return AddAssignment(ldx=operator.ldx, cdx=operator.cdx,
                             tokens=lhs.tokens + [operator] + rop.tokens,
                             left=lhs,
                             delay=delay,
                             right=rop)
    elif operator.kind_ == TokenKind.SubAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return SubAssignment(ldx=operator.ldx, cdx=operator.cdx,
                             tokens=lhs.tokens + [operator] + rop.tokens,
                             left=lhs,
                             delay=delay,
                             right=rop)
    elif operator.kind_ == TokenKind.MulAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return MulAssignment(ldx=operator.ldx, cdx=operator.cdx,
                             tokens=lhs.tokens + [operator] + rop.tokens,
                             left=lhs,
                             delay=delay,
                             right=rop)
    elif operator.kind_ == TokenKind.DivAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return DivAssignment(ldx=operator.ldx, cdx=operator.cdx,
                             tokens=lhs.tokens + [operator] + rop.tokens,
                             left=lhs,
                             delay=delay,
                             right=rop)
    elif operator.kind_ == TokenKind.ModAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return ModAssignment(ldx=operator.ldx, cdx=operator.cdx,
                             tokens=lhs.tokens + [operator] + rop.tokens,
                             left=lhs,
                             delay=delay,
                             right=rop)
    elif operator.kind_ == TokenKind.BitAndAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return BitAndAssignment(ldx=operator.ldx, cdx=operator.cdx,
                                tokens=lhs.tokens + [operator] + rop.tokens,
                                left=lhs,
                                delay=delay,
                                right=rop)
    elif operator.kind_ == TokenKind.BitOrAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return BitOrAssignment(ldx=operator.ldx, cdx=operator.cdx,
                               tokens=lhs.tokens + [operator] + rop.tokens,
                               left=lhs,
                               delay=delay,
                               right=rop)
    elif operator.kind_ == TokenKind.BitXorAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return BitXorAssignment(ldx=operator.ldx, cdx=operator.cdx,
                                tokens=lhs.tokens + [operator] + rop.tokens,
                                left=lhs,
                                delay=delay,
                                right=rop)
    elif operator.kind_ == TokenKind.LogicLeftShiftAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return LogicLeftShiftAssignment(ldx=operator.ldx, cdx=operator.cdx,
                                        tokens=lhs.tokens + [operator] + rop.tokens,
                                        left=lhs,
                                        delay=delay,
                                        right=rop)
    elif operator.kind_ == TokenKind.LogicRightShiftAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return LogicRightShiftAssignment(ldx=operator.ldx, cdx=operator.cdx,
                                         tokens=lhs.tokens + [operator] + rop.tokens,
                                         left=lhs,
                                         delay=delay,
                                         right=rop)
    elif operator.kind_ == TokenKind.ArithLeftShiftAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return ArithmeticLeftShiftAssignment(ldx=operator.ldx, cdx=operator.cdx,
                                             tokens=lhs.tokens + [operator] + rop.tokens,
                                             left=lhs,
                                             delay=delay,
                                             right=rop)
    elif operator.kind_ == TokenKind.ArithRightShiftAssignment:
        ctx.consume()
        delay = None
        token = ctx.current()
        if token.kind_ == TokenKind.SharpPat:
            delay = parse_delay(ctx=ctx)
        rop = parse_expression(depth=depth+1, ctx=ctx, ctx_bp=bp(operator, assign_statement=True))
        return ArithmeticRightShiftAssignment(ldx=operator.ldx, cdx=operator.cdx,
                                              tokens=lhs.tokens + [operator] + rop.tokens,
                                              left=lhs,
                                              delay=delay,
                                              right=rop)
    else:
        log.fatal(f"syntax error, invalid token `{operator}` as an operator\n"
                  f"{ctx.src_info.error_context(operator.ldx, operator.cdx)}\n")
        raise ParserError


def parse_delay(ctx: Context):
    token = ctx.current()
    ldx = token.ldx
    cdx = token.cdx
    start_idx = ctx.token_idx
    assert token.kind_ == TokenKind.SharpPat
    ctx.consume()

    duration = parse_expression(depth=1, ctx=ctx, ctx_bp=0)

    unit = None
    token = ctx.current()
    if token is not None and token.kind_ in [TokenKind.Second, TokenKind.MiniSecond, TokenKind.MicroSecond,
                                             TokenKind.NanoSecond, TokenKind.FemtoSecond]:
        unit = token
        ctx.consume()
    end_idx = ctx.token_idx - 1

    return Delay(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1], duration=duration, unit=unit)


if __name__ == "__main__":
    from lexer import Lexer

    import json
    import yaml

    def init(context: str, eol: str = '\n', delete_eof: bool = False, path: str = "") -> (Context, SourceInfo):
        tokens = Lexer(context, eol).tokens
        tokens = list(filter(lambda x: x.kind_ != TokenKind.LineComment and x.kind_ != TokenKind.BlockComment, tokens))
        ctx = Context(tokens, delete_eof=delete_eof)
        lines = context.split(eol)
        source_info = SourceInfo(lines, path)
        return ctx, source_info

    def re_arrange(data):
        if isinstance(data, dict):
            if 'tokens' in data:
                del data['tokens']
            if 'ldx' in data:
                del data['ldx']
            if 'ldx' in data:
                del data['ldx']
            if 'cdx' in data:
                del data['cdx']
            if 'kind' in data:
                del data['kind']
            if 'val' in data:
                del data['val']
            for key, value in data.items():
                data[key] = re_arrange(value)
        elif isinstance(data, list):
            for i in range(len(data)):
                data[i] = re_arrange(data[i])
        return data

    def get_yml_text(data, f):
        return yaml.dump(re_arrange(node_as_dict(data)), f)

    def test(verilog):
        ctx, source_info = init(context=verilog, delete_eof=True)
        expr = parse_expression(depth=0, ctx=ctx, ctx_bp=0)
        print(expr.tokens_str)
        return expr

    test("a + 1")
    test("a & b | c ^ d")
    test("!a && b || c && d")
    test("~x")
    test("^&|x")
    test("(x | y) & z")
    test("x | y && z")
    test("std::max")
    test("std::chrono::system_clock::now()")
    test("a.b")
    test("a.b.c")
    test("pp::z.zz")
    test("3'd7")
    test("x[3]")
    test("y[w-1:0]")
    test("x == 1 ? y : z")
    test("a << 1")
    test("a >> 1")
    test("a <<< b")
    test("a >>> b")
    test(
    """
    res = op_code == 4'd0 ? a + b
                   : 4'd1 ? a - b
                   : 4'd2 ? a * b
                   : 4'd3 ? a / b
                   : 4'd4 ? a % b
                   : 4'd5 ? a & b
                   : 4'd6 ? a | b
                   : 4'd7 ? a ^ b
                   : 4'd8 ? |a && |b
                   : 4'd9 ? &a || &b
                   : 4'd10 ? ~a
                   : 4'd11 ? ^b
                   : 4'd12 ? !b
                   : 4'd13 ? a < b
                   : 4'd14 ? {{8{a[7]}}, {a[6:0]}, a} <= b[w-1:w-5]
                   : $signed(8'b1111_1111)
    """
    )

    test(
    """
    res <= {8{op_code == 4'd0}} & ((a+b)*c) 
         | {8{op_code == 4'd1}} & (a+b/c)
         | {8{op_code == 4'd2}} & (+a/-b-b**c)
         | {8{op_code == 4'd3}} & (a << 7)
         | {8{op_code == 4'd4}} & (a >>> 7);
    """
    )
    _ = test("{x, y, z} = {a, b, c}")
    _ = test("{x, y, z} <= {a, b, c}")
    _ = test("res[7:3] = #1 a")
    _ = test("res[2:0] = #10us b")

    print("okay")

#     verilog = \
# """
#     a + 1
# """
#
#     ctx, source_info = init(context=verilog, delete_eof=True)
#     expr = parse_expression(depth=0, src_info=source_info, ctx=ctx, ctx_bp=0)
#     print(expr)
#
#
#     verilog = \
# """
#     a & aa & aaa + {4'b1111, 4'b0000, b, {c{x, y}}}
# """
#
#     ctx, source_info = init(context=verilog, delete_eof=True)
#     expr = parse_expression(depth=0, src_info=source_info, ctx=ctx, ctx_bp=0)
#     print(expr)
#
#     verilog = \
# """
#     x && y || a && b ? 1'b1 : custom
# """
#     ctx, source_info = init(context=verilog, delete_eof=True)
#     expr = parse_expression(depth=0, src_info=source_info, ctx=ctx, ctx_bp=0)
#     print(expr)

    verilog = \
"""
    res <= op_code == 4'b0001 ? {{8{a[7]}}, a[7:0]} :
                      4'b0010 ? $signed(aa) * ($signed(aa) + $signed(bb)) :
                      ~^&|x
"""
    ctx, source_info = init(context=verilog, delete_eof=True)
    expr = parse_expression(depth=0, ctx=ctx, ctx_bp=0)
    with open("test.yml", 'w', encoding="utf-8") as f:
        get_yml_text(expr, f)
