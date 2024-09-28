import enum
import bisect
import dataclasses
import re

from reserved_word import reserved_words


def re_cap(pat: str) -> str:
    return f"({pat})"


def re_or(*pats: str) -> str:
    return r"|".join([f"(?:{pat})" for pat in pats])


def re_might(pat: str) -> str:
    return f"(?:{pat})?"


token_kinds: list[str] = []
token_matches: list[tuple[str, re.Pattern[str]]] = []
reserved_word_pat_pat: re.Pattern[str] = re.compile(r"\\b(\w+)\\b")
implemented_reserved_word: list[str] = []


def register_token_match(kind: str, pat: re.Pattern[str]):
    assert kind not in token_kinds
    token_kinds.append(kind)
    token_matches.append((kind, pat))
    cap = reserved_word_pat_pat.match(pat.pattern)
    if cap is not None:
        implemented_reserved_word.append(cap.group(1))


literal_pat_0 = re.compile(r"[0-9]*'[sS]?[bodhBODH][_0-9a-fA-F]+")
literal_pat_1 = re.compile(r"(?:[0-9]+\.)?[0-9]+(?:e[+-]?[0-9]+)?")
literal_pat_2 = re.compile(r"[_0-9]+")
literal_pat = re.compile(re_or(literal_pat_0.pattern, literal_pat_1.pattern, literal_pat_2))
string_literal_pat = re.compile(r'"(?:\\.|[^"\\])*(?:\\\n(?:\\.|[^"\\])*)*"')
identifier_pat = re.compile(r"[a-zA-Z_][a-zA-Z0-9_]*")
directive_pat = re.compile(r"`"+identifier_pat.pattern)
line_comment_pat = re.compile(r"//.*(?=\n|$)")
block_comment_pat = re.compile(r"/\*.*?\*/", re.DOTALL)


"""
how to match token
note: the order does matter!
"""

register_token_match("LineComment", line_comment_pat)
register_token_match("BlockComment", block_comment_pat)
register_token_match("StringLiteral", string_literal_pat)
register_token_match("Literal", literal_pat)
register_token_match("Directive", directive_pat)

""" symbols and in-divisible operators: systemverilog 2017 standard p255 """
register_token_match("Inside", re.compile(r"\binside\b"))
register_token_match("dist", re.compile(r"\bdist\b"))

register_token_match("ArithLeftShiftAssignment", re.compile(r"<<<="))
register_token_match("ArithRightShiftAssignment", re.compile(r">>>="))

register_token_match("ArithLeftShift", re.compile(r"<<<"))
register_token_match("ArithRightShift", re.compile(r">>>"))
register_token_match("CaseEqual", re.compile(r"==="))
register_token_match("CaseInEqual", re.compile(r"!=="))
register_token_match("WildcardEqual", re.compile(r"==\?"))
register_token_match("WildcardInEqual", re.compile(r"!=\?"))
register_token_match("LogicLeftShiftAssignment", re.compile(r"<<="))
register_token_match("LogicRightShiftAssignment", re.compile(r">>="))
register_token_match("Equivalence", re.compile(r"<->"))

register_token_match("DoubleBackQuote", re.compile(r"``"))
register_token_match("Pow", re.compile(r"\*\*"))
register_token_match("Equal", re.compile(r"=="))
register_token_match("InEqual", re.compile(r"!="))
register_token_match("LessThan", re.compile(r"<"))
register_token_match("GreaterThan", re.compile(r">"))
register_token_match("LessEqual", re.compile(r"<="))
register_token_match("GreaterEqual", re.compile(r">="))
register_token_match("LogicAnd", re.compile(r"&&"))
register_token_match("LogicOr", re.compile(r"\|\|"))
register_token_match("LogicLeftShift", re.compile(r"<<"))
register_token_match("LogicRightShift", re.compile(r">>"))
register_token_match("AddAssignment", re.compile(r"\+="))
register_token_match("SubAssignment", re.compile(r"\-="))
register_token_match("MulAssignment", re.compile(r"\*="))
register_token_match("DivAssignment", re.compile(r"/="))
register_token_match("ModAssignment", re.compile(r"%="))
register_token_match("BitAndAssignment", re.compile(r"&="))
register_token_match("BitOrAssignment", re.compile(r"\|="))
register_token_match("BitXorAssignment", re.compile(r"\^="))
register_token_match("Implication", re.compile(r"->"))

