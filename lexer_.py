import bisect
import enum
import dataclasses
import re

from reserved_word import reserved_words


class TokenKind(enum.Enum):
    LineComment = enum.auto()
    BlockComment = enum.auto()
    StringLiteral = enum.auto()
    Literal = enum.auto()
    Directive = enum.auto()
    Inside = enum.auto()
    dist = enum.auto()
    ArithLeftShiftAssignment = enum.auto()
    ArithRightShiftAssignment = enum.auto()
    ArithLeftShift = enum.auto()
    ArithRightShift = enum.auto()
    CaseEqual = enum.auto()
    CaseInEqual = enum.auto()
    WildcardEqual = enum.auto()
    WildcardInEqual = enum.auto()
    LogicLeftShiftAssignment = enum.auto()
    LogicRightShiftAssignment = enum.auto()
    Equivalence = enum.auto()
    DoubleBackQuote = enum.auto()
    Pow = enum.auto()
    Equal = enum.auto()
    InEqual = enum.auto()
    LessThan = enum.auto()
    GreaterThan = enum.auto()
    LessEqual = enum.auto()
    GreaterEqual = enum.auto()
    LogicAnd = enum.auto()
    LogicOr = enum.auto()
    LogicLeftShift = enum.auto()
    LogicRightShift = enum.auto()
    AddAssignment = enum.auto()
    SubAssignment = enum.auto()
    MulAssignment = enum.auto()
    DivAssignment = enum.auto()
    ModAssignment = enum.auto()
    BitAndAssignment = enum.auto()
    BitOrAssignment = enum.auto()
    BitXorAssignment = enum.auto()
    Implication = enum.auto()
    BackQuote = enum.auto()
    SharpPat = enum.auto()
    LParen = enum.auto()
    RParen = enum.auto()
    SingleQuoteLBrace = enum.auto()
    LBrace = enum.auto()
    RBrace = enum.auto()
    LBracket = enum.auto()
    RBracket = enum.auto()
    Comma = enum.auto()
    Colon = enum.auto()
    SemiColon = enum.auto()
    At = enum.auto()
    Dot = enum.auto()
    ScopeResolution = enum.auto()
    SelfIncrement = enum.auto()
    SelfDecrement = enum.auto()
    SingleQuote = enum.auto()
    DoubleQuote = enum.auto()
    BackSlash = enum.auto()
    Dollar = enum.auto()
    QuestionMark = enum.auto()
    Assignment = enum.auto()
    Add = enum.auto()
    Sub = enum.auto()
    Mul = enum.auto()
    Div = enum.auto()
    Mod = enum.auto()
    BitAnd = enum.auto()
    BitOr = enum.auto()
    BitXor = enum.auto()
    BitNot = enum.auto()
    LogicNot = enum.auto()
    Begin = enum.auto()
    End = enum.auto()
    Class = enum.auto()
    EndClass = enum.auto()
    Case = enum.auto()
    EndCase = enum.auto()
    Config = enum.auto()
    EndConfig = enum.auto()
    Function = enum.auto()
    EndFunction = enum.auto()
    Generate = enum.auto()
    EndGenerate = enum.auto()
    Group = enum.auto()
    EndGroup = enum.auto()
    Interface = enum.auto()
    EndInterface = enum.auto()
    Module = enum.auto()
    EndModule = enum.auto()
    Package = enum.auto()
    EndPackage = enum.auto()
    Program = enum.auto()
    EndProgram = enum.auto()
    Property = enum.auto()
    EndProperty = enum.auto()
    Task = enum.auto()
    EndTask = enum.auto()
    If = enum.auto()
    Else = enum.auto()
    For = enum.auto()
    ForEach = enum.auto()
    Do = enum.auto()
    While = enum.auto()
    Break = enum.auto()
    Continue = enum.auto()
    Return = enum.auto()
    Always = enum.auto()
    AlwaysComb = enum.auto()
    AlwaysFF = enum.auto()
    AlwaysLatch = enum.auto()
    Initial = enum.auto()
    Final = enum.auto()
    Repeat = enum.auto()
    Forever = enum.auto()
    Fork = enum.auto()
    Join = enum.auto()
    JoinAny = enum.auto()
    JoinNone = enum.auto()
    Posedge = enum.auto()
    Negedge = enum.auto()
    Int = enum.auto()
    Integer = enum.auto()
    Real = enum.auto()
    ShortInt = enum.auto()
    ShortReal = enum.auto()
    LongInt = enum.auto()
    Byte = enum.auto()
    String = enum.auto()
    Enum = enum.auto()
    Struct = enum.auto()
    Union = enum.auto()
    Const = enum.auto()
    Signed = enum.auto()
    Unsigned = enum.auto()
    Static = enum.auto()
    Auto = enum.auto()
    Virtual = enum.auto()
    Ref = enum.auto()
    Parameter = enum.auto()
    Localparam = enum.auto()
    Input = enum.auto()
    Output = enum.auto()
    Inout = enum.auto()
    Wire = enum.auto()
    Reg = enum.auto()
    Var = enum.auto()
    Logic = enum.auto()
    Bit = enum.auto()
    Alias = enum.auto()
    Assign = enum.auto()
    Second = enum.auto()
    MiniSecond = enum.auto()
    MicroSecond = enum.auto()
    NanoSecond = enum.auto()
    PicoSecond = enum.auto()
    FemtoSecond = enum.auto()
    Accept_on = enum.auto()
    And = enum.auto()
    Assert = enum.auto()
    Assume = enum.auto()
    Automatic = enum.auto()
    Before = enum.auto()
    Bind = enum.auto()
    Bins = enum.auto()
    Binsof = enum.auto()
    Buf = enum.auto()
    Bufif0 = enum.auto()
    Bufif1 = enum.auto()
    Casex = enum.auto()
    Casez = enum.auto()
    Cell = enum.auto()
    Chandle = enum.auto()
    Checker = enum.auto()
    Clocking = enum.auto()
    Cmos = enum.auto()
    Constraint = enum.auto()
    Context = enum.auto()
    Cover = enum.auto()
    Covergroup = enum.auto()
    Coverpoint = enum.auto()
    Cross = enum.auto()
    Deassign = enum.auto()
    Default = enum.auto()
    Defparam = enum.auto()
    Design = enum.auto()
    Disable = enum.auto()
    Edge = enum.auto()
    Endchecker = enum.auto()
    Endclocking = enum.auto()
    Endprimitive = enum.auto()
    Endspecify = enum.auto()
    Endsequence = enum.auto()
    Endtable = enum.auto()
    Event = enum.auto()
    Eventually = enum.auto()
    Expect = enum.auto()
    Export = enum.auto()
    Extends = enum.auto()
    Extern = enum.auto()
    First_match = enum.auto()
    Force = enum.auto()
    Forkjoin = enum.auto()
    Genvar = enum.auto()
    Global = enum.auto()
    Highz0 = enum.auto()
    Highz1 = enum.auto()
    Iff = enum.auto()
    Ifnone = enum.auto()
    Ignore_bins = enum.auto()
    Illegal_bins = enum.auto()
    Implements = enum.auto()
    Implies = enum.auto()
    Import = enum.auto()
    Incdir = enum.auto()
    Include = enum.auto()
    Instance = enum.auto()
    Interconnect = enum.auto()
    Intersect = enum.auto()
    Large = enum.auto()
    Let = enum.auto()
    Liblist = enum.auto()
    Library = enum.auto()
    Local = enum.auto()
    Macromodule = enum.auto()
    Matches = enum.auto()
    Medium = enum.auto()
    Modport = enum.auto()
    Nand = enum.auto()
    Nettype = enum.auto()
    New = enum.auto()
    Nexttime = enum.auto()
    Nmos = enum.auto()
    Nor = enum.auto()
    Noshowcancelled = enum.auto()
    Not = enum.auto()
    Notif0 = enum.auto()
    Notif1 = enum.auto()
    Null = enum.auto()
    Or = enum.auto()
    Packed = enum.auto()
    Pmos = enum.auto()
    Primitive = enum.auto()
    Priority = enum.auto()
    Protected = enum.auto()
    Pull0 = enum.auto()
    Pull1 = enum.auto()
    Pulldown = enum.auto()
    Pullup = enum.auto()
    Pulsestyle_ondetect = enum.auto()
    Pulsestyle_onevent = enum.auto()
    Pure = enum.auto()
    Rand = enum.auto()
    Randc = enum.auto()
    Randcase = enum.auto()
    Randsequence = enum.auto()
    Rcmos = enum.auto()
    Realtime = enum.auto()
    Reject_on = enum.auto()
    Release = enum.auto()
    Restrict = enum.auto()
    Rnmos = enum.auto()
    Rpmos = enum.auto()
    Rtran = enum.auto()
    Rtranif0 = enum.auto()
    Rtranif1 = enum.auto()
    S_always = enum.auto()
    S_eventually = enum.auto()
    S_nexttime = enum.auto()
    S_until = enum.auto()
    S_until_with = enum.auto()
    Scalared = enum.auto()
    Sequence = enum.auto()
    Showcancelled = enum.auto()
    Small = enum.auto()
    Soft = enum.auto()
    Solve = enum.auto()
    Specify = enum.auto()
    Specparam = enum.auto()
    Strong = enum.auto()
    Strong0 = enum.auto()
    Strong1 = enum.auto()
    Super = enum.auto()
    Supply0 = enum.auto()
    Supply1 = enum.auto()
    Sync_accept_on = enum.auto()
    Sync_reject_on = enum.auto()
    Table = enum.auto()
    Tagged = enum.auto()
    This = enum.auto()
    Throughout = enum.auto()
    Time = enum.auto()
    Timeprecision = enum.auto()
    Timeunit = enum.auto()
    Tran = enum.auto()
    Tranif0 = enum.auto()
    Tranif1 = enum.auto()
    Tri = enum.auto()
    Tri0 = enum.auto()
    Tri1 = enum.auto()
    Triand = enum.auto()
    Trior = enum.auto()
    Trireg = enum.auto()
    Type = enum.auto()
    Typedef = enum.auto()
    Unique = enum.auto()
    Unique0 = enum.auto()
    Until = enum.auto()
    Until_with = enum.auto()
    Untyped = enum.auto()
    Use = enum.auto()
    Uwire = enum.auto()
    Vectored = enum.auto()
    Void = enum.auto()
    Wait = enum.auto()
    Wait_order = enum.auto()
    Wand = enum.auto()
    Weak = enum.auto()
    Weak0 = enum.auto()
    Weak1 = enum.auto()
    Wildcard = enum.auto()
    With = enum.auto()
    Within = enum.auto()
    Wor = enum.auto()
    Xnor = enum.auto()
    Xor = enum.auto()
    Identifier = enum.auto()
    EOF = enum.auto()



