from typing import Union, Any, Match, Callable, List
import re

import tokens
from high_order import foldL

INSTRUCTIONS = ["MOV", "LDR", "LDRH", "LDRB", "STR", "STRRH", "STRB", "LDRSH", "LDRSB",
                "PUSH", "POP", "LDM", "LDMIA", "STMIA",
                "ADD", "ADC", "SUB", "SBC", "MUL",
                "AND", "EOR", "ORR", "BIC", "MOVN",
                "LSL", "LSR", "ASR", "ROR",
                "SXTH", "SXTB", "UXTH", "UXTB",
                "TST", "CMP", "CMN",
                "REV", "REV16", "REVSH",
                "B", "BX", "BL", "BLX",
                "BCC", "BCS", "BEQ", "BGE", "BGT", "BHI", "BLE", "BLS", "BLT", "BMI", "BNE", "BPL", "BVC", "BVS"]

R_INSTRUCTION = r"(?P<INSTRUCTION>" + \
                foldL(lambda text, instr: text + "|" + instr+"", INSTRUCTIONS[0], INSTRUCTIONS[1:]) + \
                ")|"

# ^[^\d\W] matches a character that is a letter or a underscore at the start of the string
# \w*\Z matches a letter, a number or a underscore at the rest of the string
# https://stackoverflow.com/questions/5474008/regular-expression-to-confirm-whether-a-string-is-a-valid-identifier-in-python
R_LABEL = r"[^\d\W]\w*"

TOKEN_REGEX = re.compile(R_INSTRUCTION +
                         r"(?P<REGISTER>SP|LR|PC|r1[0-2]|r[0-9])|"
                         r"(?P<LD_LABEL>=[ \t]*(" + R_LABEL + "))|"
                         r"(?P<LABEL>" + R_LABEL + ")|"
                         r"(?P<IMMED_VALUE>"
                         r"#[ \t]*0x[0-9a-f]*|#[ \t]*0b[01]*|#[ \t]*'((\\[tnrfv])|(.))'?|#[ \t]*[0-9]*)|"
                         r"(?P<LD_IMMED_VALUE>"
                         r"=[ \t]*0x[0-9a-f]*|=[ \t]*0b[01]*|=[ \t]*'((\\[tnrfv])|(.))'?|=[ \t]*[0-9]*)|"
                         r"(?P<ALIGN>\.align[ \t]*[1248])|"
                         r"(?P<ASCII_ASCIZ>\.ascii|\.asciz)|"
                         r"(?P<SECTION>\.text|\.bss|\.data)|"
                         r"(?P<CPU>\.cpu[^\n]*)|"
                         r"(?P<GLOBAL>\.global)|"
                         r"(?P<SEPARATOR>[,:\[\]{}])|"
                         r"(?P<SINGELINECOMMENT>;[^\n]*|//[^\n]*)|"
                         r"(?P<MULTILINECOMMENT>/\*.*?\*/)|"
                         r"(?P<STRINGLITERAL>\".*?\")|"
                         r"(?P<IGNORE>[ \t]+)|"
                         r"(?P<NEWLINE>\n)|"
                         r"(?P<MISMATCH>[^\n]+)", re.DOTALL+re.ASCII+re.IGNORECASE)


# lastIndex:: String -> String -> int
# Get the index to the last occurrence of search in string
def lastIndex(string: str, search: str) -> int:
    if len(string) < len(search):
        return -1
    if string[len(string)-len(search):] == search:
        return len(string)-len(search)
    else:
        return lastIndex(string[:-1], search)


# match_to_token:: Match -> String -> int -> Token | None
def match_to_token(match: Match[Union[str, Any]], file_contents: str, offset: int) -> Union[tokens.Token, None]:
    kind: str = match.lastgroup
    value: str = match.group()

    func: Callable[[str, int, int, int], tokens.Token] = tokens.tokenConstructors[kind]
    if func is None:
        return None

    processed: str = file_contents[:match.start()+offset]
    line = processed.count('\n') + 1
    if line > 1:
        lastNewLine = lastIndex(processed, '\n')
    else:
        lastNewLine = 0
    token = func(value, match.start()+offset, line, match.start()+offset-lastNewLine, match.end()+offset-lastNewLine)
    return token


def lexFrom(file_contents: str, indexFrom: int) -> List[tokens.Token]:
    matches = TOKEN_REGEX.finditer(file_contents[indexFrom:])
    tokenList = list(filter(lambda x: x is not None,
                            map(lambda a: match_to_token(a, file_contents, indexFrom), matches)))
    return tokenList


def lexFile(file_contents: str) -> List[tokens.Token]:
    return lexFrom(file_contents, 0)


def fixMismatches(tokenList: List[tokens.Token], file_contents: str) -> List[tokens.Token]:
    if len(tokenList) == 0:
        return []
    head, *tail = tokenList
    head: tokens.Token = head
    if isinstance(head, tokens.Error):
        return [head] + fixMismatches(tail, file_contents)
    if head.is_mismatch:
        idx: int = head.start_index
        text: str = head.contents
        # error: tokens.Token = None

        if text[0] == '"':
            error: tokens.Token = \
                tokens.Error(f"\033[31m"  # red color
                             f"File \"$fileName$\"\n"
                             f"\tSyntax warning: Unterminated string at end of file, '\"' inserted"
                             f"\033[0m", tokens.Error.ErrorType.Warning)
            file_contents = file_contents + "\""
        elif text[0:2] == '/*':
            error: tokens.Token = \
                tokens.Error(f"\033[31m"  # red color
                             f"File \"$fileName$\"\n"
                             f"\tSyntax warning: Multi-line comment opened, but not closed (*/ is missing)"
                             f"\033[0m", tokens.Error.ErrorType.Warning)
            file_contents = file_contents + "*/"
        else:
            error: tokens.Token = \
                tokens.Error(f"\033[31m"  # red color
                             f"File \"$fileName$\", line {head.line}\n"
                             f"\tUnknown token: {text[0]}"
                             f"\033[0m", tokens.Error.ErrorType.Error)
            return [error] + fixMismatches(tail, file_contents)

        newTokens = lexFrom(file_contents, idx)
        if error is not None:
            return [error] + fixMismatches(newTokens, file_contents)
        else:
            return fixMismatches(newTokens, file_contents)
    else:
        return [head] + fixMismatches(tail, file_contents)