register_token_match("BackQuote", re.compile(r"`"))
register_token_match("SharpPat", re.compile(r"#"))
register_token_match("LParen", re.compile(r"\("))
register_token_match("RParen", re.compile(r"\)"))
register_token_match("LBrace", re.compile(r"\{"))
register_token_match("RBrace", re.compile(r"\}"))
register_token_match("LBracket", re.compile(r"\["))
register_token_match("RBracket", re.compile(r"\]"))
register_token_match("Comma", re.compile(r","))
register_token_match("Colon", re.compile(r":"))
register_token_match("SemiColon", re.compile(r";"))
register_token_match("At", re.compile(r"@"))
register_token_match("Dot", re.compile(r"\."))
register_token_match("SingleQuote", re.compile(r"'"))
register_token_match("DoubleQuote", re.compile(r'"'))
register_token_match("BackSlash", re.compile(r"\\"))
register_token_match("Dollar", re.compile(r"\$"))
register_token_match("QuestionMark", re.compile(r"\?"))
register_token_match("Assignment", re.compile(r"="))
register_token_match("Add", re.compile(r"\+"))
register_token_match("Sub", re.compile(r"\-"))
register_token_match("Mul", re.compile(r"\*"))
register_token_match("Div", re.compile(r"/"))
register_token_match("Mod", re.compile(r"%"))
register_token_match("BitAnd", re.compile(r"&"))
register_token_match("BitOr", re.compile(r"\|"))
register_token_match("BitXor", re.compile(r"\^"))
register_token_match("BitNot", re.compile(r"~"))
register_token_match("LogicNot", re.compile(r"!"))

""" pairs """
register_token_match("Begin", re.compile(r"\bbegin\b"))
register_token_match("End", re.compile(r"\bend\b"))
register_token_match("Class", re.compile(r"\bclass\b"))
register_token_match("EndClass", re.compile(r"\bendclass\b"))
register_token_match("Case", re.compile(r"\bcase\b"))
register_token_match("EndCase", re.compile(r"\bendcase\b"))
register_token_match("Config", re.compile(r"\bconfig\b"))
register_token_match("EndConfig", re.compile(r"\bendconfig\b"))
register_token_match("Function", re.compile(r"\bfunction\b"))
register_token_match("EndFunction", re.compile(r"\bendfunction\b"))
register_token_match("Generate", re.compile(r"\bgenerate\b"))
register_token_match("EndGenerate", re.compile(r"\bendgenerate\b"))
register_token_match("Group", re.compile(r"\bgroup\b"))
register_token_match("EndGroup", re.compile(r"\bendgroup\b"))
register_token_match("Interface", re.compile(r"\binterface\b"))
register_token_match("EndInterface", re.compile(r"\bendinterface\b"))
register_token_match("Module", re.compile(r"\bmodule\b"))
register_token_match("EndModule", re.compile(r"\bendmodule\b"))
register_token_match("Package", re.compile(r"\bpackage\b"))
register_token_match("EndPackage", re.compile(r"\bendpackage\b"))
register_token_match("Program", re.compile(r"\bprogram\b"))
register_token_match("EndProgram", re.compile(r"\bendprogram\b"))
register_token_match("Property", re.compile(r"\bproperty\b"))
register_token_match("EndProperty", re.compile(r"\bendproperty\b"))
register_token_match("Task", re.compile(r"\btask\b"))
register_token_match("EndTask", re.compile(r"\bendtask\b"))

