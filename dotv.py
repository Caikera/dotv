import regex as re
from enum import Enum
from typing import IO, List, Tuple, Dict
from common import *

def get_module_text(vf: IO) -> List[List[str]]:
    """
    :param vf: Handle for a .v file
    :return: A list of module text. One module text is a list of string, each cell stands for a row of text ending with
     '\n'.
    Analyze .v file, separetely output text for each module.
    """
    class states(Enum):
        plain  = 0
        module = 1
    module_pat = re.compile("(?:\s+|^)module(.*\n?)$")
    endmodule_pat = re.compile("(.*?endmodule)(.*\n?)$")
    state = states.plain
    modules = []
    module = []
    line_idx = 0
    start_line_idx = -1
    for line in vf:
        line_idx += 1
        collating = ""
        res = line # collating + res = line[blank before first char not blank is not essential: end]
        while res:
            if module_pat.match(res):
                if state == states.plain:
                    start_line_idx = line_idx
                    state = states.module
                    cap = module_pat.match(res)
                    module = []
                    collating = "module"
                    res = cap.group(1)
                else:
                    raise VerilogSyntaxError(f"Encountering `module` at line {line_idx}. But previous module definition at"
                                             f" line {start_line_idx} has no matching `endmodule`.", line_idx)
            elif endmodule_pat.match(res):
                if state == states.module:
                    start_line_idx = -1
                    state = states.plain
                    cap = endmodule_pat.match(res)
                    collating += cap.group(1)
                    res = cap.group(2)
                    if collating[-1:] != '\n':
                        collating += '\n'
                    module.append(collating)
                    modules.append(module)
                else:
                    raise VerilogSyntaxError(f"Encountering \"endmodule\" at line {line_idx}, but no matching \"module\".",
                                             line_idx)
            else:
                collating += res
                res = ""
        if state == states.module:
            if collating[-1:] != '\n':
                collating += '\n'
            module.append(collating)
    if state == states.module:
        raise VerilogSyntaxError(f"No matching \"endmodule\" for module declaration at line {start_line_idx}" , line_idx)
    return modules

def get_module_text_v2(vf: IO) -> List[List[str]]:
    """
    :param vf: Handle for a .v file
    :return: A list of module text. One module text is a list of string, each cell stands for a row of text ending with
     '\n'.
    Analyze .v file, separetely output text for each module.
    """
    class char_queue:
        def __init__(self, len: int):
            self.chars: str = ' ' * len
        def input(self, char: str):
            self.chars = f"{self.chars[1:]}{char}"
        def plain_eq(self, other: str):
            if re.search(re.escape(other) + r'$', self.chars):
                return True
            else:
                return False
        def identity_eq(self, other: str):
            if re.search(r'[^_0-9a-zA-Z]' + re.escape(other) + r'[^_0-9a-zA-Z]$', self.chars):
                return True
            else:
                return False
    chars = char_queue(11)  # not shorter than " endmodule "
    class states(Enum):
        bdef = 0
        body = 1

    next_state = states.bdef
    state = states.bdef
    bcmt = False
    lcmt = False
    module : List[str] = []
    modules : List[List[str]] = []
    line_idx = 0
    for line in vf:
        line_idx += 1
        line = line + '\n' if not line or line[-1] != '\n' else line
        collating = ""
        for char in line:
            chars.input(char)
            if state == states.bdef:
                if chars.identity_eq("module") and not (bcmt or lcmt):
                    module = []
                    next_state = states.body
                    collating += f"module{char}"
            elif state == states.body:
                collating += char
                if chars.identity_eq("endmodule") and not (bcmt or lcmt):
                    next_state = states.bdef
                    if collating[-1] != '\n':
                        collating = collating[:-1] + '\n'
                    module.append(collating)
                    collating = ""
                    modules.append(module)
            state = next_state
            if state == states.body and collating and collating[-1] == '\n':
                module.append(collating)

            if chars.plain_eq('//') and not bcmt:
                lcmt = True
            elif char == '\n':
                if lcmt:
                    lcmt = False
            elif chars.plain_eq('/*') and not lcmt:
                bcmt = True
            elif chars.plain_eq('*/') and not lcmt:
                if not bcmt:
                    raise VerilogSyntaxError("Encountering \"/*\" with no matching \"*/\".", line_idx)
                bcmt = False
    return modules