def re_cap(pat: str) -> str:
    return f"({pat})"


def re_or(*pats: str) -> str:
    return r"|".join([f"(?:{pat})" for pat in pats])


def re_might(pat: str) -> str:
    return f"(?:{pat})?"


token_kinds: list[str] = []
token_matches: list[tuple[str, re.Pattern[str]]] = []
reserved_word_pat_pat: re.Pattern[str] = re.compile(r"\^"+r"\\b(\w+)\\b")
implemented_reserved_word: list[str] = []


def register_token_match(kind: str, pat: re.Pattern[str]):
    assert kind not in token_kinds
    token_kinds.append(kind)
    token_matches.append((kind, pat))
    cap = reserved_word_pat_pat.match(pat.pattern)
    if cap is not None:
        implemented_reserved_word.append(cap.group(1))


literal_pat_0 = re.compile(r"^"+r"[0-9]*'[sS]?[bodhBODH][_0-9a-fA-F]+")
literal_pat_1 = re.compile(r"^"+r"(?:[0-9]+\.)?[0-9]+(?:e[+-]?[0-9]+)?")
literal_pat_2 = re.compile(r"^"+r"[_0-9]+")
literal_pat = re.compile(r"^"+re_or(literal_pat_0.pattern, literal_pat_1.pattern, literal_pat_2))
string_literal_pat = re.compile(r"^"+r'"(?:\\.|[^"\\])*(?:\\\n(?:\\.|[^"\\])*)*"')
identifier_pat = re.compile(r"^"+r"[\$a-zA-Z_][a-zA-Z0-9_]*")
directive_pat = re.compile(r"^"+r"`"+identifier_pat.pattern[1:])
line_comment_pat = re.compile(r"^"+r"//.*(?=\n|$)")
block_comment_pat = re.compile(r"^"+r"/\*.*?\*/", re.DOTALL)


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
register_token_match("Inside", re.compile(r"^"+r"\binside\b"))
register_token_match("dist", re.compile(r"^"+r"\bdist\b"))

