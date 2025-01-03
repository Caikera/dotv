import re

from lexer_ import Lexer, Token, TokenKind
from log import log
from syntax.node_ import *


class ParserError(Exception):
    pass


class ExpectedTokenNotFound(ParserError):
    pass


class SourceInfo:
    def __init__(self, lines: list[str], path: str):
        self.lines: list[str] = lines
        self.path: str = path

    def error_context(self, rdx: int, cdx: int):
        msg = [f"line: {rdx+1}, column: {cdx+1}, file: {self.path}"]
        if rdx > 0:
            msg.append(f"    {self.lines[rdx-1]}\n")
        msg.append(f"    {self.lines[rdx]}\n")
        msg.append(f"    {' '*cdx}^\n")
        if rdx < len(self.lines) - 1:
            msg.append(f"    {self.lines[rdx+1]}\n")
        return "".join(msg)

        # log.list_fatal(title=f"line: {rdx+1}, column: {cdx+1}, file: {self.path}",
        #                contents=msg)


class Context:
    def __init__(self, tokens: list[Token], delete_eof: bool = False):
        if delete_eof:
            tokens = list(filter(lambda x: x.kind_ != TokenKind.EOF, tokens))
        self.tokens: list[Token] = tokens
        self.token_idx: int = 0

    def current(self) -> Token | None:
        if self.token_idx >= len(self.tokens):
            return None
        return self.tokens[self.token_idx]

    def peek(self) -> Token | None:
        if self.token_idx+1 >= len(self.tokens):
            return None
        return self.tokens[self.token_idx+1]

    def consume(self):
        self.token_idx += 1

    def consume_until(self, token_kind: TokenKind, error_info: str, just_try: bool = False):
        while True:
            token = self.current()
            if token is None or token.kind_ == TokenKind.EOF:
                if just_try:
                    return False
                log.fatal(error_info)
                raise ExpectedTokenNotFound
            elif token.kind_ == token_kind:
                end_idx = self.token_idx
                return True
            else:
                self.consume()

    def consume_until_matching_pair(self, left: TokenKind, right: TokenKind, error_info: str, just_try: bool = False):
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
    def __init__(self, context: str, eol: str = '\n', delete_eof: bool = False, path: str = ""):
        tokens = Lexer(context, eol).tokens
        tokens = list(filter(lambda x: x.kind_ != TokenKind.LineComment and x.kind_ != TokenKind.BlockComment, tokens))
        self.ctx = Context(tokens, delete_eof=delete_eof)
        lines = context.split(eol)
        self.source_info = SourceInfo(lines, path)

    def error_context(self, rdx: int, cdx: int):
        return self.source_info.error_context(rdx, cdx)

    def parse(self):
        while True:
            token = self.ctx.current()
            if token is None or token.kind_ == TokenKind.EOF:
                break
            elif token.kind_ == TokenKind.LineComment:
                break
            elif token.kind_ == TokenKind.BlockComment:
                break
            elif token.kind_ == TokenKind.Module:
                module_node: ModuleNode = self.parse_module()

    def parse_module(self):
        token = self.ctx.current()
        start_idx = self.ctx.token_idx
        assert token == TokenKind.Module
        rdx = token.rdx
        cdx = token.cdx

        self.ctx.consume()
        self.ctx.consume_until(
            token_kind=TokenKind.EndModule,
            error_info=f"invalid syntax, module definition is not closed by 'endmodule',\n"
                       f"{self.error_context(rdx, cdx)}\n"
        )
        end_idx = self.ctx.token_idx
        self.ctx.consume()

        return self.parse_module_detail(sub_ctx=Context(self.ctx.tokens[start_idx:end_idx]))

    def parse_module_detail(self, sub_ctx: Context):
        token = sub_ctx.current()
        rdx = token.rdx
        cdx = token.cdx
        assert token.kind_ == TokenKind.Module

        name = None
        para_list = None
        port_list = None
        body = None

        sub_ctx.consume()
        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax, module name is not specified,\n"
                      f"{self.error_context(rdx, cdx)}\n")
            raise ParserError
        name = token.val

        sub_ctx.consume()
        token = sub_ctx.current()

        if token.kind_ == TokenKind.SharpPat:
            sub_ctx.consume()
            token = sub_ctx.current()
            if token.kind_ != TokenKind.LParen:
                log.fatal(f"invalid syntax, '(' is expected after '#' to define parameter\n"
                          f"{self.error_context(rdx, cdx)}\n")
                raise ParserError

            start_idx = sub_ctx.token_idx
            lparen_rdx = token.rdx
            lparen_cdx = token.cdx
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.LParen, right=TokenKind.RParen,
                error_info=f"invalid syntax, for the parameter list block, '(' is not closed by ')',\n"
                           f"{self.error_context(lparen_rdx, lparen_cdx)}\n"
            )
            end_idx = sub_ctx.token_idx
            sub_ctx.consume()
            para_list = self.parse_parameter_list(sub_ctx=Context(sub_ctx.tokens[start_idx:end_idx]))

        token = sub_ctx.current()
        if token.kind_ == TokenKind.LParen:
            start_idx = sub_ctx.token_idx
            lparen_rdx = token.rdx
            lparan_cdx = token.cdx
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.LParen, right=TokenKind.RParen,
                error_info=f"invalid syntax, for the port list block, '(' is not closed by ')'\n"
                           f"{self.error_context(lparen_rdx, lparan_cdx)}\n"
            )
            end_idx = sub_ctx.token_idx
            sub_ctx.consume()
            port_list = self.parse_port_list(sub_ctx=Context(sub_ctx.tokens[start_idx:end_idx]))

        token = sub_ctx.current()
        if token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax, expected ';'\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        start_idx = sub_ctx.token_idx
        sub_ctx.consume_until(
            token_kind=TokenKind.EndModule,
            error_info=f"invalid syntax, module definition is not closed by 'endmodule'\n"
                       f"{self.error_context(rdx, cdx)}\n")
        end_idx = sub_ctx.token_idx
        sub_ctx.consume()

        body = self.parse_module_body(sub_ctx=Context(tokens=sub_ctx.tokens[start_idx:end_idx+1]))

        return ModuleNode(ldx=rdx, cdx=cdx, tokens=sub_ctx.tokens,
                          name=name, para_list=para_list, port_list=port_list, body=body)

    def parse_parameter_list(self, sub_ctx: Context) -> list[ParamDefNode]:
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.LParen
        sub_ctx.consume()

        param_def_s = []
        while True:
            token = sub_ctx.current()
            if token.kind_ != TokenKind.Parameter:
                log.fatal(f"invalid syntax, 'parameter' is expected,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            start_idx = sub_ctx.token_idx

            sub_ctx.consume()
            while True:
                token = sub_ctx.current()
                if sub_ctx.token_idx == len(sub_ctx.tokens) - 1 or token.kind_ == TokenKind.Parameter:
                    break
                sub_ctx.consume()
            end_idx = sub_ctx.token_idx - 1

            param_def = self.parse_parameter_def(sub_ctx=Context(sub_ctx.tokens[start_idx:end_idx+1]))
            param_def_s.append(param_def)

            if sub_ctx.token_idx == len(sub_ctx.tokens) - 1:
                break

        return param_def_s

    def parse_parameter_def(self, sub_ctx: Context) -> ParamDefNode:
        """
        start with "parameter", end with expression / '\0' / ',' / ';':
            parameter x = 3;
            parameter int y = 4,
            parameter logic [2:0] z = 5
        """

        token = sub_ctx.current()
        assert token.kind_ == TokenKind.Parameter
        rdx = token.rdx
        cdx = token.cdx

        data_typ = None
        identifier = None
        default = None

        sub_ctx.consume()

        # data type - (bit/logic) (signed/unsigned) (range) / int / string, others are not implemented
        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            data_typ = self.parse_data_type_or_implicit_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax, parameter name is not specified,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        identifier = token
        sub_ctx.consume()

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Assignment:
            log.fatal(f"invalid syntax, '=' is expected to set default value for parameter,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        default_start_idx = sub_ctx.token_idx
        if sub_ctx.tokens[-1].kind_ in [TokenKind.EOF, TokenKind.Comma, TokenKind.SemiColon]:
            default_end_idx = len(sub_ctx.tokens) - 2
        else:
            default_end_idx = len(sub_ctx.tokens) - 1

        if sub_ctx.tokens[-1].kind == TokenKind.EOF:
            end_idx = len(sub_ctx.tokens) - 2
        else:
            end_idx = len(sub_ctx.tokens) - 1

        default = sub_ctx.tokens[default_start_idx:default_end_idx+1]

        return ParamDefNode(ldx=rdx, cdx=cdx, tokens=sub_ctx.tokens[:end_idx+1],
                            identifier=identifier,
                            data_type=data_typ,
                            default=default)

    def parse_port_list(self, sub_ctx: Context) -> list[AnsiPortDefNode] | list[NonAnsiPortDefNode]:
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.LParen

        nxt_token = sub_ctx.peek()
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
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.LParen
        sub_ctx.consume()

        array_identifiers = self.parse_array_identifiers_locally(Context(sub_ctx.tokens[1:-1]))
        non_ansi_port_s = []
        for identifier, _ in array_identifiers.identifier_size_s:
            non_ansi_port = NonAnsiPortDefNode(ldx=token.rdx, cdx=token.cdx, tokens=[identifier],
                                               identifier=identifier)
            non_ansi_port_s.append(non_ansi_port)

        return non_ansi_port_s

    def parse_ansi_port_def_list(self, sub_ctx: Context) -> list[AnsiPortDefNode]:
        """
        start with '(', end with ')'
        """
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.LParen
        sub_ctx.consume()

        ansi_port_def_s = []
        start_idx = -1
        while True:
            token = sub_ctx.current()
            if sub_ctx.token_idx == len(sub_ctx.tokens) - 1:
                assert token.kind_ == TokenKind.RParen
                break
            if sub_ctx.token_idx > len(sub_ctx.tokens) - 1:
                break
            if token.kind_ not in [TokenKind.Input, TokenKind.Output, TokenKind.Inout]:
                log.fatal(f"invalid syntax, 'input'/'output'/'inout' is expected,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            start_idx = sub_ctx.token_idx

            sub_ctx.consume()
            while True:
                token = sub_ctx.current()
                if sub_ctx.token_idx == len(sub_ctx.tokens) - 1:
                    end_idx = sub_ctx.token_idx
                elif token is None or token.kind_ in [TokenKind.Input, TokenKind.Output, TokenKind.Inout]:
                    end_idx = sub_ctx.token_idx - 1
                    break
                sub_ctx.consume()

            ansi_port_def = self.parse_ansi_port_def(sub_ctx=Context(sub_ctx.tokens[start_idx:end_idx+1]))
            ansi_port_def_s.append(ansi_port_def)

        return ansi_port_def_s

    def parse_ansi_port_def(self, sub_ctx: Context) -> AnsiPortDefNode:
        """
        start with "input" / "output" / "inout", end with <array_identifiers> / ',' / ';' / '\0'
        """

        token = sub_ctx.current()
        assert token.kind_ == TokenKind.Input or token.kind_ == TokenKind.Output or token.kind_ == TokenKind.Inout
        rdx = token.rdx
        cdx = token.cdx

        direction = None
        typ = None
        data_typ = None
        array_identifiers = None

        # direction - input/output/inout
        direction = token
        sub_ctx.consume()

        # type - wire/reg/var, others are not implemented
        token = sub_ctx.current()
        if token.kind_ == TokenKind.Wire or token.kind_ == TokenKind.Reg or token.kind_ == TokenKind.Var:
            typ = token
            sub_ctx.consume()

        # data type - (bit/logic) (signed/unsigned) (range) / int / string, others are not implemented
        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            data_typ = self.parse_data_type_or_implicit_locally(ctx=sub_ctx)

        # array identifiers
        token = sub_ctx.current()
        if token is not None and token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax, identifier is expected, rather than '{token}'\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        array_identifiers = self.parse_array_identifiers_locally(sub_ctx)

        return AnsiPortDefNode(ldx=rdx, cdx=cdx, tokens=sub_ctx.tokens,
                               direction=direction,
                               typ=typ,
                               data_type=data_typ,
                               array_identifiers=array_identifiers)

    def parse_data_type_or_implicit_locally(self, ctx: Context) -> DatatypeNode | None:
        token = ctx.current()
        rdx = token.rdx
        cdx = token.cdx

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
                          f"{self.error_context(token.rdx, token.cdx)}\n")
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
            return DatatypeNode(ldx=rdx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                                logic_or_bit=logic_or_bit,
                                signing=signing,
                                range_=range_,
                                inherent_data_type=inherent_data_type)

    def parse_range_or_index_locally(self, ctx: Context) -> RangeNode | IndexNode:
        token = ctx.current()
        assert token.kind_ == TokenKind.LBracket

        copied_ctx = Context(tokens=ctx.tokens, delete_eof=False)

        start_idx = ctx.token_idx
        ctx.consume_until_matching_pair(
            left=TokenKind.LBracket, right=TokenKind.RBracket,
            error_info=f"invalid syntax, '[' is not closed by ']'\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n"
        )
        end_idx = ctx.token_idx
        ctx.consume()
        tokens = ctx.tokens[start_idx:end_idx+1]

        copied_ctx.token_idx = start_idx
        has_colon = copied_ctx.consume_until_at_depth(
            left=TokenKind.LBracket, right=TokenKind.RBracket,
            expect=TokenKind.Colon,
            expected_depth=1,
            error_info="",
            just_try = True
        )

        if has_colon:
            return self.parse_range(sub_ctx=Context(tokens))
        else:
            return self.parse_index(sub_ctx=Context(tokens))

    def parse_range(self, sub_ctx: Context) -> RangeNode:
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.LBracket

        sub_ctx.consume_until_at_depth(
            left=TokenKind.LBracket, right=TokenKind.RBracket,
            expect=TokenKind.Colon,
            expected_depth=1,
            error_info=f"invalid syntax, ':' not found in range definition\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n"
        )
        colon_idx = sub_ctx.token_idx

        left = sub_ctx.tokens[1:colon_idx]
        right = sub_ctx.tokens[colon_idx+1:-1]

        return RangeNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens, left=left, right=right)

    def parse_index(self, sub_ctx: Context):
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.LBracket
        return IndexNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens, index=sub_ctx.tokens[1:-1])

    def parse_array_identifiers_locally(self, ctx: Context):
        """
        end with: <array_identifier> / ',' / '\0'
            a
            a, b
            a[2:0], b
            a[2:0], b, c[2:0][3:2]
            a, b, c,
        """

        token = ctx.current()
        rdx = token.rdx
        cdx = token.cdx
        assert token.kind_ == TokenKind.Identifier
        start_idx = ctx.token_idx

        identifier_size_s = []
        while True:
            token = ctx.current()
            if token.kind_ != TokenKind.Identifier:
                log.fatal(f"invalid syntax, identifier is expected, rather than '{token}',\n"
                          f"{self.error_context(rdx, cdx)}\n")
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

            if len(size) == 0:
                size = None
            identifier_size = (identifier, size)
            identifier_size_s.append(identifier_size)

            token = ctx.current()
            if token is not None and token.kind_ == TokenKind.Comma:
                end_idx = ctx.token_idx
                nxt_token = ctx.peek()
                if nxt_token is None:
                    break
                elif nxt_token.kind_ == TokenKind.Identifier:
                    ctx.consume()
                    continue
                else:
                    ctx.consume()
                    break
            elif token is not None and token.kind_ == TokenKind.SemiColon:
                end_idx = ctx.token_idx
                ctx.consume()
                break
            else:
                end_idx = ctx.token_idx - 1
                break

        return ArrayIdentifiersNode(ldx=rdx, cdx=cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                                    identifier_size_s=identifier_size_s)

    def parse_module_body(self, sub_ctx: Context) -> list[ModuleBodyItemNode]:
        items = []
        while True:
            token = sub_ctx.current()
            if token is None or token.kind_ == TokenKind.EOF:
                break
            elif token.kind_ == TokenKind.Parameter:
                items.append(self.parse_parameter_def_in_body_locally(sub_ctx))
            elif token.kind_ in [TokenKind.Input, TokenKind.Output, TokenKind.Inout]:
                items.append(self.parse_port_def_in_body_locally(sub_ctx))
            elif token.kind_ == TokenKind.Localparam:
                items.append(self.parse_localparam_def_locally(sub_ctx))
            elif token.kind_ in [TokenKind.Reg, TokenKind.Var, TokenKind.Wire]:
                items.append(self.parse_rvw_def_locally(sub_ctx))
            elif token.kind_ in [TokenKind.Int, TokenKind.ShortInt, TokenKind.LongInt,
                                 TokenKind.Real, TokenKind.ShortReal, TokenKind.Byte,
                                 TokenKind.Byte, TokenKind.String, TokenKind.Integer]:
                items.append(self.parse_inherent_type_var_locally(sub_ctx))
            elif token.kind_ in [TokenKind.Bit, TokenKind.Logic]:
                items.append(self.parse_bl_def_locally(sub_ctx))
            elif token.kind_ == TokenKind.Assign:
                items.append(self.parse_assign_locally(sub_ctx))
            elif token.kind_ in [TokenKind.Always, TokenKind.AlwaysComb, TokenKind.AlwaysFF, TokenKind.AlwaysLatch]:
                items.append(self.parse_always_block_locally(sub_ctx))
            elif token.kind_ == TokenKind.SemiColon:
                # empty statement
                sub_ctx.consume()
                continue
            elif token.kind_ == TokenKind.Identifier and sub_ctx.peek() is not None and sub_ctx.peek().kind_ in [
                TokenKind.Identifier, TokenKind.SharpPat
            ]:
                items.append(self.parse_instantiation_locally(sub_ctx))
            elif token.kind_ == TokenKind.EndModule:
                sub_ctx.consume()
                break
            else:
                assert 0, f"got token: {token}, not implemented yet\n"\
                          f"{self.error_context(token.rdx, token.cdx)}\n"
        return items

    def parse_parameter_def_in_body_locally(self, ctx: Context) -> ParamDefInBodyNode:
        """
        start with parameter, end with ';'
        """
        token = ctx.current()
        assert token.kind_ == TokenKind.Parameter
        start_idx = ctx.token_idx

        ctx.consume_until(
            token_kind=TokenKind.SemiColon,
            error_info=f"invalid syntax, ';' not found at the end of definition,\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n"
        )
        end_idx = ctx.token_idx
        ctx.consume()

        param_def_node = self.parse_parameter_def(sub_ctx=Context(ctx.tokens[start_idx:end_idx+1]))
        return ParamDefInBodyNode(ldx=param_def_node.ldx, cdx=param_def_node.cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                                  param_def_node=param_def_node)

    def parse_port_def_in_body_locally(self, ctx: Context) -> PortDefInBodyNode:
        """
        start with "input" / "output" / "inout", end with ';'
        """
        token = ctx.current()
        assert token.kind_ in [TokenKind.Input, TokenKind.Output, TokenKind.Inout]
        start_idx = ctx.token_idx

        ctx.consume_until(token_kind=TokenKind.SemiColon,
                          error_info=f"invalid syntax, ';' not found at the end of definition,\n"
                                     f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        port_def_node = self.parse_ansi_port_def(sub_ctx=Context(ctx.tokens[start_idx:end_idx+1]))
        return PortDefInBodyNode(ldx=port_def_node.ldx, cdx=port_def_node.cdx, tokens=ctx.tokens[start_idx:end_idx+1],
                                 port_def_node=port_def_node)

    def parse_localparam_def_locally(self, ctx: Context) -> LocalParamDefNode:
        """
        start with "localparam", end with ';'
        """
        token = ctx.current()
        assert token.kind_ == TokenKind.Localparam
        start_idx = ctx.token_idx

        ctx.consume_until(token_kind=TokenKind.SemiColon,
                          error_info=f"invalid syntax, ';' not found at the end of definition,\n"
                                     f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_localparam_def(sub_ctx=Context(ctx.tokens[start_idx:end_idx+1]))

    def parse_localparam_def(self, sub_ctx: Context) -> LocalParamDefNode:
        """
        start with "localparam", end with expression / '\0' / ';':
            localparam x = 3;
            localparam logic [2:0] z = 5
        """

        token = sub_ctx.current()
        assert token.kind_ == TokenKind.Localparam

        data_typ = None
        identifier = None
        val = None

        sub_ctx.consume()

        # data type - (bit/logic) (signed/unsigned) (range) / int / string, others are not implemented
        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            data_typ = self.parse_data_type_or_implicit_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax, localparam name is not specified,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        identifier = token
        sub_ctx.consume()

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Assignment:
            log.fatal(f"invalid syntax, '=' is expected to set value for localparam,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        val_start_idx = sub_ctx.token_idx
        if sub_ctx.tokens[-1].kind_ in [TokenKind.EOF, TokenKind.SemiColon]:
            val_end_idx = len(sub_ctx.tokens) - 2
        else:
            val_end_idx = len(sub_ctx.tokens) - 1

        if sub_ctx.tokens[-1].kind == TokenKind.EOF:
            end_idx = len(sub_ctx.tokens) - 2
        else:
            end_idx = len(sub_ctx.tokens) - 1

        val = sub_ctx.tokens[val_start_idx:val_end_idx+1]

        return LocalParamDefNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens[:end_idx+1],
                                 identifier=identifier,
                                 data_type=data_typ,
                                 val=val)

    def parse_rvw_def_locally(self, ctx: Context) -> VariableDefNode | VariableDefAndInitNode:
        """
        start with "reg/var/wire", end with ';'
        """
        token = ctx.current()
        assert token.kind_ in [TokenKind.Reg, TokenKind.Var, TokenKind.Wire]

        start_idx = ctx.token_idx

        ctx.consume_until(token_kind=TokenKind.SemiColon,
                          error_info=f"invalid syntax, ';' not found at the end of definition,"
                                     f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_rvw_def(sub_ctx=Context(ctx.tokens[start_idx:end_idx + 1]))

    def parse_rvw_def(self, sub_ctx: Context)  -> VariableDefNode | VariableDefAndInitNode:
        token = sub_ctx.current()
        assert token.kind_ in [TokenKind.Reg, TokenKind.Var, TokenKind.Wire]

        typ = token
        data_typ = None
        identifier = None
        val = None

        sub_ctx.consume()
        data_typ = self.parse_data_type_or_implicit_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax, identifier is expected to define {typ.src},\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        identifier = token
        sub_ctx.consume()

        token = sub_ctx.current()
        if token.kind_ == TokenKind.SemiColon:
            sub_ctx.consume()
            return VariableDefNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                   typ=typ,
                                   data_type=data_typ,
                                   identifier=identifier)

        if token.kind_ != TokenKind.Assignment:
            log.fatal(f"invalid syntax, '=' is expected to set initial value\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        start_idx = sub_ctx.token_idx
        sub_ctx.consume_until(
            token_kind=TokenKind.SemiColon,
            error_info=f"invalid syntax, ';' not found at the end of the statement,"
                       f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = sub_ctx.token_idx
        val = sub_ctx.tokens[start_idx:end_idx + 1]

        return VariableDefAndInitNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                      typ=typ,
                                      data_type=data_typ,
                                      identifier=identifier,
                                      val=val)

    def parse_bl_def_locally(self, ctx: Context) -> VariableDefNode | VariableDefAndInitNode:
        """
        start with "bit/logic", end with ';'
        """
        token = ctx.current()
        assert token.kind_ in [TokenKind.Bit, TokenKind.Logic]

        start_idx = ctx.token_idx

        ctx.consume_until(
            token_kind=TokenKind.SemiColon,
            error_info=f"invalid syntax, ';' not found at the end of the statement,\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_bl_def(sub_ctx=Context(ctx.tokens[start_idx:end_idx + 1]))

    def parse_bl_def(self, sub_ctx: Context)  -> VariableDefNode | VariableDefAndInitNode:
        token = sub_ctx.current()
        assert token.kind_ in [TokenKind.Bit, TokenKind.Logic]

        typ = None
        data_typ = None
        identifier = None
        val = None

        data_typ = self.parse_data_type_or_implicit_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax, identifier is expected to define {token.src} variable,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        identifier = token
        sub_ctx.consume()

        token = sub_ctx.current()
        if token.kind_ == TokenKind.SemiColon:
            sub_ctx.consume()
            return VariableDefNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                   typ=typ,
                                   data_type=data_typ,
                                   identifier=identifier)

        if token.kind_ != TokenKind.Assignment:
            log.fatal(f"invalid syntax, '=' is expected to set initial value,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        start_idx = sub_ctx.token_idx
        sub_ctx.consume_until(
            token_kind=TokenKind.SemiColon,
            error_info=f"invalid syntax, ';' not found at the end of the statement,\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = sub_ctx.token_idx
        val = sub_ctx.tokens[start_idx:end_idx + 1]

        return VariableDefAndInitNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                      typ=None,
                                      data_type=data_typ,
                                      identifier=identifier,
                                      val=val)

    def parse_inherent_type_var_locally(self, ctx: Context) -> VariableDefNode | VariableDefAndInitNode:
        """
        """
        token = ctx.current()
        assert token.kind_ in [TokenKind.Int, TokenKind.ShortInt, TokenKind.LongInt,
                               TokenKind.Real, TokenKind.ShortReal, TokenKind.Byte,
                               TokenKind.Byte, TokenKind.String, TokenKind.Integer]

        start_idx = ctx.token_idx

        ctx.consume_until(
            token_kind=TokenKind.SemiColon,
            error_info=f"invalid syntax, ';' not found at the end of the statement,"
                       f"{self.error_context(token.rdx, token.cdx)}\n"
        )
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_inherent_type_var(sub_ctx=Context(ctx.tokens[start_idx:end_idx + 1]))

    def parse_inherent_type_var(self, sub_ctx: Context)  -> VariableDefNode | VariableDefAndInitNode:
        token = sub_ctx.current()
        assert token.kind_ in [TokenKind.Int, TokenKind.ShortInt, TokenKind.LongInt,
                               TokenKind.Real, TokenKind.ShortReal, TokenKind.Byte,
                               TokenKind.Byte, TokenKind.String, TokenKind.Integer]

        typ = None
        data_typ = None
        identifier = None
        val = None

        data_typ = self.parse_data_type_or_implicit_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax, identifier is expected at the end of the statement,"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        identifier = token
        sub_ctx.consume()

        token = sub_ctx.current()
        if token.kind_ == TokenKind.SemiColon:
            sub_ctx.consume()
            return VariableDefNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                   typ=None,
                                   data_type=data_typ,
                                   identifier=identifier)

        if token.kind_ != TokenKind.Assignment:
            log.fatal(f"invalid syntax, '=' is expected at the end of the statement,"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        sub_ctx.consume()

        start_idx = sub_ctx.token_idx
        sub_ctx.consume_until(
            token_kind=TokenKind.SemiColon,
            error_info=f"invalid syntax, ';' not found,\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n"
        )
        end_idx = sub_ctx.token_idx
        val = sub_ctx.tokens[start_idx:end_idx + 1]

        return VariableDefAndInitNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                      typ=None,
                                      data_type=data_typ,
                                      identifier=identifier,
                                      val=val)

    def parse_assign_locally(self, ctx: Context) -> AssignNode:
        """
        end with ';'
        """
        token = ctx.current()
        start_idx = ctx.token_idx

        ctx.consume_until(
            token_kind=TokenKind.SemiColon,
            error_info=f"invalid syntax, ';' not found at the end of the statement,\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_assign(sub_ctx=Context(ctx.tokens[start_idx:end_idx + 1]))

    def parse_assign(self, sub_ctx: Context) -> AssignNode:
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.Assign
        sub_ctx.consume()

        sub_ctx.consume_until(
            token_kind=TokenKind.Assignment,
            error_info=f"invalid syntax, '=' not found in the assign statement,\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n")
        lhs_end_idx = sub_ctx.token_idx - 1
        sub_ctx.consume()

        return AssignNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens,
                          lhs=sub_ctx.tokens[1:lhs_end_idx+1], rhs=sub_ctx.tokens[lhs_end_idx+2:-1])

    def parse_always_block_locally(self, sub_ctx: Context) -> AlwaysBlockNode:
        token = sub_ctx.current()
        rdx = token.rdx
        cdx = token.cdx
        assert token.kind_ in [TokenKind.Always, TokenKind.AlwaysComb, TokenKind.AlwaysFF, TokenKind.AlwaysLatch]
        start_idx = sub_ctx.token_idx

        always_typ = token
        sensitivity_list = []

        sub_ctx.consume()
        token = sub_ctx.current()
        if token is not None and token.kind_ == TokenKind.At:
            sensitivity_list = self.parse_sensitivity_list_locally(ctx=sub_ctx)

        token = sub_ctx.current()
        if token is None or token.kind == TokenKind.EOF:
            log.fatal(f"invalid always block, it's in-complete,\n"
                      f"{self.error_context(rdx, cdx)}\n")
        elif token.kind_ == TokenKind.Begin:
            body_begin_idx = sub_ctx.token_idx
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.Begin, right=TokenKind.End,
                error_info=f"invalid syntax, no matching 'end' for 'begin',\n"
                           f"{self.error_context(rdx, cdx)}\n"
            )
            body_end_idx = sub_ctx.token_idx
            sub_ctx.consume()
            return AlwaysBlockNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens[start_idx:body_end_idx+1],
                                   always_typ=always_typ,
                                   sensitivity_list=sensitivity_list,
                                   body=sub_ctx.tokens[body_begin_idx+1:body_end_idx+1])
        else:
            body_begin_idx = sub_ctx.token_idx
            sub_ctx.consume_until(
                token_kind=TokenKind.SemiColon,
                error_info=f"invalid syntax, ';' not found at the end of the always block,\n"
                           f"{self.error_context(rdx, cdx)}\n"
            )
            body_end_idx = sub_ctx.token_idx
            sub_ctx.consume()
            return AlwaysBlockNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens[start_idx:body_end_idx+1],
                                   always_typ=always_typ,
                                   sensitivity_list=sensitivity_list,
                                   body=sub_ctx.tokens[body_begin_idx+1:body_end_idx+1])

    def parse_sensitivity_list_locally(self, ctx: Context) -> list[Token]:
        token = ctx.current()
        assert token.kind_ == TokenKind.At

        start_idx = ctx.token_idx
        ctx.consume()
        token = ctx.current()
        if token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax for sensitivity list, '(' is expected,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        ctx.consume_until(
            token_kind=TokenKind.RParen,
            error_info=f"invalid syntax for sensitivity list, no matching ')' found,\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n"
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
                                     f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = ctx.token_idx
        ctx.consume()

        return self.parse_instantiation(sub_ctx=Context(ctx.tokens[start_idx:end_idx + 1]))

    def parse_instantiation(self, sub_ctx: Context) -> InstantiationNode:
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.Identifier

        prototype_identifier = token
        para_set_list = []
        instance_identifier = None
        port_connect_list = []

        sub_ctx.consume()
        token = sub_ctx.current()

        if token.kind_ == TokenKind.SharpPat:
            # parameter set list
            sub_ctx.consume()
            token = sub_ctx.current()
            if token.kind_ != TokenKind.LParen:
                log.fatal(f"invalid syntax for instantiation, '(' is expected for parameter set block,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            start_idx = sub_ctx.token_idx
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.LParen, right=TokenKind.RParen,
                error_info=f"no matching ')' found at the end of parameter set block,\n"
                           f"{self.error_context(token.rdx, token.cdx)}\n")
            end_idx = sub_ctx.token_idx
            sub_ctx.consume()
            para_set_list = self.parse_para_set_list(sub_ctx=Context(sub_ctx.tokens[start_idx:end_idx + 1]))

        token = sub_ctx.current()
        if token.kind_ != TokenKind.Identifier:
            log.fatal(f"invalid syntax for instantiation, identifier is expected,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        instance_identifier = token
        sub_ctx.consume()

        token = sub_ctx.current()
        if token.kind_ != TokenKind.LParen:
            log.fatal(f"invalid syntax for instantiation, '(' is expected for port connection block,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError
        start_idx = sub_ctx.token_idx
        sub_ctx.consume_until_matching_pair(
            left=TokenKind.LParen, right=TokenKind.RParen,
            error_info=f"no matching ')' found at the end of port connection block,\n"
                       f"{self.error_context(token.rdx, token.cdx)}\n")
        end_idx = sub_ctx.token_idx
        sub_ctx.consume()
        port_connect_list = self.parse_port_connect_list(sub_ctx=Context(sub_ctx.tokens[start_idx:end_idx + 1]))

        token = sub_ctx.current()
        if token.kind_ != TokenKind.SemiColon:
            log.fatal(f"invalid syntax for instantiation, ';' is expected,\n"
                      f"{self.error_context(token.rdx, token.cdx)}\n")
            raise ParserError

        return InstantiationNode(ldx=token.rdx, cdx=token.cdx, tokens=sub_ctx.tokens,
                                 prototype_identifier=prototype_identifier,
                                 para_set_list=para_set_list,
                                 instance_identifier=instance_identifier,
                                 port_connect_list=port_connect_list)

    def parse_para_set_list(self, sub_ctx: Context) -> list[ParaSetNode]:
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.LParen
        assert sub_ctx.tokens[-1].kind_ == TokenKind.RParen
        para_set_list = []

        sub_ctx.consume()
        while True:
            token = sub_ctx.current()
            if token.kind_ == TokenKind.RParen:
                break
            if token.kind_ != TokenKind.Dot:
                log.fatal(f"invalid syntax for instantiation, to set the value of parameter, '.' is expected,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            para_set_start_idx = sub_ctx.token_idx
            para_set_rdx = sub_ctx.tokens[para_set_start_idx].rdx
            para_set_cdx = sub_ctx.tokens[para_set_start_idx].cdx
            sub_ctx.consume()

            token = sub_ctx.current()
            if token.kind_ != TokenKind.Identifier:
                log.fatal(f"invalid syntax for instantiation, to set the value of parameter, identifier is expected,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            para_name = token
            sub_ctx.consume()

            token = sub_ctx.current()
            if token.kind_ != TokenKind.LParen:
                log.fatal(f"invalid syntax for instantiation, to set the value of parameter, '(' is expected,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            start_idx = sub_ctx.token_idx + 1
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.LParen, right=TokenKind.RParen,
                error_info=f"no matching ')' found at the end of parameter set statement,\n"
                           f"{self.error_context(token.rdx, token.cdx)}\n")
            end_idx = sub_ctx.token_idx - 1
            sub_ctx.consume()
            para_val = sub_ctx.tokens[start_idx:end_idx+1]

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
                              f"{self.error_context(token.rdx, token.cdx)}\n")
                    raise ParserError
            para_set_list.append(ParaSetNode(ldx=para_set_rdx, cdx=para_set_cdx, tokens=sub_ctx.tokens[para_set_start_idx:para_set_end_idx+1],
                                             param_name=para_name,
                                             param_value=para_val))
        return para_set_list

    def parse_port_connect_list(self, sub_ctx: Context) -> list[PortConnectNode]:
        token = sub_ctx.current()
        assert token.kind_ == TokenKind.LParen
        assert sub_ctx.tokens[-1].kind_ == TokenKind.RParen
        port_connect_node = []

        sub_ctx.consume()
        while True:
            token = sub_ctx.current()
            if token.kind_ == TokenKind.RParen:
                break
            if token.kind_ != TokenKind.Dot:
                log.fatal(f"invalid syntax for instantiation, '.' is expected to connect port,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            port_connect_start_idx = sub_ctx.token_idx
            port_connect_rdx = sub_ctx.tokens[port_connect_start_idx].rdx
            port_connect_cdx = sub_ctx.tokens[port_connect_start_idx].cdx
            sub_ctx.consume()

            token = sub_ctx.current()
            if token.kind_ != TokenKind.Identifier:
                log.fatal(f"invalid syntax for instantiation, identifier is expected to connect port,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            port_name = token
            sub_ctx.consume()

            token = sub_ctx.current()
            if token.kind_ != TokenKind.LParen:
                log.fatal(f"invalid syntax for instantiation, '(' is expected to connect port,\n"
                          f"{self.error_context(token.rdx, token.cdx)}\n")
                raise ParserError
            start_idx = sub_ctx.token_idx + 1
            sub_ctx.consume_until_matching_pair(
                left=TokenKind.LParen, right=TokenKind.RParen,
                error_info=f"no matching ')' found at the end of port connect statement,\n"
                           f"{self.error_context(token.rdx, token.cdx)}\n"
            )
            end_idx = sub_ctx.token_idx - 1
            sub_ctx.consume()
            port_val = sub_ctx.tokens[start_idx:end_idx+1]

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
                              f"{self.error_context(token.rdx, token.cdx)}\n")
                    raise ParserError
            port_connect_node.append(PortConnectNode(ldx=port_connect_rdx, cdx=port_connect_cdx, tokens=sub_ctx.tokens[port_connect_start_idx:port_set_end_idx+1],
                                                     port_name=port_name,
                                                     port_value=port_val))
        return port_connect_node


if __name__ == "__main__":
#     verilog = \
# """
# (
#     input  wire logic [3:0] a, b[2][3], c, d[5:0], e,
#     output var  logic [3:0] f
# )
# """
#
#     parser = Parser(verilog, delete_eof=True)
#     print(parser.parse_ansi_port_def_list(sub_ctx=Context(tokens=parser.ctx.tokens)))
#
#     verilog = \
# """
# (a,b,c,d,e,f,g)
# """
#     parser = Parser(verilog, delete_eof=True)
#     print(parser.parse_non_ansi_port_def_list(sub_ctx=Context(tokens=parser.ctx.tokens)))
#
#
#     verilog = \
# """
# (
#     parameter int x = 1,
#     parameter logic [3:0] y = 0,
#     parameter logic z = -1
# )
# """
#     parser = Parser(verilog, delete_eof=True)
#     print(parser.parse_parameter_list(sub_ctx=Context(tokens=parser.ctx.tokens)))


    verilog = \
"""
module test_wrapper
#(
    parameter int     depth = 1024,
    parameter int     width = 10
 )
(
    input  wire logic [width-1:0]       op_a,
    input  wire logic [width-1:0]       op_b,
    input  wire logic [log2(depth)-1:0] addr,
    output var  logic [width-1:0]       res,
    
    inout                               dummy_0,
    input       bit                     dummy_1,
    input       bit  [9:0]              dummy_2,
    input  wire      [9:0]              dummy_3,
    output var       [9:0]              dummy_4,
    output      string                  dummy_5 
);


parameter int                  w = width;

input  wire logic [7:0]        non_ansi_a;
output var  logic              non_ansi_b;
inout              [w-1:0]     non_ansi_c;

localparam logic [w-1:0] dummy_param = 0;

wire logic   x = 1;
var          y = 2;
logic [15:0] z;
int          zz;
real         zzz;

assign       zzz = 3.0;

always@(posedge clk or negedge rstn) begin
    if(~rstn) begin
        z <= 1;
    end
    else if(en)
        z <= z + 1;
end

always_comb
    zz = x + y;
    
test u_test
(
    .a (a),
    .b ({b, b}),
    .c ((x+y)-z)
);

test
#(
  .width (log2(d+1)),
  .depth (d)
 )
u_test
(
    .a (a),
    .b ({b, b}),
    .c ((x+y)-z)
);

endmodule
"""
    parser = Parser(verilog, delete_eof=True)
    module = parser.parse_module_detail(sub_ctx=Context(tokens=parser.ctx.tokens))

    import yaml
    import dataclasses

    def remove_tokens_recursive(data):
        if isinstance(data, dict):
            if 'tokens' in data:
                del data['tokens']
            for key, value in data.items():
                data[key] = remove_tokens_recursive(value)
        elif isinstance(data, list):
            for i in range(len(data)):
                data[i] = remove_tokens_recursive(data[i])
        return data

    d = dataclasses.asdict(module)
    # d = remove_tokens_recursive(d)

    with open("test.yml", 'w', encoding="utf-8") as f:
        yaml.dump(d, f)
