import regex as re
from enum import Enum
from typing import IO, List, Tuple, Dict


class VerilogSyntaxError(Exception):
    def __init__(self, dscrpt: str, line_idx: int = -1):
        self.line_idx = line_idx
        self.dscrpt = dscrpt
    def __str__(self):
        return repr(f"[DOTV] Error! {self.dscrpt}")

def message(msg: str):
    print("[DOTV] {msg}", end='')

def warning(msg: str):
    print("[DOTV] Warning! {msg}", end='')

def error(msg: str):
    print("[DOTV] Error! {msg}", end='')
    raise Exception("DOTV encounter error.")

def is_vld_idnty_char(char):  # valid character for verilog identity
    if char == '_' or 48 <= char <= 57 or 65 <= char <= 90 or \
            97 <= char <= 122:
        return True

def is_valid_idnty(chars: str):  # valid name for verilog identity
    for char in chars:
        if not is_vld_idnty_char(char):
            return False
    return True


def blank_split(string: str):
    return re.split(r'\s', string)


def get_module_text(vf: IO):  # vf: .v file
    module_pat = re.compile(r"module")  # pat: pattern
    endmodule_pat = re.compile(r"endmodule")
    valid_name_pat = re.compile(r"[_a-zA-Z]+[_0-9a-zA-Z]*")
    class states(Enum):
        plain  = 0
        module = 1
    state = states.plain
    modules = []
    module = []
    line_idx = 0
    start_line_idx = -1
    for line in vf:
        line_idx += 1
        collating = ""
        tokens = blank_split(line)
        for token in tokens:
            if module_pat.match(token):
                if state == states.plain:
                    state = states.module
                    module = []
                    collating = token # collated = "module"
                    start_line_idx = line_idx
                else:
                    raise VerilogSyntaxError(f"Encountering `module` at line {line_idx}. But previous module definition at"
                                             f" line {start_line_idx} has no matching `endmodule`.", line_idx)
            elif endmodule_pat.match(token):
                if state == states.module:
                    state = state.plain
                    if valid_name_pat.match(token) and not collating:
                        collating += " "
                    collating += token
                    module.append(collating)
                    modules.append(module)
                    start_line_idx = -1
                else:
                    raise VerilogSyntaxError(f"Encountering `endmodule` at line {line_idx}, but no matching `module`.",
                                             line_idx)
            else:
                if state == states.module:
                    if valid_name_pat.match(token):
                        collating += " "
                    collating += token
        if state == states.module:
            module.append(collating)
    if state == states.module:
        raise VerilogSyntaxError(f"No matching `endmodule` for module declaration at line {start_line_idx}", line_idx)
    return modules