register_token_match("ArithLeftShiftAssignment", re.compile(r"^"+r"<<<="))
register_token_match("ArithRightShiftAssignment", re.compile(r"^"+r">>>="))

register_token_match("ArithLeftShift", re.compile(r"^"+r"<<<"))
register_token_match("ArithRightShift", re.compile(r"^"+r">>>"))
register_token_match("CaseEqual", re.compile(r"^"+r"==="))
register_token_match("CaseInEqual", re.compile(r"^"+r"!=="))
register_token_match("WildcardEqual", re.compile(r"^"+r"==\?"))
register_token_match("WildcardInEqual", re.compile(r"^"+r"!=\?"))
register_token_match("LogicLeftShiftAssignment", re.compile(r"^"+r"<<="))
register_token_match("LogicRightShiftAssignment", re.compile(r"^"+r">>="))
register_token_match("Equivalence", re.compile(r"^"+r"<->"))

register_token_match("DoubleBackQuote", re.compile(r"^"+r"``"))
register_token_match("Pow", re.compile(r"^"+r"\*\*"))
register_token_match("Equal", re.compile(r"^"+r"=="))
register_token_match("LessEqual", re.compile(r"^"+r"<="))
register_token_match("GreaterEqual", re.compile(r"^"+r">="))
register_token_match("LogicAnd", re.compile(r"^"+r"&&"))
register_token_match("LogicOr", re.compile(r"^"+r"\|\|"))
register_token_match("LogicLeftShift", re.compile(r"^"+r"<<"))
register_token_match("LogicRightShift", re.compile(r"^"+r">>"))
register_token_match("AddAssignment", re.compile(r"^"+r"\+="))
register_token_match("SubAssignment", re.compile(r"^"+r"\-="))
register_token_match("MulAssignment", re.compile(r"^"+r"\*="))
register_token_match("DivAssignment", re.compile(r"^"+r"/="))
register_token_match("ModAssignment", re.compile(r"^"+r"%="))
register_token_match("BitAndAssignment", re.compile(r"^"+r"&="))
register_token_match("BitOrAssignment", re.compile(r"^"+r"\|="))
register_token_match("BitXorAssignment", re.compile(r"^"+r"\^="))
register_token_match("Implication", re.compile(r"^"+r"->"))
register_token_match("ScopeResolution", re.compile(r"^"+r"::"))
register_token_match("SelfIncrement", re.compile(r"^"+r"\+\+"))
register_token_match("SelfDecrement", re.compile(r"^"+r"--"))
register_token_match("SingleQuoteLBrace", re.compile(r"^"+r"'\{"))

