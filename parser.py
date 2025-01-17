import re
from typing import TYPE_CHECKING

from lexer import Lexer, Token, TokenKind
from log import log
from syntax.node import *

from syntax.expression import *


class ParserError(Exception):
    pass


class ExpectedTokenNotFound(ParserError):
    pass


class SourceInfo:
    def __init__(self, lines: list[str], path: str):
        self.lines: list[str] = lines
        self.path: str = path

    def error_context(self, ldx: int, cdx: int):
        msg = [f"line: {ldx+1}, column: {cdx+1}, file: {self.path}\n"]
        if ldx > 1:
            msg.append(f"    {self.lines[ldx-2]}\n")
        if ldx > 0:
            msg.append(f"    {self.lines[ldx-1]}\n")
        msg.append(f"    {self.lines[ldx]}\n")
        msg.append(f"    {' '*cdx}^\n")
        if ldx < len(self.lines) - 1:
            msg.append(f"    {self.lines[ldx+1]}\n")
        if ldx < len(self.lines) - 2:
            msg.append(f"    {self.lines[ldx+2]}\n")
        return "".join(msg)


class Context:
    def __init__(self, tokens: list[Token], delete_eof: bool = False, src_info: SourceInfo | None = None):
        if delete_eof:
            tokens = list(filter(lambda x: x.kind_ != TokenKind.EOF, tokens))
        self.tokens: list[Token] = tokens
        self.token_idx: int = 0
        self.src_info: SourceInfo | None = src_info

    def current(self) -> Token | None:
        if self.token_idx >= len(self.tokens):
            return None
        return self.tokens[self.token_idx]

    def current_nn(self) -> Token:
        current = self.current()
        if current is None:
            log.fatal(f"token expected, but got None. token_idx: {self.token_idx}")
            raise ParserError
        return current

    def peek(self) -> Token | None:
        if self.token_idx+1 >= len(self.tokens):
            return None
        return self.tokens[self.token_idx+1]

    def peek_nn(self) -> Token:
        peek = self.peek()
        if peek is None:
            log.fatal(f"token expected, but got None. token_idx: {self.token_idx}")
            raise ParserError
        return peek

    def last(self) -> Token | None:
        if self.token_idx == 0:
            return None
        return self.tokens[self.token_idx-1]

    def near(self) -> Token:
        current = self.current()
        if current is not None:
            return current
        last = self.last()
        if last is not None:
            return last
        assert 0

    def consume(self):
        self.token_idx += 1

    def consume_until(self, token_kind: TokenKind | list[TokenKind], error_info: str, just_try: bool = False):
        while True:
            token = self.current()
            if token is None or token.kind_ == TokenKind.EOF:
                if just_try:
                    return False
                log.fatal(error_info)
                raise ExpectedTokenNotFound
            elif isinstance(token.kind_, TokenKind) and token.kind_ == token_kind or \
                 isinstance(token.kind_, list) and token.kind_ in token_kind:
                return True
            else:
                self.consume()

    def consume_until_matching_pair(self, left: TokenKind | list[TokenKind], right: TokenKind | list[TokenKind],
                                    error_info: str, just_try: bool = False):
        depth = 0
        assert self.current().kind_ == left
        while True:
            token = self.current()
            if token is None or token.kind_ == TokenKind.EOF:
                if just_try:
                    return False
                log.fatal(error_info)
                raise ExpectedTokenNotFound
            elif isinstance(left, TokenKind) and token.kind_ == left or \
                 isinstance(left, list) and token.kind_ in left:
                depth += 1
            elif isinstance(left, TokenKind) and token.kind_ == right or \
                 isinstance(left, list) and token.kind_ in right:
                depth -= 1
            if depth == 0:
                return True
            self.consume()

    def consume_until_at_depth(self,
                               left: TokenKind,
                               right: TokenKind,
                               expect: TokenKind,
                               expected_depth: int,
                               error_info: str,
                               just_try: bool = False):

        depth = 0
        assert self.current().kind_ == left
        while True:
            token = self.current()
            if token is None or token.kind_ == TokenKind.EOF:
                if just_try:
                    return False
                log.fatal(error_info)
                raise ExpectedTokenNotFound
            elif token.kind_ == left:
                depth += 1
            elif token.kind_ == right:
                depth -= 1
            if depth == 0:
                if just_try:
                    return False
                log.fatal(error_info)
                raise ExpectedTokenNotFound
            if depth == expected_depth and token.kind_ == expect:
                return True
            self.consume()