""" control statement """
register_token_match("If", re.compile(r"\bif\b"))
register_token_match("Else", re.compile(r"\belse\b"))
register_token_match("For", re.compile(r"\bfor\b"))
register_token_match("ForEach", re.compile(r"\bforeach\b"))
register_token_match("Do", re.compile(r"\bdo\b"))
register_token_match("While", re.compile(r"\bwhile\b"))
register_token_match("Break", re.compile(r"\bbreak\b"))
register_token_match("Continue", re.compile(r"\bcontinue\b"))
register_token_match("Return", re.compile(r"\breturn\b"))

""" procedure statement """
register_token_match("Always", re.compile(r"\balways\b"))
register_token_match("AlwaysComb", re.compile(r"\balways_comb\b"))
register_token_match("AlwaysFF", re.compile(r"\balways_ff\b"))
register_token_match("AlwaysLatch", re.compile(r"\balways_latch\b"))
register_token_match("Initial", re.compile(r"\binitial\b"))
register_token_match(f"Final", re.compile(r"\bfinal\b"))
register_token_match("Repeat", re.compile(r"\brepeat\b"))
register_token_match("Forever", re.compile(r"\bforever\b"))
register_token_match("Fork", re.compile(r"\bfork\b"))
register_token_match("Join", re.compile(r"\bjoin\b"))
register_token_match("JoinAny", re.compile(r"\bjoin_any\b"))
register_token_match("JoinNone", re.compile(r"\bjoin_none\b"))

""" event """
register_token_match("Posedge", re.compile(r"\bposedge\b"))
register_token_match("Negedge", re.compile(r"\bnegedge\b"))

""" type """
register_token_match("Int", re.compile(r"\bint\b"))
register_token_match("Integer", re.compile(r"\binteger\b"))
register_token_match("Real", re.compile(r"\breal\b"))
register_token_match("ShortInt", re.compile(r"\bshortint\b"))
register_token_match("ShortReal", re.compile(r"\bshortreal\b"))
register_token_match("LongInt", re.compile(r"\blongint\b"))
register_token_match("Byte", re.compile(r"\bbyte\b"))
register_token_match("String", re.compile(r"\bstring\b"))
register_token_match("Enum", re.compile(r"\benum\b"))
register_token_match("Struct", re.compile(r"\bstruct\b"))
register_token_match("Union", re.compile(r"\bunion\b"))
register_token_match("Const", re.compile(r"\bconst\b"))
register_token_match("Signed", re.compile(r"\bsigned\b"))
register_token_match("Unsigned", re.compile(r"\bunsigned\b"))
register_token_match("Static", re.compile(r"\bstatic\b"))
register_token_match("Auto", re.compile(r"\bauto\b"))
register_token_match("Virtual", re.compile(r"\bvirtual\b"))
register_token_match("Ref", re.compile(r"\bref\b"))

register_token_match("Parameter", re.compile(r"\bparameter\b"))
register_token_match("Localparam", re.compile(r"\blocalparam\b"))
register_token_match("Input", re.compile(r"\binput\b"))
register_token_match("Output", re.compile(r"\boutput\b"))
register_token_match("Inout", re.compile(r"\binout\b"))
register_token_match("Wire", re.compile(r"\bwire\b"))
register_token_match("Reg", re.compile(r"\breg\b"))
register_token_match("Var", re.compile(r"\bvar\b"))
register_token_match("Logic", re.compile(r"\blogic\b"))
register_token_match("Bit", re.compile(r"\bbit\b"))
register_token_match("Alias", re.compile(r"\balias\b"))
register_token_match("Assign", re.compile(r"\bassign\b"))

""" time """
register_token_match("Second", re.compile(r"\bs\b"))
register_token_match("MiniSecond", re.compile(r"\bms\b"))
register_token_match("MicroSecond", re.compile(r"\bus\b"))
register_token_match("NanoSecond", re.compile(r"\bns\b"))
register_token_match("PicoSecond", re.compile(r"\bps\b"))
register_token_match("FemtoSecond", re.compile(r"\bfs\b"))

for word in reserved_words:
    if word not in implemented_reserved_word:
        register_token_match(word[0].upper()+word[1:], re.compile(fr"\b{word}\b"))
