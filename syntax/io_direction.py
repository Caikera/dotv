from enum import auto, Enum


class IODirection(Enum):
    Input = auto()
    Output = auto()
    Inout = auto()