class Parser:
    def __init__(self, context: str, eol: str = '\n', delete_eof: bool = False, path: str = "",
                 parse_body: bool = True):
        tokens = Lexer(context, eol).tokens
        tokens = list(filter(lambda x: x.kind_ != TokenKind.LineComment and x.kind_ != TokenKind.BlockComment, tokens))
        lines = context.split(eol)
        src_info = SourceInfo(lines, path)
        self.ctx = Context(src_info=src_info, tokens=tokens, delete_eof=delete_eof)
        self.parse_body = parse_body

    def error_context(self, ldx: int, cdx: int):
        return self.ctx.src_info.error_context(ldx, cdx)

    def parse(self) -> list[SyntaxNode]:
        nodes = []
        while True:
            token = self.ctx.current()
            if token is None or token.kind_ == TokenKind.EOF:
                break
            elif token.kind_ == TokenKind.Directive:
                node = self.parse_pre_compile_directive_locally(ctx=self.ctx)
            elif token.kind_ == TokenKind.Module:
                node = self.parse_module_locally(ctx=self.ctx)
            else:
                log.fatal(f"token `{token.src}` is not supported yet:\n"
                          f"{self.ctx.src_info.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            nodes.append(node)
        return nodes

    def parse_module_locally(self, ctx: Context) -> ModuleNode:
        token = ctx.current()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Module
        ldx, cdx = token.pos

        ctx.consume()
        ctx.consume_until(
            token_kind=TokenKind.EndModule,
            error_info=f"invalid syntax, module definition is not closed by 'endmodule',\n"
                       f"{ctx.src_info.error_context(ldx, cdx)}\n"
        )
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_module_detail(sub_ctx=Context(src_info=self.ctx.src_info,
                                                        tokens=ctx.tokens[start_idx:end_idx+1]))

    def parse_module_detail(self, sub_ctx: Context):
        token = sub_ctx.current_nn()
        ldx, cdx = token.pos

        assert token.kind_ == TokenKind.Module

        name = None
        para_list = None
        port_list = None
        body = None

        sub_ctx.consume()
        token = sub_ctx.current_nn()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax, module name is not specified,\n"
                      f"{self.error_context(ldx, cdx)}\n")
            raise ParserError
        name = token.val

        sub_ctx.consume()
        token = sub_ctx.current_nn()

        if token.kind_ == TokenKind.SharpPat:
            sub_ctx.consume()
            token = sub_ctx.current_nn()
            if token.kind_ != TokenKind.LParen:
                log.fatal(f"invalid syntax, '(' is expected after '#' to define parameter\n"
                          f"{self.error_context(ldx, cdx)}\n")
                raise ParserError

            start_idx = sub_ctx.token_idx
            lparen_ldx = token.ldx
            lparen_cdx = token.cdx
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.LParen, right=TokenKind.RParen,
                error_info=f"invalid syntax, for the parameter list block, '(' is not closed by ')',\n"
                           f"{self.error_context(lparen_ldx, lparen_cdx)}\n"
            )
            end_idx = sub_ctx.token_idx
            sub_ctx.consume()
            para_list = self.parse_parameter_list(sub_ctx=Context(src_info=self.ctx.src_info,
                                                                  tokens=sub_ctx.tokens[start_idx:end_idx+1]))

        token = sub_ctx.current_nn()
        if token.kind_ == TokenKind.LParen:
            start_idx = sub_ctx.token_idx
            lparen_ldx = token.ldx
            lparan_cdx = token.cdx
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.LParen, right=TokenKind.RParen,
                error_info=f"invalid syntax, for the port list block, '(' is not closed by ')'\n"
                           f"{self.error_context(lparen_ldx, lparan_cdx)}\n"
            )
            end_idx = sub_ctx.token_idx
            sub_ctx.consume()
            port_list = self.parse_port_list(sub_ctx=Context(src_info=self.ctx.src_info,
                                                             tokens=sub_ctx.tokens[start_idx:end_idx+1]))

        token = sub_ctx.current_nn()
        if token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax, expected ';'\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        start_idx = sub_ctx.token_idx

        if self.parse_body:
            body = self.parse_module_body(sub_ctx=Context(src_info=self.ctx.src_info, tokens=sub_ctx.tokens[start_idx:]))
        else:
            body = []

        return ModuleNode(ldx=ldx, cdx=cdx, tokens=sub_ctx.tokens,
                          name=name, paras=para_list, ports=port_list, body_items=body)

    def parse_parameter_list(self, sub_ctx: Context) -> list[ParamDefNode]:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.LParen
        sub_ctx.consume()

        param_def_s = []
        while True:
            token = sub_ctx.current_nn()
            if token.kind_ == TokenKind.RParen:
                sub_ctx.consume()
                break
            if token.kind_ != TokenKind.Parameter:
                log.fatal(f"invalid syntax, 'parameter' is expected,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            param_def = self.parse_parameter_def_locally(ctx=sub_ctx)
            param_def_s.append(param_def)

            token = sub_ctx.current_nn()
            if token.kind_ == TokenKind.RParen:
                sub_ctx.consume()
                break
            if token.kind_ != TokenKind.Comma:
                log.fatal(f"invalid syntax, ',' or ')' is expected after parameter definition,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            sub_ctx.consume()

        return param_def_s

    def parse_parameter_def_locally(self, ctx: Context) -> ParamDefNode:
        """
        start with "parameter", end with expression / '\0' / ',' / ';':
            parameter x = 3;
            parameter int y = 4,
            parameter logic [2:0] z = 5
        '\0' /',' / ';' at the end will not be consumed
        """

        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Parameter
        ldx, cdx = token.pos


        ctx.consume()
        typ, data_typ, identifier_array_val_pairs = self.parse_typ_data_typ_identifier_array_val_pairs_locally(ctx=ctx)

        token = ctx.current()
        if token is None or token.kind_ == TokenKind.EOF:
            end_idx = ctx.token_idx - 1
        else:
            end_idx = ctx.token_idx

        return ParamDefNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                            data_type=data_typ, identifier_array_val_pairs=identifier_array_val_pairs)

    def parse_port_list(self, sub_ctx: Context) -> list[AnsiPortDefNode] | list[NonAnsiPortDefNode]:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.LParen

        nxt_token = sub_ctx.peek_nn()
        if nxt_token.kind_ == TokenKind.Input or nxt_token.kind_ == TokenKind.Output or nxt_token.kind_ == TokenKind.Inout:
            return self.parse_ansi_port_def_list(sub_ctx)
        else:
            return self.parse_non_ansi_port_def_list(sub_ctx)

    def parse_non_ansi_port_def_list(self, sub_ctx: Context) -> list[NonAnsiPortDefNode]:
        """
        start with '(' end with ')'
        non-ansi port definition support is very limited
            module(a, b, c, d, e, f ... )
        """
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.LParen
        sub_ctx.consume()

        array_identifiers = self.parse_array_identifiers_locally(ctx=sub_ctx)
        non_ansi_port_s = []
        for array_identifier in array_identifiers:
            if len(array_identifier.size) != 0:
                log.fatal(f"invalid syntax in non-ansi port definition\n"
                          f"{self.error_context(array_identifier.ldx, array_identifier.cdx)}\n")
            non_ansi_port = NonAnsiPortDefNode(ldx=token.ldx, cdx=token.cdx, tokens=array_identifier.tokens,
                                               identifier=array_identifier.identifier)
            non_ansi_port_s.append(non_ansi_port)

        return non_ansi_port_s

    def parse_ansi_port_def_list(self, sub_ctx: Context) -> list[AnsiPortDefNode]:
        """
        start with '(', end with ')'
        """
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.LParen
        sub_ctx.consume()

        ansi_port_def_s = []
        while True:
            token = sub_ctx.current_nn()
            if sub_ctx.token_idx == len(sub_ctx.tokens) - 1:
                assert token.kind_ == TokenKind.RParen
                break
            if sub_ctx.token_idx > len(sub_ctx.tokens) - 1:
                break
            if token.kind_ not in [TokenKind.Input, TokenKind.Output, TokenKind.Inout]:
                log.fatal(f"invalid syntax, 'input'/'output'/'inout' is expected,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError

            ansi_port_def = self.parse_ansi_port_def_locally(ctx=sub_ctx)
            ansi_port_def_s.append(ansi_port_def)

            # check the end
            token = sub_ctx.current_nn()
            if token is None:
                assert 0, f"un-reachable branch"
            elif token.kind_ == TokenKind.RParen:
                break
            elif token.kind_ == TokenKind.Comma:
                sub_ctx.consume()
                continue
            else:
                log.fatal(f"invalid token in ANSI port definition list, ',' or ')' is expected, rather than '{token}'\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError

        return ansi_port_def_s

    def parse_ansi_port_def_locally(self, ctx: Context) -> AnsiPortDefNode:
        """
        start with "input" / "output" / "inout", end with <array_identifiers> / ',' / ';' / '\0',
        will not consume ';' / ',' / '\0' at the end
        """

        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Input or token.kind_ == TokenKind.Output or token.kind_ == TokenKind.Inout
        ldx, cdx = token.pos


        direction = None
        typ = None
        data_typ = None
        array_identifiers = None

        # direction - input/output/inout
        direction = token
        ctx.consume()

        # type - wire/reg/var, others are not implemented
        token = ctx.current_nn()
        if token.kind_ == TokenKind.Wire or token.kind_ == TokenKind.Reg or token.kind_ == TokenKind.Var:
            typ = token
            ctx.consume()

        # data type - (bit/logic) (signed/unsigned) (range) / int / string, others are not implemented
        token = ctx.current_nn()
        if token.kind_ != TokenKind.Identifier:
            data_typ = self.parse_data_type_or_implicit_locally(ctx=ctx)

        # array identifiers
        token = ctx.current_nn()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax for ANSI port definition, identifier is expected, rather than '{token}'\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError
        array_identifiers = self.parse_array_identifiers_locally(ctx)

        token = ctx.current()
        if token is None or token.kind_ == TokenKind.EOF:
            end_idx = ctx.token_idx - 1
        else:
            end_idx = ctx.token_idx

        return AnsiPortDefNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                               direction=direction,
                               typ=typ,
                               data_type=data_typ,
                               array_identifiers=array_identifiers)

    def parse_data_type_or_implicit_locally(self, ctx: Context) -> DataTypeNode | None:
        token = ctx.current()
        ldx, cdx = token.pos


        start_idx = ctx.token_idx

        logic_or_bit = None
        signing = None
        range_ = None
        inherent_data_type = None

        if token is not None and token.kind_ == TokenKind.Bit or token.kind_ == TokenKind.Logic:
            logic_or_bit = token
            ctx.consume()

        token = ctx.current()
        if token is not None and token.kind_ == TokenKind.Signed or token.kind_ == TokenKind.Unsigned:
            signing = token
            ctx.consume()

        token = ctx.current()
        if token is not None and token.kind_ == TokenKind.LBracket:
            range_ = self.parse_range_or_index_locally(ctx)
            if isinstance(range_, IndexNode):
                log.fatal(f"invalid syntax, range definition is expected, rather than '{range_}',\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError

        token = ctx.current()
        if token is not None and token.kind_ in [TokenKind.Int, TokenKind.ShortInt, TokenKind.LongInt,
                                                 TokenKind.Real, TokenKind.ShortReal, TokenKind.Byte,
                                                 TokenKind.Byte, TokenKind.String, TokenKind.Integer]:
            inherent_data_type = token
            ctx.consume()

        end_idx = ctx.token_idx - 1

        if logic_or_bit is None and signing is None and range_ is None and inherent_data_type is None:
            return None
        else:
            return DataTypeNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                logic_or_bit=logic_or_bit,
                                signing=signing,
                                range_=range_,
                                inherent_data_type=inherent_data_type)

    def parse_range_or_index_locally(self, ctx: Context) -> RangeNode | IndexNode:
        token = ctx.current_nn()
        ldx, cdx = token.pos
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.LBracket
        ctx.consume()

        expr_0 = self.parse_expression_locally(ctx=ctx)
        token = ctx.current_nn()

        if token.kind_ == TokenKind.RBracket:
            end_idx = ctx.token_idx
            ctx.consume()
            return IndexNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                             index=expr_0)

        if token.kind_ != TokenKind.Colon:
            log.fatal(f"invalid syntax, ':' or ']' is expected to index or take range, rather than '{token}'\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError
        ctx.consume()

        expr_1 = self.parse_expression_locally(ctx=ctx)

        token = ctx.current_nn()
        if token.kind_ != TokenKind.RBracket:
            log.fatal(f"invalid syntax, ']' is expected, rather than '{token}'\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError

        end_idx = ctx.token_idx
        ctx.consume()
        return RangeNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                         left=expr_0, right=expr_1)

    def parse_array_identifier_locally(self, ctx: Context):
        token = ctx.current_nn()
        ldx, cdx = token.pos

        assert token.kind_ == TokenKind.Identifier
        start_idx = ctx.token_idx

        identifier = token
        ctx.consume()

        size = []
        while True:
            token = ctx.current()
            if token is not None and token.kind_ == TokenKind.LBracket:
                range_or_index = self.parse_range_or_index_locally(ctx)
                size.append(range_or_index)
            else:
                break
        end_idx = ctx.token_idx - 1

        return ArrayIdentifierInitNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                       identifier=identifier, size=size)

    def parse_array_identifiers_locally(self, ctx: Context) -> list[ArrayIdentifierInitNode]:
        """
        end with: <array_identifier> / ',' / '\0'
            a
            a, b
            a[2:0], b
            a[2:0], b, c[2:0][3:2]
            a, b, c,
        """

        token = ctx.current_nn()
        ldx, cdx = token.pos

        assert token.kind_ == TokenKind.Identifier
        start_idx = ctx.token_idx

        array_identifier_s = []
        while True:
            token = ctx.current()
            if token is None or token.kind_ != TokenKind.Identifier:
                break

            array_identifier = self.parse_array_identifier_locally(ctx)
            array_identifier_s.append(array_identifier)

            token = ctx.current()
            if token is not None and token.kind_ == TokenKind.Comma:
                nxt = ctx.peek()
                if nxt is not None and nxt.kind_ == TokenKind.Identifier:
                    ctx.consume()
                    continue
                else:
                    break
            else:
                break

        return array_identifier_s

    def parse_module_body(self, sub_ctx: Context) -> list[ModuleBodyItemNode]:
        items = []
        while True:
            token = sub_ctx.current()
            if token is None or token.kind_ == TokenKind.EOF:
                break
            elif token.kind_ == TokenKind.EndModule:
                sub_ctx.consume()
                break
            else:
                item = self.parse_module_body_item_locally(sub_ctx)
                if item is not None:
                    items.append(item)
        return items

    def parse_module_body_item_locally(self, ctx: Context) -> ModuleBodyItemNode | None:
        token = ctx.current()
        if token is None or token.kind_ == TokenKind.EOF:
            return None
        elif token.kind_ == TokenKind.Parameter:
            return self.parse_parameter_def_in_body_locally(ctx)
        elif token.kind_ in [TokenKind.Input, TokenKind.Output, TokenKind.Inout]:
            return self.parse_port_def_in_body_locally(ctx)
        elif token.kind_ == TokenKind.Localparam:
            return self.parse_localparam_def_locally(ctx)
        elif token.kind_ in [TokenKind.Reg, TokenKind.Var, TokenKind.Wire]:
            return self.parse_rvw_def_locally(ctx)
        elif token.kind_ in [TokenKind.Int, TokenKind.ShortInt, TokenKind.LongInt,
                             TokenKind.Real, TokenKind.ShortReal, TokenKind.Byte,
                             TokenKind.Byte, TokenKind.String, TokenKind.Integer]:
            return self.parse_inherent_type_var_locally(ctx)
        elif token.kind_ == TokenKind.Genvar:
            return self.parse_genvar_def_locally(ctx)
        elif token.kind_ in [TokenKind.Bit, TokenKind.Logic]:
            return self.parse_bl_def_locally(ctx)
        elif token.kind_ == TokenKind.Assign:
            return self.parse_assign_locally(ctx)
        elif token.kind_ in [TokenKind.Always, TokenKind.AlwaysComb, TokenKind.AlwaysFF, TokenKind.AlwaysLatch]:
            return self.parse_always_block_locally(ctx)
        elif token.kind_ == TokenKind.Initial:
            return self.parse_initial_block_locally(ctx)
        elif token.kind_ == TokenKind.SemiColon:
            ctx.consume()
            return None
        elif token.kind_ == TokenKind.Identifier and ctx.peek() is not None and ctx.peek().kind_ in [
            TokenKind.Identifier, TokenKind.SharpPat
        ]:
            return self.parse_instantiation_locally(ctx)
        elif token.kind_ == TokenKind.Begin:
            return self.parse_begin_end_locally(ctx)
        elif token.kind_ == TokenKind.SemiColon:
            ctx.consume()
            return EmptyModuleBodyItem(ldx=token.ldx, cdx=token.cdx, tokens=[token])
        elif token.kind_ == TokenKind.EndModule:
            return None
        elif token.kind_ == TokenKind.Directive:
            directive = self.parse_pre_compile_directive_locally(ctx=ctx)
            return PreCompileDirectiveInsideBodyNode(ldx=directive.ldx, cdx=directive.cdx, tokens=directive.tokens,
                                                      directive=directive)
        elif token.kind_ == TokenKind.Module:
            log.fatal(f"define module inside a module is not supported:\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError
        else:
            assert 0, f"got token: {token}, it's invalid inside module definition, or it is not implemented yet\n" \
                      f"{self.error_context(token.ldx, token.cdx)}\n"

    def parse_begin_end_locally(self, ctx: Context) -> BeginEndNode:
        token = ctx.current_nn()
        ldx, cdx = token.pos
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Begin
        ctx.consume()

        name = None
        token = ctx.current()
        if token is not None and token.kind_ == TokenKind.Colon:
            ctx.consume()
            token = ctx.current()
            if token is None or token.kind_ != TokenKind.Identifier:
                log.fatal(f"invalid syntax in begin-end block, an identifier is expected after ';',\n"
                          f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
                raise Exception
            name = token
            ctx.consume()

        items = []
        while True:
            token = ctx.current()
            if token is None or token.kind_ == TokenKind.End:
                break
            item = self.parse_module_body_item_locally(ctx)
            if item is not None:
                items.append(item)
        end_idx = ctx.token_idx
        ctx.consume()

        return BeginEndNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                            name=name, body_item=items)

    def parse_typ_data_typ_identifier_array_val_pairs_locally(self, ctx: Context) -> \
            (Token, DataTypeNode, list[(ArrayIdentifierInitNode, Expression)]):
        """
        '\0' /',' / ';' at the end will not be consumed
        """

        typ = None
        data_typ = None
        identifier = None
        val = None

        token = ctx.current()
        if token is not None and token.kind_ in [TokenKind.Reg, TokenKind.Var, TokenKind.Wire]:
            typ = token
            ctx.consume()

        data_typ = self.parse_data_type_or_implicit_locally(ctx=ctx)

        identifier_array_val_pairs = []
        while True:
            token = ctx.current()
            if token is None or token.kind_ != TokenKind.Identifier:
                if typ is not None:
                    typ_src =  typ.src
                elif data_typ is not None:
                    typ_src = data_typ.tokens_str
                else:
                    typ_src = "variable"
                log.fatal(f"invalid syntax, identifier is expected to define {typ_src},\n"
                          f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
                raise ParserError
            identifier_array = self.parse_array_identifier_locally(ctx=ctx)

            token = ctx.current()
            val = None
            if token is not None and token.kind_ == TokenKind.Assignment:
                ctx.consume()
                val = self.parse_expression_locally(ctx=ctx)

            identifier_array_val_pairs.append((identifier_array, val))

            token = ctx.current()
            if token is not None and token.kind_ == TokenKind.Comma:
                nxt = ctx.peek()
                if nxt is not None and nxt.kind_ == TokenKind.Identifier:
                    ctx.consume()
                    continue
                else:
                    break
            elif token is not None and token.kind_ == TokenKind.SemiColon:
                break
            else:
                break

        return typ, data_typ, identifier_array_val_pairs

    def parse_parameter_def_in_body_locally(self, ctx: Context) -> ParamDefInBodyNode:
        """
        start with parameter, end with ';'
        """
        token = ctx.current_nn()
        assert token.kind_ == TokenKind.Parameter
        start_idx = ctx.token_idx
        ctx.consume()

        typ, data_typ, identifier_array_val_pairs = self.parse_typ_data_typ_identifier_array_val_pairs_locally(ctx=ctx)
        end_idx = ctx.token_idx

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax, ';' is expected to at the end of parameter definition,\n"
                      f"{self.error_context(ctx.last().ldx, ctx.last().cdx)}\n")
            raise ParserError
        ctx.consume()

        return ParamDefInBodyNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                  data_type=data_typ, identifier_array_val_pairs=identifier_array_val_pairs)

    def parse_port_def_in_body_locally(self, ctx: Context) -> PortDefAndInitInBodyNode:
        """
        start with "input" / "output" / "inout", end with ';'
        """
        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ in [TokenKind.Input, TokenKind.Output, TokenKind.Inout]

        direction = token
        ctx.consume()

        typ, data_typ, identifier_array_val_pairs = self.parse_typ_data_typ_identifier_array_val_pairs_locally(ctx=ctx)
        end_idx = ctx.token_idx

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax, ';' is expected to at the end of port definition,\n"
                      f"{self.error_context(ctx.last().ldx, ctx.last().cdx)}\n")
            raise ParserError
        ctx.consume()

        return PortDefAndInitInBodyNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                        direction=direction,
                                        typ=typ, data_type=data_typ, identifier_array_val_pairs=identifier_array_val_pairs)

    def parse_localparam_def_locally(self, ctx: Context) -> LocalParamDefNode:
        """
        start with "localparam", end  ';':
            localparam x = 3;
            localparam logic [2:0] z = 5
        '';' at the end will be consumed
        """

        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Localparam
        ctx.consume()

        typ, data_typ, identifier_array_val_pairs = self.parse_typ_data_typ_identifier_array_val_pairs_locally(ctx=ctx)
        end_idx = ctx.token_idx

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax, ';' is expected to at the end of localparam definition,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError
        ctx.consume()

        return LocalParamDefNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                 data_type=data_typ, identifier_array_val_pairs=identifier_array_val_pairs)

    def parse_rvw_def_locally(self, ctx: Context)  -> VariableDefInitNode:
        """
        start with "reg/var/wire", end with ';'
        ';' will be consumed
        """
        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ in [TokenKind.Reg, TokenKind.Var, TokenKind.Wire]

        typ, data_typ, identifier_array_val_pairs = self.parse_typ_data_typ_identifier_array_val_pairs_locally(ctx=ctx)
        end_idx = ctx.token_idx - 1

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax, ';' is expected to at the end of {typ.src} definition,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError
        ctx.consume()

        return VariableDefInitNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                   typ=typ,
                                   data_type=data_typ,
                                   identifier_array_val_pairs=identifier_array_val_pairs)

    def parse_bl_def_locally(self, ctx: Context)  -> VariableDefInitNode:
        """
        ';' will be consumed
        """

        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ in [TokenKind.Bit, TokenKind.Logic]

        typ, data_typ, identifier_array_val_pairs = self.parse_typ_data_typ_identifier_array_val_pairs_locally(ctx=ctx)
        end_idx = ctx.token_idx

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax, ';' is expected to at the end of {data_typ.tokens_str} definition,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError
        ctx.consume()

        return VariableDefInitNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                   typ=None,
                                   data_type=data_typ,
                                   identifier_array_val_pairs=identifier_array_val_pairs)

    def parse_inherent_type_var_locally(self, ctx: Context)  -> VariableDefInitNode:
        """
        ';' will be consumed
        """
        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ in [TokenKind.Int, TokenKind.ShortInt, TokenKind.LongInt,
                               TokenKind.Real, TokenKind.ShortReal, TokenKind.Byte,
                               TokenKind.Byte, TokenKind.String, TokenKind.Integer]

        typ, data_typ, identifier_array_val_pairs = self.parse_typ_data_typ_identifier_array_val_pairs_locally(ctx=ctx)
        end_idx = ctx.token_idx

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax, ';' is expected to at the end of {data_typ.tokens_str} definition,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError
        ctx.consume()

        return VariableDefInitNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                   typ=None,
                                   data_type=data_typ,
                                   identifier_array_val_pairs=identifier_array_val_pairs)

    def parse_assign_locally(self, ctx: Context) -> AssignNode:
        """
        ';' will be consumed
        """

        from syntax.expression import Assignment

        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Assign
        ctx.consume()

        assignment = self.parse_expression_locally(ctx=ctx)
        if not isinstance(assignment, Assignment):
            log.fatal(f"invalid syntax in assign statement, expect assignment expression after assign, rather than "
                      f"{assignment}\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            ldx = ctx.last().ldx
            cdx = ctx.last().cdx
            log.fatal(f"invalid syntax in assign statement, ';' is expected at the end,\n"
                      f"{self.error_context(ldx, cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        return AssignNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx+1], assignment=assignment)

    def parse_genvar_def_locally(self, ctx: Context) -> GenvarDefNode | GenvarDefAndInitNode:
        """
        ';' will be consumed
        """
        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Genvar
        ctx.consume()

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax in genvar definition, identifier is expected, "
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError
        ctx.consume()

        token = ctx.current()
        if token is not None and token.kind_ == TokenKind.SemiColon:
            end_idx = ctx.token_idx
            ctx.consume()
            return GenvarDefNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                 identifier=token)

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.Assignment:
            log.fatal(f"invalid syntax in genvar definition, '=' is expected, "
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError
        ctx.consume()

        val = self.parse_expression_locally(ctx=ctx)

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax in genvar definition, ';' is expected at the end,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        return GenvarDefAndInitNode(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                    identifier=token,
                                    val=val)

    def parse_procedure_statement_locally(self, ctx: Context) -> ProcedureStatementNode | None:
        token = ctx.current()
        if token is None:
            log.fatal(f"invalid syntax in procedure statement, '{token}'\n",
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError
        if token.kind_ == TokenKind.Begin:
            return self.parse_procedure_begin_end_block_locally(ctx=ctx)
        elif token.kind_ == TokenKind.If:
            return self.parse_if_else_locally(ctx=ctx)
        elif token.kind_ == TokenKind.Case:
            return self.parse_case_locally(ctx=ctx)
        elif token.kind_ == TokenKind.For:
            return self.parse_for_statement(ctx=ctx)
        elif token.kind_ == TokenKind.SharpPat:
            return self.parse_delay_locally(ctx=ctx)
        elif token.kind_ == TokenKind.Identifier or token.kind_ == TokenKind.LBrace:
            return self.parse_procedure_assignment_locally(ctx=ctx)
        elif token.kind_ == TokenKind.SemiColon:
            ctx.consume()
            return EmptyProcedureStatementNode(ldx=token.ldx, cdx=token.cdx, tokens=[token])
        else:
            log.fatal(f"invalid syntax in procedure statement, '{token}'\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError

    def parse_assignment_statement(self, ctx: Context) -> 'Assignment | NonBlockingAssignment':
        from syntax.expression import Assignment, NonBlockingAssignment
        ldx, cdx = ctx.near().pos
        expr = self.parse_expression_locally(ctx=ctx)
        if not isinstance(expr, (Assignment, NonBlockingAssignment, AddAssignment, SubAssignment, MulAssignment,
                                 DivAssignment, ModAssignment, BitAndAssignment, BitOrAssignment, BitXorAssignment,
                                 LogicLeftShiftAssignment, LogicRightShiftAssignment,
                                 ArithmeticLeftShiftAssignment, ArithmeticRightShiftAssignment)):
            log.fatal(f"invalid syntax in assignment statement, '{expr}'\n",
                      f"{self.error_context(ldx, cdx)}\n")
            raise ParserError
        return expr

    def parse_for_statement(self, ctx: Context) -> 'ForStatementNode':
        token = ctx.current_nn()
        ldx, cdx = token.pos
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.For
        ctx.consume()

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax in for statement, '(' is expected,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError

        data_type = None
        init_statement = None
        token = ctx.current()
        if token is not None and token.kind_ != TokenKind.SemiColon:
            data_type = self.parse_data_type_or_implicit_locally(ctx=ctx)
            init_statement = self.parse_assignment_statement(ctx=ctx)

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax in for statement, ';' is expected,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError

        stop = None
        token = ctx.current()
        if token is not None and token.kind_ != TokenKind.SemiColon:
            stop = self.parse_expression_locally(ctx=ctx)

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax in for statement, ';' is expected,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError

        step = None
        token = ctx.current()
        if token is not None and token.kind_ != TokenKind.RParen:
            step = self.parse_expression_locally(ctx=ctx)

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.RParen:
            log.fatal(f"invalid syntax in for statement, ')' is expected after 'for',\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError

        body = self.parse_procedure_statement_locally(ctx=ctx)
        end_idx = ctx.token_idx - 1

        return ForStatementNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx + 1],
                                data_type=data_type, init=init_statement, stop=stop, step=step, body=body)

    def parse_procedure_begin_end_block_locally(self, ctx: Context) -> 'ProcedureBeginEndBlockNode':
        token = ctx.current()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Begin

        ctx.consume_until_matching_pair(
            left=TokenKind.Begin, right=TokenKind.End,
            error_info=f"invalid syntax, no matching 'end' found for 'begin',\n"
                       f"{self.error_context(token.ldx, token.cdx)}\n"
        )
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_begin_end_block(sub_ctx=Context(src_info=self.ctx.src_info, tokens=ctx.tokens[start_idx:end_idx+1]))

    def parse_begin_end_block(self, sub_ctx: Context) -> ProcedureBeginEndBlockNode:
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.Begin
        sub_ctx.consume()

        name = None
        token = sub_ctx.current()
        if token.kind_ == TokenKind.Colon:
            sub_ctx.consume()
            token = sub_ctx.current()
            if token is None or token.kind_ != TokenKind.Identifier:
                log.fatal(f"invalid syntax in begin-end block, identifier is expected after ':',\n"
                          f"{self.error_context(sub_ctx.last().ldx, sub_ctx.last().cdx)}\n")
                raise ParserError
            name = token
            sub_ctx.consume()

        body = []
        while True:
            if sub_ctx.token_idx == len(sub_ctx.tokens) - 1:
                break
            item = self.parse_procedure_statement_locally(ctx=sub_ctx)
            body.append(item)

        return ProcedureBeginEndBlockNode(ldx=token.ldx, cdx=token.cdx, tokens=sub_ctx.tokens, name=name, body=body)

    def parse_procedure_assignment_locally(self, ctx: Context) -> ProcedureAssignmentNode:
        assignment = self.parse_assignment_statement(ctx=ctx)
        token = ctx.current_nn()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax in assignment statement, ';' is expected at the end,\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            raise ParserError
        ctx.consume()
        return ProcedureAssignmentNode(ldx=assignment.ldx, cdx=assignment.cdx, tokens=assignment.tokens,
                                       assignment=assignment)

    def parse_if_else_locally(self, ctx: Context) -> IfElseBlock:
        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.If
        ctx.consume()

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax, '(' is expected after 'if',\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
        ctx.consume()

        condition = self.parse_expression_locally(ctx=ctx)

        token = ctx.current()
        if token is None or token.kind_ != TokenKind.RParen:
            log.fatal(f"invalid syntax, ')' is expected after condition for 'if',\n"
                      f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
        ctx.consume()

        if_block = self.parse_procedure_statement_locally(ctx=ctx)

        token = ctx.current()
        else_block = None
        if token is not None and token.kind_ == TokenKind.Else:
            ctx.consume()
            else_block = self.parse_procedure_statement_locally(ctx=ctx)

        return IfElseBlock(ldx=token.ldx, cdx=token.cdx, tokens=ctx.tokens[start_idx:ctx.token_idx + 1],
                           condition=condition, if_body=if_block, else_body=else_block)

    def parse_case_locally(self, ctx: Context) -> CaseStatementNode:
        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Case

        ctx.consume_until_matching_pair(
            left=TokenKind.Case, right=TokenKind.EndCase,
            error_info=f"invalid syntax, no matching 'endcase' found for 'case',\n"
                       f"{self.error_context(token.ldx, token.cdx)}\n"
        )

        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_case(sub_ctx=Context(src_info=self.ctx.src_info, tokens=ctx.tokens[start_idx:end_idx+1]))

    def parse_case(self, sub_ctx: Context) -> CaseStatementNode:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.Case
        sub_ctx.consume()

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax, '(' is expected after 'case',\n"
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
        sub_ctx.consume()

        expr = self.parse_expression_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.RParen:
            log.fatal(f"invalid syntax, ')' is expected after expression for 'case',\n"
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
        sub_ctx.consume()

        pairs = []
        default = None
        while True:
            token = sub_ctx.current()
            if token.kind_ == TokenKind.EndCase:
                break
            elif token.kind_ == TokenKind.Default:
                sub_ctx.consume()
                token = sub_ctx.current()
                if token is None or token.kind_ != TokenKind.Colon:
                    log.fatal(f"invalid syntax, ':' is expected after condition for 'case',\n"
                              f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
                sub_ctx.consume()
                default = self.parse_procedure_statement_locally(ctx=sub_ctx)
                break
            condition = self.parse_expression_locally(ctx=sub_ctx)
            token = sub_ctx.current()
            if token is None or token.kind_ != TokenKind.Colon:
                log.fatal(f"invalid syntax, ':' is expected after condition for 'case',\n"
                          f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            sub_ctx.consume()
            ps = self.parse_procedure_statement_locally(ctx=sub_ctx)
            pairs.append((condition, ps))

        return CaseStatementNode(ldx=token.ldx, cdx=token.cdx,
                                 tokens=sub_ctx.tokens,
                                 expression=expr,
                                 case_pairs=pairs,
                                 default_statement=default)

    def parse_always_block_locally(self, ctx: Context) -> AlwaysBlockNode:
        token = ctx.current_nn()
        ldx, cdx = token.pos

        assert token.kind_ in [TokenKind.Always, TokenKind.AlwaysComb, TokenKind.AlwaysFF, TokenKind.AlwaysLatch]
        start_idx = ctx.token_idx

        always_typ = token
        sensitivity_list = []

        ctx.consume()
        token = ctx.current()
        if token is not None and token.kind_ == TokenKind.At:
            sensitivity_list = self.parse_sensitivity_list_locally(ctx=ctx)

        ps = self.parse_procedure_statement_locally(ctx=ctx)

        return AlwaysBlockNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:ctx.token_idx+1],
                               always_typ=always_typ, sensitivity_list=sensitivity_list, body=ps)

    def parse_initial_block_locally(self, ctx: Context) -> InitialBlockNode:
        token = ctx.current_nn()
        ldx, cdx = token.pos

        assert token.kind_ == TokenKind.Initial
        start_idx = ctx.token_idx
        ctx.consume()

        ps = self.parse_procedure_statement_locally(ctx=ctx)

        return InitialBlockNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:ctx.token_idx+1], body=ps)

    def parse_sensitivity_list_locally(self, ctx: Context) -> list[Token]:
        token = ctx.current()
        assert token.kind_ == TokenKind.At

        start_idx = ctx.token_idx
        ctx.consume()
        token = ctx.current()
        if token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax for sensitivity list, '(' is expected,\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError
        ctx.consume_until_matching_pair(
            left=TokenKind.LParen,
            right=TokenKind.RParen,
            error_info=f"invalid syntax for sensitivity list, no matching ')' found,\n"
                       f"{self.error_context(token.ldx, token.cdx)}\n"
        )

        end_idx = ctx.token_idx
        ctx.consume()

        return ctx.tokens[start_idx:end_idx + 1]

    def parse_instantiation_locally(self, ctx: Context) -> InstantiationNode:
        token = ctx.current()
        assert token.kind_ == TokenKind.Identifier
        start_idx = ctx.token_idx

        ctx.consume_until(token_kind=TokenKind.SemiColon,
                          error_info=f"invalid syntax, ';' not found at the end of the module instantiation,\n"
                                     f"{self.error_context(token.ldx, token.cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_instantiation(sub_ctx=Context(src_info=self.ctx.src_info, tokens=ctx.tokens[start_idx:end_idx+1]))

    def parse_instantiation(self, sub_ctx: Context) -> InstantiationNode:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.Identifier

        prototype_identifier = token
        para_set_list = []

        sub_ctx.consume()
        token = sub_ctx.current()

        if token.kind_ == TokenKind.SharpPat:
            # parameter set list
            sub_ctx.consume()
            token = sub_ctx.current()
            if token.kind_ != TokenKind.LParen:
                log.fatal(f"invalid syntax for instantiation, '(' is expected for parameter set block,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            start_idx = sub_ctx.token_idx
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.LParen, right=TokenKind.RParen,
                error_info=f"no matching ')' found at the end of parameter set block,\n"
                           f"{self.error_context(token.ldx, token.cdx)}\n")
            end_idx = sub_ctx.token_idx
            sub_ctx.consume()
            para_set_list = self.parse_para_set_list(sub_ctx=Context(src_info=self.ctx.src_info,
                                                                     tokens=sub_ctx.tokens[start_idx:end_idx+1]))

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax for instantiation, identifier is expected,\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError
        instance_identifier = token
        sub_ctx.consume()

        token = sub_ctx.current()
        if token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax for instantiation, '(' is expected for port connection block,\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError
        start_idx = sub_ctx.token_idx
        sub_ctx.consume_until_matching_pair(
            left=TokenKind.LParen, right=TokenKind.RParen,
            error_info=f"no matching ')' found at the end of port connection block,\n"
                       f"{self.error_context(token.ldx, token.cdx)}\n")
        end_idx = sub_ctx.token_idx
        sub_ctx.consume()
        port_connect_list = self.parse_port_connect_list(sub_ctx=Context(src_info=self.ctx.src_info,
                                                                         tokens=sub_ctx.tokens[start_idx:end_idx+1]))

        token = sub_ctx.current()
        if token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax for instantiation, ';' is expected,\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError

        return InstantiationNode(ldx=token.ldx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                 prototype_identifier=prototype_identifier,
                                 para_sets=para_set_list,
                                 instance_identifier=instance_identifier,
                                 port_connects=port_connect_list)

    def parse_para_set_list(self, sub_ctx: Context) -> list[ParaSetNode]:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.LParen
        assert sub_ctx.tokens[-1].kind_ == TokenKind.RParen
        para_set_list = []

        sub_ctx.consume()
        while True:
            token = sub_ctx.current_nn()
            if token.kind_ == TokenKind.RParen:
                break
            if token.kind_ != TokenKind.Dot:
                log.fatal(f"invalid syntax for instantiation, to set the value of parameter, '.' is expected,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            para_set_start_idx = sub_ctx.token_idx
            para_set_ldx = sub_ctx.tokens[para_set_start_idx].ldx
            para_set_cdx = sub_ctx.tokens[para_set_start_idx].cdx
            sub_ctx.consume()

            token = sub_ctx.current_nn()
            if token.kind_ != TokenKind.Identifier:
                log.fatal(f"invalid syntax for instantiation, to set the value of parameter, identifier is expected,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            para_name = token
            sub_ctx.consume()

            token = sub_ctx.current_nn()
            if token.kind_ != TokenKind.LParen:
                log.fatal(f"invalid syntax for instantiation, to set the value of parameter, '(' is expected,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            sub_ctx.consume()

            para_val = self.parse_expression_locally(ctx=sub_ctx)

            token = sub_ctx.current_nn()
            if token.kind_ != TokenKind.RParen:
                log.fatal(f"invalid syntax for instantiation, ')' is expected,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            sub_ctx.consume()

            token = sub_ctx.current()
            if token.kind_ == TokenKind.Comma:
                para_set_end_idx = sub_ctx.token_idx
                sub_ctx.consume()
            else:
                para_set_end_idx = sub_ctx.token_idx - 1
                if token.kind != TokenKind.RParen:
                    pass
                else:
                    log.fatal(f"invalid syntax for instantiation, in the parameter set block, ')' or ',' is expected,\n"
                              f"{self.error_context(token.ldx, token.cdx)}\n")
                    raise ParserError
            para_set_list.append(ParaSetNode(ldx=para_set_ldx, cdx=para_set_cdx, tokens=sub_ctx.tokens[para_set_start_idx:para_set_end_idx+1],
                                             param_name=para_name,
                                             param_value=para_val))
        return para_set_list

    def parse_port_connect_list(self, sub_ctx: Context) -> list[PortConnectNode]:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.LParen
        assert sub_ctx.tokens[-1].kind_ == TokenKind.RParen
        port_connect_node = []

        sub_ctx.consume()
        while True:
            token = sub_ctx.current_nn()
            if token.kind_ == TokenKind.RParen:
                break
            if token.kind_ != TokenKind.Dot:
                log.fatal(f"invalid syntax for instantiation, '.' is expected to connect port,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            port_connect_start_idx = sub_ctx.token_idx
            port_connect_ldx = sub_ctx.tokens[port_connect_start_idx].ldx
            port_connect_cdx = sub_ctx.tokens[port_connect_start_idx].cdx
            sub_ctx.consume()

            token = sub_ctx.current_nn()
            if token.kind_ != TokenKind.Identifier:
                log.fatal(f"invalid syntax for instantiation, identifier is expected to connect port,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            port_name = token
            sub_ctx.consume()

            token = sub_ctx.current_nn()
            if token.kind_ != TokenKind.LParen:
                log.fatal(f"invalid syntax for instantiation, '(' is expected to connect port,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            sub_ctx.consume()

            port_val = self.parse_expression_locally(ctx=sub_ctx)

            token = sub_ctx.current_nn()
            if token.kind_ != TokenKind.RParen:
                log.fatal(f"invalid syntax for instantiation, ')' is expected,\n"
                          f"{self.error_context(token.ldx, token.cdx)}\n")
                raise ParserError
            sub_ctx.consume()

            token = sub_ctx.current()
            if token.kind_ == TokenKind.Comma:
                port_set_end_idx = sub_ctx.token_idx
                sub_ctx.consume()
            else:
                port_set_end_idx = sub_ctx.token_idx - 1
                if token.kind != TokenKind.RParen:
                    pass
                else:
                    log.fatal(f"invalid syntax for instantiation, ')' or ',' is expected,\n"
                              f"{self.error_context(token.ldx, token.cdx)}\n")
                    raise ParserError
            port_connect_node.append(PortConnectNode(ldx=port_connect_ldx, cdx=port_connect_cdx, tokens=sub_ctx.tokens[port_connect_start_idx:port_set_end_idx+1],
                                                     port_name=port_name,
                                                     port_value=port_val))
        return port_connect_node

    def parse_expression_locally(self, ctx: Context) -> 'Expression':
        from pratt import parse_expression
        expr = parse_expression(depth=0, ctx=ctx, ctx_bp=0)
        return expr

    def parse_delay_locally(self, ctx: Context) -> DelayStatementNode:
        from pratt import parse_delay
        delay = parse_delay(ctx=ctx)
        return DelayStatementNode(ldx=delay.ldx, cdx=delay.cdx, tokens=delay.tokens, delay=delay)

    def parse_generate_locally(self, ctx: Context) -> GenerateNode:
        token = ctx.current_nn()
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Generate

        nxt = ctx.peek()
        if nxt is None or nxt.kind_ not in [TokenKind.Case, TokenKind.For, TokenKind.If]:
            log.fatal(f"invalid syntax for generate statement, 'case', 'for' or 'if' is expected,\n"
                      f"{self.error_context(token.ldx, token.cdx)}\n")
            raise ParserError

        ctx.consume_until_matching_pair(
            left=TokenKind.Generate, right=TokenKind.EndGenerate,
            error_info=f"invalid syntax, no matching 'endgenerate' found for 'generate',\n"
                       f"{self.error_context(token.ldx, token.cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()
        sub_ctx = Context(src_info=self.ctx.src_info, tokens=ctx.tokens[start_idx:end_idx])

        if nxt.kind_ == TokenKind.Case:
            return self.parse_generate_case(sub_ctx=sub_ctx)
        elif nxt.kind_ == TokenKind.For:
            return self.parse_generate_for(sub_ctx=sub_ctx)
        else:
            return self.parse_generate_if(sub_ctx=sub_ctx)

    def parse_generate_case(self, sub_ctx: Context) -> GenerateNodeCase:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.Generate
        sub_ctx.consume()

        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.Case
        sub_ctx.consume()

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax in generate case statement, '(' is expected after 'case',\n",
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError
        sub_ctx. consume()

        expr = self.parse_expression_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.RParen:
            log.fatal(f"invalid syntax in generate case statement, ')' is expected after expression,\n",
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError

        pairs = []
        default = None
        while True:
            token = sub_ctx.current()
            if token.kind_ == TokenKind.EndCase:
                sub_ctx.consume()
                break
            elif token.kind_ == TokenKind.Default:
                sub_ctx.consume()
                default = self.parse_module_body_item_locally(ctx=sub_ctx)
                break
            condition = self.parse_expression_locally(ctx=sub_ctx)
            token = sub_ctx.current()
            if token is None or token.kind_ != TokenKind.Colon:
                log.fatal(f"invalid syntax, ':' is expected after condition for 'case',\n"
                          f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            sub_ctx.consume()
            i = self.parse_module_body_item_locally(ctx=sub_ctx)
            pairs.append((condition, i))

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.EndGenerate:
            log.fatal(f"invalid syntax, 'endgenerate' after 'endcase',\n"
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        return GenerateNodeCase(ldx=token.ldx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                expression=expr, case_pairs=pairs, default_statement=default)

    def parse_generate_for(self, sub_ctx: Context) -> GenerateNodeFor:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.Generate
        sub_ctx.consume()

        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.For
        sub_ctx.consume()

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax in generate case statement, '(' is expected after 'for',\n",
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        data_type = None
        token = sub_ctx.current()
        if token is not None and token.kind_ == TokenKind.Genvar:
            data_type = token
            sub_ctx.consume()

        init = None
        token = sub_ctx.current()
        if token is not None and token.kind_ != TokenKind.SemiColon:
            init = self.parse_expression_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax in generate case statement, ';' is expected after initialization statement,\n",
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        stop = None
        token = sub_ctx.current()
        if token is not None and token.kind_ != TokenKind.SemiColon:
            stop = self.parse_expression_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax in generate case statement, ';' is expected after stop condition statement,\n",
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        step = None
        token = sub_ctx.current()
        if token is not None and token.kind_ != TokenKind.SemiColon:
            step = self.parse_expression_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.RParen:
            log.fatal(f"invalid syntax in generate case statement, ')' is expected after step statement,\n",
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        body = self.parse_module_body_item_locally(ctx=sub_ctx)

        return GenerateNodeFor(ldx=token.ldx, cdx=token.cdx, tokens=sub_ctx.tokens,
                               genvar_data_type=data_type, init=init, stop=stop, step=step, body=body)

    def parse_generate_if(self, sub_ctx: Context) -> GenerateNodeIf:
        token = sub_ctx.current_nn()
        assert token.kind_ == TokenKind.Generate
        sub_ctx.consume()

        token = sub_ctx.current()
        assert token.kind_ == TokenKind.For
        sub_ctx.consume()

        token = sub_ctx.current_nn()
        if token is None or token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax in generate case statement, '(' is expected after 'if',\n",
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        condition = self.parse_expression_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token is None or token.kind_ != TokenKind.RParen:
            log.fatal(f"invalid syntax in generate case statement, ')' is expected after condition,\n",
                      f"{self.error_context(sub_ctx.near().ldx, sub_ctx.near().cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        body = self.parse_module_body_item_locally(ctx=sub_ctx)

        return GenerateNodeIf(ldx=token.ldx, cdx=token.cdx, tokens=sub_ctx.tokens,
                              condition=condition, body=body)

    def parse_pre_compile_directive_locally(self, ctx: Context) -> PreCompileDirectiveNode:
        token = ctx.current_nn()
        ldx, cdx = token.pos
        start_idx = ctx.token_idx
        assert token.kind_ == TokenKind.Directive

        def consume_until_src_matching_pair(left: list[str], right: list[str]):
            token = ctx.current_nn()
            assert token.src in left
            depth = 0
            while True:
                token = ctx.current()
                if token is None or token.kind_ == TokenKind.EOF:
                    log.fatal(f"invalid syntax, no matching '`endif` found for '{start_src}'\n"
                              f"{self.error_context(ldx, cdx)}\n")
                    raise ParserError
                if token.src in left:
                    depth += 1
                elif token.src in right:
                    depth -= 1
                    if depth == 0:
                        break
                ctx.consume()

        if token.src == "`define" or token.src == "`undef":
            log.fatal(f"{token.src} is not supported, you may need to use other tools to do pre-compile first\n"
                      f"{self.error_context(ldx, cdx)}\n")
            raise ParserError
        elif token.src == "`resetall":
            ctx.consume()
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=[token])
        elif token.src == "`ifdef" or token.src == "`ifndef":
            start_src = token.src
            start_idx = ctx.token_idx
            log.warning(f"precompile directive support is very limited, text between '{token.src}' and "
                        f"the matching 'endif' will be ignored:\n"
                        f"{self.error_context(ldx, cdx)}\n")
            consume_until_src_matching_pair(left=["`ifdef", "`ifndef"], right=["`endif"])
            end_idx = ctx.token_idx
            ctx.consume()
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1])
        elif token.src == "`endif":
            log.fatal(f"invalid syntax, no matching '`ifdef`/'`ifndef' found for '`endif'\n"
                      f"{self.error_context(ldx, cdx)}\n")
            raise ParserError
        elif token.src == "`elsif":
            log.fatal(f"invalid syntax, '`elsif` should be between '`ifdef/`ifndef' and `endif`\n"
                      f"{self.error_context(ldx, cdx)}\n")
            raise ParserError
        elif token.src == "`celldefine":
            start_src = token.src
            start_idx = ctx.token_idx
            log.warning(f"precompile directive support is very limited, text between '{token.src}' and "
                        f"the matching 'endcelldefine' will be ignored:\n"
                        f"{self.error_context(ldx, cdx)}\n")
            consume_until_src_matching_pair(left=["`celldefine"], right=["`endcelldefine"])
            end_idx = ctx.token_idx
            ctx.consume()
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1])
        elif token.src == "`endcelldefine":
            log.fatal(f"invalid syntax, no matching '`celldefine` found for '`endcelldefine'\n"
                      f"{self.error_context(ldx, cdx)}\n")
            raise ParserError
        elif token.src == "`begin_keyword":
            start_src = token.src
            start_idx = ctx.token_idx
            log.warning(f"precompile directive support is very limited, text between '{token.src}' and "
                        f"the matching 'end_keyword' will be ignored:\n"
                        f"{self.error_context(ldx, cdx)}\n")
            consume_until_src_matching_pair(left=["`begin_keyword"], right=["`end_keyword"])
            end_idx = ctx.token_idx
            ctx.consume()
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1])
        elif token.src == "`include":
            start_idx = ctx.token_idx
            ctx.consume()
            x = ctx.current()
            if x is None or x.kind_ not in [TokenKind.StringLiteral, TokenKind.LessThan]:
                log.fatal(f"invalid syntax, '<filepath>' or '\"filepath\"' is expected after `include\n"
                          f"{self.error_context(ldx, cdx)}\n")
                raise ParserError
            if x.kind_ == TokenKind.StringLiteral:
                end_idx = ctx.token_idx
                ctx.consume()
            else:
                assert x.kind == TokenKind.LessThan
                ctx.consume_until(TokenKind.GreaterThan,
                                  error_info=f"invalid syntax, no matching '>' found for '<'\n"
                                             f"{self.error_context(ldx, cdx)}\n")
                end_idx = ctx.token_idx
                ctx.consume()
            log.warning(f"precompile directive support is very limited, '`include` will not take effect\n"
                        f"{self.error_context(ldx, cdx)}\n")
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1])
        elif token.src == "`timescale":
            start_idx = ctx.token_idx
            ctx.consume()
            unit_mag = ctx.current()
            if unit_mag is None or unit_mag.kind_ != TokenKind.Literal:
                log.fatal(f"invalid syntax, time unit is expected after `timescale\n"
                          f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
                raise ParserError
            ctx.consume()
            unit_unit = ctx.current()
            if unit_unit is None or unit_unit.kind_ not in [TokenKind.Second, TokenKind.MiniSecond, TokenKind.MicroSecond,
                                                            TokenKind.NanoSecond, TokenKind.PicoSecond, TokenKind.FemtoSecond]:
                log.fatal(f"invalid syntax, time unit should be specified after literal\n"
                          f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
                raise ParserError
            ctx.consume()
            token = ctx.current()
            if token is None or token.kind_ != TokenKind.Div:
                log.fatal(f"invalid syntax, '/' is expected after time unit\n"
                          f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
            ctx.consume()
            precision_mag = ctx.current()
            if precision_mag is None or precision_mag.kind_ != TokenKind.Literal:
                log.fatal(f"invalid syntax, precision is expected after time unit\n"
                          f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
                raise ParserError
            ctx.consume()
            precision_unit = ctx.current()
            if precision_unit is None or precision_unit.kind_ not in [TokenKind.Second, TokenKind.MiniSecond,
                                                                      TokenKind.MicroSecond, TokenKind.NanoSecond,
                                                                      TokenKind.PicoSecond, TokenKind.FemtoSecond]:
                log.fatal(f"invalid syntax, precision unit should be specified after literal\n"
                          f"{self.error_context(ctx.near().ldx, ctx.near().cdx)}\n")
                raise ParserError
            ctx.consume()
            end_idx = ctx.token_idx
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1])
        elif token.src == "`pragma":
            log.fatal(f"`pragma cannot be parsed since we don't know how to parse them. Please remove them fist.\n"
                      f"{self.error_context(ldx, cdx)}\n")
            raise ParserError
        elif token.src == "`default_nettype":
            start_idx = ctx.token_idx
            ctx.consume()
            token = ctx.current()
            if token is None or token.src not in ["wire", "tri", "tri0", "tri1", "wand", "triand", "wor", "trior",
                                                  "trireg", "uwire", "none"]:
                log.fatal(f"invalid syntax, 'wire', 'tri', 'tri0', 'tri1', 'wand', 'triand', 'wor', 'trior', 'trireg',"
                          f"'uwire', 'none' is expected after `default_nettype\n"
                          f"{self.error_context(ldx, cdx)}\n")
                raise ParserError
            end_idx = ctx.token_idx
            ctx.consume()
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1])
        elif token.src in ["`unconnected_drive", "`nounconnected_drive"]:
            start_idx = ctx.token_idx
            start_src = token.src
            ctx.consume()
            token = ctx.current()
            if token is None or token.src not in ["pull0", "pull1"]:
                log.fatal(f"invalid syntax, 'pull0', 'pull1' is expected after '{start_src}'\n"
                          f"{self.error_context(ldx, cdx)}\n")
                raise ParserError
            end_idx = ctx.token_idx
            ctx.consume()
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1])
        elif token.src == "`resetall":
            start_idx = ctx.token_idx
            ctx.consume()
            return PreCompileDirectiveNode(ldx=ldx, cdx=cdx, tokens=[ctx.tokens[start_idx]])
        else:
            log.fatal(f"un-supported pre-compile directive `{token.src}` (macro is not supported also)\n"
                      f"{self.error_context(ldx, cdx)}\n")
            raise ParserError


def parse_file(path: str, parse_body: bool = False) -> list[SyntaxNode]:
    with open(path, 'r', encoding="utf-8") as f:
        verilog = f.read()
    parser = Parser(verilog, parse_body=parse_body)
    return parser.parse()


if __name__ == "__main__":
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
        elif isinstance(data, tuple):
            for c in data:
                re_arrange(c)
        return data

    nodes = re_arrange(parse_file("rich_grammar.sv"))

    import yaml

    with open("test.yml", 'w', encoding="utf-8") as f:
        yaml.dump(nodes, f)
