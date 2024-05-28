from typing import List

import inspect
import re
import traceback as tb


__all__ = ['Logger', 'log']


def print_green(string: str):
    print(f"\033[1;32m{string}\033[0m", end='')


def print_blue(string: str):
    print(f"\033[1;34m{string}\033[0m", end='')


def print_red(string: str):
    print(f"\033[1;31m{string}\033[0m", end='')


def print_orange(string: str):
    print(f"\033[38;5;208m{string}\033[0m", end='')


_nl = re.compile("\n(?!$)")


class Logger:
    disable_verbose_info = True
    disable_hint = False
    disable_info = False
    disable_warning = False
    traceback = False

    def __init__(self, name: str):
        self.name = name
        self.msgs: List[str] = []

    def verbose_info(self, msg: str):
        if not self.disable_verbose_info:
            msg = re.sub(_nl, f"\n{' ' * (len(self.name) + 3)}", msg)
            print(f"[{self.name}] {msg}", end='')
            self.msgs.append(f"[{self.name}] {msg}")

    def info(self, msg: str):
        if not self.disable_info:
            msg = re.sub(_nl, f"\n{' ' * (len(self.name) + 3)}", msg)
            print(f"[{self.name}] {msg}", end='')
            self.msgs.append(f"[{self.name}] {msg}")

    def hint(self, msg: str):
        if not self.disable_hint:
            msg = re.sub(_nl, f"\n{' ' * (len(self.name) + 3)}", msg)
            print_green(f"[{self.name}] hint! {msg}")
            self.msgs.append(f"[{self.name}] hint! {msg}")

    def warning_begin(self):
        if not self.disable_warning:
            print_blue(f"====================\n")
            self.msgs.append(f"====================\n")

    def warning_end(self):
        if not self.disable_warning:
            print_blue(f"^^^^^^^^^^^^^^^^^^^^\n")
            self.msgs.append(f"^^^^^^^^^^^^^^^^^^^^\n")

    def warning(self, msg: str, begin: bool = False, end: bool = False):
        msg += f"reported by {get_caller_location_str(0)}\n"
        if not self.disable_warning:
            if begin:
                self.warning_begin()
            msg = re.sub(_nl, f"\n{' ' * (len(self.name) + 3)}", msg)
            print_blue(f"[{self.name}] warning! {msg}")
            self.msgs.append(f"[{self.name}] warning! {msg}")
            if self.traceback:
                tb.print_stack()
            if end:
                self.warning_end()

    def error_begin(self):
        print_red(f"====================\n")
        self.msgs.append(f"====================\n")

    def error_end(self):
        print_red(f"^^^^^^^^^^^^^^^^^^^^\n")
        self.msgs.append(f"^^^^^^^^^^^^^^^^^^^^\n")

    def error(self, msg: str, begin=False, end=False):
        msg += f"reported by {get_caller_location_str(0)}\n"
        if begin:
            self.error_begin()
        msg = re.sub(_nl, f"\n{' ' * (len(self.name) + 3)}", msg)
        self.msgs.append(f"[{self.name}] error! {msg}")
        print_red(f"[{self.name}] error! {msg}")
        if self.traceback:
            tb.print_stack()
        if end:
            self.error_end()

    def fatal_begin(self):
        print_orange(f"====================\n")
        self.msgs.append(f"====================\n")

    def fatal_end(self):
        print_orange(f"^^^^^^^^^^^^^^^^^^^^\n")
        self.msgs.append(f"^^^^^^^^^^^^^^^^^^^^\n")

    def fatal(self, msg: str, exceptionType = None, begin = False, end = False):
        msg += f"reported by {get_caller_location_str(0)}\n"
        if begin:
            self.fatal_begin()
        msg = re.sub(_nl, f"\n{' ' * (len(self.name) + 3)}", msg)
        print_orange(f"[{self.name}] fatal! {msg}")
        self.msgs.append(f"[{self.name}] fatal! {msg}")
        if end:
            self.fatal_end()
        if exceptionType is not None:
            raise exceptionType(msg)

    def indented_info(self, indent: int, msg: str):
        if not self.disable_info:
            msg = re.sub(_nl, f"\n{' ' * (len(self.name) + 3)}", msg)
            print(f"{' ' * indent}{msg}")
            self.msgs.append(f"{' ' * indent}{msg}")

    def list_info(self, title: str, contents: List[str]):
        if not self.disable_info:
            if contents:
                title = f"[{self.name}] {title}:"
                print(f"{title}")
                self.msgs.append(f"{title}\n")
                for i in range(0, len(contents)):
                    print(f"            {contents[i]}")
                    self.msgs.append(f"            {contents[i]}\n")

    def list_warning(self, title: str, contents: List[str]):
        if not self.disable_warning:
            if contents:
                title = f"[{self.name}] warning! {title}:\n"
                print_blue(f"{title}")
                self.msgs.append(f"{title}\n")
                for i in range(0, len(contents)):
                    print_blue(f"            {contents[i]}")
                    self.msgs.append(f"            {contents[i]}\n")

    def list_error(self, title: str, contents: List[str]):
        if contents:
            title = f"[{self.name}] error! {title}:\n"
            print_red(f"{title}")
            self.msgs.append(f"{title}\n")
            for i in range(0, len(contents)):
                print_red(f"            {contents[i]}")
                self.msgs.append(f"            {contents[i]}\n")

    def list_fatal(self, title: str, contents: List[str]):
        if contents:
            title = f"[{self.name}] {title}:\n"
            print_orange(f"{title}")
            self.msgs.append(f"{title}\n")
            for i in range(0, len(contents)):
                print_orange(f"            {contents[i]}")
                self.msgs.append(f"            {contents[i]}\n")


def find_caller_frameinfo(frame, depth: int):
    if depth == 0:
        return inspect.getframeinfo(frame)
    nxt = frame.f_back
    if nxt is None:
        return inspect.getframeinfo(frame)
    # If the frame is not in user's script, continue tracing back
    return find_caller_frameinfo(nxt, depth - 1)


def find_caller_location(depth: int):
    frame = inspect.currentframe().f_back
    caller_frame = find_caller_frameinfo(frame, depth+1)
    return caller_frame.filename, caller_frame.lineno


def get_caller_location_str(depth: int):
    filename, lineno = find_caller_location(depth+1)
    return f"file: {filename}:{lineno}"


log = Logger("dotv")