def get_module_text_2(vf: IO) -> List[List[str]]:
    """
    :param vf: Handle for a .v file
    :return: A list of module text. One module text is a list of string, each cell stands for a row of text.
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
                    module.append(collating)
                    modules.append(module)
                else:
                    raise VerilogSyntaxError(f"Encountering `endmodule` at line {line_idx}, but no matching `module`.",
                                             line_idx)
            else:
                collating += res
                res = ""
        if state == states.module:
            module.append(collating)
    if state == states.module:
        raise VerilogSyntaxError(f"No matching `endmodule` for module declaration at line {start_line_idx}" , line_idx)
    return modules

def remove_line_comment(text: List[str]) -> List[str]:
    """
    :param text: Module definition context.
    :return: Module definition context with no comment after "//".
    Remove contents after "//" in a line.
    """
    return list(map(lambda line: re.sub("//.*$", '', line), text))

def remove_block_comment(text: List[str]) -> List[str]:
    """
    :param text: Module definition context.
    :return: Module definition context with no comment.
    Remove contents after "//" in a line or between "/*" and "*/".
    """
    left_pat = re.compile(r"/\*")
    right_pat = re.compile(r"\*/")
    class states(Enum):
        plain = 0
        left = 1
    state = states.plain
    line_idx = 0
    start_line_idx = -1
    no_block_comment = []
    for line in text:
        line_idx += 1
        collating = ""
        res = line
        while res:
            if left_pat.search(res):
                if state == states.plain:
                    state = states.left
                    start_line_idx = line_idx
                rslt = left_pat.search(res)
                collating += res[0:rslt.start()]
                res = res[rslt.start() + 2:]
            elif right_pat.search(res):
                rslt = right_pat.search(res)
                if state != states.left:
                    raise VerilogSyntaxError(f"`*/` at {line_idx} have no matching `/*`.", line_idx)
                state = state.plain
                res = res[rslt.start() + 2:]
            else:
                if state != state.left:
                    collating += res
                res = ""
        if re.sub("\s+", '', collating):
            no_block_comment.append(collating)
    return no_block_comment

def remove_comment(text: List[str]) -> List[str]:
    """
    :param text: Module definition context.
    :return: Module definition context with no comment.
    Remove contents after "//" in a line or between "/*" and "*/".
    """
    return remove_block_comment(remove_line_comment(text))

class module_info:
    def __init__(self, name: str, paras: List[str], ios: List[Tuple[str, str, str, int]]
                 , subs: List[Tuple[str, List[Tuple[str, str]]]] = []):
        self.name: str = name
        self.paras: List[str] = paras
        self.ios: List[Tuple[str, str, str, int]] = ios
        # io: name, input/output, reg/wire, width
        self.subs: List[Tuple[str, List[Tuple[str, str]]]] = subs
        # submodule name, List of io (io: inner_port_name, outter_name)

name_pat = re.compile(r"module\s*([_a-zA-Z][_0-9a-zA-Z]*)")
paras_pat = re.compile(r"#\((.*?)\)", re.DOTALL) #(?:.|\n)
ios_pat = re.compile(r"(?<!#\s*)\((.*?)\)", re.DOTALL)
def get_module_info(text: List[str]) -> module_info:
    """
    Extract module information from its text.
    :param text: text of a module definition. Must guarantee safe befor input.
    :return: information of the module.
    """
    class states(Enum):
        plain = -1
        module = 0
        name = 1
        jump = 2
        paras = 3
        ios = 4
        body = 5
        endmodule = 6
    class queue:
        def __init__(self, init_val: List[str]):
            self.contents = init_val
            self.length = len(init_val)
        def input(self, content: str):
            for i in range(0, self.length-1):
                self.contents[i] = self.contents[i+1]
            self.contents[i-1] = content
        def eq(self, contents: str):
            if len(contents) >= self.length:
                return False
            sub = self.contents[-len(contents)-1:]
            return sub == ['  '].extend(contents) \
                or sub == ['\n'].extend(contents) \
                or sub == ['\0'].extend(contents)

    name: str = ""
    paras_text = ""
    ios_text = ""
    # io: name, input/output, reg/wire, width
    subs: List[Tuple[str, List[Tuple[str, str]]]] = []
    hierarchy = 0
    chars = queue(['\0']*10)
    state = states.plain
    line_idx = 0
    # submodule name, List of io (io: inner_port_name, outter_name)
    # text = list(map(lambda line: re.sub(r"[^\S\r\n]+", ' ', line), text))
    ## text = list(map(lambda line: re.sub(r"(?<![_a-zA-Z]) | (?![_0-9a-zA-Z])", '', line), text))
    # text = list(map(lambda line: re.sub(r"(?<![_0-9a-zA-Z]) (?![_0-9a-zA-Z])", '', line), text))
    for line in text:
        line_idx += 1
        for char in line:
            chars.input(char)
            # event

            # state transform
            if state == states.plain:
                if chars.eq("module"):
                    state = states.module
            elif state == states.module:
                if is_valid_idnty(char):
                    state = states.name

            elif state == states.name:
                if char == ' ' or char == '\n':
                    state = module


            if chars.eq("module"):
                if state == states.plain:
                    state = module

            elif chars.eq("endmodule"):
                if state != states.name and state != states.body:
                    raise VerilogSyntaxError("Invalid endmodule statement.", line_idx)
                state = states.endmodule

            elif is_valid_idnty(char):
                if state == states.module:
                    state = states.name
                    name += char
                elif state == states.name
                    name += char


            elif char == ''
            elif char == '#':
                if state == states.module and hierarchy == 0:
                    state = states.paras
            elif char == '(':
                if state == states.module and hierarchy == 0:
                    state = states.ios
                hierarchy += 1
            elif char == ')':
                if (state == state.paras or state == state.ios) and hierarchy == 1:
                    state = states.module
                hierarchy -= 1
            if hierarchy < 0:
                raise  VerilogSyntaxError(f"More '(' than ')' in module context.", line_idx)
            if state == paras and char != '#' and \
                not (hierarchy == 1 and (char == '(' or char == ')')):
                    paras +=

with open("./cmp_clbrt.v", 'r', encoding="utf-8") as vf:
    modules = get_module_text_2(vf)
    a = modules[4]
    b = list(map(lambda line: re.sub(r"[^\S\r\n]+", ' ', line), a))
    for module in modules:
        for line in remove_comment(module):
            print(line, end="")
        print("\n")