register_token_match("BackQuote", re.compile(r"^"+r"`"))
register_token_match("SharpPat", re.compile(r"^"+r"#"))
register_token_match("LParen", re.compile(r"^"+r"\("))
register_token_match("RParen", re.compile(r"^"+r"\)"))
register_token_match("LBrace", re.compile(r"^"+r"\{"))
register_token_match("RBrace", re.compile(r"^"+r"\}"))
register_token_match("LBracket", re.compile(r"^"+r"\["))
register_token_match("RBracket", re.compile(r"^"+r"\]"))
register_token_match("Comma", re.compile(r"^"+r","))
register_token_match("Colon", re.compile(r"^"+r":"))
register_token_match("SemiColon", re.compile(r"^"+r";"))
register_token_match("At", re.compile(r"^"+r"@"))
register_token_match("Dot", re.compile(r"^"+r"\."))
register_token_match("SingleQuote", re.compile(r"^"+r"'"))
register_token_match("DoubleQuote", re.compile(r"^"+r'"'))
register_token_match("BackSlash", re.compile(r"^"+r"\\"))
register_token_match("QuestionMark", re.compile(r"^"+r"\?"))
register_token_match("Assignment", re.compile(r"^"+r"="))
register_token_match("Add", re.compile(r"^"+r"\+"))
register_token_match("Sub", re.compile(r"^"+r"\-"))
register_token_match("Mul", re.compile(r"^"+r"\*"))
register_token_match("Div", re.compile(r"^"+r"/"))
register_token_match("Mod", re.compile(r"^"+r"%"))
register_token_match("BitAnd", re.compile(r"^"+r"&"))
register_token_match("BitOr", re.compile(r"^"+r"\|"))
register_token_match("BitXor", re.compile(r"^"+r"\^"))
register_token_match("BitNot", re.compile(r"^"+r"~"))
register_token_match("LogicNot", re.compile(r"^"+r"!"))
register_token_match("InEqual", re.compile(r"^"+r"!="))
register_token_match("LessThan", re.compile(r"^"+r"<"))
register_token_match("GreaterThan", re.compile(r"^"+r">"))