register_token_match("Identifier", identifier_pat)
register_token_match("EOF", re.compile('\0'))

print(f"{implemented_reserved_word}")


@dataclasses.dataclass
class Token:
    kind: str
    rdx: int
    cdx: int
    val: str

    def __str__(self):
        return f"kind: {self.kind:<20}, rdx: {self.rdx:<5}, cdx: {self.cdx:<5}, val: {self.val}"


class Lexer:
    def __init__(self, context: str, eol: str = '\n'):
        self.eol: str = eol
        self.context: str = context
        self.context_len: str = len(context)
        self.char_num_on_each_row: int = self.get_char_num_on_each_row(context)
        self.accumulated_char_num_on_each_row: int = \
            [sum(self.char_num_on_each_row[0:i+1]) for i in range(len(self.char_num_on_each_row))]
        self.idx: int = 0
        self.tokens: list[Token] = []
        self.tokenize()

    def get_char_num_on_each_row(self, context: str) -> list[int]:
        lines = context.split(self.eol)
        return [len(lines[ldx]) + 1 if ldx != len(lines)-1 else len(lines[ldx]) for ldx in range(len(lines))]

    def get_rcdx_from_idx(self, idx: int) -> int:
        rdx = bisect.bisect_right(self.accumulated_char_num_on_each_row, idx)
        if rdx != 0:
            cdx = idx - self.accumulated_char_num_on_each_row[rdx-1]
        else:
            cdx = idx
        return rdx, cdx

    def tokenize(self):
        while True:
            remains = self.context[self.idx:]
            rdx, cdx = self.get_rcdx_from_idx(self.idx)
            if not remains:
                token = Token(kind="EOF", rdx=rdx, cdx=cdx, val="\0")
                print(f"idx: {self.idx:<5}, {token}")
                self.tokens.append(token)
                break
            matched = False
            if remains[0] == ' ' or remains[0] == '\t' or remains[0] == '\n':
                self.idx += 1
                continue
            if remains[0] == '\0':
                break
            if len(remains) > 6 and remains[0:6] == "25_789":
                print("")
            for token_match in token_matches:
                re_pat = token_match[1]
                _ = re_pat.search(remains)
                if _ is not None and _.start() == 0:
                    token = Token(kind=token_match[0], rdx=rdx, cdx=cdx, val=_.group(0))
                    print(f"idx: {self.idx:<5}, {token}")
                    self.tokens.append(token)
                    self.idx += len(_.group(0))
                    matched = True
                    break
            if not matched:
                assert 0, f"invalid syntax, idx: {self.idx}, rdx: {rdx}, cdx: {cdx}, remains:\n"\
                          f"{remains}"


if __name__ == "__main__":
    code = r"8'b0"
    _ = literal_pat.match(code)
    assert _ is not None

    code = r"16'sh17ff"
    _ = literal_pat.match(code)
    assert _ is not None

    code = r"'o777"
    _ = literal_pat.match(code)
    assert _ is not None

    code = r"1324"
    _ = literal_pat.match(code)
    assert _ is not None

    code = r'''
    $display("Humpty Dumpty sat on a wall. \
    Humpty Dumpty had a great fall.");
    '''
    _ = string_literal_pat.search(code)
    assert _ is not None

    code = r"foo"
    _ = identifier_pat.match(code)
    assert _ is not None

    code = r"bar_"
    _ = identifier_pat.match(code)
    assert _ is not None

    code = "`timescale"
    _ = directive_pat.match(code)
    assert _ is not None

    cdoe = "`define"
    _ = directive_pat.match(code)
    assert _ is not None

    code = "// comment // comment"
    _ = line_comment_pat.match(code)
    assert _ is not None

    code = "/* comment */"
    _ = block_comment_pat.match(code)
    assert _ is not None

    code = """/* comment
    /*
    */
    """
    _ = block_comment_pat.match(code)
    print(code)
    assert _ is not None

    with open("./rich_grammar.sv", 'r', encoding='utf-8') as f:
        context = f.read()

    lexer = Lexer(context=context)