def get_module_info(module: List[str]):
    class char_queue:
        def __init__(self, len: int):
            self.chars: str = ' '*len
        def input(self, char: str):
            self.chars = f"{self.chars[1:]}{char}"
        def plain_eq(self, other: str):
            if re.search(re.escape(other)+r'$', self.chars):
                return True
            else:
                return False
        def identity_eq(self, other: str):
            if re.search(r'[^_0-9a-zA-Z]'+re.escape(other)+r'[^_0-9a-zA-Z]$', self.chars):
                return True
            else:
                return False
    chars = char_queue(11) # not shorter than " endmodule "
    class states(Enum):
        bdef = 0  # before "module"
        bnme = 1  # after  "module" before {module_name}
        name = 2  # after  the first character of name
        anme = 3  # after  {module_name} out of comment on bnme
        pjin = 4  # after  '#' out of comment on bnme
        para = 5  # after  '(' out of comment on pjin
        ioss = 6  # after  '(' out of comment on anme
        body = 7  # after  ';' out of comment on anme
        endd = 8  # after  "endmodule" out of comment on body
    state = states.bdef
    next_state = states.bdef
    hierarchy = 0
    bcmt = False
    lcmt = False
    line_idx = 0
    name = ""
    paras: List[str] = []
    ios: List[str] = []
    body: List[str] = []
    for line in module:
        line_idx += 1
        for char in line:
            chars.input(char)
            next_state = state
            # state events
            if state == states.bdef:
                if chars.identity_eq("module") and not (bcmt or lcmt):
                    name_flag  = False
                    next_state = states.bnme
            elif state == states.bnme:
                if is_first_vld_idnty_char(char) and not (bcmt or lcmt):
                    next_state = states.name
                    name += char
            elif state == states.name:
                if is_vld_idnty_char(char) and not (bcmt or lcmt):
                    name += char
                else:
                    next_state = states.anme
            elif state == states.anme:
                if char == '#' and not (bcmt or lcmt):
                    next_state = states.pjin
                if char == '(' and hierarchy == 0 and not (bcmt or lcmt):
                    next_state = states.ioss
                    ios.append("")
                    wtsc = False
            elif state == states.pjin:
                if char == '(' and hierarchy == 0 and not (bcmt or lcmt):
                    next_state = states.para
                    paras.append("")
            elif state == states.para:
                if char == ')' and hierarchy == 1 and not (bcmt or lcmt):
                    next_state = states.anme
                else:
                    paras[-1] += char
                    if char == '\n':
                        paras.append("")
            elif state == states.ioss:
                if char == ')' and hierarchy == 1 and not (bcmt or lcmt):
                    wtsc = True  ## wait for semicolon ';'
                elif wtsc and char == ';' and not (bcmt or lcmt):
                    next_state = states.body
                    body.append("")
                else:
                    ios[-1] += char
                    if char == '\n':
                        ios.append("")
            elif state == states.body:
                if chars.identity_eq("endmodule") and not (bcmt or lcmt):
                    next_state = states.endd
                body[-1] += char
                if char == '\n':
                    body.append("")
            # handle hierarchy
            if char == '(' and not (bcmt or lcmt):
                hierarchy += 1
            elif char == ')' and not (bcmt or lcmt):
                    hierarchy -= 1
            # handle comment
            if chars.plain_eq('//') and not bcmt:
                lcmt = True
            elif char == '\n':
                if lcmt:
                    lcmt = False
            elif chars.plain_eq('/*') and not lcmt:
                bcmt = True
            elif chars.plain_eq('*/') and not lcmt:
                if not bcmt:
                    raise VerilogSyntaxError("Encountering \"/*\" with no matching \"*/\".", line_idx)
                bcmt = False
            state = next_state
    if paras and not paras[-1]:
        del(paras[-1])
    if ios and not ios[-1]:
        del(ios[-1])
    if body and not body[-1]:
        del(body[-1])
    if body:
        body[-1] = body[-1][:-10]
    if body and not body[-1]:
        del(body[-1])
    return name, paras, ios, body


class module_info:
    def __init__(self, name: str, paras: List[str], ios: List[Tuple[str, str, str, int]]
                 , subs: List[Tuple[str, List[Tuple[str, str]]]] = []):
        self.name: str = name
        self.paras: List[str] = paras
        self.ios: List[Tuple[str, str, str, int]] = ios
        # io: name, input/output, reg/wire, width
        self.subs: List[Tuple[str, List[Tuple[str, str]]]] = subs
        # submodule name, List of io (io: inner_port_name, outter_name)

#name_pat = re.compile(r"module\s*([_a-zA-Z][_0-9a-zA-Z]*)")
#paras_pat = re.compile(r"#\((.*?)\)", re.DOTALL) #(?:.|\n)
#ios_pat = re.compile(r"(?<!#\s*)\((.*?)\)", re.DOTALL)

with open("./cmp_clbrt.v", 'r', encoding="utf-8") as vf:
    modules = get_module_text_v2(vf)
    #a = modules[4]
    #b = list(map(lambda line: re.sub(r"[^\S\r\n]+", ' ', line), a))
    for module in modules:
        (name, paras, ios, body) = get_module_info(module)
        print(f"module info:")
        print(f"    name: {name}")
        print(f"    paras:")
        for line in paras:
            print(f"        {line}", end='')
        print(f"    ios:")
        for line in ios:
            print(f"        {line}", end='')
        print(f"    body:")
        for line in body:
            print(f"        {line}", end='')