""" pairs """
register_token_match("Begin", re.compile(r"^"+r"\bbegin\b"))
register_token_match("End", re.compile(r"^"+r"\bend\b"))
register_token_match("Class", re.compile(r"^"+r"\bclass\b"))
register_token_match("EndClass", re.compile(r"^"+r"\bendclass\b"))
register_token_match("Case", re.compile(r"^"+r"\bcase\b"))
register_token_match("EndCase", re.compile(r"^"+r"\bendcase\b"))
register_token_match("Config", re.compile(r"^"+r"\bconfig\b"))
register_token_match("EndConfig", re.compile(r"^"+r"\bendconfig\b"))
register_token_match("Function", re.compile(r"^"+r"\bfunction\b"))
register_token_match("EndFunction", re.compile(r"^"+r"\bendfunction\b"))
register_token_match("Generate", re.compile(r"^"+r"\bgenerate\b"))
register_token_match("EndGenerate", re.compile(r"^"+r"\bendgenerate\b"))
register_token_match("Group", re.compile(r"^"+r"\bgroup\b"))
register_token_match("EndGroup", re.compile(r"^"+r"\bendgroup\b"))
register_token_match("Interface", re.compile(r"^"+r"\binterface\b"))
register_token_match("EndInterface", re.compile(r"^"+r"\bendinterface\b"))
register_token_match("Module", re.compile(r"^"+r"\bmodule\b"))
register_token_match("EndModule", re.compile(r"^"+r"\bendmodule\b"))
register_token_match("Package", re.compile(r"^"+r"\bpackage\b"))
register_token_match("EndPackage", re.compile(r"^"+r"\bendpackage\b"))
register_token_match("Program", re.compile(r"^"+r"\bprogram\b"))
register_token_match("EndProgram", re.compile(r"^"+r"\bendprogram\b"))
register_token_match("Property", re.compile(r"^"+r"\bproperty\b"))
register_token_match("EndProperty", re.compile(r"^"+r"\bendproperty\b"))
register_token_match("Task", re.compile(r"^"+r"\btask\b"))
register_token_match("EndTask", re.compile(r"^"+r"\bendtask\b"))

