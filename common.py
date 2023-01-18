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

def is_first_vld_idnty_char(char):
    print(f"{char}")
    char = ord(char)
    if char == '_' or 65 <= char <= 90 or \
            97 <= char <= 122:
        return True
    else:
        return False

def is_vld_idnty_char(char):  # valid character for verilog identity
    char = ord(char)
    if char == '_' or 48 <= char <= 57 or 65 <= char <= 90 or \
            97 <= char <= 122:
        return True
    else:
        return False

def is_valid_idnty(chars: str):  # valid name for verilog identity
    if not chars:
        return False
    elif not is_first_vld_idnty_char(chars[0]):
        return False
    for char in chars:
        if not is_vld_idnty_char(char):
            return False
    return True

def blank_split(string: str):
    return re.split(r'\s', string)

def remove_line_comment(text: List[str]) -> List[str]:
    """
    :param text: verilog code.
    :return: verilog code with no comment following "//".
    Remove contents after "//" in a line.
    """
    return list(map(lambda line: re.sub("//.*$", '', line), text))

def remove_block_comment(text: List[str]) -> List[str]:
    """
    :param text: verilog code
    :return: verilog code with no block comment.
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


