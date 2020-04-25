from typing import Union, Any, Match, Callable, List, Dict, Iterator
from copy import deepcopy


class ProgramState:
    def __init__(self, regs: List[int]):
        self.registers: List[int] = regs

    def __str__(self) -> str:
        return "{}({})". \
            format(type(self).__name__, self.registers)

    def __repr__(self) -> str:
        return self.__str__()


# regToID:: str -> int
def regToID(name: str) -> int:
    name = name.upper()
    if name[0] == "R":
        return int(name[1:3])
    elif name == "SP":
        return 13
    elif name == "LR":
        return 14
    elif name == "PC":
        return 15
    else:
        # The name of the register can't be unknown because it then would not be recognized as such
        return -1


# setReg:: ProgramState -> str -> int -> ProgramState
def setReg(state: ProgramState, name: str, value: int) -> ProgramState:
    newState = deepcopy(state)
    regID = regToID(name)
    newState.registers[regID] = value
    return newState


# setReg:: ProgramState -> str -> int
def getReg(state: ProgramState, name: str) -> int:
    regID: int = regToID(name)
    return state.registers[regID]


# getFromMem:: ProgramState -> int -> int -> int
# bitSize: the number ob bits to load, either 32, 16 or 8 bit
def getFromMem(state: ProgramState, adress: int, bitsize: int) -> int:
    # TODO implement memory
    return -1


# getLabelAddress:: ProgramState -> str -> int
def getLabelAddress(state: ProgramState, label: str) -> int:
    # TODO implement memory
    return -1