""" control statement """
register_token_match("If", re.compile(r"^"+r"\bif\b"))
register_token_match("Else", re.compile(r"^"+r"\belse\b"))
register_token_match("For", re.compile(r"^"+r"\bfor\b"))
register_token_match("ForEach", re.compile(r"^"+r"\bforeach\b"))
register_token_match("Do", re.compile(r"^"+r"\bdo\b"))
register_token_match("While", re.compile(r"^"+r"\bwhile\b"))
register_token_match("Break", re.compile(r"^"+r"\bbreak\b"))
register_token_match("Continue", re.compile(r"^"+r"\bcontinue\b"))
register_token_match("Return", re.compile(r"^"+r"\breturn\b"))

""" procedure statement """
register_token_match("Always", re.compile(r"^"+r"\balways\b"))
register_token_match("AlwaysComb", re.compile(r"^"+r"\balways_comb\b"))
register_token_match("AlwaysFF", re.compile(r"^"+r"\balways_ff\b"))
register_token_match("AlwaysLatch", re.compile(r"^"+r"\balways_latch\b"))
register_token_match("Initial", re.compile(r"^"+r"\binitial\b"))
register_token_match(f"Final", re.compile(r"^"+r"\bfinal\b"))
register_token_match("Repeat", re.compile(r"^"+r"\brepeat\b"))
register_token_match("Forever", re.compile(r"^"+r"\bforever\b"))
register_token_match("Fork", re.compile(r"^"+r"\bfork\b"))
register_token_match("Join", re.compile(r"^"+r"\bjoin\b"))
register_token_match("JoinAny", re.compile(r"^"+r"\bjoin_any\b"))
register_token_match("JoinNone", re.compile(r"^"+r"\bjoin_none\b"))

""" event """
register_token_match("Posedge", re.compile(r"^"+r"\bposedge\b"))
register_token_match("Negedge", re.compile(r"^"+r"\bnegedge\b"))

""" type """
register_token_match("Int", re.compile(r"^"+r"\bint\b"))
register_token_match("Integer", re.compile(r"^"+r"\binteger\b"))
register_token_match("Real", re.compile(r"^"+r"\breal\b"))
register_token_match("ShortInt", re.compile(r"^"+r"\bshortint\b"))
register_token_match("ShortReal", re.compile(r"^"+r"\bshortreal\b"))
register_token_match("LongInt", re.compile(r"^"+r"\blongint\b"))
register_token_match("Byte", re.compile(r"^"+r"\bbyte\b"))
register_token_match("String", re.compile(r"^"+r"\bstring\b"))
register_token_match("Enum", re.compile(r"^"+r"\benum\b"))
register_token_match("Struct", re.compile(r"^"+r"\bstruct\b"))
register_token_match("Union", re.compile(r"^"+r"\bunion\b"))
register_token_match("Const", re.compile(r"^"+r"\bconst\b"))
register_token_match("Signed", re.compile(r"^"+r"\bsigned\b"))
register_token_match("Unsigned", re.compile(r"^"+r"\bunsigned\b"))
register_token_match("Static", re.compile(r"^"+r"\bstatic\b"))
register_token_match("Auto", re.compile(r"^"+r"\bauto\b"))
register_token_match("Virtual", re.compile(r"^"+r"\bvirtual\b"))
register_token_match("Ref", re.compile(r"^"+r"\bref\b"))

register_token_match("Parameter", re.compile(r"^"+r"\bparameter\b"))
register_token_match("Localparam", re.compile(r"^"+r"\blocalparam\b"))
register_token_match("Input", re.compile(r"^"+r"\binput\b"))
register_token_match("Output", re.compile(r"^"+r"\boutput\b"))
register_token_match("Inout", re.compile(r"^"+r"\binout\b"))
register_token_match("Wire", re.compile(r"^"+r"\bwire\b"))
register_token_match("Reg", re.compile(r"^"+r"\breg\b"))
register_token_match("Var", re.compile(r"^"+r"\bvar\b"))
register_token_match("Logic", re.compile(r"^"+r"\blogic\b"))
register_token_match("Bit", re.compile(r"^"+r"\bbit\b"))
register_token_match("Alias", re.compile(r"^"+r"\balias\b"))
register_token_match("Assign", re.compile(r"^"+r"\bassign\b"))

""" time """
register_token_match("Second", re.compile(r"^"+r"\bs\b"))
register_token_match("MiniSecond", re.compile(r"^"+r"\bms\b"))
register_token_match("MicroSecond", re.compile(r"^"+r"\bus\b"))
register_token_match("NanoSecond", re.compile(r"^"+r"\bns\b"))
register_token_match("PicoSecond", re.compile(r"^"+r"\bps\b"))
register_token_match("FemtoSecond", re.compile(r"^"+r"\bfs\b"))

for word in reserved_words:
    if word not in implemented_reserved_word:
        register_token_match(word[0].upper()+word[1:], re.compile(r"^"+fr"\b{word}\b"))
register_token_match("Identifier", identifier_pat)
register_token_match("Dollar", re.compile(r"^"+r"\$"))
register_token_match("EOF", re.compile('\0'))

#print(f"{implemented_reserved_word}")


@dataclasses.dataclass
class Token:
    kind: str
    rdx: int
    cdx: int
    val: str
    src: str

    # def __str__(self):
    #     return f"kind: {self.kind_:<24}, rdx: {self.rdx:<5}, cdx: {self.cdx:<5}, val: {self.val}"

    def __str__(self):
        return self.src

    def __repr__(self):
        return self.__str__()

    @property
    def kind_(self) -> TokenKind:
        return TokenKind[self.kind]


class Lexer:
    def __init__(self, context: str, eol: str = '\n'):
        self.eol: str = eol
        self.context: str = context
        self.context_len: int = len(context)
        self.char_num: list[int] = self.get_char_num(context)  # char number per row
        self.accumulated_char_num: list[int] = \
            [sum(self.char_num[0:i + 1]) for i in range(len(self.char_num))]
        self.idx: int = 0
        self.tokens: list[Token] = []
        self.tokenize()

    def get_char_num(self, context: str) -> list[int]:
        lines = context.split(self.eol)
        return [len(lines[ldx]) + 1 if ldx != len(lines)-1 else len(lines[ldx]) for ldx in range(len(lines))]

    def get_rcdx_from_idx(self, idx: int) -> (int, int):
        rdx = bisect.bisect_right(self.accumulated_char_num, idx)
        if rdx != 0:
            cdx = idx - self.accumulated_char_num[rdx - 1]
        else:
            cdx = idx
        return rdx, cdx

    def tokenize(self):
        while True:
            remains = self.context[self.idx:]
            rdx, cdx = self.get_rcdx_from_idx(self.idx)
            if not remains:
                token = Token(kind="EOF", rdx=rdx, cdx=cdx, val="\0", src="\0")
                # print(f"idx: {self.idx:<5}, {token}")
                self.tokens.append(token)
                break
            matched = False
            if remains[0] == ' ' or remains[0] == '\t' or remains[0] == '\n':
                self.idx += 1
                continue
            if remains[0] == '\0':
                break
            for token_match in token_matches:
                re_pat = token_match[1]
                _ = re_pat.search(remains)
                if _ is not None and _.start() == 0:
                    token = Token(kind=token_match[0], rdx=rdx, cdx=cdx, val=_.group(0), src=_.group(0))
                    # print(f"idx: {self.idx:<5}, {token}")
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

    code = r'''"Humpty Dumpty sat on a wall. \
    Humpty Dumpty had a great fall."
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

    code = "`define"
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
